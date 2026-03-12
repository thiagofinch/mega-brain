#!/usr/bin/env node

/**
 * Mega Brain — Git Hook Installer
 *
 * Creates symlink: .git/hooks/pre-commit → ../../.claude/hooks/pre_commit_audit.py
 *
 * Run manually or via `npm install` (postinstall).
 * Backs up existing hook as .pre-commit.bak if present.
 */

import { existsSync, readlinkSync, renameSync, symlinkSync, chmodSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, '..');

// ANSI colors
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const NC = '\x1b[0m';

const HOOKS_DIR = resolve(PROJECT_ROOT, '.git', 'hooks');
const HOOK_PATH = resolve(HOOKS_DIR, 'pre-commit');
const TARGET_REL = '../../.claude/hooks/pre_commit_audit.py';
const TARGET_ABS = resolve(PROJECT_ROOT, '.claude', 'hooks', 'pre_commit_audit.py');

// Check we're in a git repo
if (!existsSync(resolve(PROJECT_ROOT, '.git'))) {
  console.log(`${YELLOW}[install-hooks] Not a git repository — skipping hook install.${NC}`);
  process.exit(0);
}

// Check target hook script exists
if (!existsSync(TARGET_ABS)) {
  console.error(`${YELLOW}[install-hooks] Hook script not found: ${TARGET_ABS}${NC}`);
  process.exit(0); // Don't fail postinstall for consumers
}

// Check if hook already installed correctly
if (existsSync(HOOK_PATH)) {
  try {
    const current = readlinkSync(HOOK_PATH);
    if (current === TARGET_REL) {
      console.log(`${GREEN}[install-hooks] pre-commit hook already installed.${NC}`);
      process.exit(0);
    }
  } catch {
    // Not a symlink — it's a regular file
  }

  // Backup existing hook
  const backupPath = resolve(HOOKS_DIR, '.pre-commit.bak');
  renameSync(HOOK_PATH, backupPath);
  console.log(`${YELLOW}[install-hooks] Backed up existing pre-commit hook → .pre-commit.bak${NC}`);
}

// Create symlink (relative path so repo can move)
try {
  symlinkSync(TARGET_REL, HOOK_PATH);
  chmodSync(HOOK_PATH, 0o755);
  console.log(`${GREEN}[install-hooks] pre-commit hook installed → ${TARGET_REL}${NC}`);
} catch (err) {
  console.error(`${YELLOW}[install-hooks] Failed to create symlink: ${err.message}${NC}`);
  process.exit(0); // Don't fail postinstall
}
