#!/usr/bin/env node
/**
 * emit-execution-log.js — Append entry to pipeline-execution-log.yaml
 *
 * Story: W8-4 (Wave 8) — closes DEV-OG-005 / M10 (Observabilidade)
 * Consumer: audit-plan.js (called after each plan-architect emission)
 *
 * Schema: see data/pipeline-execution-log.yaml schema section.
 * Mandatory fields: plan_id, timestamp, mode, duration_seconds, cost_actual_usd, quality_score_overall.
 *
 * Usage:
 *   node emit-execution-log.js \
 *     --plan-id <id> --mode <SIMPLE|STANDARD|COMPLEX|CRITICAL|DRY-RUN> \
 *     --duration <seconds> --cost <usd> --quality <0-5> \
 *     [--meta-axiomas <0-1>] [--drift] [--veto-reason <text>] \
 *     [--elicitations <count>] [--models-used <json>]
 */
'use strict';

const fs = require('fs');
const path = require('path');

const SCRIPT_DIR = __dirname;
const LOG_PATH = path.resolve(SCRIPT_DIR, '../data/pipeline-execution-log.yaml');

function parseArgs(argv) {
  const args = {
    plan_id: null,
    mode: null,
    duration_seconds: null,
    cost_actual_usd: null,
    quality_score_overall: null,
    meta_axiomas_overall: null,
    drift_detected: false,
    veto_triggered: false,
    veto_reasons: [],
    elicitations_count: 0,
    human_signoff_required: false,
    human_signoff_received: false,
    models_used: null,
    dryRun: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--plan-id') args.plan_id = argv[++i];
    else if (a === '--mode') args.mode = argv[++i];
    else if (a === '--duration') args.duration_seconds = parseInt(argv[++i], 10);
    else if (a === '--cost') args.cost_actual_usd = parseFloat(argv[++i]);
    else if (a === '--quality') args.quality_score_overall = parseFloat(argv[++i]);
    else if (a === '--meta-axiomas') args.meta_axiomas_overall = parseFloat(argv[++i]);
    else if (a === '--drift') args.drift_detected = true;
    else if (a === '--veto-reason') { args.veto_triggered = true; args.veto_reasons.push(argv[++i]); }
    else if (a === '--elicitations') args.elicitations_count = parseInt(argv[++i], 10);
    else if (a === '--signoff-required') args.human_signoff_required = true;
    else if (a === '--signoff-received') args.human_signoff_received = true;
    else if (a === '--models-used') args.models_used = JSON.parse(argv[++i]);
    else if (a === '--dry-run') args.dryRun = true;
    else if (a === '--help' || a === '-h') { printHelp(); process.exit(0); }
  }
  return args;
}

function printHelp() {
  console.log(`Usage: emit-execution-log.js --plan-id <id> --mode <M> --duration <s> --cost <usd> --quality <0-5> [options]

Required:
  --plan-id <id>          Plan identifier (must match plan.schema.json pattern)
  --mode <M>              SIMPLE | STANDARD | COMPLEX | CRITICAL | DRY-RUN
  --duration <seconds>    Total pipeline duration in seconds
  --cost <usd>            Actual cost in USD (from estimate-cost.js + provider billing)
  --quality <0-5>         Overall quality score (0.0-5.0)

Optional:
  --meta-axiomas <0-1>    Meta-axiomas overall score (D8 input)
  --drift                 Flag if capability cache drift was detected
  --veto-reason <text>    Veto trigger (use multiple times for multiple reasons)
  --elicitations <count>  Number of elicitation questions asked
  --signoff-required      Set if human signoff was required (CRITICAL mode)
  --signoff-received      Set if human signoff was received
  --models-used <json>    JSON object mapping agent_id → model_name
  --dry-run               Validate input + show entry preview, NO file mutation

Exit codes:
  0  Entry appended successfully
  1  Validation failure
  2  Argument/environment error`);
}

function validateArgs(args) {
  const errors = [];
  if (!args.plan_id) errors.push("--plan-id is required");
  if (!/^[a-z0-9-]+-\d{8}-\d{6}$/.test(args.plan_id || '')) errors.push(`--plan-id must match pattern '{slug}-{YYYYMMDD-HHmmss}'; got '${args.plan_id}'`);
  if (!['SIMPLE', 'STANDARD', 'COMPLEX', 'CRITICAL', 'DRY-RUN'].includes(args.mode)) errors.push(`--mode must be SIMPLE|STANDARD|COMPLEX|CRITICAL|DRY-RUN; got '${args.mode}'`);
  if (typeof args.duration_seconds !== 'number' || args.duration_seconds < 0) errors.push(`--duration must be positive integer; got '${args.duration_seconds}'`);
  if (typeof args.cost_actual_usd !== 'number' || args.cost_actual_usd < 0) errors.push(`--cost must be non-negative number; got '${args.cost_actual_usd}'`);
  if (typeof args.quality_score_overall !== 'number' || args.quality_score_overall < 0 || args.quality_score_overall > 5) errors.push(`--quality must be 0.0-5.0; got '${args.quality_score_overall}'`);
  return errors;
}

function buildEntry(args) {
  const entry = {
    plan_id: args.plan_id,
    timestamp: new Date().toISOString(),
    mode: args.mode,
    duration_seconds: args.duration_seconds,
    cost_actual_usd: args.cost_actual_usd,
    quality_score_overall: args.quality_score_overall,
  };
  if (args.meta_axiomas_overall !== null) entry.meta_axiomas_overall = args.meta_axiomas_overall;
  if (args.drift_detected) entry.drift_detected = true;
  if (args.veto_triggered) {
    entry.veto_triggered = true;
    entry.veto_reasons = args.veto_reasons;
  }
  if (args.elicitations_count > 0) entry.elicitations_count = args.elicitations_count;
  if (args.human_signoff_required) entry.human_signoff_required = true;
  if (args.human_signoff_received) entry.human_signoff_received = true;
  if (args.models_used) entry.models_used = args.models_used;
  return entry;
}

function entryToYaml(entry) {
  // Manual minimal YAML emitter (avoids js-yaml dependency)
  const lines = ['  - plan_id: ' + JSON.stringify(entry.plan_id)];
  for (const [k, v] of Object.entries(entry)) {
    if (k === 'plan_id') continue;
    if (Array.isArray(v)) {
      lines.push(`    ${k}:`);
      for (const item of v) lines.push(`      - ${JSON.stringify(item)}`);
    } else if (typeof v === 'object' && v !== null) {
      lines.push(`    ${k}:`);
      for (const [k2, v2] of Object.entries(v)) lines.push(`      ${k2}: ${JSON.stringify(v2)}`);
    } else if (typeof v === 'string') {
      lines.push(`    ${k}: ${JSON.stringify(v)}`);
    } else {
      lines.push(`    ${k}: ${v}`);
    }
  }
  return lines.join('\n');
}

function appendToLog(entry, dryRun) {
  if (!fs.existsSync(LOG_PATH)) {
    console.error(`[ERR] log file not found: ${LOG_PATH}`);
    process.exit(2);
  }
  const content = fs.readFileSync(LOG_PATH, 'utf8');

  // Find `entries: []` line and replace with entries: + indented entry.
  // Idempotent across repeated calls (each call appends one entry).
  const yamlBlock = entryToYaml(entry);

  let newContent;
  if (content.match(/^entries: \[\]$/m)) {
    // First entry: replace `entries: []` with `entries:` + entry block
    newContent = content.replace(/^entries: \[\]$/m, `entries:\n${yamlBlock}`);
  } else if (content.match(/^entries:$/m)) {
    // Subsequent entries: append before audit_trail (or at end of entries block)
    const auditTrailIdx = content.indexOf('\n# ====');
    if (auditTrailIdx > 0) {
      const beforeAudit = content.slice(0, auditTrailIdx);
      const entriesEnd = beforeAudit.lastIndexOf('\n', auditTrailIdx - 1);
      newContent = content.slice(0, entriesEnd + 1) + yamlBlock + '\n' + content.slice(entriesEnd + 1);
    } else {
      newContent = content + '\n' + yamlBlock;
    }
  } else {
    console.error(`[ERR] log file format unexpected (no 'entries:' anchor)`);
    process.exit(2);
  }

  // Update metadata.last_appended_at + total_entries
  const now = new Date().toISOString();
  newContent = newContent.replace(/^\s+last_appended_at: .*$/m, `  last_appended_at: "${now}"`);
  const totalMatch = newContent.match(/^\s+total_entries: (\d+)$/m);
  if (totalMatch) {
    const newTotal = parseInt(totalMatch[1], 10) + 1;
    newContent = newContent.replace(/^\s+total_entries: \d+$/m, `  total_entries: ${newTotal}`);
  }

  if (dryRun) {
    console.log("=== DRY-RUN: entry preview (NOT written) ===");
    console.log(yamlBlock);
    console.log("=== Run without --dry-run to append ===");
    return;
  }

  fs.writeFileSync(LOG_PATH, newContent, 'utf8');
  console.log(`Entry appended: plan_id=${entry.plan_id} mode=${entry.mode} → ${LOG_PATH}`);
}

function main() {
  const args = parseArgs(process.argv);
  const errors = validateArgs(args);
  if (errors.length > 0) {
    console.error("Validation errors:\n  - " + errors.join("\n  - "));
    process.exit(1);
  }
  const entry = buildEntry(args);
  appendToLog(entry, args.dryRun);
  process.exit(0);
}

main();
