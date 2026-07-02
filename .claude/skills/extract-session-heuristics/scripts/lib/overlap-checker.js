/**
 * overlap-checker — detect duplicates or near-duplicates against decision-cards.yaml.
 *
 * Used in Phase 3 (OVERLAP) of extract-session-heuristics pipeline.
 * Given a candidate (keywords + draft rule), returns ranked matches from existing cards.
 *
 * Strategy:
 *   1. Normalize candidate keywords (lowercase, strip punctuation)
 *   2. For each existing card: tokenize name + rule + trigger + evidence
 *   3. Compute Jaccard similarity against candidate tokens
 *   4. Also flag exact substring hits on the rule SE/ENTÃO fragment
 *   5. Return top N matches above threshold
 */

'use strict';

const { readDecisionCards } = require('./yaml-io');

// Jaccard thresholds are low because candidate keyword lists are short (3-8 tokens)
// while existing cards have rich text (20-50 tokens). Even "meaningful overlap"
// rarely exceeds 0.2. Calibrated empirically against 150+ existing KA_KE cards.
const DEFAULT_THRESHOLD = 0.05;
const DEFAULT_TOP_N = 5;

function tokenize(text) {
  if (!text) return new Set();
  return new Set(
    text
      .toLowerCase()
      .replace(/[^a-z0-9áéíóúâêôãõç\s]/gi, ' ')
      .split(/\s+/)
      .filter(w => w.length >= 3)
  );
}

function jaccard(setA, setB) {
  if (setA.size === 0 || setB.size === 0) return 0;
  const intersection = [...setA].filter(x => setB.has(x)).length;
  const union = new Set([...setA, ...setB]).size;
  return intersection / union;
}

/**
 * Score a single card against candidate keywords.
 * Returns { score, matches, reason }.
 */
function scoreCard(card, candidateTokens, candidateRuleFragment) {
  const cardText = [
    card.name || '',
    card.rule || '',
    card.trigger || '',
    card.anti_pattern || '',
  ].join(' ');
  const cardTokens = tokenize(cardText);

  const jaccardScore = jaccard(candidateTokens, cardTokens);

  // Exact substring bonus — if the candidate rule fragment appears in the existing card
  let substringBonus = 0;
  if (candidateRuleFragment && card.rule) {
    const frag = candidateRuleFragment.toLowerCase().trim();
    if (frag.length > 10 && card.rule.toLowerCase().includes(frag)) {
      substringBonus = 0.3;
    }
  }

  return {
    id: card.id,
    name: card.name,
    score: jaccardScore + substringBonus,
    jaccard: jaccardScore,
    substring_bonus: substringBonus,
  };
}

/**
 * Check a candidate heuristic against existing decision-cards.
 * candidate = { keywords: string[] | string, rule_fragment?: string }
 * Returns { topMatches, anyAboveThreshold, totalCards }.
 */
function checkOverlap(decisionCardsPath, candidate, opts = {}) {
  const threshold = opts.threshold ?? DEFAULT_THRESHOLD;
  const topN = opts.topN ?? DEFAULT_TOP_N;

  const data = readDecisionCards(decisionCardsPath);
  const cards = data.cards || [];

  const keywordsText = Array.isArray(candidate.keywords)
    ? candidate.keywords.join(' ')
    : (candidate.keywords || '');
  const candidateTokens = tokenize(keywordsText);

  if (candidateTokens.size === 0) {
    return {
      topMatches: [],
      anyAboveThreshold: false,
      totalCards: cards.length,
      warning: 'No valid candidate keywords (all too short or missing)',
    };
  }

  const scored = cards
    .map(card => scoreCard(card, candidateTokens, candidate.rule_fragment))
    .filter(m => m.score >= threshold)
    .sort((a, b) => b.score - a.score)
    .slice(0, topN);

  return {
    topMatches: scored,
    anyAboveThreshold: scored.length > 0,
    totalCards: cards.length,
  };
}

module.exports = {
  tokenize,
  jaccard,
  scoreCard,
  checkOverlap,
  DEFAULT_THRESHOLD,
  DEFAULT_TOP_N,
};
