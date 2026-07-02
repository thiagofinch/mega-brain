#!/usr/bin/env node
/**
 * classify-loop-node.js — STORY-LC-4 / ADR-LC-004.
 *
 * DETERMINISTIC loop-signature classifier. Replaces the stochastic prose decision in dag-architect:
 * given a DAG node, decides single | loop | ambiguous by a transparent weighted scorer (no LLM, no
 * randomness). Protects BOTH directions (catches real loops; rejects one-shots typed as loop).
 *
 * API:   classifyLoopNode(node) -> { kind: 'single'|'loop'|'ambiguous', score, signals[], confidence }
 * CLI:   node classify-loop-node.js --annotate <plan.json> [--out <file>]   # annotate a plan in place
 *        node classify-loop-node.js --self-test
 *
 * Annotate semantics (AC4): high-confidence loop -> set execution_kind:loop (+ minimal loop_hint if absent);
 * high-confidence single -> leave as-is; AMBIGUOUS -> NEVER auto-type; set loop_candidate:true so the human /
 * validate-plan Class-C gate reviews it. Deterministic. Zero deps beyond js-yaml (only for --annotate of .yaml).
 */
'use strict';

// Transparent signal lexicons (hand-set weights; tunable via telemetry per ADR-LC-004 open question 3).
const LOOP_VERBS = /\b(discover|enumerate|audit|sweep|scan|harvest|find all|verify each|check each|collect all|review all|surface all)\b/;
const COVERAGE = /\b(all|every|each|until|no more|exhaustive|remaining|as many|unknown number|however many)\b/;
const ONESHOT = /\b(draft|write|create|generate|produce|compose|send|deploy|publish|render|summarize|a single|exactly one|one-shot)\b/;

const THRESHOLD_HIGH = 4; // >= HIGH -> loop
const THRESHOLD_LOW = 1;  // <= LOW  -> single ; strictly between -> ambiguous

/** Pure deterministic classifier. */
function classifyLoopNode(node) {
  const n = node || {};
  const h = n.loop_hint || {};
  const text = `${n.task || ''} ${n.label || ''} ${h.task || ''}`.toLowerCase();
  let score = 0;
  const signals = [];
  const add = (pts, sig) => { score += pts; signals.push(sig); };

  if (LOOP_VERBS.test(text)) add(3, 'loop-verb');
  if (COVERAGE.test(text)) add(2, 'uncertain-coverage');
  if (/\buntil\b/.test(text)) add(1, 'until-shape');
  if (h.verification === 'critical') add(1, 'verification-critical');
  if (h.parallelizable === 'yes' || h.parallelizable === 'partial') add(1, 'parallelizable');
  if (h.termination_hint === 'until-dry' || h.termination_hint === 'until-budget') add(2, 'iterative-termination');
  // Negative: a one-shot verb with NO loop verb is a single deliverable.
  if (ONESHOT.test(text) && !LOOP_VERBS.test(text)) add(-2, 'one-shot-verb');

  let kind, confidence;
  if (score >= THRESHOLD_HIGH) { kind = 'loop'; confidence = 'high'; }
  else if (score <= THRESHOLD_LOW) { kind = 'single'; confidence = 'high'; }
  else { kind = 'ambiguous'; confidence = 'low'; }
  return { kind, score, signals, confidence };
}

/** Annotate a plan's DAG nodes (AC4 semantics). Returns { plan, report[] }. Deterministic. */
function annotatePlan(plan) {
  const nodes = (plan && plan.dag && plan.dag.nodes) || [];
  const report = [];
  for (const node of nodes) {
    delete node.loop_candidate; // reset stale flag — annotate is idempotent across re-classification.
    const c = classifyLoopNode(node);
    report.push({ id: node.id, ...c });
    if (c.kind === 'loop') {
      node.execution_kind = 'loop';
      if (!node.loop_hint) {
        node.loop_hint = { task: node.label || node.task || node.id, termination_hint: 'until-dry' };
      }
    } else if (c.kind === 'ambiguous') {
      // NEVER auto-type/route ambiguous as loop (AC4). A node previously typed loop is downgraded so it is
      // not silently routed; the loop_candidate flag sends it to the Class-C human / validate-plan review.
      if (node.execution_kind === 'loop') delete node.execution_kind;
      node.loop_candidate = true;
    } else if (c.kind === 'single') {
      // Hardening: a high-confidence single must CLEAR a stale auto-annotated execution_kind:loop, else a
      // reclassified node keeps routing to loop-compiler. Respect an explicit human typing (human_typed: true).
      if (node.execution_kind === 'loop' && node.human_typed !== true) delete node.execution_kind;
    }
  }
  return { plan, report };
}

function selfTest() {
  const cases = [
    ['loop-shaped (discover+until) -> loop', { id: 'A', label: 'Discover and verify all risk clauses until no more remain', loop_hint: { verification: 'critical', parallelizable: 'yes', termination_hint: 'until-dry' } }, 'loop'],
    ['audit all -> loop', { id: 'B', label: 'Audit every supplier contract for missing clauses' }, 'loop'],
    ['one-shot draft -> single', { id: 'C', label: 'Draft a single launch announcement post' }, 'single'],
    ['deploy -> single', { id: 'D', label: 'Deploy the gateway service to staging' }, 'single'],
    ['no signal -> safe-default single', { id: 'E0', label: 'Review the quarterly document' }, 'single'],
    ['partial signal (coverage only) -> ambiguous', { id: 'E', label: 'Process all the records' }, 'ambiguous'],
    ['determinism: same node twice', { id: 'F', label: 'Enumerate all edge cases', loop_hint: { termination_hint: 'until-dry' } }, 'loop'],
  ];
  let pass = 0;
  for (const [name, node, expect] of cases) {
    const r = classifyLoopNode(node);
    const ok = r.kind === expect;
    console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ` (expected ${expect}, got ${r.kind} score=${r.score} ${JSON.stringify(r.signals)})`}`);
    if (ok) pass++;
  }
  // determinism check: classify F twice, identical output
  const a = JSON.stringify(classifyLoopNode({ id: 'F', label: 'Enumerate all edge cases', loop_hint: { termination_hint: 'until-dry' } }));
  const b = JSON.stringify(classifyLoopNode({ id: 'F', label: 'Enumerate all edge cases', loop_hint: { termination_hint: 'until-dry' } }));
  const det = a === b;
  console.log(`  ${det ? 'PASS' : 'FAIL'}  deterministic: identical output on repeat`);
  if (det) pass++;
  const total = cases.length + 1;
  console.log(`\nself-test: ${pass}/${total} passed`);
  process.exit(pass === total ? 0 : 1);
}

function main() {
  if (process.argv.includes('--self-test')) return selfTest();
  const fs = require('fs');
  const path = require('path');
  const i = process.argv.indexOf('--annotate');
  if (i === -1 || !process.argv[i + 1]) {
    console.error('Usage: classify-loop-node.js --annotate <plan.json> [--out <file>] | --self-test');
    process.exit(2);
  }
  const inPath = process.argv[i + 1];
  const raw = fs.readFileSync(inPath, 'utf8');
  const plan = /\.ya?ml$/.test(inPath) ? require('js-yaml').load(raw) : JSON.parse(raw);
  const { report } = annotatePlan(plan);
  const oi = process.argv.indexOf('--out');
  const outPath = oi !== -1 ? process.argv[oi + 1] : inPath;
  // Preserve the input format: .yaml/.yml -> YAML, else JSON (Hardening QA fix — no silent YAML->JSON).
  const serialized = /\.ya?ml$/.test(outPath) ? require('js-yaml').dump(plan) : JSON.stringify(plan, null, 2);
  fs.writeFileSync(outPath, serialized, 'utf8');
  console.log(`Annotated ${report.length} nodes -> ${outPath}`);
  report.forEach(r => console.log(`  ${r.id}: ${r.kind} (score ${r.score}, ${r.confidence}) ${JSON.stringify(r.signals)}`));
  const amb = report.filter(r => r.kind === 'ambiguous');
  if (amb.length) console.log(`\n[Class-C] ${amb.length} ambiguous node(s) flagged loop_candidate — human/validate-plan review required (AC4).`);
}

if (require.main === module) main();
module.exports = { classifyLoopNode, annotatePlan };
