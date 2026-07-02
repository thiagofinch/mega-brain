#!/usr/bin/env node
/**
 * plan-to-swarm.js — Adapter from plan-architect plan.json to /swarm-execute input
 *
 * Bridges the gap between:
 *  - INPUT:  outputs/plans/{slug}/plan.json (schema 2.0, produced by /orquestrador-global)
 *  - OUTPUT: array of {agent, prompt, mode, effort, file_set, checklist} batches
 *            consumable by /swarm-execute
 *
 * Respects:
 *  - dag.edges (data_dependency / sequence / gate)
 *  - dag.parallel_groups
 *  - dag.critical_path
 *  - RoutingDecision v2 resolution when present
 *  - capability resolution via selected_capabilities[].id as legacy fallback
 *
 * Does NOT execute anything (P1 plan-only invariant of orquestrador-global).
 *
 * Usage:
 *   node plan-to-swarm.js --in <plan.json> [--out <file>] [--format json|yaml]
 *                         [--batch <N>] [--swarm-input-only] [--dry-run]
 *
 * Source: STORY-PA-7.1 (handoff to executor) — closes the gap identified
 * in the post-mortem 2026-05-03 where users expected /orquestrador-global to
 * activate agents. It does not. This adapter does.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..', '..');
const DEFAULT_ROUTING_DECISIONS_DIR = path.join(ROOT, 'outputs', 'routing', 'decisions');

// ─────────────────────────────────────────────────────────────────────────────
// CLI parsing
// ─────────────────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = {
    in: null,
    out: null,
    format: 'json',
    batch: null,
    swarmInputOnly: false,
    dryRun: false,
    routingDecisionsDir: null,
    help: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--in') args.in = argv[++i];
    else if (a === '--out') args.out = argv[++i];
    else if (a === '--format') args.format = argv[++i];
    else if (a === '--batch') args.batch = parseInt(argv[++i], 10);
    else if (a === '--routing-decisions-dir') args.routingDecisionsDir = argv[++i];
    else if (a === '--swarm-input-only') args.swarmInputOnly = true;
    else if (a === '--dry-run') args.dryRun = true;
    else if (a === '--help' || a === '-h') args.help = true;
    else if (!args.in && !a.startsWith('--')) args.in = a;
  }
  return args;
}

function printHelp() {
  console.log(`
plan-to-swarm.js — Adapter from /orquestrador-global plan.json to /swarm-execute batches

USAGE:
  node plan-to-swarm.js --in <plan.json> [options]

OPTIONS:
  --in <path>              Path to plan.json (required)
  --out <path>             Write output to file (default: stdout)
  --format json|yaml       Output format (default: json)
  --batch <N>              Emit only batch N (1-indexed). Default: emit all batches.
  --routing-decisions-dir  Directory containing RoutingDecision JSON files.
  --swarm-input-only       Emit only the tasks array of the chosen batch (pipe-friendly)
  --dry-run                Print summary stats only, do not emit tasks
  --help, -h               Show this help

EXAMPLES:
  # Full plan converted to all batches
  node plan-to-swarm.js --in outputs/plans/2026-05-03_launch/plan.json

  # Just batch 1 as swarm-execute input
  node plan-to-swarm.js --in outputs/plans/2026-05-03_launch/plan.json \\
                        --batch 1 --swarm-input-only > batch1.json

  # YAML for human review
  node plan-to-swarm.js --in plan.json --format yaml --out batches.yaml

EXIT CODES:
  0  success
  1  invalid plan.json (schema mismatch, missing fields, cycle detected)
  2  invalid CLI args
  3  filesystem error
`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Plan validation
// ─────────────────────────────────────────────────────────────────────────────
function validatePlan(plan, planPath) {
  const errors = [];
  if (plan.schema_version !== '2.0') {
    errors.push(`schema_version expected "2.0", got "${plan.schema_version}"`);
  }
  if (!plan.dag || !Array.isArray(plan.dag.nodes)) {
    errors.push('dag.nodes missing or not an array');
  }
  if (!Array.isArray(plan.selected_capabilities)) {
    errors.push('selected_capabilities missing or not an array');
  }
  if (errors.length) {
    throw new Error(`Plan validation failed for ${planPath}:\n  - ${errors.join('\n  - ')}`);
  }
  return plan;
}

// ─────────────────────────────────────────────────────────────────────────────
// RoutingDecision v2 resolution
// ─────────────────────────────────────────────────────────────────────────────
function normalizeAgentId(agentId) {
  if (!agentId) return null;
  let normalized = String(agentId).trim();
  if (!normalized) return null;
  if (normalized.startsWith('@')) normalized = normalized.slice(1);
  if (normalized.includes(':')) normalized = normalized.replace(':', '--');
  return normalized;
}

function selectedCapabilityForNode(node, plan) {
  const capabilityRef = node.capability || node.capability_ref;
  return (plan.selected_capabilities || []).find((capability) => capability.id === capabilityRef) || null;
}

function resolveRoutingDecisionsDir(plan, options = {}) {
  const configured = options.routingDecisionsDir ||
    process.env.ROUTING_DECISIONS_DIR ||
    (plan.routing_summary && plan.routing_summary.decisions_dir) ||
    DEFAULT_ROUTING_DECISIONS_DIR;
  return path.isAbsolute(configured) ? configured : path.resolve(ROOT, configured);
}

function routingDecisionIdForNode(node, capability) {
  return node.routing_decision_id ||
    (node.routing && node.routing.decision_id) ||
    (node.routing_decision && node.routing_decision.decision_id) ||
    (capability && capability.routing_decision_id) ||
    (capability && capability.routing && capability.routing.decision_id) ||
    null;
}

function inlineRoutingDecisionForNode(node, capability) {
  return node.routing_decision ||
    (node.routing && node.routing.decision) ||
    (capability && capability.routing_decision) ||
    (capability && capability.routing && capability.routing.decision) ||
    null;
}

function routingDecisionPath(decisionId, node, capability, plan, options = {}) {
  const persistedPath = (node.routing && node.routing.persisted_path) ||
    (capability && capability.routing && capability.routing.persisted_path) ||
    null;
  if (persistedPath) {
    return path.isAbsolute(persistedPath) ? persistedPath : path.resolve(ROOT, persistedPath);
  }
  return path.join(resolveRoutingDecisionsDir(plan, options), `${decisionId}.json`);
}

function loadRoutingDecisionForNode(node, plan, options = {}) {
  const capability = selectedCapabilityForNode(node, plan);
  const inlineDecision = inlineRoutingDecisionForNode(node, capability);
  if (inlineDecision && inlineDecision.selected) {
    return {
      decision: inlineDecision,
      decision_id: inlineDecision.decision_id || routingDecisionIdForNode(node, capability),
      source: 'inline',
      capability,
      warning: null,
    };
  }

  const decisionId = routingDecisionIdForNode(node, capability);
  if (!decisionId) {
    return {
      decision: null,
      decision_id: null,
      source: 'legacy',
      capability,
      warning: `node ${node.id} has no RoutingDecision; using legacy capability "${node.capability || node.capability_ref || '<missing>'}".`,
    };
  }

  const decisionPath = routingDecisionPath(decisionId, node, capability, plan, options);
  if (!fs.existsSync(decisionPath)) {
    return {
      decision: null,
      decision_id: decisionId,
      source: 'missing-file',
      capability,
      warning: `node ${node.id} references RoutingDecision ${decisionId}, but ${decisionPath} was not found; using legacy capability fallback.`,
    };
  }

  try {
    return {
      decision: JSON.parse(fs.readFileSync(decisionPath, 'utf8')),
      decision_id: decisionId,
      source: decisionPath,
      capability,
      warning: null,
    };
  } catch (error) {
    return {
      decision: null,
      decision_id: decisionId,
      source: 'invalid-file',
      capability,
      warning: `node ${node.id} references RoutingDecision ${decisionId}, but JSON parsing failed: ${error.message}; using legacy capability fallback.`,
    };
  }
}

function routingDecisionBlocked(decision) {
  if (!decision) return false;
  if (decision.confidence && decision.confidence.band === 'blocked') return true;
  return (decision.hard_gate_results || []).some((gate) => gate.status === 'fail');
}

function hardGateSummary(decision) {
  return (decision && decision.hard_gate_results || []).map((gate) => `${gate.id}:${gate.status}`);
}

function routingDecisionWarnings(node, decision, legacyAgent, decisionAgent) {
  const warnings = [];
  if (!decision) return warnings;
  if (legacyAgent && decisionAgent && legacyAgent !== decisionAgent) {
    warnings.push(
      `node ${node.id} legacy capability maps to "${legacyAgent}", but RoutingDecision ${decision.decision_id} selects "${decisionAgent}".`,
    );
  }
  if (routingDecisionBlocked(decision)) {
    warnings.push(`node ${node.id} RoutingDecision ${decision.decision_id} is blocked by hard gates.`);
  }
  return warnings;
}

function appendRoutingContext(prompt, routing) {
  if (!routing || !routing.decision_id) return prompt;
  const lines = [
    '',
    'RoutingDecision v2:',
    `- decision_id: ${routing.decision_id}`,
    `- primary_executor: ${routing.primary_executor}`,
    `- quality_gate_agent: ${routing.quality_gate_agent || '-'}`,
    `- support_agents: ${(routing.support_agents || []).join(', ') || '-'}`,
    `- confidence: ${routing.confidence_score ?? '-'} (${routing.confidence_band || '-'})`,
  ];
  if (routing.hard_gates && routing.hard_gates.length) {
    lines.push(`- hard_gates: ${routing.hard_gates.join(', ')}`);
  }
  return `${prompt}\n${lines.join('\n')}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Capability resolution: capability ref → swarm agent id
// ─────────────────────────────────────────────────────────────────────────────
function resolveAgentId(capabilityRef, selectedCapabilities) {
  // capability ref examples:
  //   "megabrain-sop:sop-creator"   → squad:agent format
  //   "megabrain-sop--sop-creator"  → swarm-execute format (already)
  //   "megabrain-sop"               → squad-only (entry agent)
  //   "develop-story"          → skill (swarm-execute can call skill agents)
  if (!capabilityRef) return null;

  // Look up to confirm capability is registered in the plan
  const cap = selectedCapabilities.find((c) => c.id === capabilityRef);
  if (!cap) {
    // Not fatal — node may reference a capability not in selected (unusual).
    // We'll still emit the agent id.
  }

  // Format normalization: swarm-execute uses `{squad}--{agent}` separator
  let agentId = capabilityRef;
  if (agentId.includes(':')) {
    agentId = agentId.replace(':', '--');
  }

  // If type is squad-only (no agent suffix) and we have selected_capabilities
  // info, try to resolve to entry agent (heuristic: same name + "-chief" or same)
  if (cap && cap.type === 'squad' && !agentId.includes('--')) {
    // For squad refs, swarm-execute expects an agent id. Without an entry agent
    // hint in the plan, we leave the squad id alone — caller must decide.
    // Future: read squad.yaml for entry_agent declaration.
  }

  return normalizeAgentId(agentId);
}

// ─────────────────────────────────────────────────────────────────────────────
// Effort mapping: estimated_duration_minutes → 1-10 effort scale
// (aligned with .claude/skills/swarm-execute/SKILL.md effort table)
// ─────────────────────────────────────────────────────────────────────────────
function durationToEffort(minutes) {
  if (typeof minutes !== 'number' || minutes <= 0) return 3; // default moderate
  if (minutes < 1) return 1;        // trivial
  if (minutes < 2) return 2;        // simple
  if (minutes < 10) return 3;       // moderate
  if (minutes < 30) return 4;       // complex
  if (minutes < 60) return 5;       // complex+
  return 6;                          // very-complex
}

// ─────────────────────────────────────────────────────────────────────────────
// Mode inference: write if any outputs produced, else read
// ─────────────────────────────────────────────────────────────────────────────
function inferMode(node) {
  if (Array.isArray(node.outputs_produced) && node.outputs_produced.length > 0) {
    return 'write';
  }
  return 'read';
}

// ─────────────────────────────────────────────────────────────────────────────
// Prompt composition from node fields
// ─────────────────────────────────────────────────────────────────────────────
function composePrompt(node, plan) {
  const parts = [];

  // Header: label + capability
  parts.push(`Task: ${node.label || node.id}`);
  parts.push(`Capability: ${node.capability} (${node.capability_type || 'unknown'})`);

  // Demand context (carry over the user's original demand)
  if (plan.demand && plan.demand.raw) {
    parts.push(`\nUser demand: ${plan.demand.raw}`);
  }
  if (plan.demand && plan.demand.parsed) {
    const p = plan.demand.parsed;
    if (p.business_units && p.business_units.length) {
      parts.push(`Business units: ${p.business_units.join(', ')}`);
    }
    if (p.primary_domain) {
      parts.push(`Primary domain: ${p.primary_domain}`);
    }
  }

  // Inputs
  if (Array.isArray(node.inputs_required) && node.inputs_required.length) {
    parts.push(`\nInputs required: ${node.inputs_required.join(', ')}`);
  }

  // Outputs
  if (Array.isArray(node.outputs_produced) && node.outputs_produced.length) {
    parts.push(`Outputs to produce: ${node.outputs_produced.join(', ')}`);
  }

  // Quality gate
  if (node.quality_gate) {
    parts.push(`Quality gate (run after): ${node.quality_gate}`);
  }

  // Risk callout (only if RPN >= 50)
  if (node.risk && typeof node.risk.rpn === 'number' && node.risk.rpn >= 50) {
    parts.push(`\n⚠ Risk RPN=${node.risk.rpn} — review mitigation in plan.risks before executing.`);
  }

  return parts.join('\n');
}

// ─────────────────────────────────────────────────────────────────────────────
// Quality gate path resolution
// ─────────────────────────────────────────────────────────────────────────────
function resolveChecklistPath(qualityGate, _plan) {
  if (!qualityGate) return undefined;
  // Heuristic: if it's already a path, use as-is. Otherwise look up by name.
  if (qualityGate.includes('/') || qualityGate.endsWith('.md')) {
    return qualityGate;
  }
  // Try squads/{owner}/checklists/{quality_gate}.md
  // We don't know the owner here; emit name only and let swarm-execute resolve.
  return qualityGate;
}

// ─────────────────────────────────────────────────────────────────────────────
// Topological sort + batch grouping
// Algorithm:
//   1. Build adjacency from edges (from → to)
//   2. Kahn's algorithm to compute layers (each layer = parallel batch)
//   3. Override: if dag.parallel_groups is non-empty, validate against layers
// ─────────────────────────────────────────────────────────────────────────────
function buildBatches(plan) {
  const nodes = plan.dag.nodes;
  const edges = plan.dag.edges || [];
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  // Build in-degree map and adjacency
  const inDegree = new Map(nodes.map((n) => [n.id, 0]));
  const adj = new Map(nodes.map((n) => [n.id, []]));
  for (const e of edges) {
    if (!nodeMap.has(e.from) || !nodeMap.has(e.to)) {
      throw new Error(`Edge references unknown node: ${e.from} → ${e.to}`);
    }
    inDegree.set(e.to, (inDegree.get(e.to) || 0) + 1);
    adj.get(e.from).push(e.to);
  }

  // Kahn's: process all in-degree-0 nodes per layer
  const batches = [];
  const remaining = new Set(nodes.map((n) => n.id));
  let safety = nodes.length + 1;
  while (remaining.size > 0 && safety-- > 0) {
    const ready = [];
    for (const id of remaining) {
      if ((inDegree.get(id) || 0) === 0) ready.push(id);
    }
    if (ready.length === 0) {
      throw new Error('Cycle detected in DAG (no in-degree-0 nodes left).');
    }
    batches.push(ready);
    for (const id of ready) {
      remaining.delete(id);
      for (const neighbor of adj.get(id)) {
        inDegree.set(neighbor, inDegree.get(neighbor) - 1);
      }
    }
  }
  if (remaining.size > 0) {
    throw new Error('DAG topological sort did not converge — cycle suspected.');
  }
  return batches; // array of arrays of node ids
}

// ─────────────────────────────────────────────────────────────────────────────
// Validate batches against declared parallel_groups (advisory)
// ─────────────────────────────────────────────────────────────────────────────
function validateAgainstParallelGroups(batches, plan) {
  const groups = plan.dag.parallel_groups || [];
  const warnings = [];
  for (const g of groups) {
    if (!Array.isArray(g.nodes) || g.nodes.length < 2) continue;
    // All nodes in a parallel_group should appear in the same batch
    const batchIdx = batches.findIndex((b) => b.includes(g.nodes[0]));
    if (batchIdx === -1) continue;
    for (const n of g.nodes) {
      if (!batches[batchIdx].includes(n)) {
        warnings.push(
          `parallel_group ${g.group_id || '<unnamed>'}: node ${n} not in same topological batch as ${g.nodes[0]} ` +
          `(may indicate edges constraining what plan claims is parallel)`,
        );
      }
    }
  }
  return warnings;
}

// ─────────────────────────────────────────────────────────────────────────────
// Emit task per node, batch per layer
// ─────────────────────────────────────────────────────────────────────────────
// STORY-LC-3 / ADR-LC-002 — a loop node compiles to a /loop-compiler directive, NOT a swarm task.
// Exclusivity (AC3): it never resolves to a normal capability agent. compile != execute (D4): emits a
// loop-spec for review, never runs. Output threads to dependents via file_set (AC5).
function loopNodeToDirective(node) {
  const h = node.loop_hint || {};
  const constraints = [
    h.complexity && `complexity=${h.complexity}`,
    h.verification && `verification=${h.verification}`,
    (h.parallelizable != null) && `parallelizable=${h.parallelizable}`,  // Hardening: preserve explicit false
    (h.recurring != null) && `recurring=${h.recurring}`,
    h.termination_hint && `termination=${h.termination_hint}`,
    (h.budget_tokens != null) && `budget_tokens=${h.budget_tokens}`,
  ].filter(Boolean).join(', ');
  const task = {
    agent: 'loop-compiler',          // skill agent — operator/runtime routes to /loop-compiler
    loop: true,                      // exclusivity marker: a loop directive, never a swarm task
    mode: 'compile',                 // compile != execute (ADR-LC-001 D3 / ADR-LC-002 D4)
    prompt: `Compile a bespoke loop for: ${h.task || node.capability_ref || node.id}`
      + (constraints ? `\nConstraints: ${constraints}` : '')
      + `\nEmit loop-spec.yaml (do NOT execute).`,
    effort: durationToEffort(node.estimated_duration_minutes),
    loop_hint: h,
  };
  if (Array.isArray(node.outputs_produced) && node.outputs_produced.length) {
    task.file_set = node.outputs_produced.slice();   // AC5: loop output threads to dependents
  }
  task._node_id = node.id;
  task._capability_ref = node.capability_ref || node.capability;
  task._warnings = [];
  return task;
}

function nodeToTask(node, plan, options = {}) {
  if (node.execution_kind === 'loop') return loopNodeToDirective(node);
  const legacyAgent = resolveAgentId(node.capability || node.capability_ref, plan.selected_capabilities || []);
  const routingResult = loadRoutingDecisionForNode(node, plan, options);
  const decision = routingResult.decision;
  const decisionAgent = decision && normalizeAgentId(decision.selected && decision.selected.primary_executor);
  const warnings = [];
  if (routingResult.warning) warnings.push(routingResult.warning);
  warnings.push(...routingDecisionWarnings(node, decision, legacyAgent, decisionAgent));

  const blocked = routingDecisionBlocked(decision) || node.routing_blocked === true;
  const routing = decision ? {
    decision_id: decision.decision_id || routingResult.decision_id,
    source: routingResult.source,
    primary_executor: decision.selected.primary_executor,
    primary_executor_agent: decisionAgent,
    support_agents: decision.selected.support_agents || [],
    support_agent_ids: (decision.selected.support_agents || []).map(normalizeAgentId).filter(Boolean),
    quality_gate_agent: decision.selected.quality_gate_agent,
    quality_gate_agent_id: normalizeAgentId(decision.selected.quality_gate_agent),
    confidence_score: decision.confidence && decision.confidence.score,
    confidence_band: decision.confidence && decision.confidence.band,
    hard_gates: hardGateSummary(decision),
  } : null;

  const task = {
    agent: decisionAgent || legacyAgent,
    prompt: appendRoutingContext(composePrompt(node, plan), routing),
    mode: inferMode(node),
    effort: durationToEffort(node.estimated_duration_minutes),
  };
  if (Array.isArray(node.outputs_produced) && node.outputs_produced.length) {
    task.file_set = node.outputs_produced.slice();
  }
  const checklist = resolveChecklistPath(node.quality_gate, plan);
  if (checklist) task.checklist = checklist;
  if (routing) {
    task.routing = routing;
    task.support_agents = routing.support_agents;
    task.quality_gate_agent = routing.quality_gate_agent;
  }
  if (blocked) {
    task.blocked = true;
    task.block_reason = `RoutingDecision ${routing && routing.decision_id || routingResult.decision_id || '<unknown>'} is blocked by hard gates.`;
  }
  // Carry node id for traceability
  task._node_id = node.id;
  task._capability_ref = node.capability || node.capability_ref;
  task._legacy_agent = legacyAgent;
  task._warnings = warnings;
  return task;
}

function buildOutput(plan, options = {}) {
  const layeredBatches = buildBatches(plan);
  const warnings = validateAgainstParallelGroups(layeredBatches, plan);
  const nodeMap = new Map(plan.dag.nodes.map((n) => [n.id, n]));

  const batches = layeredBatches.map((nodeIds, idx) => {
    const tasks = nodeIds
      .map((id) => nodeMap.get(id))
      .filter(Boolean)
      .map((node) => nodeToTask(node, plan, options));
    for (const task of tasks) {
      warnings.push(...(task._warnings || []));
    }

    // Compute estimated batch wall-time = max(task.effort durations)
    const batchDurationMinutes = Math.max(
      ...nodeIds
        .map((id) => nodeMap.get(id))
        .map((n) => (n && typeof n.estimated_duration_minutes === 'number' ? n.estimated_duration_minutes : 0)),
      0,
    );

    return {
      id: `batch-${idx + 1}`,
      level: idx + 1,
      tasks,
      rationale: nodeIds.length > 1
        ? `${nodeIds.length} tasks in parallel (no inter-dependency at this level)`
        : 'single task',
      estimated_duration_minutes: batchDurationMinutes,
      node_ids: nodeIds,
    };
  });

  return {
    plan_id: plan.plan_id || '<unknown>',
    source_schema_version: plan.schema_version,
    generated_by: 'plan-to-swarm.js',
    generated_at: new Date().toISOString(),
    batches,
    warnings,
    metadata: {
      total_nodes: plan.dag.nodes.length,
      total_batches: batches.length,
      total_tasks: batches.reduce((acc, b) => acc + b.tasks.length, 0),
      critical_path: plan.dag.critical_path || [],
      critical_path_duration_minutes: plan.dag.critical_path_duration_minutes || 0,
      total_wall_time_estimate_minutes: batches.reduce((acc, b) => acc + b.estimated_duration_minutes, 0),
      routing_decisions: batches.reduce((acc, batch) => {
        return acc + batch.tasks.filter((task) => task.routing && task.routing.decision_id).length;
      }, 0),
      blocked_tasks: batches.reduce((acc, batch) => acc + batch.tasks.filter((task) => task.blocked).length, 0),
    },
    handoff: {
      next_action_suggested: plan.handoff && plan.handoff.next_action_suggested,
      next_action_executor: plan.handoff && plan.handoff.next_action_executor,
      approvals_required: (plan.handoff && plan.handoff.approvals_required) || [],
      do_not_execute_until: (plan.handoff && plan.handoff.do_not_execute_until) || [],
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Output formatting
// ─────────────────────────────────────────────────────────────────────────────
function formatOutput(payload, format) {
  if (format === 'yaml') {
    let yaml;
    try {
      yaml = require('js-yaml');
    } catch (e) {
      throw new Error('js-yaml not available — install with `npm i js-yaml` or use --format json');
    }
    return yaml.dump(payload, { noRefs: true, lineWidth: 120 });
  }
  return JSON.stringify(payload, null, 2);
}

function selectBatch(payload, batchN, swarmInputOnly) {
  if (!batchN) return payload;
  const idx = batchN - 1;
  if (idx < 0 || idx >= payload.batches.length) {
    throw new Error(`--batch ${batchN} out of range (have ${payload.batches.length} batches)`);
  }
  const selected = payload.batches[idx];
  if (swarmInputOnly) {
    const blockedTasks = selected.tasks.filter((task) => task.blocked);
    if (blockedTasks.length) {
      throw new Error(`batch ${batchN} contains ${blockedTasks.length} blocked task(s); refusing to emit executable swarm input`);
    }
    // Strip internal fields (_node_id, _capability_ref) for clean swarm-execute input
    return selected.tasks.map(({ _node_id, _capability_ref, _legacy_agent, _warnings, ...rest }) => rest);
  }
  return {
    plan_id: payload.plan_id,
    batch: selected,
    metadata: payload.metadata,
    handoff: payload.handoff,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Entry point
// ─────────────────────────────────────────────────────────────────────────────
function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.in) {
    printHelp();
    process.exit(args.help ? 0 : 2);
  }
  if (!['json', 'yaml'].includes(args.format)) {
    console.error(`Invalid --format "${args.format}" (expected json|yaml)`);
    process.exit(2);
  }

  const planPath = path.resolve(args.in);
  if (!fs.existsSync(planPath)) {
    console.error(`Plan file not found: ${planPath}`);
    process.exit(3);
  }

  let plan;
  try {
    plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  } catch (e) {
    console.error(`Failed to parse plan JSON: ${e.message}`);
    process.exit(1);
  }

  try {
    validatePlan(plan, planPath);
  } catch (e) {
    console.error(e.message);
    process.exit(1);
  }

  let payload;
  try {
    payload = buildOutput(plan, { routingDecisionsDir: args.routingDecisionsDir });
  } catch (e) {
    console.error(`Failed to build batches: ${e.message}`);
    process.exit(1);
  }

  if (args.dryRun) {
    console.error(`plan_id: ${payload.plan_id}`);
    console.error(`total_nodes: ${payload.metadata.total_nodes}`);
    console.error(`total_batches: ${payload.metadata.total_batches}`);
    console.error(`total_tasks: ${payload.metadata.total_tasks}`);
    console.error(`total_wall_time_estimate_minutes: ${payload.metadata.total_wall_time_estimate_minutes}`);
    if (payload.warnings.length) {
      console.error(`warnings: ${payload.warnings.length}`);
      for (const w of payload.warnings) console.error(`  - ${w}`);
    }
    process.exit(0);
  }

  const selected = selectBatch(payload, args.batch, args.swarmInputOnly);
  const output = formatOutput(selected, args.format);

  if (args.out) {
    const outPath = path.resolve(args.out);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, output, 'utf8');
    console.error(`Wrote ${outPath} (${output.length} bytes)`);
  } else {
    process.stdout.write(output);
    if (args.format === 'json') process.stdout.write('\n');
  }
}

if (require.main === module) {
  try {
    main();
  } catch (e) {
    console.error(`Fatal: ${e.message}`);
    if (process.env.DEBUG) console.error(e.stack);
    process.exit(1);
  }
}

// Exports for testing
module.exports = {
  parseArgs,
  validatePlan,
  resolveAgentId,
  durationToEffort,
  inferMode,
  composePrompt,
  resolveChecklistPath,
  buildBatches,
  validateAgainstParallelGroups,
  nodeToTask,
  loopNodeToDirective,
  buildOutput,
  loadRoutingDecisionForNode,
  normalizeAgentId,
  routingDecisionBlocked,
  selectBatch,
  formatOutput,
};
