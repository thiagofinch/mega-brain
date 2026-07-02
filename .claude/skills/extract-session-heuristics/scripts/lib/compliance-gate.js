/**
 * compliance-gate — Phase 4.5 template compliance check.
 *
 * Validates that a heuristic L3 .md file has the 6 mandatory fields required
 * by the extract-session-heuristics SKILL.md Phase 4.5 EXIT GATE:
 *
 *   1. [SOURCE:] present in header + L2 evidence
 *   2. Zone header (Genialidade | Excelência | Impacto)
 *   3. rule block with "SE ... ENTÃO ... NUNCA" pattern in Configuration YAML
 *   4. sys_tension field in Configuration YAML
 *   5. failure_modes field in Configuration YAML
 *   6. anti_pattern reference (or NEVER: in Decision Tree)
 *
 * Returns { valid, checks, missing, blockers }.
 * Called from Phase 4.5 before Phase 5 PERSIST.
 */

'use strict';

const fs = require('fs');

const MANDATORY_CHECKS = [
  {
    id: 'source',
    label: '[SOURCE:] traceability',
    test: (content) => {
      const count = (content.match(/\[SOURCE:/g) || []).length;
      return { ok: count >= 1, count, required: 1 };
    },
  },
  {
    id: 'zone',
    label: 'Zone header',
    test: (content) => {
      const hasZone = /\*\*Zone:\*\*/i.test(content);
      const hasCategory = /(genialidade|excelência|excelencia|impacto)/i.test(content);
      return { ok: hasZone && hasCategory };
    },
  },
  {
    id: 'rule',
    label: 'rule SE/ENTÃO/NUNCA pattern',
    test: (content) => {
      // Accept any word-boundary after the keyword (space, colon, punctuation, newline)
      const hasSE = /\bSE\b[^a-zA-Z]/.test(content);
      const hasENTAO = /ENT[ÃA]O[^a-zA-Z]/.test(content);
      const hasNUNCA = /\bNUNCA\b[^a-zA-Z]|NEVER:/.test(content);
      return { ok: hasSE && hasENTAO && hasNUNCA };
    },
  },
  {
    id: 'sys_tension',
    label: 'sys_tension field',
    test: (content) => {
      return { ok: /sys_tension\s*:/.test(content) };
    },
  },
  {
    id: 'failure_modes',
    label: 'failure_modes field',
    test: (content) => {
      return { ok: /failure_modes\s*:/.test(content) };
    },
  },
  {
    id: 'anti_pattern',
    label: 'anti_pattern or NEVER section',
    test: (content) => {
      const hasAntiPattern = /anti_pattern\s*:/.test(content);
      const hasNever = /NEVER:/.test(content);
      return { ok: hasAntiPattern || hasNever };
    },
  },
];

const RECOMMENDED_CHECKS = [
  {
    id: 'confidence_requirements',
    label: 'Confidence Requirements section',
    test: (content) => ({ ok: /Confidence Requirements/i.test(content) }),
  },
  {
    id: 'cross_mind_divergence',
    label: 'Cross-Mind Divergence section',
    test: (content) => ({ ok: /(Cross-Mind Divergence|Divergence Analysis)/i.test(content) }),
  },
  {
    id: 'behavioral_evidence',
    label: 'Behavioral Evidence section',
    test: (content) => ({ ok: /Behavioral Evidence/i.test(content) }),
  },
];

/**
 * Validate a single heuristic L3 .md file against the mandatory + recommended checks.
 * Returns { valid, status, mandatory, recommended, blockers }.
 */
function validateHeuristicFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {
      valid: false,
      status: 'missing',
      file: filePath,
      error: 'File does not exist',
      mandatory: [],
      recommended: [],
      blockers: ['file_missing'],
    };
  }

  const content = fs.readFileSync(filePath, 'utf-8');

  const mandatoryResults = MANDATORY_CHECKS.map(check => ({
    id: check.id,
    label: check.label,
    ...check.test(content),
  }));

  const recommendedResults = RECOMMENDED_CHECKS.map(check => ({
    id: check.id,
    label: check.label,
    ...check.test(content),
  }));

  const mandatoryPassing = mandatoryResults.filter(r => r.ok).length;
  const mandatoryTotal = mandatoryResults.length;
  const recommendedPassing = recommendedResults.filter(r => r.ok).length;
  const recommendedTotal = recommendedResults.length;

  const blockers = mandatoryResults
    .filter(r => !r.ok)
    .map(r => r.id);

  // Status logic:
  // - All 6 mandatory present → validated
  // - Missing non-SOURCE mandatory → draft (persist with flag)
  // - Missing SOURCE → BLOCK (VETO-ESH-001)
  let status;
  if (blockers.length === 0) {
    status = 'validated';
  } else if (blockers.includes('source')) {
    status = 'block';
  } else if (blockers.length === 1) {
    status = 'draft';
  } else {
    status = 'incomplete';
  }

  return {
    valid: status === 'validated' || status === 'draft',
    status,
    file: filePath,
    mandatory: {
      passing: mandatoryPassing,
      total: mandatoryTotal,
      results: mandatoryResults,
    },
    recommended: {
      passing: recommendedPassing,
      total: recommendedTotal,
      results: recommendedResults,
    },
    blockers,
  };
}

/**
 * Batch validate multiple heuristic files. Returns per-file + aggregate.
 */
function validateBatch(filePaths) {
  const results = filePaths.map(validateHeuristicFile);
  const validated = results.filter(r => r.status === 'validated').length;
  const drafts = results.filter(r => r.status === 'draft').length;
  const blocked = results.filter(r => r.status === 'block').length;
  const incomplete = results.filter(r => r.status === 'incomplete').length;

  return {
    total: results.length,
    validated,
    drafts,
    blocked,
    incomplete,
    all_passing: blocked === 0 && incomplete === 0,
    results,
  };
}

module.exports = {
  MANDATORY_CHECKS,
  RECOMMENDED_CHECKS,
  validateHeuristicFile,
  validateBatch,
};
