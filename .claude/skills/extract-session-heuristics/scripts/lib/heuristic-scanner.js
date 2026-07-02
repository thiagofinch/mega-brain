/**
 * heuristic-scanner — scan a heuristics namespace for existing files.
 *
 * Returns stats: prefix family, count, last ID, next ID, recent titles.
 * Used by Phase 0.5 fast path to validate namespace health.
 */

'use strict';

const fs = require('fs');
const path = require('path');

/**
 * Scan a heuristics namespace directory (e.g. squads/squad-creator-pro/minds/knowledge-architect/heuristics).
 * Returns { prefix, count, lastId, nextId, files, lastTitles }.
 */
function scanNamespace(namespacePath) {
  const heuristicsDir = path.join(namespacePath, 'heuristics');

  if (!fs.existsSync(heuristicsDir)) {
    return {
      namespace: namespacePath,
      heuristics_dir: heuristicsDir,
      exists: false,
      prefix: null,
      count: 0,
      lastId: null,
      nextId: null,
      files: [],
      lastTitles: [],
    };
  }

  // Match both 2-letter (KA_KE) and longer prefixes (PV_KE, etc)
  const FAMILY_RE = /^([A-Z]{2,4}_KE)_(\d+)\.md$/;

  const files = fs
    .readdirSync(heuristicsDir)
    .filter(f => FAMILY_RE.test(f))
    .sort();

  const count = files.length;
  let prefix = null;
  let lastId = null;
  let nextId = null;

  if (count > 0) {
    const last = files[files.length - 1];
    const m = last.match(FAMILY_RE);
    prefix = m[1];
    const num = parseInt(m[2], 10);
    lastId = `${prefix}_${String(num).padStart(3, '0')}`;
    nextId = `${prefix}_${String(num + 1).padStart(3, '0')}`;
  }

  // Collect last 5 titles for sanity/diagnostic output
  const lastTitles = files.slice(-5).map(f => {
    const fullPath = path.join(heuristicsDir, f);
    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      const firstLine = content.split('\n')[0].replace(/^#\s*/, '');
      return { id: f.replace(/\.md$/, ''), title: firstLine };
    } catch (err) {
      return { id: f.replace(/\.md$/, ''), title: '(unreadable)' };
    }
  });

  return {
    namespace: namespacePath,
    heuristics_dir: heuristicsDir,
    exists: true,
    prefix,
    count,
    lastId,
    nextId,
    files,
    lastTitles,
  };
}

/**
 * Given a namespace scan result, compute drift vs declared state in operator file.
 * Returns { hasDrift, drift: { field, declared, actual }[] }.
 */
function checkDrift(scanResult, declaredState) {
  const drift = [];

  if (declaredState.heuristic_count !== scanResult.count) {
    drift.push({
      field: 'heuristic_count',
      declared: declaredState.heuristic_count,
      actual: scanResult.count,
    });
  }

  if (declaredState.last_heuristic_id !== scanResult.lastId) {
    drift.push({
      field: 'last_heuristic_id',
      declared: declaredState.last_heuristic_id,
      actual: scanResult.lastId,
    });
  }

  if (declaredState.next_heuristic_id !== scanResult.nextId) {
    drift.push({
      field: 'next_heuristic_id',
      declared: declaredState.next_heuristic_id,
      actual: scanResult.nextId,
    });
  }

  if (declaredState.heuristic_id_prefix !== scanResult.prefix && scanResult.prefix !== null) {
    drift.push({
      field: 'heuristic_id_prefix',
      declared: declaredState.heuristic_id_prefix,
      actual: scanResult.prefix,
    });
  }

  return {
    hasDrift: drift.length > 0,
    drift,
  };
}

module.exports = {
  scanNamespace,
  checkDrift,
};
