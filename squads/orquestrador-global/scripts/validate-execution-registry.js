#!/usr/bin/env node
/**
 * validate-execution-registry.js — deterministic validator for execution-registry.yaml.
 *
 * Story: OG runtime closure Item 6
 * Contract: schemas/contracts/orchestration-execution.schema.json
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
const DEFAULT_SCHEMA = path.join(REPO_ROOT, 'schemas/contracts/orchestration-execution.schema.json');
const DEFAULT_NODE_STATUS_SCHEMA = path.join(REPO_ROOT, 'schemas/contracts/orchestration-node-status.schema.json');

function parseArgs(argv) {
  const args = {
    registry: DEFAULT_REGISTRY,
    schema: DEFAULT_SCHEMA,
    nodeStatusSchema: DEFAULT_NODE_STATUS_SCHEMA,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--schema') args.schema = path.resolve(argv[++i]);
    else if (arg === '--node-status-schema') args.nodeStatusSchema = path.resolve(argv[++i]);
    else if (!args.registry) args.registry = path.resolve(arg);
    else args.registry = path.resolve(arg);
  }

  return args;
}

function loadRegistry(filePath) {
  return yaml.load(fs.readFileSync(filePath, 'utf8'));
}

function validateRegistrySchema(schemaPath, registry) {
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  const valid = validate(registry);
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

function validateSemantics(registry, args) {
  const errors = [];
  const warnings = [];
  const seenExecutions = new Set();
  const executions = registry.executions || [];

  if ((registry.metadata || {}).total_executions !== executions.length) {
    errors.push({
      type: 'TOTAL_EXECUTIONS_MISMATCH',
      message: `metadata.total_executions (${(registry.metadata || {}).total_executions}) does not match executions.length (${executions.length}).`,
    });
  }

  for (const execution of executions) {
    if (seenExecutions.has(execution.execution_id)) {
      errors.push({
        type: 'DUPLICATE_EXECUTION_ID',
        execution_id: execution.execution_id,
        message: `Duplicate execution_id: ${execution.execution_id}`,
      });
    }
    seenExecutions.add(execution.execution_id);

    const sidecarPath = path.resolve(REPO_ROOT, execution.node_status_path);
    if (!fs.existsSync(sidecarPath)) {
      errors.push({
        type: 'NODE_STATUS_NOT_FOUND',
        execution_id: execution.execution_id,
        path: execution.node_status_path,
        message: `node_status_path does not exist: ${execution.node_status_path}`,
      });
      continue;
    }

    const sidecar = loadStructuredFile(sidecarPath);
    const sidecarSchema = validateNodeStatusSchema(args.nodeStatusSchema, sidecar);
    const sidecarSemantics = validateNodeStatusSemantics(sidecar, { checkPlan: true });
    for (const error of [...sidecarSchema.errors, ...sidecarSemantics.errors]) {
      errors.push({
        type: 'NODE_STATUS_INVALID',
        execution_id: execution.execution_id,
        detail: error,
      });
    }
    warnings.push(...sidecarSemantics.warnings.map((warning) => ({
      ...warning,
      execution_id: execution.execution_id,
    })));

    if (sidecar.execution_id !== execution.execution_id) {
      errors.push({
        type: 'EXECUTION_ID_MISMATCH',
        execution_id: execution.execution_id,
        sidecar_execution_id: sidecar.execution_id,
        message: 'Registry execution_id does not match sidecar execution_id.',
      });
    }

    if (sidecar.plan_id !== execution.plan_id) {
      errors.push({
        type: 'PLAN_ID_MISMATCH',
        execution_id: execution.execution_id,
        plan_id: execution.plan_id,
        sidecar_plan_id: sidecar.plan_id,
        message: 'Registry plan_id does not match sidecar plan_id.',
      });
    }

    if (sidecar.status_aggregate !== execution.status) {
      errors.push({
        type: 'STATUS_MISMATCH',
        execution_id: execution.execution_id,
        status: execution.status,
        sidecar_status: sidecar.status_aggregate,
        message: 'Registry status does not match sidecar status_aggregate.',
      });
    }

    if ((sidecar.nodes || []).length !== execution.node_count) {
      errors.push({
        type: 'NODE_COUNT_MISMATCH',
        execution_id: execution.execution_id,
        node_count: execution.node_count,
        sidecar_node_count: (sidecar.nodes || []).length,
        message: 'Registry node_count does not match sidecar nodes length.',
      });
    }

    const sidecarNodeStatus = new Map((sidecar.nodes || []).map((node) => [node.node_id, node.status]));
    for (const node of execution.nodes || []) {
      if (sidecarNodeStatus.get(node.node_id) !== node.status) {
        errors.push({
          type: 'NODE_STATUS_MISMATCH',
          execution_id: execution.execution_id,
          node_id: node.node_id,
          status: node.status,
          sidecar_status: sidecarNodeStatus.get(node.node_id) || null,
          message: 'Registry node status does not match sidecar node status.',
        });
      }
    }
  }

  return { errors, warnings };
}

function main() {
  const args = parseArgs(process.argv);
  const registry = loadRegistry(args.registry);
  const schemaResult = validateRegistrySchema(args.schema, registry);
  const semanticResult = validateSemantics(registry, args);
  const errors = [...schemaResult.errors, ...semanticResult.errors];

  const result = {
    valid: errors.length === 0,
    registry: path.relative(REPO_ROOT, args.registry),
    execution_count: ((registry || {}).executions || []).length,
    errors,
    warnings: semanticResult.warnings,
  };

  console.log(JSON.stringify(result, null, 2));
  process.exit(result.valid ? 0 : 1);
}

if (require.main === module) main();

module.exports = {
  parseArgs,
  loadRegistry,
  validateRegistrySchema,
  validateSemantics,
};
