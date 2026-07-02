#!/usr/bin/env node
/**
 * plan-run.js — STORY-LC-5 (EPIC-LOOP-AUTO) Waves 1+2 — DRY-RUN topological executor + guardrails.
 *
 * W1: parse a validated plan -> Kahn topological layers -> emit the execution sequence (single nodes ->
 *     plan-to-swarm/swarm-execute directive; loop nodes -> loop-compiler/Workflow directive). WITHOUT executing.
 * W2: guardrail layer — budget ceiling, pause posture (first-loop / budget-threshold / human-gate / @devops
 *     authority), kill-switch, resumable run-state (--from-node).
 *
 * W3 (LIVE dispatch via /swarm-execute + Workflow) is DEFERRED — this module never spawns an agent. It produces
 * the plan a human reviews (compile != execute). Deterministic. Dep: js-yaml (only for .yaml plans).
 *
 * API:  computeLayers(dag) · planExecution(plan, opts) · nodeBudget(node)
 * CLI:  node plan-run.js --plan <plan.json> [--budget-ceiling N] [--pause-budget N] [--from-node ID] | --self-test
 *       env PLAN_RUN_FORCE_MANUAL=1 -> kill-switch (autonomy off, manual-handoff plan).
 */
'use strict';

const PAUSE_BUDGET_DEFAULT = 100000;        // pause before any node above this budget
const LOOP_DEFAULT_BUDGET = 200000;          // a loop node with no declared budget
const SINGLE_DEFAULT_BUDGET = 6000;          // a single agent node estimate
const KILL_SWITCH_ENV = 'PLAN_RUN_FORCE_MANUAL';
const AUTHORITY_RE = /push|deploy|release/i;

/** Kahn topological layers over dag.nodes + edges (+ depends_on). Throws on cycle. */
function computeLayers(dag) {
  const ids = (dag.nodes || []).map(n => n.id);
  const known = new Set(ids);
  const indeg = {}; const adj = {};
  ids.forEach(id => { indeg[id] = 0; adj[id] = []; });
  // Hardening: an edge / depends_on referencing a NON-EXISTENT node must fail closed, not be silently dropped
  // (a dropped dependency lets a node run prematurely).
  const link = (from, to, src) => {
    if (!known.has(from) || !known.has(to)) throw new Error(`plan DAG references unknown node in ${src}: ${known.has(from) ? to : from}`);
    if (!adj[from].includes(to)) { adj[from].push(to); indeg[to]++; }
  };
  for (const e of (dag.edges || [])) link(e.from, e.to, `edge ${e.from}->${e.to}`);
  for (const n of (dag.nodes || [])) for (const d of (n.depends_on || [])) link(d, n.id, `depends_on of ${n.id}`);

  const layers = []; const seen = new Set();
  let frontier = ids.filter(id => indeg[id] === 0).sort();
  while (frontier.length) {
    layers.push(frontier.slice());
    frontier.forEach(id => seen.add(id));
    const next = [];
    for (const id of frontier) for (const m of adj[id]) { if (--indeg[m] === 0) next.push(m); }
    frontier = next.sort();
  }
  if (seen.size !== ids.length) throw new Error('cycle detected — plan DAG is not acyclic');
  return layers;
}

function nodeBudget(node) {
  if (node.execution_kind === 'loop') return (node.loop_hint && node.loop_hint.budget_tokens) || LOOP_DEFAULT_BUDGET;
  return node.estimated_cost_tokens || SINGLE_DEFAULT_BUDGET;
}

function nodePauses(node, budget, pauseBudget, firstLoopSeen) {
  const pauses = [];
  if (node.execution_kind === 'loop' && !firstLoopSeen) pauses.push('first-loop-review');         // compile!=execute
  if (budget > pauseBudget) pauses.push(`budget-threshold(${budget}>${pauseBudget})`);
  if (node.human_gate === true) pauses.push('human-gate');
  if (AUTHORITY_RE.test(JSON.stringify({ id: node.id, label: node.label || '', cap: node.capability_ref || '', agents: node.agents || [], action: node.action || '' }))) {
    pauses.push('agent-authority(@devops+approval)');                                              // G4 — never autonomous
  }
  return pauses;
}

/** W1+W2 dry-run planner. Returns the ordered execution plan with pauses, budget, run-state. Never executes. */
function planExecution(plan, opts = {}) {
  const dag = plan.dag || {};
  const nodeMap = new Map((dag.nodes || []).map(n => [n.id, n]));
  const layers = computeLayers(dag);
  const pauseBudget = opts.pause_budget || PAUSE_BUDGET_DEFAULT;
  const ceiling = opts.budget_ceiling || null;
  const fromNode = opts.from_node || null;

  // Hardening (LC-6): mirror the driveRun safeguard — an unknown --from-node must ERROR, not leave `resuming`
  // true and silently skip every node as a no-op dry-run.
  if (fromNode && !nodeMap.has(fromNode)) throw new Error(`--from-node "${fromNode}" is not a node in the plan`);

  if (opts.kill_switch) {
    return { mode: 'manual-handoff', reason: `kill-switch ${KILL_SWITCH_ENV} set — autonomy disabled; use the manual plan-architect-execution-handoff flow (G7).`, layers };
  }

  const steps = []; let cum = 0; let firstLoopSeen = false; let resuming = !!fromNode;
  for (let li = 0; li < layers.length; li++) {
    for (const id of layers[li]) {
      const node = nodeMap.get(id) || { id };
      if (resuming) {
        if (id === fromNode) resuming = false;
        else { steps.push({ layer: li, node: id, status: 'skipped-resume' }); continue; }
      }
      const isLoop = node.execution_kind === 'loop';
      const budget = nodeBudget(node);
      const pauses = nodePauses(node, budget, pauseBudget, firstLoopSeen);
      if (isLoop) firstLoopSeen = true;
      // Hardening (LC-7): mirror driveRun exactly — halt BEFORE debiting the halting node's budget, so the dry-run
      // and the live runner report the same cum_budget at the ceiling.
      const halt = ceiling && cum + budget > ceiling;
      if (!halt) cum += budget;
      steps.push({
        layer: li,
        node: id,
        kind: isLoop ? 'loop' : 'single',
        dispatch: isLoop ? 'loop-compiler->Workflow' : 'plan-to-swarm->/swarm-execute',
        node_budget: budget,
        cum_budget: cum,
        pauses,
        on_failure: node.on_failure || 'halt',
        outputs: node.outputs_produced || [],
        status: halt ? 'HALT-budget-ceiling' : 'planned',
      });
      if (halt) return { mode: 'dry-run', layers, steps, halted: 'budget-ceiling', cum_budget: cum, ceiling };
    }
  }
  return { mode: 'dry-run', layers, steps, total_budget: cum, ceiling };
}

// ── W3 — execution state machine (driveRun) ─────────────────────────────────
// Deterministic core of live execution: drives the plan in topological order through an INJECTED
// dispatcher (single→swarm / loop→Workflow live; or a fake for tests) and an approver (conductor / human).
// Enforces the W2 guardrails AT EXECUTION TIME: pause gates, budget ceiling, kill-switch, resume, output
// threading. The live /plan-run skill provides a real dispatcher; this module never spawns an agent itself.

function depsOf(node, plan) {
  const ds = new Set(node.depends_on || []);
  for (const e of ((plan.dag && plan.dag.edges) || [])) if (e.to === node.id) ds.add(e.from);
  return [...ds];
}

// STORY-LC-5 W3 hardening (live-audit finding g6): a stable hash of the plan's DAG structure. Bound into
// run-state so a resume against a DIVERGED plan (node inserted/renamed/removed) fails closed instead of
// silently replaying the wrong nodes.
function planHash(plan) {
  // Hardening (LC-7): hash the SEMANTIC fields that drive gating + dispatch, not just the DAG shape — so a change
  // to a node's behavior (budget, gate, capability, action, label) also invalidates a stale review-ack, not only a
  // topology edit. loop_hint carries budget_tokens + termination_hint.
  const nodes = (((plan.dag && plan.dag.nodes) || []).map(n => ({
    id: n.id,
    ek: n.execution_kind || 'single',
    deps: (n.depends_on || []).slice().sort(),
    loop_hint: n.loop_hint || null,
    human_gate: n.human_gate || false,
    cap: n.capability || n.capability_ref || null,
    action: n.action || null,
    label: n.label || null,
    cost: n.estimated_cost_tokens != null ? n.estimated_cost_tokens : null,  // Hardening: budget change invalidates ack
    agents: (n.agents || []).slice().sort(),                                  // Hardening: agent routing change invalidates ack
  }))).sort((a, b) => (a.id < b.id ? -1 : 1));
  const edges = (((plan.dag && plan.dag.edges) || []).map(e => `${e.from}->${e.to}`)).sort();
  return require('crypto').createHash('sha256').update(JSON.stringify({ nodes, edges })).digest('hex').slice(0, 16);
}

function initRunState(plan, opts = {}) {
  return {
    slug: plan.plan_id || plan.slug || 'run',
    plan_hash: planHash(plan),  // g6 — bind run-state to the plan structure
    order: computeLayers(plan.dag || {}).flat(),
    done: {},                 // nodeId -> output (external, resumable run-state)
    cum_budget: 0,
    pause_budget: opts.pause_budget || PAUSE_BUDGET_DEFAULT,
    budget_ceiling: opts.budget_ceiling || null,
    first_loop_seen: false,
    approved: opts.approved || {},
    review_acks: opts.review_acks || {},  // STORY-LC-6 (W3.1) — persisted review-ack tokens: nodeId -> {plan_hash, ts}
  };
}

// STORY-LC-6 (W3.1 — reify g2): the compile≠execute review pause as a fail-closed STRUCTURAL gate. A node's
// execute phase is gated on a persisted review-ack token bound to the CURRENT plan hash. A skipped / timed-out /
// headless review yields NO ack and therefore HALTS execution (default-deny). An ack "expires" when the plan
// changes (plan_hash mismatch), composing with g6.
function hasValidReviewAck(state, node, plan) {
  const ack = state.review_acks && state.review_acks[node.id];
  return !!ack && ack.plan_hash === planHash(plan);
}
function recordReviewAck(state, node, plan, ts) {
  state.review_acks = state.review_acks || {};
  state.review_acks[node.id] = { node_id: node.id, plan_hash: planHash(plan), ts: ts || null };
}

/** Inputs threaded from completed upstream nodes (LC-3 data_dependency edges / depends_on). */
function threadInputs(state, plan, node) {
  return depsOf(node, plan).map(id => ({ from: id, output: state.done[id] }));
}

/**
 * Drive a run. dispatcher({node, isLoop, inputs}) -> output (live: swarm/Workflow; tests: fake).
 * approver(nodeId, pauses) -> bool (conductor/human; tests: fake). Returns { trace, state, ... }.
 * Deterministic given a deterministic dispatcher/approver. NEVER spawns an agent itself (G2/G5).
 */
async function driveRun(plan, opts, dispatcher, approver) {
  const nodeMap = new Map(((plan.dag && plan.dag.nodes) || []).map(n => [n.id, n]));
  const state = initRunState(plan, opts);
  const trace = [];
  if (opts.kill_switch) { trace.push({ type: 'manual-handoff' }); return { trace, state, mode: 'manual-handoff' }; }
  const order = state.order;
  let startIdx = 0;
  if (opts.from_node) {
    // g6 (live-audit finding): a resume must be bound to the plan it was started against. If a persisted
    // run-state carries an expected_plan_hash that diverges from the current plan (node inserted/renamed/
    // removed), fail closed instead of replaying against a divergent DAG — unless the operator explicitly
    // acknowledges drift via allow_plan_drift.
    if (opts.expected_plan_hash && !opts.allow_plan_drift && opts.expected_plan_hash !== planHash(plan)) {
      throw new Error(`plan drift detected on resume — run-state plan_hash (${opts.expected_plan_hash}) does not match the current plan (${planHash(plan)}); pass allow_plan_drift to override`);
    }
    // Hardening QA fix: an unknown --from-node must ERROR, not silently restart the whole plan.
    startIdx = order.indexOf(opts.from_node);
    if (startIdx === -1) throw new Error(`--from-node "${opts.from_node}" is not a node in the plan`);
  }
  // Hardening: on resume, hydrate skipped nodes from the persisted run-state (opts.prior_outputs) so dependents
  // thread the REAL upstream output. A skipped node with no persisted output keeps a unique sentinel (a Symbol —
  // cannot collide with any real node output) and any dependent that needs it fails closed at dispatch (below).
  const RESUMED_SKIP = Symbol('resumed-skip');
  const priorOutputs = opts.prior_outputs || {};
  for (let i = 0; i < startIdx; i++) {
    const nid = order[i];
    state.done[nid] = Object.prototype.hasOwnProperty.call(priorOutputs, nid) ? priorOutputs[nid] : RESUMED_SKIP;
    trace.push({ type: 'skip-resume', node: nid, hydrated: state.done[nid] !== RESUMED_SKIP });
  }
  for (let i = startIdx; i < order.length; i++) {
    const id = order[i];
    const node = nodeMap.get(id) || { id };
    const isLoop = node.execution_kind === 'loop';
    const budget = nodeBudget(node);
    if (state.budget_ceiling && state.cum_budget + budget > state.budget_ceiling) {
      trace.push({ type: 'halt-budget', node: id, cum: state.cum_budget });
      return { trace, state, halted: 'budget-ceiling' };
    }
    const pauses = nodePauses(node, budget, state.pause_budget, state.first_loop_seen);
    if (isLoop) state.first_loop_seen = true;
    if (pauses.length) {
      // STORY-LC-6 (W3.1) — dispatch is gated on a valid review-ack for the CURRENT plan hash (fail-closed).
      // A persisted ack (from a prior run, matching plan_hash) lets the node proceed without re-prompting; an
      // expired ack (plan changed) or no ack forces the review NOW (approver / conductor resolution file). The
      // review outcome is recorded as an ack. No approval -> HALT (default-deny). This makes the pause a
      // STRUCTURAL gate, not just an in-memory default — a skipped/headless review cannot bypass execution.
      // Hardening: an in-memory pre-approval is plan_hash-SCOPED — approved[id] must equal the current plan hash
      // (or true === "this exact run's plan", coerced to the current hash). A stale/unscoped pre-approval from a
      // since-changed plan no longer applies (composes with g6) — it falls through to the live approver, fail-closed.
      const approvedFor = state.approved[id];
      const preApproved = approvedFor === planHash(plan) || approvedFor === true;
      if (hasValidReviewAck(state, node, plan)) {
        trace.push({ type: 'review-ack', node: id, source: 'persisted' });
      } else if (preApproved) {
        recordReviewAck(state, node, plan, opts.now);
        trace.push({ type: 'review-ack', node: id, source: 'pre-approved' });
      } else {
        const ok = approver ? await approver(id, pauses) : false;
        trace.push({ type: 'pause', node: id, pauses, approved: !!ok });
        if (!ok) return { trace, state, paused: id };
        recordReviewAck(state, node, plan, opts.now);
        trace.push({ type: 'review-ack', node: id, source: 'live' });
      }
    }
    const inputs = threadInputs(state, plan, node);
    // Hardening: fail closed if a dependency's threaded output is a resume sentinel (the upstream ran in a prior
    // run but its output was not persisted) — never dispatch a node on a placeholder input.
    const missing = inputs.find(x => x.output === RESUMED_SKIP);
    if (missing) throw new Error(`resume: node "${id}" needs the output of "${missing.from}", which was skipped without a persisted output — provide opts.prior_outputs["${missing.from}"] or resume from an earlier node`);
    const output = await dispatcher({ node, isLoop, inputs });
    state.done[id] = output;
    state.cum_budget += budget;
    trace.push({ type: 'dispatch', node: id, kind: isLoop ? 'loop' : 'single', deps: inputs.map(x => x.from), output });
  }
  return { trace, state, done: true, total_budget: state.cum_budget };
}

// ── self-test (deterministic, no agents) ───────────────────────────────────
async function selfTest() {
  const plan = {
    dag: {
      nodes: [
        { id: 'A', label: 'discover', capability_ref: 'c' },
        { id: 'B', execution_kind: 'loop', loop_hint: { task: 't', termination_hint: 'until-dry', budget_tokens: 150000 }, depends_on: ['A'] },
        { id: 'C', capability_ref: 'reviewer', depends_on: ['B'] },
        { id: 'D', capability_ref: 'worker', label: 'deploy to staging', depends_on: ['C'] },
      ],
      edges: [{ from: 'A', to: 'B' }, { from: 'B', to: 'C' }, { from: 'C', to: 'D' }],
    },
  };
  const checks = [];
  const r = planExecution(plan);
  checks.push(['layers are topological (A<B<C<D)', JSON.stringify(r.layers) === JSON.stringify([['A'], ['B'], ['C'], ['D']])]);
  checks.push(['loop node B -> loop-compiler dispatch', r.steps.find(s => s.node === 'B').dispatch.includes('loop-compiler')]);
  checks.push(['single node A -> swarm dispatch', r.steps.find(s => s.node === 'A').dispatch.includes('swarm')]);
  checks.push(['first loop pauses for review (W2)', r.steps.find(s => s.node === 'B').pauses.includes('first-loop-review')]);
  checks.push(['B above budget-threshold pauses', r.steps.find(s => s.node === 'B').pauses.some(p => p.startsWith('budget-threshold'))]);
  checks.push(['deploy node D -> @devops authority pause (G4)', r.steps.find(s => s.node === 'D').pauses.some(p => p.includes('@devops'))]);
  checks.push(['default on_failure = halt', r.steps.every(s => s.on_failure === 'halt')]);

  // budget ceiling halt
  const rc = planExecution(plan, { budget_ceiling: 100000 });
  checks.push(['budget ceiling halts the run', rc.halted === 'budget-ceiling']);

  // kill-switch
  const rk = planExecution(plan, { kill_switch: true });
  checks.push(['kill-switch -> manual-handoff (G7)', rk.mode === 'manual-handoff']);

  // resume
  const rr = planExecution(plan, { from_node: 'C' });
  checks.push(['--from-node skips before resume point', rr.steps.find(s => s.node === 'A').status === 'skipped-resume' && rr.steps.find(s => s.node === 'C').status === 'planned']);

  // Hardening (LC-6): an unknown --from-node in the dry-run path ERRORS, not a silent all-skip
  let badDryResume = false;
  try { planExecution(plan, { from_node: 'ZZZ' }); } catch (e) { badDryResume = /not a node/.test(e.message); }
  checks.push(['dry-run: unknown --from-node ERRORS (no silent all-skip)', badDryResume]);

  // cycle detection
  let cycleCaught = false;
  try { computeLayers({ nodes: [{ id: 'X' }, { id: 'Y' }], edges: [{ from: 'X', to: 'Y' }, { from: 'Y', to: 'X' }] }); }
  catch (e) { cycleCaught = /cycle/.test(e.message); }
  checks.push(['cycle detected', cycleCaught]);

  // determinism
  checks.push(['deterministic', JSON.stringify(planExecution(plan)) === JSON.stringify(planExecution(plan))]);

  // ── W3 driveRun (execution state machine) — fake dispatcher + auto-approver ──
  const dispatched = [];
  const fakeDispatch = async ({ node, inputs }) => { dispatched.push({ id: node.id, deps: inputs.map(x => x.from) }); return `out-${node.id}`; };
  const autoApprove = async () => true;

  const run = await driveRun(plan, {}, fakeDispatch, autoApprove);
  checks.push(['W3: drives all nodes in topological order', JSON.stringify(dispatched.map(d => d.id)) === JSON.stringify(['A', 'B', 'C', 'D'])]);
  checks.push(['W3: output threaded — C consumes B output', run.trace.find(t => t.node === 'C' && t.type === 'dispatch').deps.includes('B')]);
  checks.push(['W3: completes', run.done === true]);

  const runHalt = await driveRun(plan, { budget_ceiling: 100000 }, async () => 'x', autoApprove);
  checks.push(['W3: budget ceiling halts mid-run', runHalt.halted === 'budget-ceiling']);

  const runKill = await driveRun(plan, { kill_switch: true }, async () => 'x', autoApprove);
  checks.push(['W3: kill-switch -> manual-handoff', runKill.mode === 'manual-handoff']);

  const runDeny = await driveRun(plan, {}, async () => 'x', async () => false); // approver denies the first pause
  checks.push(['W3: denied approval pauses the run (no autonomy past a gate)', !!runDeny.paused]);

  const PRIOR = { A: 'out-A', B: 'out-B' };  // resume hydrates skipped nodes from persisted outputs
  const captured = {};
  const capDispatch = async ({ node, inputs }) => { captured[node.id] = inputs; return `out-${node.id}`; };
  const runResume = await driveRun(plan, { from_node: 'C', approved: { D: true }, prior_outputs: PRIOR }, capDispatch, autoApprove);
  checks.push(['W3: --from-node skips upstream (resume)', runResume.trace.some(t => t.type === 'skip-resume' && t.node === 'A')]);
  checks.push(['W3: resume threads the PERSISTED upstream VALUE (out-B), not a placeholder', (captured.C || []).some(x => x.from === 'B' && x.output === 'out-B') && runResume.done === true]);

  let resumeNoPrior = false;
  try { await driveRun(plan, { from_node: 'C', approved: { D: true } }, fakeDispatch, autoApprove); }
  catch (e) { resumeNoPrior = /needs the output of/.test(e.message); }
  checks.push(['W3: resume without the persisted upstream output FAILS CLOSED (no placeholder dispatch)', resumeNoPrior]);

  let badResume = false;
  try { await driveRun(plan, { from_node: 'ZZZ' }, fakeDispatch, autoApprove); } catch (e) { badResume = /not a node/.test(e.message); }
  checks.push(['W3: unknown --from-node ERRORS (no silent full restart)', badResume]);

  // ── W3 live-audit hardening (g7/g2/g6 — surfaced by the AC10 live e2e self-audit) ──
  // g7: the kill-switch is a TRUE executor-loop halt, not the conductor exit-0 semantics — assert NO node dispatched.
  const killDispatched = [];
  await driveRun(plan, { kill_switch: true }, async ({ node }) => { killDispatched.push(node.id); return 'x'; }, autoApprove);
  checks.push(['W3 g7: kill-switch dispatches ZERO nodes (true manual handoff, not just decision-router disarm)', killDispatched.length === 0]);

  // g2: a missing review (no approver) at a pause is fail-closed — the node MUST NOT execute (default-deny).
  const noApproverDispatched = [];
  const g2run = await driveRun(plan, {}, async ({ node }) => { noApproverDispatched.push(node.id); return 'x'; }, undefined);
  checks.push(['W3 g2: missing review (no approver) HALTS at the gate — node never executes (fail-closed)', !!g2run.paused && !noApproverDispatched.includes('B')]);

  // g6: resume against a DIVERGED plan fails closed unless drift is explicitly acknowledged.
  const hash = planHash(plan);
  let driftCaught = false;
  try { await driveRun(plan, { from_node: 'C', expected_plan_hash: 'deadbeefdeadbeef' }, fakeDispatch, autoApprove); }
  catch (e) { driftCaught = /plan drift/.test(e.message); }
  checks.push(['W3 g6: resume with a stale plan_hash HALTS (no replay against a divergent DAG)', driftCaught]);
  const driftOk = await driveRun(plan, { from_node: 'C', expected_plan_hash: hash, approved: { D: true }, prior_outputs: PRIOR }, fakeDispatch, autoApprove);
  checks.push(['W3 g6: resume with a MATCHING plan_hash proceeds', driftOk.done === true]);
  const driftOverride = await driveRun(plan, { from_node: 'C', expected_plan_hash: 'deadbeefdeadbeef', allow_plan_drift: true, approved: { D: true }, prior_outputs: PRIOR }, fakeDispatch, autoApprove);
  checks.push(['W3 g6: allow_plan_drift overrides the halt (explicit operator ack)', driftOverride.done === true]);

  // ── STORY-LC-6 (W3.1) — persisted review-ack: the compile≠execute pause as a fail-closed STRUCTURAL gate ──
  // A live approval RECORDS an ack bound to the current plan hash.
  const ackRun = await driveRun(plan, {}, fakeDispatch, autoApprove);
  checks.push(['W3.1: a live approval records a review-ack bound to the plan hash', !!ackRun.state.review_acks.B && ackRun.state.review_acks.B.plan_hash === planHash(plan)]);

  // A node with a VALID persisted ack proceeds WITHOUT re-prompting the approver (only B is pre-acked; D's
  // own @devops pause still routes through approval — so we assert B specifically was not re-prompted).
  const approverNodes = [];
  const trackingApprover = async (id) => { approverNodes.push(id); return true; };
  const preAck = { B: { node_id: 'B', plan_hash: planHash(plan), ts: null } };
  const ackProceed = await driveRun(plan, { review_acks: preAck }, fakeDispatch, trackingApprover);
  checks.push(['W3.1: a valid persisted review-ack lets the node proceed without re-prompting', ackProceed.done === true && !approverNodes.includes('B') && ackProceed.trace.some(t => t.type === 'review-ack' && t.node === 'B' && t.source === 'persisted')]);

  // An EXPIRED ack (wrong plan_hash) is invalid → with no approver the node HALTS (default-deny).
  const staleAck = { B: { node_id: 'B', plan_hash: 'staaaaaaaaaaaale', ts: null } };
  const staleDispatched = [];
  const ackStale = await driveRun(plan, { review_acks: staleAck }, async ({ node }) => { staleDispatched.push(node.id); return 'x'; }, undefined);
  checks.push(['W3.1: an expired review-ack (plan changed) blocks execution — re-pauses (fail-closed)', !!ackStale.paused && !staleDispatched.includes('B')]);

  // No ack + no approver → HALT before the gated node executes (the structural default-deny).
  const noAckDispatched = [];
  const ackMissing = await driveRun(plan, {}, async ({ node }) => { noAckDispatched.push(node.id); return 'x'; }, undefined);
  checks.push(['W3.1: a missing review-ack with no review HALTS — node never executes (structural gate)', !!ackMissing.paused && !noAckDispatched.includes('B')]);

  // A plan_hash-SCOPED pre-approval proceeds; a WRONG-hash (stale/unscoped) pre-approval is rejected (fail-closed).
  const scopedDispatched = [];
  const ackScoped = await driveRun(plan, { approved: { B: planHash(plan) } }, async ({ node }) => { scopedDispatched.push(node.id); return 'x'; }, undefined);
  checks.push(['W3.1: a plan_hash-scoped pre-approval proceeds (no approver needed)', scopedDispatched.includes('B')]);
  const wrongDispatched = [];
  const ackWrong = await driveRun(plan, { approved: { B: 'wronghashwronghash' } }, async ({ node }) => { wrongDispatched.push(node.id); return 'x'; }, undefined);
  checks.push(['W3.1: a wrong-plan_hash pre-approval is REJECTED — halts (no unscoped bypass)', !!ackWrong.paused && !wrongDispatched.includes('B')]);

  let pass = 0;
  for (const [name, ok] of checks) { console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}`); if (ok) pass++; }
  console.log(`\nself-test: ${pass}/${checks.length} passed`);
  process.exit(pass === checks.length ? 0 : 1);
}

function arg(name) { const i = process.argv.indexOf(name); return i !== -1 ? process.argv[i + 1] : null; }

function main() {
  if (process.argv.includes('--self-test')) return selfTest();
  const planPath = arg('--plan');
  if (!planPath) { console.error('Usage: plan-run.js --plan <plan> [--budget-ceiling N] [--pause-budget N] [--from-node ID] | --self-test'); process.exit(2); }
  const fs = require('fs');
  const raw = fs.readFileSync(planPath, 'utf8');
  const plan = /\.ya?ml$/.test(planPath) ? require('js-yaml').load(raw) : JSON.parse(raw);
  // Hardening QA fix: a present-but-invalid numeric flag must ERROR, never silently disable the guardrail.
  const numFlag = (name, def) => {
    const v = arg(name);
    if (v == null) return def;
    const n = Number(v);
    if (!Number.isFinite(n) || n <= 0) { console.error(`${name} must be a positive number (got ${JSON.stringify(v)})`); process.exit(2); }
    return n;
  };
  const opts = {
    budget_ceiling: numFlag('--budget-ceiling', null),
    pause_budget: numFlag('--pause-budget', PAUSE_BUDGET_DEFAULT),
    from_node: arg('--from-node'),
    kill_switch: process.env[KILL_SWITCH_ENV] === '1' || process.env[KILL_SWITCH_ENV] === 'true',
  };
  const result = planExecution(plan, opts);
  console.log(`=== plan-run DRY-RUN (W1+W2 — NOT executed; compile != execute) ===`);
  if (result.mode === 'manual-handoff') { console.log(result.reason); return; }
  console.log(`layers: ${result.layers.length} · total_budget(est): ${result.total_budget || result.cum_budget} tokens${result.halted ? ` · HALTED(${result.halted})` : ''}`);
  for (const s of result.steps) {
    if (s.status === 'skipped-resume') { console.log(`  [L${s.layer}] ${s.node}  (skipped — resume)`); continue; }
    const p = s.pauses.length ? `  ⏸ ${s.pauses.join(', ')}` : '';
    console.log(`  [L${s.layer}] ${s.node}  ${s.kind} -> ${s.dispatch}  (~${s.node_budget}tok)${p}${s.status !== 'planned' ? '  ' + s.status : ''}`);
  }
  console.log(`\nReview this plan, then execute via /plan-run (W3 — live dispatch, deferred). Pauses are approval gates.`);
}

if (require.main === module) main();
module.exports = { computeLayers, planExecution, nodeBudget, initRunState, threadInputs, driveRun, depsOf, planHash, hasValidReviewAck, recordReviewAck, nodePauses, PAUSE_BUDGET_DEFAULT };
