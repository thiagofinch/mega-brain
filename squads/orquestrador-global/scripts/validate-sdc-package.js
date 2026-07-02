#!/usr/bin/env node
/**
 * validate-sdc-package.js — deterministic validator for plan-to-sdc output.
 *
 * Story: OG-88.9
 * Contract: schemas/contracts/orchestration-sdc-package.schema.json
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
const DEFAULT_SCHEMA = path.join(REPO_ROOT, 'schemas/contracts/orchestration-sdc-package.schema.json');

function parseArgs(argv) {
  const args = {
    manifest: null,
    schema: DEFAULT_SCHEMA,
    skipFiles: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--schema') args.schema = path.resolve(argv[++i]);
    else if (arg === '--skip-files') args.skipFiles = true;
    else if (!args.manifest) args.manifest = path.resolve(arg);
    else throw new Error(`Unexpected argument: ${arg}`);
  }

  if (!args.manifest) {
    throw new Error('Usage: validate-sdc-package.js <manifest.yaml|manifest.json> [--schema <schema>] [--skip-files]');
  }

  return args;
}

function loadStructuredFile(filePath) {
  const src = fs.readFileSync(filePath, 'utf8');
  if (filePath.endsWith('.json')) return JSON.parse(src);
  return yaml.load(src);
}

function validateSchema(schemaPath, manifest) {
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  const valid = validate(manifest);
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

function loadSourcePlan(manifest) {
  const planPath = path.resolve(REPO_ROOT, manifest.source_plan_path);
  if (!fs.existsSync(planPath)) return { plan: null, error: `source_plan_path does not exist: ${manifest.source_plan_path}` };
  return { plan: loadStructuredFile(planPath), error: null };
}

function validateSemantics(manifest, args) {
  const errors = [];
  const warnings = [];
  const units = manifest.sdc_units || [];
  const storyIds = new Set();
  const nodeIds = new Set();

  if (manifest.execution_policy && manifest.execution_policy.auto_execute !== false) {
    errors.push({ type: 'AUTO_EXECUTE_NOT_ALLOWED', message: 'execution_policy.auto_execute must be false.' });
  }

  for (const unit of units) {
    if (storyIds.has(unit.story_id)) {
      errors.push({ type: 'DUPLICATE_STORY_ID', story_id: unit.story_id });
    }
    storyIds.add(unit.story_id);
    nodeIds.add(unit.node_id);

    for (const dependency of unit.depends_on || []) {
      if (!storyIds.has(dependency) && !units.some((candidate) => candidate.story_id === dependency)) {
        errors.push({
          type: 'UNKNOWN_STORY_DEPENDENCY',
          story_id: unit.story_id,
          dependency,
        });
      }
    }
  }

  const { plan, error } = loadSourcePlan(manifest);
  if (error) {
    errors.push({ type: 'SOURCE_PLAN_NOT_FOUND', message: error });
  } else {
    const planNodeIds = new Set((((plan || {}).dag || {}).nodes || []).map((node) => node.id));
    if (plan.plan_id !== manifest.plan_id) {
      errors.push({
        type: 'PLAN_ID_MISMATCH',
        plan_id: manifest.plan_id,
        source_plan_id: plan.plan_id,
      });
    }
    for (const nodeId of nodeIds) {
      if (!planNodeIds.has(nodeId)) {
        errors.push({ type: 'UNKNOWN_PLAN_NODE', node_id: nodeId });
      }
    }
    if (manifest.audit && manifest.audit.node_count !== planNodeIds.size) {
      errors.push({
        type: 'NODE_COUNT_MISMATCH',
        manifest_count: manifest.audit.node_count,
        source_plan_count: planNodeIds.size,
      });
    }
  }

  if (!args.skipFiles) {
    const fileRefs = [
      manifest.outputs && manifest.outputs.manifest,
      manifest.outputs && manifest.outputs.idea_sop,
      manifest.outputs && manifest.outputs.epic,
      ...((manifest.outputs && manifest.outputs.stories) || []).map((ref) => ref.path),
      ...((manifest.outputs && manifest.outputs.handoffs) || []).map((ref) => ref.path),
      ...units.flatMap((unit) => [unit.story_path, unit.handoff_path]),
    ].filter(Boolean);

    for (const fileRef of [...new Set(fileRefs)]) {
      const absolute = path.resolve(REPO_ROOT, fileRef);
      if (!fs.existsSync(absolute)) {
        errors.push({ type: 'OUTPUT_FILE_NOT_FOUND', path: fileRef });
      }
    }

    for (const unit of units) {
      const storyPath = path.resolve(REPO_ROOT, unit.story_path);
      if (fs.existsSync(storyPath)) {
        const story = fs.readFileSync(storyPath, 'utf8');
        if (!story.includes(unit.story_id)) {
          errors.push({ type: 'STORY_ID_NOT_RENDERED', story_id: unit.story_id, path: unit.story_path });
        }
        if (!/status:\s*Draft/.test(story)) {
          errors.push({ type: 'STORY_NOT_DRAFT', story_id: unit.story_id, path: unit.story_path });
        }
      }
    }
  } else {
    warnings.push({ type: 'FILES_SKIPPED', message: 'Output file existence checks skipped by flag.' });
  }

  return { errors, warnings };
}

function validatePackage(args) {
  const manifest = loadStructuredFile(args.manifest);
  const schemaResult = validateSchema(args.schema, manifest);
  const semanticResult = validateSemantics(manifest, args);
  const errors = [...schemaResult.errors, ...semanticResult.errors];
  return {
    valid: errors.length === 0,
    package_id: manifest.package_id || null,
    plan_id: manifest.plan_id || null,
    unit_count: ((manifest || {}).sdc_units || []).length,
    errors,
    warnings: semanticResult.warnings,
  };
}

function main() {
  try {
    const result = validatePackage(parseArgs(process.argv));
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.valid ? 0 : 1);
  } catch (error) {
    console.error(JSON.stringify({ valid: false, error: error.message }, null, 2));
    process.exit(1);
  }
}

if (require.main === module) main();

module.exports = {
  parseArgs,
  validateSchema,
  validateSemantics,
  validatePackage,
};
