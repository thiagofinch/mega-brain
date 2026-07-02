#!/usr/bin/env node
/**
 * test-runner — end-to-end test suite for the extract-session-heuristics runner.
 *
 * Validates STORY-MIG-1.13 ACs 11-14 by exercising each subcommand with
 * deterministic assertions against the real working tree.
 *
 * Exit codes:
 *   0 — all tests passed
 *   1 — at least one test failed
 *   2 — test harness error (setup/teardown failure)
 *
 * Usage: node .claude/skills/extract-session-heuristics/scripts/tests/test-runner.js
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// ================================================================
// Resolve paths
// ================================================================

function findRepoRoot(startDir = __dirname) {
  let d = startDir;
  while (d !== '/') {
    if (fs.existsSync(path.join(d, '.git'))) return d;
    d = path.dirname(d);
  }
  throw new Error('Could not find repo root');
}

const REPO_ROOT = findRepoRoot();
const RUNNER = path.join(REPO_ROOT, '.claude/skills/extract-session-heuristics/scripts/runner.js');
const NAMESPACE = path.join(REPO_ROOT, 'squads/squad-creator-pro/minds/knowledge-architect/heuristics');
const DECISION_CARDS = path.join(NAMESPACE, 'decision-cards.yaml');

// ================================================================
// Test harness
// ================================================================

const tests = [];
function test(name, fn) {
  tests.push({ name, fn });
}

function assert(cond, msg) {
  if (!cond) throw new Error(`Assertion failed: ${msg}`);
}

function assertEq(actual, expected, msg) {
  if (actual !== expected) {
    throw new Error(`${msg}\n  expected: ${JSON.stringify(expected)}\n  actual:   ${JSON.stringify(actual)}`);
  }
}

function assertTruthy(value, msg) {
  if (!value) throw new Error(`${msg} (got: ${JSON.stringify(value)})`);
}

function assertContains(haystack, needle, msg) {
  if (!haystack.includes(needle)) {
    throw new Error(`${msg}\n  looking for: ${JSON.stringify(needle)}\n  in: ${JSON.stringify(haystack).slice(0, 200)}...`);
  }
}

function runRunner(args, input = null) {
  try {
    const cmd = `node "${RUNNER}" ${args}`;
    const opts = { cwd: REPO_ROOT, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] };
    if (input !== null) {
      opts.input = input;
    }
    const stdout = execSync(cmd, opts);
    return { ok: true, stdout, exitCode: 0 };
  } catch (err) {
    return {
      ok: false,
      stdout: err.stdout?.toString() || '',
      stderr: err.stderr?.toString() || err.message,
      exitCode: err.status ?? 1,
    };
  }
}

function parseJson(stdout, label) {
  try {
    return JSON.parse(stdout);
  } catch (err) {
    throw new Error(`${label}: stdout is not valid JSON\n  stdout: ${stdout.slice(0, 300)}`);
  }
}

// ================================================================
// T1 — help subcommand
// ================================================================

test('T1 help prints usage', () => {
  const result = runRunner('help');
  assert(result.ok, `help failed: ${result.stderr}`);
  assertContains(result.stdout, 'bootstrap', 'help should mention bootstrap');
  assertContains(result.stdout, 'scan', 'help should mention scan');
  assertContains(result.stdout, 'check-overlap', 'help should mention check-overlap');
  assertContains(result.stdout, 'validate', 'help should mention validate');
  assertContains(result.stdout, 'persist', 'help should mention persist');
  assertContains(result.stdout, 'status', 'help should mention status');
  assertContains(result.stdout, 'LLM does', 'help should document responsibility split');
});

// ================================================================
// T2 — status subcommand
// ================================================================

test('T2 status returns valid operator state', () => {
  const result = runRunner('status');
  assert(result.ok, `status failed: ${result.stderr}`);
  const data = parseJson(result.stdout, 'status');
  assertEq(data.ok, true, 'status.ok should be true');
  assertTruthy(data.operator, 'operator should exist');
  assertEq(data.operator.slug, 'knowledge-architect', 'slug should be knowledge-architect');
  assertEq(data.operator.prefix, 'KA_KE', 'prefix should be KA_KE');
  assertTruthy(data.namespace.exists, 'namespace should exist');
  assertTruthy(data.decision_cards.exists, 'decision-cards.yaml should exist');
});

// ================================================================
// T3 — scan subcommand
// ================================================================

test('T3 scan matches filesystem state', () => {
  const result = runRunner('scan');
  assert(result.ok, `scan failed: ${result.stderr}`);
  const data = parseJson(result.stdout, 'scan');

  assertEq(data.ok, true, 'scan.ok should be true');
  assertEq(data.operator, 'knowledge-architect', 'operator should be knowledge-architect');

  // Count the actual files in the namespace
  const actualFiles = fs
    .readdirSync(NAMESPACE)
    .filter(f => /^KA_KE_\d+\.md$/.test(f));
  assertEq(data.stats.count, actualFiles.length, `scan count should match filesystem (${actualFiles.length})`);

  // Last ID should match the highest numbered file
  const lastFile = actualFiles.sort().at(-1).replace(/\.md$/, '');
  assertEq(data.stats.last_id, lastFile, `last_id should be ${lastFile}`);

  // Next ID should be last+1
  const lastNum = parseInt(lastFile.match(/KA_KE_(\d+)/)[1], 10);
  const expectedNext = `KA_KE_${String(lastNum + 1).padStart(3, '0')}`;
  assertEq(data.stats.next_id, expectedNext, `next_id should be ${expectedNext}`);

  // last_5 should contain up to 5 titles
  assertTruthy(Array.isArray(data.last_5), 'last_5 should be an array');
  assert(data.last_5.length <= 5, 'last_5 should have at most 5 entries');
});

// ================================================================
// T4 — bootstrap subcommand (file exists → persistent_state)
// ================================================================

test('T4 bootstrap uses persistent_state when file exists', () => {
  const operatorFile = path.join(REPO_ROOT, '.mega-brain/active-operator.yaml');
  if (!fs.existsSync(operatorFile)) {
    throw new Error('TEST PREREQ: .mega-brain/active-operator.yaml must exist for T4');
  }
  const result = runRunner('bootstrap');
  assert(result.ok, `bootstrap failed: ${result.stderr}`);
  const data = parseJson(result.stdout, 'bootstrap');
  assertEq(data.ok, true, 'bootstrap.ok should be true');
  assertEq(data.source, 'persistent_state', 'source should be persistent_state');
  assertEq(data.operator.slug, 'knowledge-architect', 'operator should be knowledge-architect');
});

// ================================================================
// T5 — validate subcommand on a known-valid file
// ================================================================

test('T5 validate KA_KE_152 passes 6/6 mandatory', () => {
  const file = 'squads/squad-creator-pro/minds/knowledge-architect/heuristics/KA_KE_152.md';
  const result = runRunner(`validate ${file}`);
  assert(result.ok, `validate should succeed on valid file: ${result.stderr}`);
  const data = parseJson(result.stdout, 'validate');
  assertEq(data.ok, true, 'validate.ok should be true');
  assertEq(data.status, 'validated', `status should be validated (got ${data.status})`);
  assertEq(data.mandatory, '6/6', 'mandatory should be 6/6');
  assertEq(data.blockers.length, 0, 'blockers should be empty');
});

// ================================================================
// T6 — validate subcommand catches a BROKEN file
// ================================================================

test('T6 validate catches file missing SOURCE tag', () => {
  const tmpFile = path.join(os.tmpdir(), `broken-heuristic-${process.pid}.md`);
  fs.writeFileSync(tmpFile, `# BROKEN_001 - Missing SOURCE

**Zone:** 💎 4% Excelência

\`\`\`yaml
BROKEN_001:
  sys_tension:
    tension_with: "something"
  rule: |
    SE condition ENTÃO action NUNCA bypass
  failure_modes:
    omission: "something"
  anti_pattern: "something"
\`\`\`
`);
  try {
    const result = runRunner(`validate ${tmpFile}`);
    // validate returns non-zero exit when invalid, which execSync throws for
    const data = parseJson(result.stdout, 'validate-broken');
    assertEq(data.ok, false, 'ok should be false for broken file');
    assertEq(data.status, 'block', `status should be block (got ${data.status})`);
    assertContains(data.blockers, 'source', 'source should be in blockers');
  } finally {
    fs.unlinkSync(tmpFile);
  }
});

// ================================================================
// T7 — validate subcommand on ALL v143-152 heuristics
// ================================================================

test('T7 all KA_KE_143-152 pass compliance gate', () => {
  const ids = [143, 144, 145, 146, 147, 148, 149, 150, 151, 152];
  const results = {};
  for (const id of ids) {
    const fname = `KA_KE_${id}.md`;
    const fpath = path.join(NAMESPACE, fname);
    if (!fs.existsSync(fpath)) {
      throw new Error(`TEST PREREQ: ${fname} should exist in namespace`);
    }
    const rel = `squads/squad-creator-pro/minds/knowledge-architect/heuristics/${fname}`;
    const result = runRunner(`validate ${rel}`);
    const data = parseJson(result.stdout, `validate-${fname}`);
    results[id] = data;
    assertEq(data.mandatory, '6/6', `${fname} mandatory should be 6/6`);
    assertEq(data.status, 'validated', `${fname} status should be validated`);
  }
  console.log(`    (${ids.length} files validated)`);
});

// ================================================================
// T8 — check-overlap with rich keywords finds KA_KE_143
// ================================================================

test('T8 check-overlap detects existing KA_KE_143 for audit/align keywords', () => {
  const payload = JSON.stringify({
    keywords: ['audit', 'align', 'greenfield', 'preflight', 'fullsdc'],
  });
  const result = runRunner('check-overlap', payload);
  assert(result.ok, `check-overlap failed: ${result.stderr}`);
  const data = parseJson(result.stdout, 'check-overlap');
  assertEq(data.ok, true, 'check-overlap.ok should be true');
  assertTruthy(data.any_above_threshold, 'should find at least one match above threshold');
  const ids = data.top_matches.map(m => m.id);
  assertContains(ids, 'KA_KE_143', 'KA_KE_143 should be in top matches');
});

// ================================================================
// T9 — check-overlap with nonsense keywords returns no match
// ================================================================

test('T9 check-overlap returns nothing for nonsense keywords', () => {
  const payload = JSON.stringify({
    keywords: ['xyzzy', 'plugh', 'foobarbaz'],
  });
  const result = runRunner('check-overlap', payload);
  assert(result.ok, `check-overlap failed: ${result.stderr}`);
  const data = parseJson(result.stdout, 'check-overlap-nonsense');
  assertEq(data.any_above_threshold, false, 'should find no matches');
  assertEq(data.top_matches.length, 0, 'top_matches should be empty');
});

// ================================================================
// T10 — persist dry-run validates without writing
// ================================================================

test('T10 persist dry-run validates batch without side effects', () => {
  const batchFile = path.join(os.tmpdir(), `test-batch-${process.pid}.json`);
  const batch = {
    heuristic_files: [
      path.join(NAMESPACE, 'KA_KE_143.md'),
      path.join(NAMESPACE, 'KA_KE_144.md'),
    ],
    new_cards: [
      { id: 'TEST_1', name: 'stub', rule: 'stub' },
      { id: 'TEST_2', name: 'stub', rule: 'stub' },
    ],
    dry_run: true,
  };
  fs.writeFileSync(batchFile, JSON.stringify(batch));

  // Snapshot the file size BEFORE
  const sizeBefore = fs.statSync(DECISION_CARDS).size;

  try {
    const result = runRunner(`persist ${batchFile}`);
    assert(result.ok, `persist dry-run failed: ${result.stderr}`);
    const data = parseJson(result.stdout, 'persist-dry');
    assertEq(data.mode, 'dry_run', 'mode should be dry_run');
    assertEq(data.ok, true, 'dry-run.ok should be true');
    assertEq(data.would_append, 2, 'would_append should be 2');
    assertEq(data.validation.validated, 2, 'validation.validated should be 2');
  } finally {
    fs.unlinkSync(batchFile);
  }

  // Verify decision-cards.yaml was NOT modified
  const sizeAfter = fs.statSync(DECISION_CARDS).size;
  assertEq(sizeAfter, sizeBefore, 'dry-run must NOT modify decision-cards.yaml');
});

// ================================================================
// T11 — persist dry-run REJECTS a batch with mismatched count
// ================================================================

test('T11 persist dry-run rejects mismatched file/card counts', () => {
  const batchFile = path.join(os.tmpdir(), `test-batch-mismatch-${process.pid}.json`);
  const batch = {
    heuristic_files: [
      path.join(NAMESPACE, 'KA_KE_143.md'),
      path.join(NAMESPACE, 'KA_KE_144.md'),
    ],
    new_cards: [{ id: 'TEST_1', name: 'stub' }],  // only 1 card for 2 files
    dry_run: true,
  };
  fs.writeFileSync(batchFile, JSON.stringify(batch));

  try {
    const result = runRunner(`persist ${batchFile}`);
    const data = parseJson(result.stdout, 'persist-mismatch');
    assertEq(data.ok, false, 'should reject mismatched counts');
    assertTruthy(data.error, 'error should be present');
    assertContains(data.error, 'count', 'error should mention count');
  } finally {
    fs.unlinkSync(batchFile);
  }
});

// ================================================================
// T12 — drift detection: synthetic drift is reported
// ================================================================

test('T12 scan detects synthetic drift in operator file', () => {
  const operatorFile = path.join(REPO_ROOT, '.mega-brain/active-operator.yaml');
  const backup = fs.readFileSync(operatorFile, 'utf-8');

  try {
    // Inject synthetic drift
    const yaml = require('js-yaml');
    const data = yaml.load(backup);
    const originalCount = data.operator.heuristic_count;
    data.operator.heuristic_count = 9999;  // fake drift
    fs.writeFileSync(operatorFile, yaml.dump(data, { noRefs: true, sortKeys: false }));

    const result = runRunner('scan');
    const scanData = parseJson(result.stdout, 'scan-drift');
    assertTruthy(scanData.drift.has_drift, 'drift should be detected');
    const countDrift = scanData.drift.deltas.find(d => d.field === 'heuristic_count');
    assertTruthy(countDrift, 'count drift should be present');
    assertEq(countDrift.declared, 9999, 'declared should be 9999');
    assertEq(countDrift.actual, originalCount, `actual should be ${originalCount}`);
  } finally {
    fs.writeFileSync(operatorFile, backup);
  }
});

// ================================================================
// T13 — runner determinism check: no classification/generation code
// ================================================================

test('T13 runner scripts contain no semantic classification/generation', () => {
  const scriptsDir = path.join(REPO_ROOT, '.claude/skills/extract-session-heuristics/scripts');
  const files = [
    path.join(scriptsDir, 'runner.js'),
    path.join(scriptsDir, 'lib/yaml-io.js'),
    path.join(scriptsDir, 'lib/operator-bootstrap.js'),
    path.join(scriptsDir, 'lib/heuristic-scanner.js'),
    path.join(scriptsDir, 'lib/overlap-checker.js'),
    path.join(scriptsDir, 'lib/compliance-gate.js'),
    path.join(scriptsDir, 'lib/persister.js'),
  ];
  const forbiddenPatterns = [
    /\bnew\s+OpenAI/i,
    /\bnew\s+Anthropic/i,
    /@anthropic-ai\/sdk/i,
    /openai\.chat/i,
    /claude\.chat/i,
    /\bllm\(/i,
    /\bgenerate\s*\(/i,
    /\bclassify\s*\(/i,
    /\bchatCompletion/i,
  ];
  for (const f of files) {
    const content = fs.readFileSync(f, 'utf-8');
    for (const pat of forbiddenPatterns) {
      assert(!pat.test(content), `${path.basename(f)} contains forbidden pattern ${pat}`);
    }
  }
});

// ================================================================
// T14 — example file exists and is committed
// ================================================================

test('T14 active-operator.example.yaml exists and parses', () => {
  const examplePath = path.join(REPO_ROOT, '.mega-brain/active-operator.example.yaml');
  assertTruthy(fs.existsSync(examplePath), 'example file must exist');
  const yaml = require('js-yaml');
  const data = yaml.load(fs.readFileSync(examplePath, 'utf-8'));
  assertTruthy(data.schema_version, 'schema_version should be present');
  assertTruthy(data.operator, 'operator block should be present');
  assertTruthy(data.operator.slug, 'operator.slug should be present');
});

// ================================================================
// T15 — canonical yaml is gitignored
// ================================================================

test('T15 active-operator.yaml is gitignored', () => {
  try {
    execSync('git check-ignore .mega-brain/active-operator.yaml', {
      cwd: REPO_ROOT,
      stdio: 'pipe',
    });
    // exit 0 means it IS ignored
  } catch (err) {
    throw new Error('.mega-brain/active-operator.yaml should be gitignored (git check-ignore returned non-zero)');
  }
});

// ================================================================
// T16 — example yaml is NOT gitignored
// ================================================================

test('T16 active-operator.example.yaml is NOT gitignored', () => {
  try {
    execSync('git check-ignore .mega-brain/active-operator.example.yaml', {
      cwd: REPO_ROOT,
      stdio: 'pipe',
    });
    throw new Error('.mega-brain/active-operator.example.yaml should NOT be gitignored');
  } catch (err) {
    // git check-ignore returns non-zero when NOT ignored → this is what we want
    if (err.message.includes('should NOT be gitignored')) throw err;
  }
});

// ================================================================
// T17 — megabrain-operator npm script works
// ================================================================

test('T17 npm run megabrain:operator -- list works', () => {
  try {
    const stdout = execSync('npm run megabrain:operator -- list 2>&1', {
      cwd: REPO_ROOT,
      encoding: 'utf-8',
    });
    assertContains(stdout, 'knowledge-architect', 'list should mention knowledge-architect');
    assertContains(stdout, 'active', 'list should mark one as active');
  } catch (err) {
    throw new Error(`npm run megabrain:operator -- list failed: ${err.message}`);
  }
});

// ================================================================
// T18 — decision-cards.yaml structure + consistency check
// ================================================================

test('T18 decision-cards.yaml structure + file/card consistency', () => {
  const yaml = require('js-yaml');
  const data = yaml.load(fs.readFileSync(DECISION_CARDS, 'utf-8'));
  assertTruthy(data, 'decision-cards should parse');
  assertTruthy(Array.isArray(data.cards), 'cards should be an array');
  assert(data.cards.length >= 150, `should have at least 150 cards (got ${data.cards.length})`);

  // Consistency: every card should have a corresponding file in the namespace.
  // (Files without cards are tracked as known legacy gaps — see LEGACY_GAPS below.)
  const LEGACY_GAPS = ['KA_KE_115'];  // pre-existing drift from before STORY-MIG-1.13
  const cardIds = new Set(data.cards.map(c => c.id));
  const files = new Set(
    fs.readdirSync(NAMESPACE)
      .filter(f => /^KA_KE_\d+\.md$/.test(f))
      .map(f => f.replace('.md', ''))
  );

  // Every card must have a corresponding file
  for (const cardId of cardIds) {
    assert(files.has(cardId), `card ${cardId} has no corresponding .md file`);
  }

  // Files without cards are OK only if they're in LEGACY_GAPS
  const unexpectedOrphans = [...files].filter(
    id => !cardIds.has(id) && !LEGACY_GAPS.includes(id)
  );
  assert(
    unexpectedOrphans.length === 0,
    `unexpected file(s) without card entries: ${unexpectedOrphans.join(', ')}`
  );
});

// ================================================================
// Runner
// ================================================================

function main() {
  console.log(`Running ${tests.length} tests against runner at ${path.relative(REPO_ROOT, RUNNER)}`);
  console.log('');

  let passed = 0;
  let failed = 0;
  const failures = [];

  for (const t of tests) {
    try {
      t.fn();
      console.log(`  ✓ ${t.name}`);
      passed++;
    } catch (err) {
      console.log(`  ✗ ${t.name}`);
      console.log(`      ${err.message}`);
      failed++;
      failures.push({ name: t.name, error: err.message });
    }
  }

  console.log('');
  console.log(`Results: ${passed}/${tests.length} passed`);

  if (failed > 0) {
    console.log('');
    console.log('Failures:');
    for (const f of failures) {
      console.log(`  - ${f.name}: ${f.error}`);
    }
    process.exit(1);
  }

  console.log('All tests passed.');
  process.exit(0);
}

main();
