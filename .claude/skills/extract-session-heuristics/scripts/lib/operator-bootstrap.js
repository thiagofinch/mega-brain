/**
 * operator-bootstrap — resolve active operator via Phase 0.5 read-first OR cascade fallback.
 *
 * Canonical file: .mega-brain/active-operator.yaml (LOCAL, gitignored — bootstrapped per checkout).
 * Schema minimo: operator.slug + operator.heuristic_namespace (pasta existente).
 * Nao ha setter nem arquivo-modelo nesta distribuicao: o arquivo e criado manualmente.
 *
 * Implements KA_KE_152 (Runtime Ownership via Persistent State) + STORY-MIG-1.13.
 */

'use strict';

const fs = require('fs');
const path = require('path');
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
const OPERATOR_HINT = 'Crie .mega-brain/active-operator.yaml com operator.slug e operator.heuristic_namespace (pasta existente com as heuristicas do operador).';
const MINDS_ROOT = path.join(REPO_ROOT, 'squads', 'squad-creator-pro', 'minds');

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
 * Full bootstrap flow — read first, cascade if missing (sem write-back automatico).
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
    // Sem setter nesta distribuicao: o arquivo de estado precisa ser criado manualmente.
    throw new Error(
      `Operador inferido (${cascade.resolved}, via ${cascade.source}), mas ${OPERATOR_FILE} nao existe. ` +
      `${OPERATOR_HINT} Use operator.slug = ${cascade.resolved}.`
    );
  }

  // Ambiguous or no candidates — caller must prompt
  if (!allowPrompt) {
    throw new Error(
      `Cascade cannot auto-resolve operator (reason: ${cascade.source}). ` +
      `Candidates: ${(cascade.candidates || []).join(', ') || '(none)'}. ` +
      OPERATOR_HINT
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
  OPERATOR_HINT,
  MINDS_ROOT,
  loadOperator,
  cascadeFallback,
  resolveOperator,
};
