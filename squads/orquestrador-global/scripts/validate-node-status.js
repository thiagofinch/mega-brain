#!/usr/bin/env node
/**
 * validate-node-status.js — deterministic validator for orchestration node status sidecars.
 *
 * Story: OG runtime closure Item 3
 * Contract: schemas/contracts/orchestration-node-status.schema.json
 */
'use strict';

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const Ajv2020 = require('ajv/dist/2020');

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
const DEFAULT_SCHEMA = path.join(REPO_ROOT, 'schemas/contracts/orchestration-node-status.schema.json');

function parseArgs(argv) {
  const args = {
    status: null,
    schema: DEFAULT_SCHEMA,
    checkPlan: true,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--schema') args.schema = path.resolve(argv[++i]);
    else if (arg === '--no-plan-check') args.checkPlan = false;
    else if (!args.status) args.status = path.resolve(arg);
  }

  return args;
}

function loadStructuredFile(filePath) {
  const source = fs.readFileSync(filePath, 'utf8');
  if (filePath.endsWith('.json')) return JSON.parse(source);
  return yaml.load(source);
}

function isoMs(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isNaN(ms) ? null : ms;
}

function validateSchema(schemaPath, document) {
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  const valid = validate(document);
  return {
    valid,
    errors: valid ? [] : validate.errors.map((error) => ({
      type: 'SCHEMA',
      path: error.instancePath || '/',
      message: error.message,
      params: error.params,
    })),
  };
}

function loadPlanNodeIds(statusDocument) {
  if (!statusDocument.source_plan_path) return { nodeIds: null, warning: null };

  const planPath = path.resolve(REPO_ROOT, statusDocument.source_plan_path);
  if (!fs.existsSync(planPath)) {
    return {
      nodeIds: null,
      warning: {
        type: 'PLAN_NOT_FOUND',
        message: `source_plan_path does not exist: ${statusDocument.source_plan_path}`,
      },
    };
  }

  const plan = loadStructuredFile(planPath);
  const nodes = ((plan || {}).dag || {}).nodes || [];
  return {
    nodeIds: new Set(nodes.map((node) => node.id).filter(Boolean)),
    warning: null,
  };
}

function validateSemantics(document, options = {}) {
  const errors = [];
  const warnings = [];
  const seenNodes = new Set();

  let planNodeIds = null;
  if (options.checkPlan) {
    const loaded = loadPlanNodeIds(document);
    planNodeIds = loaded.nodeIds;
    if (loaded.warning) warnings.push(loaded.warning);
  }

  for (const node of document.nodes || []) {
    if (seenNodes.has(node.node_id)) {
      errors.push({
        type: 'DUPLICATE_NODE_ID',
        node_id: node.node_id,
        message: `Duplicate node_id: ${node.node_id}`,
      });
    }
    seenNodes.add(node.node_id);

    if (planNodeIds && !planNodeIds.has(node.plan_node_ref)) {
      errors.push({
        type: 'UNKNOWN_PLAN_NODE_REF',
        node_id: node.node_id,
        plan_node_ref: node.plan_node_ref,
        message: `plan_node_ref not found in source plan: ${node.plan_node_ref}`,
      });
    }

    const history = node.history || [];
    const last = history[history.length - 1];
    if (last && last.status !== node.status) {
      errors.push({
        type: 'LAST_HISTORY_STATUS_MISMATCH',
        node_id: node.node_id,
        message: `Last history status (${last.status}) does not match node status (${node.status}).`,
      });
    }

    if (last && last.event_type !== node.last_event_type) {
      errors.push({
        type: 'LAST_EVENT_TYPE_MISMATCH',
        node_id: node.node_id,
        message: `Last history event (${last.event_type}) does not match last_event_type (${node.last_event_type}).`,
      });
    }

    const startedMs = isoMs(node.started_at);
    const finishedMs = isoMs(node.finished_at);
    if (startedMs !== null && finishedMs !== null && finishedMs < startedMs) {
      errors.push({
        type: 'FINISHED_BEFORE_STARTED',
        node_id: node.node_id,
        message: 'finished_at is earlier than started_at.',
      });
    }

    for (let i = 1; i < history.length; i++) {
      const previous = isoMs(history[i - 1].at);
      const current = isoMs(history[i].at);
      if (previous !== null && current !== null && current < previous) {
        errors.push({
          type: 'HISTORY_OUT_OF_ORDER',
          node_id: node.node_id,
          event_id: history[i].event_id,
          message: 'History events must be chronological.',
        });
      }
    }
  }

  return { errors, warnings };
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.status) {
    console.error('Usage: validate-node-status.js <status.yaml|json> [--schema <schema.json>] [--no-plan-check]');
    process.exit(2);
  }

  const document = loadStructuredFile(args.status);
  const schemaResult = validateSchema(args.schema, document);
  const semanticResult = validateSemantics(document, { checkPlan: args.checkPlan });
  const errors = [...schemaResult.errors, ...semanticResult.errors];

  const result = {
    valid: errors.length === 0,
    execution_id: document.execution_id || null,
    plan_id: document.plan_id || null,
    node_count: Array.isArray(document.nodes) ? document.nodes.length : 0,
    errors,
    warnings: semanticResult.warnings,
  };

  console.log(JSON.stringify(result, null, 2));
  process.exit(result.valid ? 0 : 1);
}

if (require.main === module) main();

module.exports = {
  parseArgs,
  loadStructuredFile,
  validateSchema,
  validateSemantics,
};
