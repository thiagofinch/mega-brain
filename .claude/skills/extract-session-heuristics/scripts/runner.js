#!/usr/bin/env node
/**
 * extract-session-heuristics runner — deterministic helpers for the 5-phase pipeline.
 *
 * This runner does NOT replace the SKILL.md. It executes the mechanical parts
 * of the pipeline (Phase 0.5 owner load, Phase 3 overlap, Phase 4.5 compliance,
 * Phase 5 persist) while leaving IDENTIFY + FILTER + FORMALIZE classification
 * to the LLM reading the session context.
 *
 * Usage:
 *   node scripts/runner.js bootstrap              # Phase 0.5 — ensure operator loaded
 *   node scripts/runner.js scan                   # Print namespace stats + drift
 *   node scripts/runner.js check-overlap          # Stdin JSON: { keywords, rule_fragment }
 *   node scripts/runner.js validate <file.md>     # Phase 4.5 compliance gate
 *   node scripts/runner.js persist <batch.json>   # Phase 5 — append cards + refresh
 *   node scripts/runner.js status                 # Diagnostic summary
 *   node scripts/runner.js help
 *
 * Invoked via SKILL.md Phase 0.5 and Phase 4.5/5 hooks.
 *
 * Related: STORY-MIG-1.13, KA_KE_152, KA_KE_147
 */

'use strict';

const fs = require('fs');
const path = require('path');

const {
  REPO_ROOT,
  OPERATOR_FILE,
  MEGABRAIN_OPERATOR_SCRIPT,
  loadOperator,
  resolveOperator,
} = require('./lib/operator-bootstrap');
const { scanNamespace, checkDrift } = require('./lib/heuristic-scanner');
const { checkOverlap } = require('./lib/overlap-checker');
const { validateHeuristicFile, validateBatch } = require('./lib/compliance-gate');
const { persistBatch, dryRunPersist } = require('./lib/persister');

function readStdinJson() {
  try {
    const data = fs.readFileSync(0, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    throw new Error(`stdin JSON parse error: ${err.message}`);
  }
}

function printJson(obj) {
  process.stdout.write(JSON.stringify(obj, null, 2) + '\n');
}

function getNamespaceFullPath(operator) {
  return path.join(REPO_ROOT, operator.heuristic_namespace);
}

function getDecisionCardsPath(operator) {
  return path.join(
    REPO_ROOT,
    operator.heuristic_namespace,
    'heuristics',
    'decision-cards.yaml'
  );
}

// ================================================================
// Subcommand: bootstrap
// Ensures .mega-brain/active-operator.yaml exists and is valid.
// If missing: runs cascade fallback + write-back via megabrain-operator setter.
// ================================================================

function cmdBootstrap() {
  try {
    const result = resolveOperator({ allowPrompt: false });
    printJson({
      ok: true,
      source: result.source,
      operator: {
        slug: result.operator.slug,
        handle: result.operator.handle,
        display_name: result.operator.display_name,
        heuristic_id_prefix: result.operator.heuristic_id_prefix,
        heuristic_namespace: result.operator.heuristic_namespace,
        next_heuristic_id: result.operator.next_heuristic_id,
        heuristic_count: result.operator.heuristic_count,
      },
      write_back: result.write_back || null,
    });
    return 0;
  } catch (err) {
    printJson({
      ok: false,
      error: err.message,
      hint: 'Run: npm run megabrain:operator -- list  (and then) -- set <slug>',
    });
    return 1;
  }
}

// ================================================================
// Subcommand: scan
// Scans the active operator's heuristics namespace and returns stats + drift.
// ================================================================

function cmdScan() {
  const load = loadOperator();
  if (!load.ok) {
    printJson({
      ok: false,
      error: `operator not loaded (${load.reason})`,
      hint: 'Run: node scripts/runner.js bootstrap',
    });
    return 1;
  }

  const nsPath = getNamespaceFullPath(load.operator);
  const scan = scanNamespace(nsPath);
  const drift = checkDrift(scan, load.operator);

  printJson({
    ok: true,
    operator: load.operator.slug,
    namespace: load.operator.heuristic_namespace,
    stats: {
      count: scan.count,
      prefix: scan.prefix,
      last_id: scan.lastId,
      next_id: scan.nextId,
    },
    last_5: scan.lastTitles,
    drift: {
      has_drift: drift.hasDrift,
      deltas: drift.drift,
      hint: drift.hasDrift
        ? 'Run: npm run megabrain:operator -- refresh'
        : 'operator state matches filesystem',
    },
  });
  return 0;
}

// ================================================================
// Subcommand: check-overlap
// Reads candidate from stdin JSON, returns top matches against decision-cards.
// ================================================================

function cmdCheckOverlap() {
  const load = loadOperator();
  if (!load.ok) {
    printJson({ ok: false, error: `operator not loaded (${load.reason})` });
    return 1;
  }

  let candidate;
  try {
    candidate = readStdinJson();
  } catch (err) {
    printJson({
      ok: false,
      error: err.message,
      expected: '{ "keywords": ["word1","word2"], "rule_fragment": "optional..." }',
    });
    return 1;
  }

  const cardsPath = getDecisionCardsPath(load.operator);
  if (!fs.existsSync(cardsPath)) {
    printJson({ ok: false, error: `decision-cards.yaml not found: ${cardsPath}` });
    return 1;
  }

  const result = checkOverlap(cardsPath, candidate);
  printJson({
    ok: true,
    candidate_keywords: candidate.keywords,
    total_cards_scanned: result.totalCards,
    any_above_threshold: result.anyAboveThreshold,
    top_matches: result.topMatches,
    hint: result.anyAboveThreshold
      ? 'Consider UPDATE existing card vs CREATE new one'
      : 'No significant overlap — safe to CREATE new',
  });
  return 0;
}

// ================================================================
// Subcommand: validate <file.md>
// Runs Phase 4.5 compliance gate on a single L3 heuristic file.
// ================================================================

function cmdValidate(args) {
  const filePath = args[0];
  if (!filePath) {
    printJson({ ok: false, error: 'Usage: validate <file.md>' });
    return 1;
  }

  const absPath = path.isAbsolute(filePath) ? filePath : path.join(REPO_ROOT, filePath);
  const result = validateHeuristicFile(absPath);

  printJson({
    ok: result.valid,
    status: result.status,
    file: path.relative(REPO_ROOT, result.file),
    mandatory: result.mandatory
      ? `${result.mandatory.passing}/${result.mandatory.total}`
      : null,
    recommended: result.recommended
      ? `${result.recommended.passing}/${result.recommended.total}`
      : null,
    blockers: result.blockers,
    mandatory_detail: result.mandatory?.results ?? [],
    recommended_detail: result.recommended?.results ?? [],
  });
  return result.valid ? 0 : 1;
}

// ================================================================
// Subcommand: persist <batch.json>
// Phase 5 — appends cards + refreshes operator. Reads batch from file.
// batch.json schema:
//   {
//     "heuristic_files": ["abs/path/KA_KE_143.md", ...],
//     "new_cards": [ { id: "KA_KE_143", name: "...", ... }, ... ],
//     "dry_run": false
//   }
// ================================================================

function cmdPersist(args) {
  const batchPath = args[0];
  if (!batchPath) {
    printJson({ ok: false, error: 'Usage: persist <batch.json>' });
    return 1;
  }

  const absBatchPath = path.isAbsolute(batchPath) ? batchPath : path.join(REPO_ROOT, batchPath);
  if (!fs.existsSync(absBatchPath)) {
    printJson({ ok: false, error: `Batch file not found: ${absBatchPath}` });
    return 1;
  }

  let batch;
  try {
    batch = JSON.parse(fs.readFileSync(absBatchPath, 'utf-8'));
  } catch (err) {
    printJson({ ok: false, error: `Batch JSON parse error: ${err.message}` });
    return 1;
  }

  const load = loadOperator();
  if (!load.ok) {
    printJson({ ok: false, error: `operator not loaded (${load.reason})` });
    return 1;
  }

  const decisionCardsPath = getDecisionCardsPath(load.operator);

  const params = {
    decisionCardsPath,
    heuristicFilePaths: batch.heuristic_files,
    newCards: batch.new_cards,
  };

  if (batch.dry_run) {
    const result = dryRunPersist(params);
    printJson({
      mode: 'dry_run',
      ok: result.ok,
      would_append: result.would_append,
      validation: {
        total: result.validation?.total,
        validated: result.validation?.validated,
        drafts: result.validation?.drafts,
        blocked: result.validation?.blocked,
        incomplete: result.validation?.incomplete,
      },
      error: result.error,
    });
    return result.ok ? 0 : 1;
  }

  const result = persistBatch(params);
  printJson({
    mode: 'persist',
    success: result.success,
    appended: result.appended,
    appended_count: result.appended_count,
    refreshed: result.refreshed,
    validation: {
      total: result.validation?.total,
      validated: result.validation?.validated,
      drafts: result.validation?.drafts,
    },
    errors: result.errors || [],
    error: result.error,
  });
  return result.success ? 0 : 1;
}

// ================================================================
// Subcommand: status
// Diagnostic summary — operator state + namespace health + drift.
// ================================================================

function cmdStatus() {
  const load = loadOperator();

  if (!load.ok) {
    printJson({
      ok: false,
      phase: '0.5',
      operator_file_status: load.reason,
      operator_file: OPERATOR_FILE,
      hint: load.reason === 'file_missing'
        ? 'Run: node scripts/runner.js bootstrap'
        : 'Run: npm run megabrain:operator -- set <slug>',
    });
    return 1;
  }

  const nsPath = getNamespaceFullPath(load.operator);
  const scan = scanNamespace(nsPath);
  const drift = checkDrift(scan, load.operator);
  const cardsPath = getDecisionCardsPath(load.operator);
  const cardsExist = fs.existsSync(cardsPath);

  printJson({
    ok: true,
    operator_file: path.relative(REPO_ROOT, OPERATOR_FILE),
    operator: {
      slug: load.operator.slug,
      handle: load.operator.handle,
      display_name: load.operator.display_name,
      prefix: load.operator.heuristic_id_prefix,
      next_id: load.operator.next_heuristic_id,
    },
    namespace: {
      path: load.operator.heuristic_namespace,
      exists: scan.exists,
      count_declared: load.operator.heuristic_count,
      count_actual: scan.count,
      last_id_declared: load.operator.last_heuristic_id,
      last_id_actual: scan.lastId,
    },
    decision_cards: {
      path: path.relative(REPO_ROOT, cardsPath),
      exists: cardsExist,
    },
    drift: {
      has_drift: drift.hasDrift,
      deltas: drift.drift,
    },
    metadata: load.metadata
      ? {
          last_updated: load.metadata.last_updated,
          last_updater: load.metadata.last_updater,
        }
      : null,
  });
  return 0;
}

// ================================================================
// Help
// ================================================================

function cmdHelp() {
  console.log('extract-session-heuristics runner — deterministic helpers for the 5-phase pipeline');
  console.log('');
  console.log('Subcommands:');
  console.log('  bootstrap                  Phase 0.5 — ensure .mega-brain/active-operator.yaml is loaded');
  console.log('  scan                       Print namespace stats + drift detection');
  console.log('  check-overlap              Phase 3 — read candidate JSON from stdin, return matches');
  console.log('  validate <file.md>         Phase 4.5 — compliance gate on L3 heuristic file');
  console.log('  persist <batch.json>       Phase 5 — append cards to decision-cards + refresh operator');
  console.log('  status                     Diagnostic summary (operator + namespace + drift)');
  console.log('  help                       This help');
  console.log('');
  console.log('Pipeline responsibility split:');
  console.log('  LLM does:     IDENTIFY (scan session) + FILTER (Pareto) + FORMALIZE (write L3 files)');
  console.log('  Runner does:  bootstrap, scan, overlap, validate, persist, refresh');
  console.log('');
  console.log('Related: STORY-MIG-1.13, KA_KE_152 (persistent ownership), KA_KE_147 (enforcement mechanism)');
  console.log('');
  console.log('For skill invocation: the skill markdown (SKILL.md v3.5.0+) calls these');
  console.log('subcommands at specific phases. Users should not need to invoke directly.');
}

// ================================================================
// Main dispatcher
// ================================================================

function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (!cmd || cmd === 'help' || cmd === '--help' || cmd === '-h') {
    cmdHelp();
    process.exit(0);
  }

  switch (cmd) {
    case 'bootstrap':
      process.exit(cmdBootstrap());
    case 'scan':
      process.exit(cmdScan());
    case 'check-overlap':
      process.exit(cmdCheckOverlap());
    case 'validate':
      process.exit(cmdValidate(args.slice(1)));
    case 'persist':
      process.exit(cmdPersist(args.slice(1)));
    case 'status':
      process.exit(cmdStatus());
    default:
      console.error(`Unknown subcommand: ${cmd}`);
      cmdHelp();
      process.exit(1);
  }
}

main();
