/**
 * Tests for plan-to-swarm.js adapter.
 *
 * Run: node squads/orquestrador-global/scripts/__tests__/plan-to-swarm.test.js
 *
 * Zero external deps. Asserts via node:assert. Exits non-zero on failure.
 */

'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const adapter = require('../plan-to-swarm');
const FIXTURE_PATH = path.join(__dirname, 'fixtures/plan-sample.json');
const ROUTING_FIXTURE_PATH = path.join(__dirname, 'fixtures/plan-routing-v2.json');

function loadFixture() {
  return JSON.parse(fs.readFileSync(FIXTURE_PATH, 'utf8'));
}

function loadRoutingFixture() {
  return JSON.parse(fs.readFileSync(ROUTING_FIXTURE_PATH, 'utf8'));
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

let passed = 0;
let failed = 0;
const failures = [];

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (e) {
    console.log(`  ✗ ${name}`);
    console.log(`      ${e.message}`);
    failed++;
    failures.push({ name, error: e });
  }
}

function suite(name, fn) {
  console.log(`\n${name}`);
  fn();
}

// ─── parseArgs ──────────────────────────────────────────────────────────────
suite('parseArgs', () => {
  test('parses --in', () => {
    const a = adapter.parseArgs(['node', 'plan-to-swarm.js', '--in', 'plan.json']);
    assert.strictEqual(a.in, 'plan.json');
  });

  test('parses --batch as integer', () => {
    const a = adapter.parseArgs(['node', 'plan-to-swarm.js', '--in', 'p.json', '--batch', '2']);
    assert.strictEqual(a.batch, 2);
  });

  test('parses --swarm-input-only flag', () => {
    const a = adapter.parseArgs(['node', 'plan-to-swarm.js', '--in', 'p.json', '--swarm-input-only']);
    assert.strictEqual(a.swarmInputOnly, true);
  });

  test('positional arg sets in', () => {
    const a = adapter.parseArgs(['node', 'plan-to-swarm.js', 'plan.json']);
    assert.strictEqual(a.in, 'plan.json');
  });

  test('default format is json', () => {
    const a = adapter.parseArgs(['node', 'plan-to-swarm.js', '--in', 'p.json']);
    assert.strictEqual(a.format, 'json');
  });
});

// ─── validatePlan ───────────────────────────────────────────────────────────
suite('validatePlan', () => {
  test('accepts schema 2.0 fixture', () => {
    const plan = loadFixture();
    assert.doesNotThrow(() => adapter.validatePlan(plan, FIXTURE_PATH));
  });

  test('rejects wrong schema version', () => {
    const plan = loadFixture();
    plan.schema_version = '1.0';
    assert.throws(
      () => adapter.validatePlan(plan, FIXTURE_PATH),
      /schema_version expected "2.0"/,
    );
  });

  test('rejects missing dag.nodes', () => {
    const plan = loadFixture();
    delete plan.dag.nodes;
    assert.throws(
      () => adapter.validatePlan(plan, FIXTURE_PATH),
      /dag\.nodes/,
    );
  });

  test('rejects missing selected_capabilities', () => {
    const plan = loadFixture();
    delete plan.selected_capabilities;
    assert.throws(() => adapter.validatePlan(plan, FIXTURE_PATH));
  });
});

// ─── resolveAgentId ─────────────────────────────────────────────────────────
suite('resolveAgentId', () => {
  test('converts colon to double-dash separator', () => {
    const id = adapter.resolveAgentId('megabrain-sop:sop-creator', []);
    assert.strictEqual(id, 'megabrain-sop--sop-creator');
  });

  test('preserves already double-dash format', () => {
    const id = adapter.resolveAgentId('megabrain-ads--pixel-specialist', []);
    assert.strictEqual(id, 'megabrain-ads--pixel-specialist');
  });

  test('returns null for null input', () => {
    assert.strictEqual(adapter.resolveAgentId(null, []), null);
  });

  test('handles squad-only refs unchanged', () => {
    const id = adapter.resolveAgentId('megabrain-sop', [{ id: 'megabrain-sop', type: 'squad' }]);
    assert.strictEqual(id, 'megabrain-sop');
  });
});

// ─── durationToEffort ───────────────────────────────────────────────────────
suite('durationToEffort', () => {
  test('< 1 min → 1 (trivial)', () => assert.strictEqual(adapter.durationToEffort(0.5), 1));
  test('1-2 min → 2 (simple)', () => assert.strictEqual(adapter.durationToEffort(1.5), 2));
  test('2-10 min → 3 (moderate)', () => assert.strictEqual(adapter.durationToEffort(5), 3));
  test('10-30 min → 4 (complex)', () => assert.strictEqual(adapter.durationToEffort(20), 4));
  test('30-60 min → 5 (complex+)', () => assert.strictEqual(adapter.durationToEffort(45), 5));
  test('60+ min → 6 (very-complex)', () => assert.strictEqual(adapter.durationToEffort(90), 6));
  test('zero/negative defaults to 3', () => assert.strictEqual(adapter.durationToEffort(0), 3));
  test('non-number defaults to 3', () => assert.strictEqual(adapter.durationToEffort('foo'), 3));
});

// ─── inferMode ──────────────────────────────────────────────────────────────
suite('inferMode', () => {
  test('outputs_produced non-empty → write', () => {
    assert.strictEqual(adapter.inferMode({ outputs_produced: ['file.md'] }), 'write');
  });

  test('outputs_produced empty → read', () => {
    assert.strictEqual(adapter.inferMode({ outputs_produced: [] }), 'read');
  });

  test('outputs_produced missing → read', () => {
    assert.strictEqual(adapter.inferMode({}), 'read');
  });
});

// ─── composePrompt ──────────────────────────────────────────────────────────
suite('composePrompt', () => {
  test('includes label and capability', () => {
    const plan = loadFixture();
    const node = plan.dag.nodes[0];
    const prompt = adapter.composePrompt(node, plan);
    assert.ok(prompt.includes(node.label));
    assert.ok(prompt.includes(node.capability));
  });

  test('includes user demand', () => {
    const plan = loadFixture();
    const node = plan.dag.nodes[0];
    const prompt = adapter.composePrompt(node, plan);
    assert.ok(prompt.includes(plan.demand.raw));
  });

  test('includes business units when present', () => {
    const plan = loadFixture();
    const node = plan.dag.nodes[0];
    const prompt = adapter.composePrompt(node, plan);
    assert.ok(prompt.includes('generico'));
  });

  test('flags high-risk RPN nodes', () => {
    const plan = loadFixture();
    const highRiskNode = plan.dag.nodes.find((n) => n.id === 'n2'); // RPN 60
    const prompt = adapter.composePrompt(highRiskNode, plan);
    assert.ok(prompt.includes('Risk RPN=60'));
  });

  test('does not flag low-RPN nodes', () => {
    const plan = loadFixture();
    const lowRiskNode = plan.dag.nodes.find((n) => n.id === 'n4'); // RPN 2
    const prompt = adapter.composePrompt(lowRiskNode, plan);
    assert.ok(!prompt.includes('Risk RPN'));
  });
});

// ─── buildBatches (topological) ─────────────────────────────────────────────
suite('buildBatches', () => {
  test('produces 3 batches for the fixture DAG', () => {
    const plan = loadFixture();
    const batches = adapter.buildBatches(plan);
    // Expected: [n1] → [n2, n3] → [n4]
    assert.strictEqual(batches.length, 3);
  });

  test('first batch contains only n1', () => {
    const plan = loadFixture();
    const batches = adapter.buildBatches(plan);
    assert.deepStrictEqual(batches[0], ['n1']);
  });

  test('second batch contains n2 and n3 (parallel)', () => {
    const plan = loadFixture();
    const batches = adapter.buildBatches(plan);
    assert.strictEqual(batches[1].length, 2);
    assert.ok(batches[1].includes('n2'));
    assert.ok(batches[1].includes('n3'));
  });

  test('third batch contains only n4', () => {
    const plan = loadFixture();
    const batches = adapter.buildBatches(plan);
    assert.deepStrictEqual(batches[2], ['n4']);
  });

  test('detects cycles', () => {
    const plan = loadFixture();
    plan.dag.edges.push({ from: 'n4', to: 'n1', type: 'data_dependency' });
    assert.throws(() => adapter.buildBatches(plan), /[Cc]ycle/);
  });

  test('rejects edges to unknown nodes', () => {
    const plan = loadFixture();
    plan.dag.edges.push({ from: 'n4', to: 'nGhost', type: 'sequence' });
    assert.throws(() => adapter.buildBatches(plan), /unknown node/);
  });
});

// ─── parallel_groups validation ─────────────────────────────────────────────
suite('validateAgainstParallelGroups', () => {
  test('zero warnings for consistent fixture', () => {
    const plan = loadFixture();
    const batches = adapter.buildBatches(plan);
    const warnings = adapter.validateAgainstParallelGroups(batches, plan);
    assert.strictEqual(warnings.length, 0);
  });

  test('warns when parallel_group spans multiple batches', () => {
    const plan = loadFixture();
    // Make n2 depend on n3 — they can't be in same batch anymore
    plan.dag.edges.push({ from: 'n3', to: 'n2', type: 'sequence' });
    const batches = adapter.buildBatches(plan);
    const warnings = adapter.validateAgainstParallelGroups(batches, plan);
    assert.ok(warnings.length > 0);
    assert.ok(warnings[0].includes('parallel_group'));
  });
});

// ─── nodeToTask ─────────────────────────────────────────────────────────────
suite('nodeToTask', () => {
  test('maps capability → agent (with separator normalization)', () => {
    const plan = loadFixture();
    const node = plan.dag.nodes[0]; // course-creator:course-architect
    const task = adapter.nodeToTask(node, plan);
    assert.strictEqual(task.agent, 'course-creator--course-architect');
  });

  test('mode write when outputs produced', () => {
    const plan = loadFixture();
    const node = plan.dag.nodes[0];
    const task = adapter.nodeToTask(node, plan);
    assert.strictEqual(task.mode, 'write');
  });

  test('mode read when no outputs', () => {
    const plan = loadFixture();
    const node = plan.dag.nodes.find((n) => n.id === 'n4');
    const task = adapter.nodeToTask(node, plan);
    assert.strictEqual(task.mode, 'read');
  });

  test('effort derived from estimated_duration_minutes', () => {
    const plan = loadFixture();
    // n1: 45 min → effort 5
    const task = adapter.nodeToTask(plan.dag.nodes[0], plan);
    assert.strictEqual(task.effort, 5);
    // n3: 20 min → effort 4
    const task3 = adapter.nodeToTask(plan.dag.nodes.find((n) => n.id === 'n3'), plan);
    assert.strictEqual(task3.effort, 4);
  });

  test('file_set populated from outputs_produced', () => {
    const plan = loadFixture();
    const task = adapter.nodeToTask(plan.dag.nodes[0], plan);
    assert.deepStrictEqual(task.file_set, ['course-outline.md']);
  });

  test('checklist populated from quality_gate', () => {
    const plan = loadFixture();
    const task = adapter.nodeToTask(plan.dag.nodes[0], plan);
    assert.strictEqual(task.checklist, 'course-outline-checklist');
  });

  test('omits file_set when no outputs', () => {
    const plan = loadFixture();
    const task = adapter.nodeToTask(plan.dag.nodes.find((n) => n.id === 'n4'), plan);
    assert.strictEqual(task.file_set, undefined);
  });

  test('preserves traceability fields', () => {
    const plan = loadFixture();
    const task = adapter.nodeToTask(plan.dag.nodes[0], plan);
    assert.strictEqual(task._node_id, 'n1');
    assert.strictEqual(task._capability_ref, 'course-creator:course-architect');
  });
});

// ─── buildOutput integration ────────────────────────────────────────────────
suite('buildOutput integration', () => {
  test('produces complete payload for fixture', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    assert.strictEqual(out.plan_id, plan.plan_id);
    assert.strictEqual(out.metadata.total_nodes, 4);
    assert.strictEqual(out.metadata.total_batches, 3);
    assert.strictEqual(out.metadata.total_tasks, 4);
    assert.strictEqual(out.metadata.routing_decisions, 0);
    assert.strictEqual(out.warnings.length, 4);
    assert.ok(out.warnings.every((warning) => warning.includes('has no RoutingDecision')));
  });

  test('handoff is preserved from plan', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    assert.strictEqual(out.handoff.next_action_executor, '@dev');
    assert.deepStrictEqual(out.handoff.approvals_required, ['@po']);
  });

  test('batch durations computed', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    // batch-2 has n2 (90min) and n3 (20min) → wall time = max = 90
    assert.strictEqual(out.batches[1].estimated_duration_minutes, 90);
  });

  test('total wall time = sum of batch max durations', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    // 45 (n1) + 90 (max n2/n3) + 30 (n4) = 165
    assert.strictEqual(out.metadata.total_wall_time_estimate_minutes, 165);
  });

  test('RoutingDecision inline overrides legacy capability executor', () => {
    const plan = loadRoutingFixture();
    const out = adapter.buildOutput(plan);
    const task = out.batches[0].tasks[0];
    assert.strictEqual(task.agent, 'dev');
    assert.strictEqual(task.routing.decision_id, 'route-inline-v2');
    assert.strictEqual(task.routing.primary_executor, '@dev');
    assert.deepStrictEqual(task.support_agents, ['@architect']);
    assert.strictEqual(task.quality_gate_agent, '@qa');
    assert.strictEqual(out.metadata.routing_decisions, 1);
    assert.ok(task.prompt.includes('RoutingDecision v2'));
  });

  test('reports divergence between legacy capability and RoutingDecision executor', () => {
    const plan = loadRoutingFixture();
    const out = adapter.buildOutput(plan);
    assert.ok(out.warnings.some((warning) => warning.includes('legacy capability maps to "legacy-code-capability"')));
    assert.ok(out.warnings.some((warning) => warning.includes('selects "dev"')));
  });

  test('loads RoutingDecision by id from decisions directory', () => {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'plan-to-swarm-routing-'));
    try {
      const plan = clone(loadFixture());
      const decision = clone(loadRoutingFixture().selected_capabilities[0].routing.decision);
      decision.decision_id = 'route-file-v2';
      decision.selected.primary_executor = '@qa';
      decision.selected.quality_gate_agent = '@architect';
      fs.writeFileSync(path.join(tempDir, 'route-file-v2.json'), JSON.stringify(decision, null, 2));

      plan.selected_capabilities[0].routing_decision_id = 'route-file-v2';
      plan.dag.nodes[0].routing_decision_id = 'route-file-v2';

      const out = adapter.buildOutput(plan, { routingDecisionsDir: tempDir });
      const task = out.batches[0].tasks[0];
      assert.strictEqual(task.agent, 'qa');
      assert.strictEqual(task.routing.source, path.join(tempDir, 'route-file-v2.json'));
      assert.strictEqual(task.quality_gate_agent, '@architect');
    } finally {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  test('blocked RoutingDecision marks task and prevents swarm-input-only output', () => {
    const plan = clone(loadRoutingFixture());
    const decision = plan.selected_capabilities[0].routing.decision;
    decision.confidence = { score: 0.1, band: 'blocked' };
    decision.hard_gate_results = [{ id: 'boundary-protected-path', status: 'fail', reason: 'Protected path.' }];

    const out = adapter.buildOutput(plan);
    const task = out.batches[0].tasks[0];
    assert.strictEqual(task.blocked, true);
    assert.strictEqual(out.metadata.blocked_tasks, 1);
    assert.ok(out.warnings.some((warning) => warning.includes('blocked by hard gates')));
    assert.throws(() => adapter.selectBatch(out, 1, true), /blocked task/);
  });
});

// ─── selectBatch ────────────────────────────────────────────────────────────
suite('selectBatch', () => {
  test('returns full payload when no batch selected', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    const sel = adapter.selectBatch(out, null, false);
    assert.strictEqual(sel.batches.length, 3);
  });

  test('selects batch by index (1-based)', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    const sel = adapter.selectBatch(out, 2, false);
    assert.strictEqual(sel.batch.id, 'batch-2');
  });

  test('--swarm-input-only strips internal fields', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    const sel = adapter.selectBatch(out, 1, true);
    assert.ok(Array.isArray(sel));
    assert.strictEqual(sel.length, 1);
    assert.strictEqual(sel[0]._node_id, undefined);
    assert.strictEqual(sel[0]._capability_ref, undefined);
    assert.ok(sel[0].agent);
    assert.ok(sel[0].prompt);
    assert.ok(sel[0].mode);
  });

  test('throws on out-of-range batch', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    assert.throws(() => adapter.selectBatch(out, 99, false), /out of range/);
  });
});

// ─── formatOutput ───────────────────────────────────────────────────────────
suite('formatOutput', () => {
  test('json format produces parseable JSON', () => {
    const plan = loadFixture();
    const out = adapter.buildOutput(plan);
    const json = adapter.formatOutput(out, 'json');
    const parsed = JSON.parse(json);
    assert.strictEqual(parsed.plan_id, plan.plan_id);
  });
});

// ─── STORY-LC-3 / ADR-LC-002 — loop nodes ───────────────────────────────────
const validatePlan = require('../validate-plan');

test('LC-3: loop node compiles to a /loop-compiler directive, not a swarm task', () => {
  const node = { id: 'N9', capability_ref: 'x', phase: 'p', estimated_duration_minutes: 30,
    execution_kind: 'loop',
    loop_hint: { task: 'audit X until dry', termination_hint: 'until-dry', verification: 'critical' },
    outputs_produced: ['outputs/audit.md'] };
  const task = adapter.loopNodeToDirective(node);
  assert.strictEqual(task.loop, true, 'loop marker set');
  assert.strictEqual(task.agent, 'loop-compiler', 'routed to loop-compiler, not a capability agent');
  assert.strictEqual(task.mode, 'compile', 'compile != execute');
  assert.ok(/audit X until dry/.test(task.prompt), 'prompt carries the loop task');
  assert.deepStrictEqual(task.file_set, ['outputs/audit.md'], 'output threads to dependents (AC5)');
});

test('LC-3: nodeToTask dispatches a loop node via the directive path (AC3 exclusivity)', () => {
  const plan = { selected_capabilities: [], dag: { nodes: [] } };
  const node = { id: 'N1', capability_ref: 'some-squad--agent', phase: 'p', estimated_duration_minutes: 10,
    execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dod' } };
  const task = adapter.nodeToTask(node, plan);
  assert.strictEqual(task.loop, true);
  assert.strictEqual(task.agent, 'loop-compiler');
  assert.notStrictEqual(task.agent, 'some-squad--agent', 'never resolves to the capability agent');
});

test('LC-3: single node (default) is unchanged — no loop marker', () => {
  const plan = { selected_capabilities: [], dag: { nodes: [] } };
  const node = { id: 'N1', capability_ref: 'develop-story', phase: 'p', estimated_duration_minutes: 10 };
  const task = adapter.nodeToTask(node, plan);
  assert.notStrictEqual(task.loop, true, 'no loop marker on a single node');
  assert.notStrictEqual(task.mode, 'compile');
});

test('LC-3: validate-plan flags a loop node missing loop_hint (AC4/B)', () => {
  const plan = { dag: { nodes: [{ id: 'N1', execution_kind: 'loop' }] } };
  const { errors } = validatePlan.loopNodeCheck(plan);
  assert.ok(errors.some(e => e.type === 'LOOP_NODE_MISSING_HINT'), 'missing-hint error raised');
});

test('LC-3: validate-plan flags loop_hint without execution_kind:loop (AC4/A)', () => {
  const plan = { dag: { nodes: [{ id: 'N1', execution_kind: 'single', loop_hint: { task: 't', termination_hint: 'until-dry' } }] } };
  const { errors } = validatePlan.loopNodeCheck(plan);
  assert.ok(errors.some(e => e.type === 'LOOP_HINT_WITHOUT_LOOP_KIND'), 'misconfig error raised');
});

test('LC-3: valid loop node passes + surfaces the Class-C warrants-review warning', () => {
  const plan = { dag: { nodes: [{ id: 'N1', execution_kind: 'loop', loop_hint: { task: 'audit', termination_hint: 'until-dry' } }] } };
  const { errors, warnings } = validatePlan.loopNodeCheck(plan);
  assert.strictEqual(errors.length, 0, 'no errors for a valid loop node');
  assert.ok(warnings.some(w => w.type === 'LOOP_NODE_WARRANTS_REVIEW'), 'Class-C human gate surfaced');
});

test('LC-3: estimate-cost uses loop_hint.budget_tokens for a loop node (D7)', () => {
  const ec = require('../estimate-cost');
  const pricing = { models: { sonnet: { input_per_1k_tokens: 0.003, output_per_1k_tokens: 0.015 } } };
  const loopNode = { id: 'N1', execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dry', budget_tokens: 100000 } };
  const singleNode = { id: 'N2', capability_type: 'task' };
  const loopCost = ec.estimateNodeCost(loopNode, pricing, 'sonnet');
  const singleCost = ec.estimateNodeCost(singleNode, pricing, 'sonnet');
  assert.strictEqual(loopCost.tokens.loop, true, 'loop token marker set');
  assert.strictEqual(loopCost.tokens.input + loopCost.tokens.output, 100000, 'budget_tokens drives the estimate');
  assert.ok(loopCost.cost_usd > singleCost.cost_usd, 'a loop node costs more than a single task');
});

test('LC-3 (QA fix): validate-plan rejects a non-positive loop_hint.budget_tokens (-5 AND 0)', () => {
  // Hardening: cover the 0 boundary explicitly, not just negatives.
  for (const bad of [-5, 0]) {
    const plan = { dag: { nodes: [{ id: 'N1', execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dry', budget_tokens: bad } }] } };
    const { errors } = validatePlan.loopNodeCheck(plan);
    assert.ok(errors.some(e => e.type === 'LOOP_HINT_BAD_BUDGET'), `budget_tokens=${bad} rejected`);
  }
});

test('LC-3 (QA fix): absent OR explicit null budget_tokens is accepted', () => {
  // Hardening: cover explicit null, not just the missing field.
  const absent = { dag: { nodes: [{ id: 'N1', execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dry' } }] } };
  const explicitNull = { dag: { nodes: [{ id: 'N1', execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dry', budget_tokens: null } }] } };
  assert.strictEqual(validatePlan.loopNodeCheck(absent).errors.length, 0, 'unspecified budget is fine');
  assert.strictEqual(validatePlan.loopNodeCheck(explicitNull).errors.length, 0, 'explicit null budget is fine');
});

test('LC-4: classifier flags loop-shaped node as loop (recall)', () => {
  const { classifyLoopNode } = require('../classify-loop-node');
  assert.strictEqual(classifyLoopNode({ id: 'A', label: 'Audit every contract for missing clauses until none remain' }).kind, 'loop');
});

test('LC-4: classifier keeps a one-shot as single (precision)', () => {
  const { classifyLoopNode } = require('../classify-loop-node');
  assert.strictEqual(classifyLoopNode({ id: 'B', label: 'Draft a single launch post' }).kind, 'single');
});

test('LC-4: classifier flags ambiguous (never auto-types)', () => {
  const { classifyLoopNode, annotatePlan } = require('../classify-loop-node');
  assert.strictEqual(classifyLoopNode({ id: 'C', label: 'Process all the records' }).kind, 'ambiguous');
  const plan = { dag: { nodes: [{ id: 'C', label: 'Process all the records' }] } };
  annotatePlan(plan);
  assert.notStrictEqual(plan.dag.nodes[0].execution_kind, 'loop', 'ambiguous NOT auto-typed loop');
  assert.strictEqual(plan.dag.nodes[0].loop_candidate, true, 'flagged loop_candidate');
});

test('LC-4: validate-plan surfaces loop_candidate as Class-C warning (AC4 reuse)', () => {
  const plan = { dag: { nodes: [{ id: 'C', loop_candidate: true }] } };
  const { warnings } = validatePlan.loopNodeCheck(plan);
  assert.ok(warnings.some(w => w.type === 'LOOP_NODE_WARRANTS_REVIEW'), 'Class-C gate surfaced');
});

test('LC-4: classifier is deterministic', () => {
  const { classifyLoopNode } = require('../classify-loop-node');
  const node = { id: 'D', label: 'Enumerate all edge cases', loop_hint: { termination_hint: 'until-dry' } };
  assert.deepStrictEqual(classifyLoopNode(node), classifyLoopNode(node));
});

test('LC-4 (QA fix): annotate downgrades a preexisting loop that classifies ambiguous', () => {
  const { annotatePlan } = require('../classify-loop-node');
  const plan = { dag: { nodes: [{ id: 'C', label: 'Process all the records', execution_kind: 'loop' }] } };
  annotatePlan(plan);
  assert.notStrictEqual(plan.dag.nodes[0].execution_kind, 'loop', 'downgraded — ambiguous never routes as loop');
  assert.strictEqual(plan.dag.nodes[0].loop_candidate, true, 'flagged for Class-C review');
});

// ─── STORY-LC-5 — plan-run dry-run executor (W1+W2) ─────────────────────────
const planRun = require('../plan-run');

test('LC-5 W1: Kahn layers are topological', () => {
  const layers = planRun.computeLayers({ nodes: [{ id: 'A' }, { id: 'B', depends_on: ['A'] }], edges: [{ from: 'A', to: 'B' }] });
  assert.deepStrictEqual(layers, [['A'], ['B']]);
});

test('LC-5 W1: loop node dispatches to loop-compiler, single to swarm', () => {
  const plan = { dag: { nodes: [{ id: 'A', capability_ref: 'c' }, { id: 'B', execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dry' }, depends_on: ['A'] }], edges: [{ from: 'A', to: 'B' }] } };
  const r = planRun.planExecution(plan);
  assert.ok(r.steps.find(s => s.node === 'B').dispatch.includes('loop-compiler'));
  assert.ok(r.steps.find(s => s.node === 'A').dispatch.includes('swarm'));
});

test('LC-5 W2: first loop + budget-threshold + @devops authority pause', () => {
  const plan = { dag: { nodes: [
    { id: 'A', execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dry', budget_tokens: 150000 } },
    { id: 'B', label: 'deploy to staging', depends_on: ['A'] },
  ], edges: [{ from: 'A', to: 'B' }] } };
  const r = planRun.planExecution(plan);
  assert.ok(r.steps.find(s => s.node === 'A').pauses.includes('first-loop-review'));
  assert.ok(r.steps.find(s => s.node === 'A').pauses.some(p => p.startsWith('budget-threshold')));
  assert.ok(r.steps.find(s => s.node === 'B').pauses.some(p => p.includes('@devops')));
});

test('LC-5 W2: budget ceiling halts; kill-switch -> manual-handoff', () => {
  const plan = { dag: { nodes: [{ id: 'A', estimated_cost_tokens: 50000 }, { id: 'B', estimated_cost_tokens: 60000, depends_on: ['A'] }], edges: [{ from: 'A', to: 'B' }] } };
  assert.strictEqual(planRun.planExecution(plan, { budget_ceiling: 100000 }).halted, 'budget-ceiling');
  assert.strictEqual(planRun.planExecution(plan, { kill_switch: true }).mode, 'manual-handoff');
});

// ─── STORY-LC-7 — plan-to-workflow (live drive translator) ──────────────────
const p2w = require('../plan-to-workflow');
const lc7Plan = {
  plan_id: 'lc7-suite',
  dag: {
    nodes: [
      { id: 'n1', capability: 'analyst', label: 'discover' },
      { id: 'n2', execution_kind: 'loop', loop_hint: { task: 'sweep', termination_hint: 'until-dry', budget_tokens: 150000 }, depends_on: ['n1'] },
      { id: 'n3', capability: 'devops', label: 'deploy to prod', depends_on: ['n2'] },
    ],
    edges: [{ from: 'n1', to: 'n2' }, { from: 'n2', to: 'n3' }],
  },
};

test('LC-7: emits a Workflow that drives the plan in topological order', () => {
  const out = p2w.generate(lc7Plan);
  assert.match(out, /export const meta = \{/);
  assert.match(out, /const ORDER = \["n1","n2","n3"\]/);
});

test('LC-7: loop node -> /loop-compiler, single node -> /swarm-execute', () => {
  const out = p2w.generate(lc7Plan);
  assert.ok(out.includes('[LOOP NODE]') && out.includes('/loop-compiler'));
  assert.ok(out.includes('[SINGLE NODE]') && out.includes('/swarm-execute'));
});

test('LC-7 hardening: loop node does NOT mandate a nested Workflow (one-level limit)', () => {
  const out = p2w.generate(lc7Plan);
  assert.ok(out.includes('do NOT spawn a nested Workflow'), 'explicit nesting guard');
  assert.ok(!out.includes('EXECUTE the emitted Workflow'), 'no nested-Workflow execution mandate');
});

test('LC-7: gates bake (first-loop + @devops) and HALT-and-resume', () => {
  const out = p2w.generate(lc7Plan);
  assert.match(out, /"n2":"[^"]*first-loop-review/);
  assert.match(out, /"n3":"[^"]*agent-authority/);
  assert.match(out, /"n1":null/);                        // cheap plain single is not gated
  assert.ok(out.includes('return { paused: id'));         // gate halts the run
});

test('LC-7: plan_hash baked (review-ack binding) + threading + resume guard', () => {
  const out = p2w.generate(lc7Plan);
  assert.ok(out.includes('const PLAN_HASH = "' + planRun.planHash(lc7Plan) + '"'));
  assert.match(out, /"n2":\["n1"\]/);                     // n2 threads from n1
  assert.ok(out.includes('is not a node in the plan'));   // unknown FROM_NODE throws
});

test('LC-7: an unknown FROM_NODE THROWS at runtime (not just present in source)', () => {
  // Hardening: prove the guard actually fires — execute the emitted ORDER const + the synchronous FROM_NODE guard
  // expression with an unknown node and assert it throws (the guard runs before any await, so it is synchronous).
  const out = p2w.generate(lc7Plan);
  const orderLine = out.match(/const ORDER = \[[^\]]*\];/)[0];
  const guardExpr = out.match(/if \(FROM_NODE !== null[^\n]*\)\s*throw[^\n]*;/)[0];
  const prog = `${orderLine} const FROM_NODE = "ZZZ"; ${guardExpr}`;
  assert.throws(() => { new Function(prog)(); }, /is not a node in the plan/);
});

test('LC-7: emitted Workflow is syntactically valid in the runtime context', () => {
  const body = p2w.generate(lc7Plan).replace(/^export const/m, 'const');
  const wrapped = '(async function(agent,parallel,pipeline,phase,log){\n' + body + '\n})';
  assert.doesNotThrow(() => new Function('return ' + wrapped));
});

// ─── final report ──────────────────────────────────────────────────────────
console.log('\n──────────────────────────────────────');
console.log(`PASSED: ${passed}`);
console.log(`FAILED: ${failed}`);
console.log('──────────────────────────────────────');

if (failed > 0) {
  console.log('\nFailures:');
  for (const f of failures) {
    console.log(`  - ${f.name}`);
    console.log(`    ${f.error.stack || f.error.message}`);
  }
  process.exit(1);
}

process.exit(0);
