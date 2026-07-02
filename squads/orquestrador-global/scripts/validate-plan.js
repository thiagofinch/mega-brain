#!/usr/bin/env node
/**
 * validate-plan.js — deterministic plan validator
 *
 * Validates orchestration-plan.yaml against:
 *  1. Schema (PA-0.2 template)
 *  2. DAG cycle-free (Kahn topological sort)
 *  3. Constitutional checks: CODEOWNERS, business isolation, agent authority, no-invention
 *  4. Budget cap (warn if exceeded)
 *
 * Story: STORY-PA-4.2
 * Consumer: post-plan-validate.sh hook (PA-5.2), plan-architect agent (PA-6.1)
 */
'use strict';

const fs = require('fs');


const REQUIRED_TOP_LEVEL = [
  'schema_version', 'plan_id', 'demand', 'discovery',
  'selected_capabilities', 'dag', 'risks', 'resource_estimate',
  'success_criteria', 'falsifiable_assumptions',
  'constitutional_compliance', 'handoff', 'quality_score', 'audit',
];

function parseArgs(argv) {
  const args = { plan: null, budget_cap: null, verbose: false, deterministic: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--budget-cap') args.budget_cap = parseFloat(argv[++i]);
    else if (a === '--verbose') args.verbose = true;
    else if (a === '--deterministic') args.deterministic = true;
    else if (!args.plan) args.plan = a;
  }
  return args;
}

// ── Minimal YAML parser (just enough for our schema) ──────────────────────────
function parseYAML(src) {
  // For full fidelity, defer to js-yaml when available; otherwise basic line parser.
  try {
    const yaml = require('js-yaml');
    return yaml.load(src);
  } catch {
    // Crude fallback — not full YAML, but enough to detect basic structure presence
    const lines = src.split('\n');
    const out = {};
    for (const l of lines) {
      const m = l.match(/^([a-z_]\w*):\s*(.*)$/);
      if (m) out[m[1]] = m[2] || true;
    }
    return out;
  }
}

// ── Validators ────────────────────────────────────────────────────────────────
function validateSchema(plan) {
  const errors = [];
  for (const key of REQUIRED_TOP_LEVEL) {
    if (!(key in plan)) errors.push({ type: 'SCHEMA_MISSING', key });
  }
  if (plan.schema_version && plan.schema_version !== '2.0') {
    errors.push({ type: 'SCHEMA_VERSION_MISMATCH', expected: '2.0', got: plan.schema_version });
  }
  return errors;
}

function detectCycle(dag) {
  if (!dag || !dag.nodes || !dag.edges) return [];
  const errors = [];
  const inDegree = {};
  const adj = {};
  for (const n of dag.nodes || []) {
    inDegree[n.id] = 0;
    adj[n.id] = [];
  }
  for (const e of dag.edges || []) {
    if (!(e.from in inDegree)) continue;
    if (!(e.to in inDegree)) continue;
    adj[e.from].push(e.to);
    inDegree[e.to]++;
  }
  // Kahn's
  const queue = Object.keys(inDegree).filter(k => inDegree[k] === 0);
  let visited = 0;
  while (queue.length) {
    const u = queue.shift();
    visited++;
    for (const v of adj[u] || []) {
      if (--inDegree[v] === 0) queue.push(v);
    }
  }
  if (visited !== Object.keys(inDegree).length) {
    errors.push({ type: 'CYCLE', message: 'DAG contains cycle (Kahn topological sort failed)' });
  }
  return errors;
}

function constitutionalCheck(plan) {
  const errors = [];
  const warnings = [];
  const compliance = plan.constitutional_compliance || {};

  // CHK-1 CODEOWNERS
  if (compliance.codeowners_check && compliance.codeowners_check !== 'pass') {
    errors.push({ type: 'CODEOWNERS_VIOLATION', message: `CODEOWNERS check: ${compliance.codeowners_check}` });
  }
  // CHK-2 business isolation
  if (compliance.business_isolation_check && compliance.business_isolation_check !== 'pass') {
    errors.push({ type: 'BUSINESS_ISOLATION', message: `business_isolation check: ${compliance.business_isolation_check}` });
  }
  // CHK-3 agent authority
  if (compliance.agent_authority_check && compliance.agent_authority_check !== 'pass') {
    errors.push({ type: 'AGENT_AUTHORITY', message: `agent_authority check: ${compliance.agent_authority_check}` });
  }
  // CHK-4 no-invention (warn only)
  if (compliance.no_invention_check && compliance.no_invention_check !== 'pass') {
    warnings.push({ type: 'NO_INVENTION', message: `no_invention check: ${compliance.no_invention_check}` });
  }

  // Inspect dag nodes for actions that require @devops authority
  for (const node of (plan.dag && plan.dag.nodes) || []) {
    const label = (node.label || '').toLowerCase();
    if (/git push|gh pr/.test(label) && node.capability && !node.capability.includes('devops')) {
      errors.push({
        type: 'AGENT_AUTHORITY',
        node: node.id,
        message: `node "${node.id}" implies push/PR but not assigned to @devops (got: ${node.capability})`,
      });
    }
  }
  return { errors, warnings };
}

function budgetCheck(plan, cap) {
  const warnings = [];
  if (!cap) return warnings;
  const total = plan.resource_estimate && plan.resource_estimate.total_cost_usd;
  if (typeof total === 'number' && total > cap) {
    warnings.push({ type: 'BUDGET_EXCEEDED', estimated: total, cap });
  }
  return warnings;
}

function routingCheck(plan) {
  const errors = [];
  const warnings = [];
  const nodes = (plan.dag && plan.dag.nodes) || [];
  const selectedCapabilities = plan.selected_capabilities || [];

  for (const node of nodes) {
    if (node.routing_blocked) {
      errors.push({
        type: 'ROUTING_HARD_GATE_BLOCKED',
        node: node.id,
        decision_id: node.routing_decision_id || null,
        message: `node "${node.id}" is blocked by RoutingDecision hard gates`,
      });
    }
    if (node.routing_fallback) {
      warnings.push({
        type: 'ROUTING_FALLBACK',
        node: node.id,
        message: `node "${node.id}" used legacy routing fallback`,
      });
    }
  }

  for (const capability of selectedCapabilities) {
    if (capability.routing && capability.routing.selected_by === 'legacy-fallback') {
      warnings.push({
        type: 'ROUTING_FALLBACK',
        capability: capability.id,
        message: `capability "${capability.id}" used legacy routing fallback`,
      });
    }
    if (capability.routing && capability.routing.selected_by === 'routing-engine-v2' && !capability.routing.decision_id) {
      errors.push({
        type: 'ROUTING_DECISION_MISSING',
        capability: capability.id,
        message: `capability "${capability.id}" is marked routing-engine-v2 but has no decision_id`,
      });
    }
  }

  const summary = plan.routing_summary || {};
  for (const nodeId of summary.blocked_nodes || []) {
    if (!nodes.some(node => node.id === nodeId && node.routing_blocked)) {
      warnings.push({
        type: 'ROUTING_SUMMARY_DRIFT',
        node: nodeId,
        message: `routing_summary lists blocked node "${nodeId}" but DAG node is not marked blocked`,
      });
    }
  }

  return { errors, warnings };
}

// ── Main ──────────────────────────────────────────────────────────────────────
// STORY-LC-3 / ADR-LC-002 — loop-node validation.
// Classes per PV_KE_106: LOOP_NODE_MISSING_HINT (B), LOOP_HINT_WITHOUT_LOOP_KIND (A),
// LOOP_NODE_WARRANTS_REVIEW (C — human/QG gate, surfaced as warning never auto-passed).
function loopNodeCheck(plan) {
  const errors = [];
  const warnings = [];
  const nodes = (plan.dag && plan.dag.nodes) || [];
  const TERM = ['until-dod', 'until-dry', 'until-budget'];
  for (const n of nodes) {
    if (n.execution_kind === 'loop') {
      const h = n.loop_hint;
      if (!h || typeof h.task !== 'string' || !h.task.trim() || !TERM.includes(h.termination_hint)) {
        errors.push({
          type: 'LOOP_NODE_MISSING_HINT',
          node: n.id,
          message: `loop node ${n.id} requires loop_hint.task + loop_hint.termination_hint in ${JSON.stringify(TERM)} (AC4).`,
        });
      }
      // Hardening QA fix: a present budget_tokens must be a positive integer (null = unspecified is OK).
      if (h && h.budget_tokens != null && (!Number.isInteger(h.budget_tokens) || h.budget_tokens < 1)) {
        errors.push({
          type: 'LOOP_HINT_BAD_BUDGET',
          node: n.id,
          message: `loop node ${n.id} loop_hint.budget_tokens must be a positive integer or null (got ${JSON.stringify(h.budget_tokens)}).`,
        });
      }
      warnings.push({
        type: 'LOOP_NODE_WARRANTS_REVIEW',
        node: n.id,
        message: `loop node ${n.id}: confirm the task genuinely warrants a loop (not a one-shot). Class-C human/QG gate.`,
      });
    } else if (n.loop_hint) {
      errors.push({
        type: 'LOOP_HINT_WITHOUT_LOOP_KIND',
        node: n.id,
        message: `node ${n.id} carries loop_hint but execution_kind != 'loop' (set execution_kind:loop or remove loop_hint).`,
      });
    }
    // STORY-LC-4: an ambiguous node flagged by classify-loop-node.js (never auto-typed) surfaces the
    // Class-C gate so a human/validate decides loop-vs-single. Reuses LOOP_NODE_WARRANTS_REVIEW (AC4).
    if (n.loop_candidate === true && n.execution_kind !== 'loop') {
      warnings.push({
        type: 'LOOP_NODE_WARRANTS_REVIEW',
        node: n.id,
        message: `node ${n.id}: classifier flagged it as a loop CANDIDATE (ambiguous, not auto-typed). Class-C human gate: decide loop vs single.`,
      });
    }
  }
  return { errors, warnings };
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.plan) {
    console.error('Usage: validate-plan.js <plan.yaml> [--budget-cap <usd>] [--verbose] [--deterministic]');
    process.exit(2);
  }

  const planSrc = fs.readFileSync(args.plan, 'utf8');
  const plan = parseYAML(planSrc);

  const errors = [];
  const warnings = [];

  errors.push(...validateSchema(plan));
  errors.push(...detectCycle(plan.dag || {}));

  const c = constitutionalCheck(plan);
  errors.push(...c.errors);
  warnings.push(...c.warnings);

  const routing = routingCheck(plan);
  errors.push(...routing.errors);
  warnings.push(...routing.warnings);

  const loops = loopNodeCheck(plan);
  errors.push(...loops.errors);
  warnings.push(...loops.warnings);

  warnings.push(...budgetCheck(plan, args.budget_cap));

  const result = {
    valid: errors.length === 0,
    plan_id: plan.plan_id || null,
    errors,
    warnings,
    summary: {
      schema_violations: errors.filter(e => e.type.startsWith('SCHEMA')).length,
      cycle_detected: errors.some(e => e.type === 'CYCLE'),
      constitutional_violations: errors.filter(e => /^(CODEOWNERS|BUSINESS|AGENT|NO_INVENTION)/.test(e.type)).length,
      routing_blockers: errors.filter(e => e.type === 'ROUTING_HARD_GATE_BLOCKED').length,
      routing_fallbacks: warnings.filter(w => w.type === 'ROUTING_FALLBACK').length,
      budget_warnings: warnings.filter(w => w.type === 'BUDGET_EXCEEDED').length,
      loop_node_violations: errors.filter(e => /^LOOP_/.test(e.type)).length,
    },
  };

  console.log(JSON.stringify(result, null, 2));
  process.exit(result.valid ? 0 : 1);
}

if (require.main === module) main();

module.exports = { validateSchema, detectCycle, constitutionalCheck, budgetCheck, routingCheck, loopNodeCheck, parseYAML };
