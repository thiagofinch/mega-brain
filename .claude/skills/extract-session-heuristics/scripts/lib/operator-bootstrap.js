/**
 * operator-bootstrap — resolve active operator via Phase 0.5 read-first OR cascade fallback.
 *
 * Canonical file: .mega-brain/active-operator.yaml (LOCAL, gitignored — bootstrapped per checkout).
 * Schema: .mega-brain/active-operator.example.yaml.
 * Setter: scripts/megabrain-operator.js (run via `npm run megabrain:operator -- set <slug>`).
 *
 * Implements KA_KE_152 (Runtime Ownership via Persistent State) + STORY-MIG-1.13.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { readYamlOrNull } = require('./yaml-io');

function findRepoRoot(startDir = process.cwd()) {
  let d = startDir;
  while (d !== '/') {
    if (fs.existsSync(path.join(d, '.git'))) return d;
    d = path.dirname(d);
  }
  return startDir;
}

const REPO_ROOT = findRepoRoot();
const OPERATOR_FILE = path.join(REPO_ROOT, '.mega-brain', 'active-operator.yaml');
const OPERATOR_EXAMPLE = path.join(REPO_ROOT, '.mega-brain', 'active-operator.example.yaml');
const MINDS_ROOT = path.join(REPO_ROOT, 'squads', 'squad-creator-pro', 'minds');
const MEGABRAIN_OPERATOR_SCRIPT = path.join(REPO_ROOT, 'scripts', 'megabrain-operator.js');

/**
 * Phase 0.5 fast path — read .mega-brain/active-operator.yaml and validate.
 * Returns { ok, operator, reason }.
 */
function loadOperator() {
  const data = readYamlOrNull(OPERATOR_FILE);
  if (!data) {
    return { ok: false, reason: 'file_missing', operator: null };
  }
  if (!data.operator || !data.operator.slug) {
    return { ok: false, reason: 'malformed', operator: null };
  }
  const nsPath = path.join(REPO_ROOT, data.operator.heuristic_namespace || '');
  if (!data.operator.heuristic_namespace || !fs.existsSync(nsPath)) {
    return { ok: false, reason: 'namespace_missing', operator: data.operator };
  }
  return { ok: true, operator: data.operator, metadata: data.metadata, full: data };
}

/**
 * Cascade fallback — try to infer operator from filesystem state.
 * Order (per STORY-MIG-1.13):
 *   1. Env override: MEGABRAIN_ACTIVE_OPERATOR
 *   2. Single-operator heuristic: if exactly one non-hidden dir in minds/, use it
 *   3. Explicit prompt (handled by caller — we just return null here)
 */
function cascadeFallback() {
  // 1. Env override
  const envOverride = process.env.MEGABRAIN_ACTIVE_OPERATOR;
  if (envOverride && fs.existsSync(path.join(MINDS_ROOT, envOverride))) {
    return { resolved: envOverride, source: 'env_override' };
  }

  // 2. Single-operator heuristic
  if (fs.existsSync(MINDS_ROOT)) {
    const dirs = fs.readdirSync(MINDS_ROOT, { withFileTypes: true })
      .filter(e => e.isDirectory() && !e.name.startsWith('_') && !e.name.startsWith('.'))
      .map(e => e.name);
    if (dirs.length === 1) {
      return { resolved: dirs[0], source: 'single_operator_heuristic' };
    }
    if (dirs.length > 1) {
      return { resolved: null, source: 'ambiguous', candidates: dirs };
    }
  }

  return { resolved: null, source: 'no_candidates' };
}

/**
 * Write-back via megabrain-operator setter. More robust than writing YAML manually
 * because the setter scans the filesystem and populates counts/next_id automatically.
 * Returns { success, stdout, stderr }.
 */
function writeBackViaSetter(slug) {
  try {
    const stdout = execSync(`node "${MEGABRAIN_OPERATOR_SCRIPT}" set ${slug}`, {
      cwd: REPO_ROOT,
      encoding: 'utf-8',
    });
    return { success: true, stdout, stderr: '' };
  } catch (err) {
    return {
      success: false,
      stdout: err.stdout || '',
      stderr: err.stderr || err.message,
    };
  }
}

/**
 * Full bootstrap flow — read first, cascade if missing, write-back on cascade success.
 * Returns { operator, source, drift? }.
 * Throws if cascade fails and prompt is needed (caller must handle prompting).
 */
function resolveOperator({ allowPrompt = false } = {}) {
  // Phase 0.5 fast path
  const fast = loadOperator();
  if (fast.ok) {
    return { operator: fast.operator, metadata: fast.metadata, source: 'persistent_state' };
  }

  // Fallback needed
  const cascade = cascadeFallback();

  if (cascade.resolved) {
    // Bootstrap write-back
    const writeResult = writeBackViaSetter(cascade.resolved);
    if (!writeResult.success) {
      throw new Error(`Bootstrap write-back failed for ${cascade.resolved}: ${writeResult.stderr}`);
    }
    // Re-read after write-back
    const refreshed = loadOperator();
    if (!refreshed.ok) {
      throw new Error(`Post-bootstrap load failed: ${refreshed.reason}`);
    }
    return {
      operator: refreshed.operator,
      metadata: refreshed.metadata,
      source: `cascade_bootstrap:${cascade.source}`,
      write_back: writeResult.stdout,
    };
  }

  // Ambiguous or no candidates — caller must prompt
  if (!allowPrompt) {
    throw new Error(
      `Cascade cannot auto-resolve operator (reason: ${cascade.source}). ` +
      `Candidates: ${(cascade.candidates || []).join(', ') || '(none)'}. ` +
      `Run: npm run megabrain:operator -- set <slug>`
    );
  }

  return {
    operator: null,
    source: 'cascade_ambiguous',
    candidates: cascade.candidates || [],
    reason: cascade.source,
  };
}

module.exports = {
  REPO_ROOT,
  OPERATOR_FILE,
  OPERATOR_EXAMPLE,
  MINDS_ROOT,
  MEGABRAIN_OPERATOR_SCRIPT,
  loadOperator,
  cascadeFallback,
  writeBackViaSetter,
  resolveOperator,
};
