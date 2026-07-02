#!/usr/bin/env node

/**
 * bin/mega-brain-doctor.js -- System Health Checks (self-contained)
 *
 * Performs basic, cross-platform environment checks without depending on
 * any Python engine module. Degrades gracefully — never crashes the CLI,
 * never relies on non-portable primitives (e.g. fcntl).
 *
 * Checks:
 *   - Node.js present and >= v18
 *   - Python 3 present (recommended for hooks)
 *   - Git present (recommended)
 *   - .env present in the project (recommended)
 *
 * Usage:
 *   node bin/mega-brain-doctor.js          # Human-readable output
 *   node bin/mega-brain-doctor.js --json   # JSON output
 *
 * Exit codes:
 *   0 = all REQUIRED checks pass (warnings allowed)
 *   1 = one or more REQUIRED checks failed
 */

import { execSync } from 'child_process';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = resolve(__dirname, '..');

// Load .env if available (Node 21+ native) — best effort, never throws.
const envPath = resolve(projectRoot, '.env');
if (existsSync(envPath)) {
  try { process.loadEnvFile?.(envPath); } catch { /* noop */ }
}

const wantsJson = process.argv.slice(2).includes('--json');

function runCmd(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf-8', timeout: 15000, stdio: 'pipe' }).trim();
  } catch {
    return null;
  }
}

function parseVersion(str) {
  if (!str) return null;
  const m = str.match(/(\d+)\.(\d+)\.(\d+)/);
  return m ? { major: +m[1], minor: +m[2], patch: +m[3], raw: m[0] } : null;
}

function detectPython() {
  for (const cmd of ['python3 --version', 'python --version', 'py -3 --version']) {
    const out = runCmd(cmd);
    if (out && out.toLowerCase().includes('python 3')) {
      return parseVersion(out);
    }
  }
  return null;
}

function buildChecks() {
  const checks = [];

  // Node.js (REQUIRED)
  const nodeVer = parseVersion(process.version.replace('v', ''));
  checks.push({
    name: 'Node.js',
    required: true,
    pass: !!nodeVer && nodeVer.major >= 18,
    version: nodeVer?.raw || process.version,
    hint: 'Necessário v18+. Atualize em nodejs.org',
  });

  // Python 3 (recommended)
  const pyVer = detectPython();
  checks.push({
    name: 'Python 3',
    required: false,
    pass: !!pyVer && pyVer.major >= 3,
    version: pyVer?.raw || null,
    hint: 'Recomendado para hooks. Instale em python.org',
  });

  // Git (recommended)
  const gitVer = parseVersion(runCmd('git --version'));
  checks.push({
    name: 'Git',
    required: false,
    pass: !!gitVer,
    version: gitVer?.raw || null,
    hint: 'Recomendado. Instale em git-scm.com',
  });

  // .env present (recommended)
  checks.push({
    name: '.env',
    required: false,
    pass: existsSync(resolve(process.cwd(), '.env')) || existsSync(envPath),
    version: null,
    hint: 'Configure com: npx @thiagofinch/mega-brain@latest setup',
  });

  return checks;
}

function main() {
  let checks;
  try {
    checks = buildChecks();
  } catch (err) {
    // Absolute last-resort guard: never crash the CLI.
    if (wantsJson) {
      console.log(JSON.stringify({ overall: 'error', error: String(err?.message || err), checks: [] }, null, 2));
    } else {
      console.log(`  Doctor não pôde rodar todos os checks: ${err?.message || err}`);
    }
    process.exit(0);
  }

  const requiredFailed = checks.some(c => c.required && !c.pass);
  const overall = requiredFailed ? 'fail' : 'pass';

  if (wantsJson) {
    console.log(JSON.stringify({ overall, checks }, null, 2));
    process.exit(overall === 'pass' ? 0 : 1);
  }

  // Human-readable
  console.log();
  console.log('  Mega Brain — Doctor');
  console.log('  ' + '─'.repeat(50));
  for (const c of checks) {
    const icon = c.pass ? '✓' : (c.required ? '✗' : '!');
    const ver = c.version ? ` (${c.version})` : '';
    let line = `  ${icon} ${c.name}${ver}`;
    if (!c.pass) line += `\n      ${c.hint}`;
    console.log(line);
  }
  console.log();
  if (overall === 'pass') {
    console.log('  Tudo certo para rodar o Mega Brain.');
  } else {
    console.log('  Há dependências obrigatórias faltando (veja acima).');
  }
  console.log();

  process.exit(overall === 'pass' ? 0 : 1);
}

main();
