#!/usr/bin/env node
/**
 * validate-adapter-registry.js — deterministic validator and selector for execution adapters.
 *
 * Story: OG runtime closure Item 5
 * Contract: schemas/contracts/orchestration-adapter-registry.schema.json
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
const DEFAULT_REGISTRY = path.join(REPO_ROOT, 'squads/orquestrador-global/data/execution-adapter-registry.yaml');
const DEFAULT_SCHEMA = path.join(REPO_ROOT, 'schemas/contracts/orchestration-adapter-registry.schema.json');

function parseArgs(argv) {
  const args = {
    registry: DEFAULT_REGISTRY,
    schema: DEFAULT_SCHEMA,
    select: false,
    capabilities: [],
    constraints: [],
    includeBacklog: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--schema') args.schema = path.resolve(argv[++i]);
    else if (arg === '--select') args.select = true;
    else if (arg === '--capability') args.capabilities.push(argv[++i]);
    else if (arg === '--constraint') args.constraints.push(argv[++i]);
    else if (arg === '--include-backlog') args.includeBacklog = true;
    else args.registry = path.resolve(arg);
  }

  return args;
}

function loadRegistry(filePath) {
  return yaml.load(fs.readFileSync(filePath, 'utf8'));
}

function validateSchema(schemaPath, registry) {
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

function pathExists(relativePath) {
  if (!relativePath) return true;
  return fs.existsSync(path.resolve(REPO_ROOT, relativePath));
}

function validateSemantics(registry) {
  const errors = [];
  const seen = new Set();

  for (const adapter of registry.adapters || []) {
    if (seen.has(adapter.id)) {
      errors.push({
        type: 'DUPLICATE_ADAPTER_ID',
        adapter_id: adapter.id,
        message: `Duplicate adapter id: ${adapter.id}`,
      });
    }
    seen.add(adapter.id);

    for (const schemaField of ['input_schema', 'output_schema']) {
      if (adapter[schemaField] && !pathExists(adapter[schemaField])) {
        errors.push({
          type: 'SCHEMA_PATH_NOT_FOUND',
          adapter_id: adapter.id,
          field: schemaField,
          path: adapter[schemaField],
          message: `${schemaField} path does not exist: ${adapter[schemaField]}`,
        });
      }
    }

    for (const [key, value] of Object.entries(adapter.entrypoint || {})) {
      if (!value || /^https?:\/\//.test(value)) continue;
      const firstToken = value.split(/\s+/)[0];
      if (!pathExists(firstToken)) {
        errors.push({
          type: 'ENTRYPOINT_PATH_NOT_FOUND',
          adapter_id: adapter.id,
          field: key,
          path: firstToken,
          message: `entrypoint path does not exist: ${firstToken}`,
        });
      }
    }
  }

  return errors;
}

function selectAdapters(registry, args) {
  const unavailable = new Set(args.includeBacklog ? ['disabled'] : ['backlog', 'disabled']);
  return (registry.adapters || []).filter((adapter) => {
    if (unavailable.has(adapter.status)) return false;
    const hasCapabilities = args.capabilities.every((capability) => adapter.capabilities.includes(capability));
    const hasConstraints = args.constraints.every((constraint) => adapter.constraints.includes(constraint));
    return hasCapabilities && hasConstraints;
  }).map((adapter) => ({
    id: adapter.id,
    status: adapter.status,
    risk_level: adapter.risk_level,
    max_concurrent: adapter.max_concurrent,
    supports_parallel_nodes: adapter.supports_parallel_nodes,
  }));
}

function main() {
  const args = parseArgs(process.argv);
  const registry = loadRegistry(args.registry);
  const schemaResult = validateSchema(args.schema, registry);
  const semanticErrors = validateSemantics(registry);
  const errors = [...schemaResult.errors, ...semanticErrors];
  const selected_adapters = args.select ? selectAdapters(registry, args) : [];

  const result = {
    valid: errors.length === 0,
    registry: path.relative(REPO_ROOT, args.registry),
    adapter_count: ((registry || {}).adapters || []).length,
    errors,
    selected_adapters,
  };

  console.log(JSON.stringify(result, null, 2));

  if (errors.length > 0) process.exit(1);
  if (args.select && selected_adapters.length === 0) process.exit(1);
  process.exit(0);
}

if (require.main === module) main();

module.exports = {
  parseArgs,
  loadRegistry,
  validateSchema,
  validateSemantics,
  selectAdapters,
};
