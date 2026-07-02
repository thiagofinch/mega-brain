#!/usr/bin/env node
/**
 * audit-plan.js — governance orchestrator for plan-architect pipeline
 *
 * Steps: validate → estimate → render(md+json) → persist + register + audit-trail.
 * Story: STORY-PA-5.1
 * Consumer: plan-architect (PA-6.1) post-emit step.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');


const SCRIPTS_DIR = __dirname;
const SQUAD_DATA_DIR = path.resolve(__dirname, '../data');
const REPO_ROOT = path.resolve(__dirname, '../../..');
const OUTPUTS_PLANS = path.join(REPO_ROOT, 'outputs/plans');
const PLAN_REGISTRY = path.join(SQUAD_DATA_DIR, 'plan-registry.yaml');
const AUDIT_TRAIL = path.join(REPO_ROOT, '.data/audit-trail.jsonl');

function parseArgs(argv) {
  const args = { plan: null, agent_id: 'plan-architect', cache_hash: '', scoring_version: '1.0',
    heuristics: 'IDS-G1,CPM,FMEA-RPN', dryRun: false, deterministic: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') args.dryRun = true;
    else if (a === '--deterministic') args.deterministic = true;
    else if (a === '--agent') args.agent_id = argv[++i];
    else if (a === '--cache-hash') args.cache_hash = argv[++i];
    else if (a === '--scoring-version') args.scoring_version = argv[++i];
    else if (a === '--heuristics') args.heuristics = argv[++i];
    else if (!args.plan) args.plan = a;
  }
  return args;
}

function parseYAML(src) {
  try { return require('js-yaml').load(src); }
  catch { return null; }
}

function dumpYAML(obj) {
  return require('js-yaml').dump(obj);
}

function runScript(script, args) {
  // SEGURANÇA (CWE-94): sem shell — cada arg vai como elemento de argv, então o caminho do
  // plano e o plan_id (dados externos vindos do YAML) NÃO são interpretados por /bin/sh.
  const res = spawnSync(process.execPath, [path.join(SCRIPTS_DIR, script), ...args], { encoding: 'utf8' });
  if (res.error) return { stdout: res.stdout || '', stderr: String(res.error), exitCode: 1 };
  return { stdout: res.stdout || '', stderr: res.stderr || '', exitCode: res.status || 0 };
}

function appendAuditTrail(entry) {
  fs.mkdirSync(path.dirname(AUDIT_TRAIL), { recursive: true });
  fs.appendFileSync(AUDIT_TRAIL, JSON.stringify(entry) + '\n');
}

function loadRegistry() {
  if (!fs.existsSync(PLAN_REGISTRY)) {
    return { schema_version: '1.0', plans: [] };
  }
  return parseYAML(fs.readFileSync(PLAN_REGISTRY, 'utf8')) || { schema_version: '1.0', plans: [] };
}

function saveRegistry(reg) {
  fs.writeFileSync(PLAN_REGISTRY, dumpYAML(reg));
}

function deriveSlug(plan) {
  // slugify para [a-z0-9-] — impede metacaracteres de shell / path traversal via plan_id
  const raw = plan.plan_id || (plan.demand && plan.demand.raw) || 'unknown';
  return String(raw).toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 60).replace(/-+$/, '') || 'plan';
}

function dateStamp() {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
}

// ── Main ──────────────────────────────────────────────────────────────────────
function main() {
  const args = parseArgs(process.argv);
  if (!args.plan) {
    console.error('Usage: audit-plan.js <plan.yaml> [--agent <id>] [--cache-hash <h>] [--scoring-version <v>] [--heuristics <list>] [--dry-run] [--deterministic]');
    process.exit(2);
  }

  const planSrc = fs.readFileSync(args.plan, 'utf8');
  const plan = parseYAML(planSrc);
  if (!plan) { console.error('Failed to parse plan'); process.exit(2); }

  console.log(`[audit-plan] Step 1: validate-plan.js`);
  const v = runScript('validate-plan.js', [args.plan]);
  const vResult = JSON.parse(v.stdout);
  if (!vResult.valid) {
    console.error(`[audit-plan] ABORT: validation failed (${vResult.errors.length} errors)`);
    appendAuditTrail({
      timestamp: new Date().toISOString(),
      event_type: 'plan_emit_failed',
      plan_id: plan.plan_id,
      who: args.agent_id,
      reason: 'validation_failed',
      errors: vResult.errors,
    });
    process.exit(1);
  }
  console.log(`[audit-plan] valid: true`);

  console.log(`[audit-plan] Step 2: estimate-cost.js`);
  const e = runScript('estimate-cost.js', [args.plan]);
  const eResult = JSON.parse(e.stdout);
  console.log(`[audit-plan] cost: $${eResult.total_cost_usd}`);

  if (args.dryRun) {
    console.log('[audit-plan] dry-run: skipping persistence + registry + audit-trail');
    process.exit(0);
  }

  console.log(`[audit-plan] Step 3: render-plan.js (md + json)`);
  const slug = deriveSlug(plan);
  const outDir = path.join(OUTPUTS_PLANS, `${dateStamp()}_${slug}`);
  fs.mkdirSync(outDir, { recursive: true });

  const planYamlPath = path.join(outDir, 'plan.yaml');
  fs.writeFileSync(planYamlPath, planSrc);

  runScript('render-plan.js', [args.plan, '--format', 'md', '--output', path.join(outDir, 'plan.md')]);
  runScript('render-plan.js', [args.plan, '--format', 'json', '--output', path.join(outDir, 'plan.json')]);

  // Per-plan audit log
  const auditEntry = {
    timestamp: new Date().toISOString(),
    event_type: 'plan_emitted',
    plan_id: plan.plan_id,
    who: args.agent_id,
    cache_manifest_hash: args.cache_hash || (plan.audit && plan.audit.cache_manifest_hash) || '',
    scoring_config_version: args.scoring_version,
    heuristics_applied: args.heuristics.split(','),
    constitutional_compliance_status: vResult.summary.constitutional_violations === 0 ? 'pass' : 'fail',
    cost_usd_estimate: eResult.total_cost_usd,
    quality_score: plan.quality_score,
    output_dir: path.relative(REPO_ROOT, outDir),
  };

  fs.writeFileSync(path.join(outDir, 'audit.jsonl'), JSON.stringify(auditEntry) + '\n');

  console.log(`[audit-plan] Step 4: append audit-trail.jsonl`);
  appendAuditTrail(auditEntry);

  console.log(`[audit-plan] Step 5: update plan-registry.yaml`);
  const reg = loadRegistry();
  reg.plans = reg.plans || [];
  reg.plans.push({
    plan_id: plan.plan_id,
    emitted_at: auditEntry.timestamp,
    slug,
    output_dir: auditEntry.output_dir,
    status: 'active',
    quality_score: plan.quality_score,
    constitutional_compliance: auditEntry.constitutional_compliance_status,
    cost_usd_estimate: eResult.total_cost_usd,
  });
  saveRegistry(reg);

  console.log(`[audit-plan] DONE: ${path.relative(REPO_ROOT, outDir)}`);
  console.log(JSON.stringify(auditEntry, null, 2));
}

if (require.main === module) main();

module.exports = { deriveSlug, dateStamp };
