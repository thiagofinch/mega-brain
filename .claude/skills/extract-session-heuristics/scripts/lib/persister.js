/**
 * persister — Phase 5 PERSIST for extract-session-heuristics runner.
 *
 * Given validated heuristic files + decision cards, atomically:
 *   1. Verify all L3 files exist and passed compliance gate
 *   2. Append L2 cards to decision-cards.yaml
 *   3. Report summary
 *
 * The actual L3 .md file writes happen BEFORE persist — the runner writes them
 * as part of the Phase 4 FORMALIZE stage. Persist just wires them up in the
 * decision-cards.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { appendCardsToDecisionCards } = require('./yaml-io');
const { validateBatch } = require('./compliance-gate');

/**
 * Persist a batch of validated heuristics.
 *
 * @param {Object} params
 * @param {string} params.decisionCardsPath  Path to decision-cards.yaml
 * @param {string[]} params.heuristicFilePaths  Absolute paths to the L3 .md files already written
 * @param {Object[]} params.newCards  L2 card objects to append to decision-cards.yaml
 *
 * @returns {Object}  { success, validation, appended, refreshed, errors }
 */
function persistBatch(params) {
  const {
    decisionCardsPath,
    heuristicFilePaths,
    newCards,
  } = params;

  const errors = [];

  // Step 1 — validate all files against Phase 4.5 compliance gate
  if (!heuristicFilePaths || heuristicFilePaths.length === 0) {
    return {
      success: false,
      error: 'No heuristic files provided',
      validation: null,
      appended: false,
      refreshed: false,
    };
  }

  const validation = validateBatch(heuristicFilePaths);
  if (!validation.all_passing) {
    return {
      success: false,
      error: `${validation.blocked + validation.incomplete} files failed compliance gate`,
      validation,
      appended: false,
      refreshed: false,
    };
  }

  // Step 2 — sanity: card count must match file count
  if (!Array.isArray(newCards) || newCards.length !== heuristicFilePaths.length) {
    return {
      success: false,
      error: `Card count (${newCards?.length ?? 0}) != file count (${heuristicFilePaths.length})`,
      validation,
      appended: false,
      refreshed: false,
    };
  }

  // Step 3 — append to decision-cards.yaml atomically
  try {
    appendCardsToDecisionCards(decisionCardsPath, newCards);
  } catch (err) {
    return {
      success: false,
      error: `decision-cards append failed: ${err.message}`,
      validation,
      appended: false,
      refreshed: false,
    };
  }

  return {
    success: true,
    validation,
    appended: true,
    appended_count: newCards.length,
    refreshed: false,
    errors,
  };
}

/**
 * Dry-run persist — validates everything but doesn't write anything.
 * Useful for Phase 4.5 gate check before committing to persist.
 */
function dryRunPersist(params) {
  const { heuristicFilePaths, newCards } = params;

  if (!heuristicFilePaths || heuristicFilePaths.length === 0) {
    return { ok: false, error: 'No heuristic files provided' };
  }

  const validation = validateBatch(heuristicFilePaths);

  if (!Array.isArray(newCards) || newCards.length !== heuristicFilePaths.length) {
    return {
      ok: false,
      error: `Card count (${newCards?.length ?? 0}) != file count (${heuristicFilePaths.length})`,
      validation,
    };
  }

  return {
    ok: validation.all_passing,
    validation,
    would_append: newCards.length,
  };
}

module.exports = {
  persistBatch,
  dryRunPersist,
};
