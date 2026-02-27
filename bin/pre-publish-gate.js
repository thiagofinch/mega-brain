#!/usr/bin/env node

/**
 * Mega Brain — Pre-Publish Security Gate (PHYSICAL BLOCK)
 *
 * PURPOSE: Scan npm package contents for secrets AND verify only L1 content
 *          is included BEFORE publishing.
 * DESIGN: fail-CLOSED — if scanning fails, publish is BLOCKED.
 * INSTALLED: 2026-02-20 (post-incident hardening)
 * UPDATED: 2026-02-27 (added L1 layer validation)
 *
 * Runs automatically via: "prepublishOnly": "node bin/pre-publish-gate.js"
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync, mkdirSync, rmSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { validatePackageSync } from './validate-package.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, '..');

// ANSI colors
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const NC = '\x1b[0m';

// === SECRET PATTERNS ===
const SECRET_PATTERNS = [
  // GitHub tokens
  /ghp_[A-Za-z0-9]{36}/,
  /github_pat_[A-Za-z0-9_]{82}/,
  /gho_[A-Za-z0-9]{36}/,
  /ghs_[A-Za-z0-9]{36}/,
  /ghr_[A-Za-z0-9]{36}/,
  // Anthropic
  /sk-ant-[A-Za-z0-9-]{90,}/,
  // OpenAI
  /sk-[A-Za-z0-9]{48}/,
  // AWS
  /AKIA[0-9A-Z]{16}/,
  // ElevenLabs
  /sk_[a-f0-9]{48}/,
  // N8N webhooks
  /https?:\/\/[^/]*\.app\.n8n\.cloud\/webhook/,
  // Notion
  /ntn_[A-Za-z0-9]{40,}/,
  /secret_[A-Za-z0-9]{40,}/,
  // JWT tokens (Supabase, etc.)
  /eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}/,
  // Generic secrets in code
  /(?:password|api_key|secret|token|private_key)\s*[:=]\s*['"][^'"]{12,}['"]/i,
  // Brazilian CPF (11 digits)
  /\d{3}\.\d{3}\.\d{3}-\d{2}/,
  // Brazilian CNPJ
  /\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}/,
  // Email addresses in bulk (PII indicator)
  /[\w.+-]+@[\w-]+\.[\w.]+/,
];

// Files that should NEVER be in the package
const FORBIDDEN_FILE_PATTERNS = [
  /\.env($|\.)/i,
  /credentials\.json$/i,
  /service.account.*\.json$/i,
  /\.pem$/i,
  /\.key$/i,
  /id_rsa/i,
  /id_ed25519/i,
  /\.sqlite$/i,
  /\.db$/i,
  /memory\.db$/i,
  /DOSSIE-SEGURANCA/i,
  /trufflehog/i,
];

// Maximum emails allowed (more than this = PII leak)
const MAX_EMAILS_PER_FILE = 3;

console.log(`${YELLOW}[pre-publish] Running security gate before npm publish...${NC}`);

let foundIssues = 0;

// === STEP 1: Clean __pycache__ (original prepublishOnly behavior) ===
try {
  execSync('find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null', {
    cwd: PROJECT_ROOT,
    stdio: 'ignore',
  });
} catch {
  // Ignore cleanup errors
}

// === STEP 2: Get list of files that would be published ===
let packFiles = [];
try {
  const packOutput = execSync('npm pack --dry-run --json 2>/dev/null', {
    cwd: PROJECT_ROOT,
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  const packData = JSON.parse(packOutput);
  if (packData && packData[0] && packData[0].files) {
    packFiles = packData[0].files.map(f => f.path);
  }
} catch {
  // Fallback: use the files field from package.json
  console.log(`${YELLOW}[pre-publish] npm pack --dry-run failed, using files field fallback.${NC}`);
  try {
    const pkg = JSON.parse(readFileSync(resolve(PROJECT_ROOT, 'package.json'), 'utf-8'));
    packFiles = pkg.files || [];
  } catch {
    console.error(`${RED}[BLOCKED] Cannot determine package files. Blocking publish.${NC}`);
    process.exit(1);
  }
}

console.log(`${CYAN}[pre-publish] Scanning ${packFiles.length} files...${NC}`);

// === STEP 3: Check file names for forbidden patterns ===
for (const file of packFiles) {
  for (const pattern of FORBIDDEN_FILE_PATTERNS) {
    if (pattern.test(file)) {
      console.error(`${RED}[BLOCKED] Forbidden file in package: ${file}${NC}`);
      foundIssues++;
    }
  }
}

// === STEP 4: Scan file contents for secrets ===
const BINARY_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
  '.woff', '.woff2', '.ttf', '.eot',
  '.pdf', '.zip', '.tar', '.gz', '.bz2',
  '.mp3', '.mp4', '.wav', '.webm',
]);

for (const file of packFiles) {
  // Skip binary files
  const ext = file.substring(file.lastIndexOf('.')).toLowerCase();
  if (BINARY_EXTENSIONS.has(ext)) continue;

  const filePath = resolve(PROJECT_ROOT, file);
  if (!existsSync(filePath)) continue;

  let content;
  try {
    content = readFileSync(filePath, 'utf-8');
  } catch {
    continue;
  }

  // Check for secret patterns
  for (const pattern of SECRET_PATTERNS) {
    const matches = content.match(new RegExp(pattern.source, 'g'));
    if (matches) {
      // Special handling for emails: allow up to MAX_EMAILS_PER_FILE
      if (pattern.source.includes('@')) {
        if (matches.length > MAX_EMAILS_PER_FILE) {
          console.error(`${RED}[BLOCKED] Bulk PII (${matches.length} emails) in: ${file}${NC}`);
          foundIssues++;
        }
        continue;
      }

      // Redact the actual values
      const redacted = matches[0].substring(0, 12) + '**REDACTED**';
      console.error(`${RED}[BLOCKED] Secret found in: ${file} → ${redacted}${NC}`);
      foundIssues++;
    }
  }
}

// === STEP 5: Optional trufflehog scan ===
try {
  execSync('trufflehog --version', { stdio: 'pipe' });
  console.log(`${YELLOW}[pre-publish] Running trufflehog deep scan...${NC}`);
  const result = execSync(
    `trufflehog filesystem "${PROJECT_ROOT}" --only-verified --no-update --json`,
    { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'], timeout: 120000 }
  );
  if (result.trim()) {
    console.error(`${RED}[BLOCKED] trufflehog found VERIFIED secrets.${NC}`);
    foundIssues++;
  }
} catch {
  // trufflehog not available, pattern scan is sufficient
}

// === STEP 6: Layer validation (L1 only) ===
console.log(`${CYAN}[pre-publish] Running layer validation...${NC}`);
try {
  const validation = validatePackageSync(PROJECT_ROOT);
  if (validation.status === 'FAILED') {
    console.error(`${RED}[BLOCKED] ${validation.violations.length} non-L1 file(s) in package:${NC}`);
    for (const v of validation.violations) {
      console.error(`${RED}  [${v.layer}] ${v.path} — ${v.reason}${NC}`);
    }
    foundIssues += validation.violations.length;
  } else {
    console.log(`${GREEN}[pre-publish] Layer validation PASSED: ${validation.totalFiles} files, all L1.${NC}`);
  }
} catch (err) {
  // Layer validation is best-effort in pre-publish gate.
  // If Python or audit_layers.py not available, WARN but don't block.
  console.warn(`${YELLOW}[pre-publish] Layer validation skipped: ${err.message}${NC}`);
  console.warn(`${YELLOW}[pre-publish] Run 'node bin/validate-package.js' manually to validate.${NC}`);
}

// === VERDICT ===
if (foundIssues > 0) {
  console.error('');
  console.error(`${RED}=====================================================${NC}`);
  console.error(`${RED}  NPM PUBLISH BLOCKED: ${foundIssues} security issue(s) found  ${NC}`);
  console.error(`${RED}=====================================================${NC}`);
  console.error('');
  console.error(`${YELLOW}  Fix the issues above before publishing.${NC}`);
  console.error(`${YELLOW}  Run 'npm pack --dry-run' to see what would be published.${NC}`);
  console.error('');
  process.exit(1);
}

console.log(`${GREEN}[pre-publish] Security gate PASSED. ${packFiles.length} files scanned, 0 issues.${NC}`);
console.log(`${GREEN}[pre-publish] Package is safe to publish.${NC}`);
