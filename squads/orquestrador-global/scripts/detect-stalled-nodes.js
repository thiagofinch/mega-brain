#!/usr/bin/env node
/**
 * detect-stalled-nodes.js — heartbeat/stall detector + replan proposal emitter.
 *
 * Story: OG runtime closure Item 4
 * Contracts:
 *   - squads/orquestrador-global/data/execution-registry.yaml
 *   - schemas/contracts/orchestration-replan-proposal.schema.json
 */
'use strict';

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const Ajv2020 = require('ajv/dist/2020');
const {
  loadStructuredFile,
  validateSchema: validateNodeStatusSchema,
  validateSemantics: validateNodeStatusSemantics,
} = require('./validate-node-status');

let addFormats;
try {
  addFormats = require('ajv-formats');
} catch {
  addFormats = (ajv) => {
    ajv.addFormat('date-time', {
      type: 'string',
      validate: (value) => !Number.isNaN(Date.parse(value)),
    });
  };
}

const REPO_ROOT = path.resolve(__dirname, '../../..');
const DEFAULT_REGISTRY = path.join(REPO_ROOT, 'squads/orquestrador-global/data/execution-registry.yaml');
const DEFAULT_NODE_STATUS_SCHEMA = path.join(REPO_ROOT, 'schemas/contracts/orchestration-node-status.schema.json');
const DEFAULT_REPLAN_SCHEMA = path.join(REPO_ROOT, 'schemas/contracts/orchestration-replan-proposal.schema.json');

function parseArgs(argv) {
  const args = {
    registry: DEFAULT_REGISTRY,
    nodeStatusSchema: DEFAULT_NODE_STATUS_SCHEMA,
    replanSchema: DEFAULT_REPLAN_SCHEMA,
    now: new Date().toISOString(),
    timeoutMultiplier: 1,
    minTimeoutMinutes: 5,
    output: null,
    expectStalled: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--node-status-schema') args.nodeStatusSchema = path.resolve(argv[++i]);
    else if (arg === '--replan-schema') args.replanSchema = path.resolve(argv[++i]);
    else if (arg === '--now') args.now = argv[++i];
    else if (arg === '--timeout-multiplier') args.timeoutMultiplier = parseFloat(argv[++i]);
    else if (arg === '--min-timeout-minutes') args.minTimeoutMinutes = parseFloat(argv[++i]);
    else if (arg === '--output') args.output = path.resolve(argv[++i]);
    else if (arg === '--expect-stalled') args.expectStalled = true;
    else args.registry = path.resolve(arg);
  }

  return args;
}

function loadYaml(filePath) {
  return yaml.load(fs.readFileSync(filePath, 'utf8'));
}

function validateProposalSchema(schemaPath, proposal) {
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  const valid = validate(proposal);
  return {
    valid,
    errors: valid ? [] : validate.errors.map((error) => ({
      path: error.instancePath || '/',
      message: error.message,
      params: error.params,
    })),
  };
}

function dateStamp(iso) {
  const d = new Date(iso);
  return [
    d.getUTCFullYear(),
    String(d.getUTCMonth() + 1).padStart(2, '0'),
    String(d.getUTCDate()).padStart(2, '0'),
  ].join('') + '-' + [
    String(d.getUTCHours()).padStart(2, '0'),
    String(d.getUTCMinutes()).padStart(2, '0'),
    String(d.getUTCSeconds()).padStart(2, '0'),
  ].join('');
}

function minutesBetween(laterIso, earlierIso) {
  return (Date.parse(laterIso) - Date.parse(earlierIso)) / 60000;
}

function planNodeById(plan) {
  return new Map(((((plan || {}).dag || {}).nodes) || []).map((node) => [node.id, node]));
}

function loadExecutionContext(execution, args) {
  const sidecarPath = path.resolve(REPO_ROOT, execution.node_status_path);
  const sidecar = loadStructuredFile(sidecarPath);
  const sidecarSchema = validateNodeStatusSchema(args.nodeStatusSchema, sidecar);
  const sidecarSemantics = validateNodeStatusSemantics(sidecar, { checkPlan: true });
  const errors = [...sidecarSchema.errors, ...sidecarSemantics.errors];
  if (errors.length > 0) {
    return { execution, sidecar, plan: null, errors };
  }

  const planPath = path.resolve(REPO_ROOT, sidecar.source_plan_path);
  const plan = fs.existsSync(planPath) ? loadYaml(planPath) : null;
  return { execution, sidecar, plan, errors: [] };
}

function detectStalls(registry, args) {
  const contexts = [];
  const stalled = [];
  const errors = [];

  for (const execution of registry.executions || []) {
    if (!['in_progress', 'partially_completed'].includes(execution.status)) continue;
    const context = loadExecutionContext(execution, args);
    contexts.push(context);
    if (context.errors.length > 0) {
      errors.push({ execution_id: execution.execution_id, errors: context.errors });
      continue;
    }

    const planNodes = planNodeById(context.plan);
    for (const node of context.sidecar.nodes || []) {
      if (node.status !== 'running') continue;
      const planNode = planNodes.get(node.plan_node_ref) || {};
      const estimated = Number(planNode.estimated_duration_minutes || 0);
      const timeout = Math.max(args.minTimeoutMinutes, estimated * args.timeoutMultiplier);
      const heartbeat = node.heartbeat_at || node.started_at;
      if (!heartbeat) continue;
      const elapsed = minutesBetween(args.now, heartbeat);
      if (elapsed > timeout) {
        stalled.push({
          execution_id: execution.execution_id,
          plan_id: execution.plan_id,
          node_id: node.node_id,
          status: node.status,
          elapsed_since_heartbeat_minutes: Number(elapsed.toFixed(2)),
          timeout_minutes: Number(timeout.toFixed(2)),
        });
      }
    }
  }

  return { stalled, errors, contexts };
}

function buildProposal(stalled, args) {
  const first = stalled[0];
  const affectedNodes = stalled.map((node) => ({
    node_id: node.node_id,
    status: node.status,
    elapsed_since_heartbeat_minutes: node.elapsed_since_heartbeat_minutes,
    timeout_minutes: node.timeout_minutes,
  }));
  const replaceNodes = affectedNodes.map((node) => node.node_id);

  return {
    schema_version: '1.0',
    proposal_id: `replan-${first.execution_id}-${dateStamp(args.now)}`,
    status: 'proposed',
    plan_id: first.plan_id,
    execution_id: first.execution_id,
    created_at: args.now,
    trigger: {
      type: 'stalled_node',
      detected_at: args.now,
      reason: `Detected ${stalled.length} running node(s) past heartbeat timeout.`,
    },
    classification: 'needs_replan',
    affected_nodes: affectedNodes,
    human_gate_required: false,
    gate_owner: null,
    recommended_actions: [
      {
        type: 'inspect_node',
        owner: '@qa',
        description: 'Inspect stalled node evidence and confirm whether the worker is still alive.',
      },
      {
        type: 'replan_node',
        owner: 'orquestrador-global--plan-architect',
        description: 'Emit a revised sidecar/plan proposal for affected nodes only.',
      },
    ],
    plan_diff: {
      summary: 'Preserve completed nodes and propose replanning only the stalled running nodes.',
      preserve_nodes: [],
      replace_nodes: replaceNodes,
      add_nodes: [],
      remove_nodes: [],
    },
  };
}

function main() {
  const args = parseArgs(process.argv);
  const registry = loadYaml(args.registry);
  const detection = detectStalls(registry, args);
  let proposal = null;
  let proposalValidation = { valid: true, errors: [] };

  if (detection.stalled.length > 0) {
    proposal = buildProposal(detection.stalled, args);
    proposalValidation = validateProposalSchema(args.replanSchema, proposal);
    if (proposalValidation.valid && args.output) {
      fs.mkdirSync(path.dirname(args.output), { recursive: true });
      fs.writeFileSync(args.output, yaml.dump(proposal, { lineWidth: 120, noRefs: true }), 'utf8');
    }
  }

  const result = {
    valid: detection.errors.length === 0 && proposalValidation.valid,
    registry: path.relative(REPO_ROOT, args.registry),
    now: args.now,
    stalled_count: detection.stalled.length,
    stalled_nodes: detection.stalled,
    proposal_path: args.output ? path.relative(REPO_ROOT, args.output) : null,
    proposal_valid: proposalValidation.valid,
    errors: [...detection.errors, ...proposalValidation.errors],
  };

  console.log(JSON.stringify(result, null, 2));
  if (!result.valid) process.exit(1);
  if (args.expectStalled && detection.stalled.length === 0) process.exit(1);
  process.exit(0);
}

if (require.main === module) main();

module.exports = {
  parseArgs,
  detectStalls,
  buildProposal,
  validateProposalSchema,
};
