#!/usr/bin/env node

/**
 * Mega Brain — Package Layer Validation
 *
 * Compares npm pack --dry-run output against L1 audit classifications.
 * Reports PASSED or FAILED with details on any non-L1 files.
 *
 * Usage:
 *   node bin/validate-package.js          # Validate and report
 *   node bin/validate-package.js --json   # JSON output for CI
 *
 * Exit codes:
 *   0 = PASSED (all files are L1)
 *   1 = FAILED (non-L1 files found)
 *   2 = ERROR (could not run validation)
 */

import { execSync } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { writeFileSync, unlinkSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, '..');

// ANSI colors
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const NC = '\x1b[0m';

/**
 * Get the list of files that npm pack would include.
 * @param {string} projectRoot - Path to project root
 * @returns {string[]} Array of relative file paths
 */
function getPackFiles(projectRoot) {
  try {
    const packOutput = execSync('npm pack --dry-run --json 2>/dev/null', {
      cwd: projectRoot,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    const packData = JSON.parse(packOutput);
    if (packData && packData[0] && packData[0].files) {
      return packData[0].files.map(f => f.path);
    }
    return [];
  } catch {
    return null; // Signal failure
  }
}

/**
 * Classify pack files using audit_layers.py via Python subprocess.
 * @param {string[]} files - Array of relative file paths
 * @param {string} projectRoot - Path to project root
 * @returns {Object} Map of file path -> {layer, reason}
 */
function classifyFiles(files, projectRoot) {
  const auditPath = resolve(projectRoot, 'core/intelligence');

  // Write a temp Python script to avoid shell quoting issues
  const pythonScript = `
import sys, json
sys.path.insert(0, ${JSON.stringify(auditPath)})
from pathlib import Path
from audit_layers import classify_path

repo = Path(${JSON.stringify(projectRoot)})
paths = json.loads(sys.stdin.read())
results = {}
for p in paths:
    layer, reason = classify_path(repo / p, repo, is_file=True)
    results[p] = {"layer": layer, "reason": reason}
print(json.dumps(results))
`;

  const tmpFile = join(tmpdir(), `validate-package-${process.pid}.py`);
  try {
    writeFileSync(tmpFile, pythonScript, 'utf-8');
    const result = execSync(`python3 "${tmpFile}"`, {
      input: JSON.stringify(files),
      encoding: 'utf-8',
      cwd: projectRoot,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return JSON.parse(result);
  } finally {
    try { unlinkSync(tmpFile); } catch { /* ignore cleanup errors */ }
  }
}

/**
 * Validate that the npm package contains only L1 content.
 * @param {string} projectRoot - Path to project root
 * @returns {{ status: string, totalFiles: number, violations: Array<{path: string, layer: string, reason: string}> }}
 */
export function validatePackageSync(projectRoot) {
  // Step 1: Get pack files
  const packFiles = getPackFiles(projectRoot);
  if (packFiles === null) {
    throw new Error('Failed to run npm pack --dry-run');
  }

  if (packFiles.length === 0) {
    throw new Error('npm pack returned 0 files — check package.json files field');
  }

  // Step 2: Classify each file
  let classifications;
  try {
    classifications = classifyFiles(packFiles, projectRoot);
  } catch (err) {
    throw new Error(`Failed to classify files: ${err.message}`);
  }

  // Step 3: Find violations (anything not L1)
  const violations = [];
  for (const file of packFiles) {
    const info = classifications[file];
    if (!info) {
      violations.push({ path: file, layer: 'UNKNOWN', reason: 'Not classified' });
    } else if (info.layer !== 'L1') {
      violations.push({ path: file, layer: info.layer, reason: info.reason });
    }
  }

  return {
    status: violations.length === 0 ? 'PASSED' : 'FAILED',
    totalFiles: packFiles.length,
    violations,
  };
}

/**
 * Print a human-readable validation report.
 * @param {{ status: string, totalFiles: number, violations: Array }} result
 */
function printReport(result) {
  if (result.status === 'PASSED') {
    console.log(`${GREEN}[validate] PASSED: All ${result.totalFiles} pack files are L1${NC}`);
  } else {
    console.error(`${RED}[validate] FAILED: ${result.violations.length} non-L1 file(s) found in package:${NC}`);
    for (const v of result.violations) {
      console.error(`${RED}  [${v.layer}] ${v.path} — ${v.reason}${NC}`);
    }
    console.error('');
    console.error(`${YELLOW}[validate] ${result.totalFiles} total files scanned, ${result.violations.length} violation(s).${NC}`);
  }
}

// CLI entry point
const isDirectRun = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (isDirectRun) {
  const jsonMode = process.argv.includes('--json');

  console.log(`${CYAN}[validate] Scanning pack files against L1 audit...${NC}`);

  try {
    const result = validatePackageSync(PROJECT_ROOT);

    if (jsonMode) {
      // JSON output for CI
      const output = {
        status: result.status,
        total_files: result.totalFiles,
        violations: result.violations,
      };
      console.log(JSON.stringify(output, null, 2));
    } else {
      printReport(result);
    }

    process.exit(result.status === 'PASSED' ? 0 : 1);
  } catch (err) {
    if (jsonMode) {
      console.log(JSON.stringify({ status: 'ERROR', error: err.message }));
    } else {
      console.error(`${RED}[validate] ERROR: ${err.message}${NC}`);
    }
    process.exit(2);
  }
}
