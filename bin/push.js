#!/usr/bin/env node

/**
 * Mega Brain - Smart Multi-Layer Push System v2.0
 *
 * Pushes content to the appropriate git remote based on layer selection:
 *   Layer 1 (public)  → Community content, respects .gitignore → remote "origin"
 *   Layer 2 (premium) → Layer 1 + premium manifest paths → remote "premium"
 *   Layer 3 (backup)  → Everything, no filtering → remote "backup"
 *
 * Usage:
 *   mega-brain push               Interactive layer selection
 *   mega-brain push --layer 1     Direct push to Layer 1
 *   mega-brain push --layer 2     Direct push to Layer 2
 *   mega-brain push --layer 3     Direct push to Layer 3
 *   mega-brain push --dry-run     Show what would happen without executing
 *   mega-brain push --message "x" Commit message (skips prompt)
 *
 * Remotes (configure via git remote):
 *   origin  → <your-github>/mega-brain.git
 *   premium → <your-github>/mega-brain-premium.git
 *   backup  → <your-github>/mega-brain-full.git
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import boxen from 'boxen';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, '..');

const LAYER_CONFIG = {
  1: {
    name: 'Community',
    label: 'Layer 1 — Community (publico, npm)',
    remote: 'origin',
    remoteUrl: 'https://github.com/<your-username>/mega-brain.git',
    color: '#6366f1',
  },
  2: {
    name: 'Premium',
    label: 'Layer 2 — Premium (MoneyClub, privado)',
    remote: 'premium',
    remoteUrl: 'https://github.com/<your-username>/mega-brain-premium.git',
    color: '#f59e0b',
  },
  3: {
    name: 'Full Backup',
    label: 'Layer 3 — Full Backup (tudo, privado)',
    remote: 'backup',
    remoteUrl: 'https://github.com/<your-username>/mega-brain-full.git',
    color: '#ef4444',
  },
};

const SENSITIVE_PATTERNS = [
  /github_pat_[A-Za-z0-9_]{20,}/,
  /ghp_[A-Za-z0-9]{20,}/,
  /gho_[A-Za-z0-9]{20,}/,
  /ghs_[A-Za-z0-9]{20,}/,
];

// sk-ant- check: match the prefix but NOT the known placeholder
const SK_ANT_REAL = /sk-ant-(?!api03-sua-chave-aqui)[A-Za-z0-9_-]+/;

// Excluded personas — add names of persona directories that should NOT go to Layer 2
const LAYER2_EXCLUDED_PERSONAS = ['example-persona-1', 'example-persona-2'];

// ---------------------------------------------------------------------------
// Git helpers
// ---------------------------------------------------------------------------

function git(cmd, opts = {}) {
  try {
    // Signal pre-push hook that push.js already validated this push
    const env = cmd.startsWith('push ')
      ? { ...process.env, MEGA_BRAIN_PUSH_VALIDATED: 'true', ...opts.env }
      : { ...process.env, ...opts.env };

    return execSync(`git ${cmd}`, {
      cwd: PROJECT_ROOT,
      encoding: 'utf-8',
      stdio: opts.silent ? 'pipe' : 'inherit',
      env,
      ...opts,
    });
  } catch (err) {
    if (opts.silent) return '';
    throw err;
  }
}

function gitSilent(cmd) {
  return git(cmd, { silent: true, stdio: 'pipe' }).trim();
}

function getRemotes() {
  const output = gitSilent('remote -v');
  const remotes = {};
  for (const line of output.split('\n')) {
    const match = line.match(/^(\S+)\s+(\S+)\s+\(push\)/);
    if (match) remotes[match[1]] = match[2];
  }
  return remotes;
}

function getCurrentBranch() {
  return gitSilent('rev-parse --abbrev-ref HEAD') || 'main';
}

function hasUncommittedChanges() {
  return gitSilent('status --porcelain').length > 0;
}

function getStatusSummary() {
  const status = gitSilent('status --porcelain');
  if (!status) return null;
  const lines = status.split('\n').filter(Boolean);
  return {
    total: lines.length,
    preview: lines.slice(0, 8),
    hasMore: lines.length > 8,
    remaining: Math.max(0, lines.length - 8),
  };
}

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const args = argv.slice(2).filter((a) => a !== 'push');
  const result = { layer: null, dryRun: false, message: null };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--layer' && args[i + 1]) {
      const num = parseInt(args[i + 1], 10);
      if ([1, 2, 3].includes(num)) result.layer = num;
      i++;
    } else if (args[i] === '--dry-run') {
      result.dryRun = true;
    } else if ((args[i] === '--message' || args[i] === '-m') && args[i + 1]) {
      result.message = args[i + 1];
      i++;
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Layer 2 manifest parsing
// ---------------------------------------------------------------------------

function loadLayer2ManifestPaths() {
  const manifestPath = resolve(PROJECT_ROOT, '.github', 'layer2-manifest.txt');
  if (!existsSync(manifestPath)) return [];

  const content = readFileSync(manifestPath, 'utf-8');
  const paths = [];
  let inExclusions = false;

  for (const raw of content.split('\n')) {
    const line = raw.trim();
    if (line.includes('LAYER 3 EXCLUSIONS')) {
      inExclusions = true;
      continue;
    }
    if (inExclusions) continue;
    if (!line || line.startsWith('#')) continue;
    paths.push(line.replace(/\/+$/, ''));
  }

  return paths;
}

function loadLayer3ManifestPaths() {
  const manifestPath = resolve(PROJECT_ROOT, '.github', 'layer3-manifest.txt');
  if (!existsSync(manifestPath)) return [];

  const content = readFileSync(manifestPath, 'utf-8');
  const paths = [];

  for (const raw of content.split('\n')) {
    const line = raw.trim();
    if (line.includes('ALWAYS EXCLUDED')) break;
    if (!line || line.startsWith('#')) continue;
    paths.push(line.replace(/\/+$/, ''));
  }

  return paths;
}

// Files that must NEVER be pushed to any remote
const SECRET_FILES = [
  '.env', '.env.local', '.env.production', '.env.development',
  '.mcp.json', 'credentials.json', 'token.json', 'token_write.json',
  'settings.local.json', '.claude/settings.json',
];

// ---------------------------------------------------------------------------
// Pre-push validation
// ---------------------------------------------------------------------------

/**
 * Validate the repository state for the target layer.
 * Returns { ok: boolean, warnings: string[], errors: string[] }
 */
function validateForLayer(layer) {
  const warnings = [];
  const errors = [];

  if (layer === 1) {
    // --- Check phantom tracked files (files tracked but should be ignored) ---
    const phantoms = gitSilent('ls-files -ci --exclude-standard');
    if (phantoms) {
      const phantomList = phantoms.split('\n').filter(Boolean);
      warnings.push(
        `${phantomList.length} arquivo(s) fantasma encontrado(s) (tracked mas deveria ser ignorado):\n` +
        phantomList.slice(0, 5).map((f) => `      ${chalk.dim(f)}`).join('\n') +
        (phantomList.length > 5 ? `\n      ${chalk.dim(`... e mais ${phantomList.length - 5}`)}` : '')
      );
    }

    // --- Check for real API keys in tracked files ---
    const trackedFiles = gitSilent('ls-files').split('\n').filter(Boolean);
    const keyFindings = [];

    for (const file of trackedFiles) {
      // Skip binary-like extensions
      if (/\.(png|jpg|jpeg|gif|ico|svg|woff2?|ttf|eot|pdf|zip|tar|gz)$/i.test(file)) continue;

      const filePath = resolve(PROJECT_ROOT, file);
      if (!existsSync(filePath)) continue;

      let content;
      try {
        content = readFileSync(filePath, 'utf-8');
      } catch {
        continue; // skip unreadable files
      }

      for (const pattern of SENSITIVE_PATTERNS) {
        if (pattern.test(content)) {
          keyFindings.push(`${file} contém token sensível (${pattern.source.slice(0, 15)}...)`);
          break;
        }
      }

      if (SK_ANT_REAL.test(content)) {
        keyFindings.push(`${file} contém chave Anthropic real (sk-ant-...)`);
      }
    }

    if (keyFindings.length > 0) {
      errors.push(
        `Chaves/tokens sensíveis detectados em arquivos tracked:\n` +
        keyFindings.map((f) => `      ${chalk.red(f)}`).join('\n')
      );
    }

    // --- Check no .env is tracked (exclude .env.example which is OK) ---
    const trackedEnv = trackedFiles.filter((f) =>
      (f === '.env' || f.match(/^\.env\.\w/)) && !f.endsWith('.example')
    );
    if (trackedEnv.length > 0) {
      errors.push(
        `Arquivo .env está tracked:\n` +
        trackedEnv.map((f) => `      ${chalk.red(f)}`).join('\n')
      );
    }
  }

  if (layer === 2) {
    const manifestPaths = loadLayer2ManifestPaths();

    // --- Check excluded personas are not in manifest paths ---
    for (const persona of LAYER2_EXCLUDED_PERSONAS) {
      const found = manifestPaths.filter((p) => p.includes(persona));
      if (found.length > 0) {
        errors.push(
          `Persona excluída "${persona}" encontrada nos caminhos do manifest:\n` +
          found.map((f) => `      ${chalk.red(f)}`).join('\n')
        );
      }
    }

    // --- Check no .env or .claude/agent-memory/ in manifest paths ---
    for (const mp of manifestPaths) {
      if (mp.includes('.env')) {
        errors.push(`Caminho do manifest contém .env: ${mp}`);
      }
      if (mp.includes('.claude/agent-memory')) {
        errors.push(`Caminho do manifest contém agent-memory: ${mp}`);
      }
    }

    // --- Check on-disk files: no excluded personas in premium content ---
    for (const mp of manifestPaths) {
      const fullPath = resolve(PROJECT_ROOT, mp);
      if (!existsSync(fullPath)) continue;

      for (const persona of LAYER2_EXCLUDED_PERSONAS) {
        // Check if any file inside the manifest path contains excluded persona name
        try {
          const checkOutput = execSync(
            `git ls-files "${mp}"`,
            { cwd: PROJECT_ROOT, encoding: 'utf-8', stdio: 'pipe' }
          ).trim();
          const matchingFiles = checkOutput.split('\n').filter((f) => f && f.includes(persona));
          if (matchingFiles.length > 0) {
            warnings.push(
              `Conteúdo Layer 3 "${persona}" encontrado em ${mp}:\n` +
              matchingFiles.slice(0, 3).map((f) => `      ${chalk.dim(f)}`).join('\n')
            );
          }
        } catch {
          // Ignore errors
        }
      }
    }
  }

  // Layer 3: no validation needed

  return {
    ok: errors.length === 0,
    warnings,
    errors,
  };
}

// ---------------------------------------------------------------------------
// Interactive layer selection
// ---------------------------------------------------------------------------

async function selectLayerInteractive() {
  console.log();

  const { layer } = await inquirer.prompt([
    {
      type: 'list',
      name: 'layer',
      message: chalk.cyan('Para qual layer deseja publicar?'),
      choices: [
        {
          name:
            chalk.bold.hex('#6366f1')('Layer 1') +
            chalk.white(' — Community ') +
            chalk.dim('(publico, npm)'),
          value: 1,
        },
        {
          name:
            chalk.bold.hex('#f59e0b')('Layer 2') +
            chalk.white(' — Premium ') +
            chalk.dim('(MoneyClub, privado)'),
          value: 2,
        },
        {
          name:
            chalk.bold.hex('#ef4444')('Layer 3') +
            chalk.white(' — Full Backup ') +
            chalk.dim('(tudo, privado)'),
          value: 3,
        },
      ],
      loop: false,
    },
  ]);

  return layer;
}

// ---------------------------------------------------------------------------
// Commit message prompt
// ---------------------------------------------------------------------------

async function promptCommitMessage(defaultPrefix) {
  const { message } = await inquirer.prompt([
    {
      type: 'input',
      name: 'message',
      message: chalk.cyan('Mensagem do commit:'),
      default: defaultPrefix,
      validate: (input) => (input.trim() ? true : chalk.red('Mensagem nao pode estar vazia.')),
    },
  ]);
  return message.trim();
}

// ---------------------------------------------------------------------------
// Confirmation prompt
// ---------------------------------------------------------------------------

async function confirmAction(question) {
  const { confirmed } = await inquirer.prompt([
    {
      type: 'confirm',
      name: 'confirmed',
      message: chalk.cyan(question),
      default: true,
    },
  ]);
  return confirmed;
}

// ---------------------------------------------------------------------------
// Layer 1 Push Flow
// ---------------------------------------------------------------------------

async function pushLayer1({ dryRun, message }) {
  const config = LAYER_CONFIG[1];
  const branch = getCurrentBranch();

  // Step 1: Validate
  const spinner = ora({ text: 'Validando para Layer 1...', color: 'cyan' }).start();
  const validation = validateForLayer(1);

  if (validation.warnings.length > 0) {
    spinner.warn(chalk.yellow('Avisos de validacao:'));
    for (const w of validation.warnings) {
      console.log(`    ${chalk.yellow('!')} ${w}`);
    }
  }

  if (!validation.ok) {
    spinner.fail(chalk.red('Validacao falhou com erros:'));
    for (const e of validation.errors) {
      console.log(`    ${chalk.red('x')} ${e}`);
    }
    console.log();
    console.log(chalk.dim('  Corrija os erros acima antes de fazer push para Layer 1.'));
    console.log(chalk.dim('  Para remover arquivos do tracking: git rm --cached <arquivo>'));
    console.log();
    process.exit(1);
  }

  if (validation.warnings.length === 0) {
    spinner.succeed(chalk.green('Validacao OK'));
  }

  if (dryRun) {
    showDryRun(1, config, branch);
    return;
  }

  // Step 2: git add -A (respects .gitignore)
  const addSpinner = ora({ text: 'Staging arquivos (respeitando .gitignore)...', color: 'cyan' }).start();
  try {
    git('add -A', { silent: true, stdio: 'pipe' });
    addSpinner.succeed(chalk.green('Arquivos staged'));
  } catch (err) {
    addSpinner.fail(chalk.red(`Falha ao fazer staging: ${err.message}`));
    process.exit(1);
  }

  // Check if there's anything to commit
  const staged = gitSilent('diff --cached --stat');
  if (!staged) {
    console.log(chalk.dim('\n  Nenhuma mudanca para commit. Verificando se existe algo para push...\n'));

    // Still try to push in case there are local commits not yet pushed
    const pushSpinner = ora({ text: `Pushing para ${config.remote}/${branch}...`, color: 'cyan' }).start();
    try {
      git(`push ${config.remote} ${branch}`, { silent: true, stdio: 'pipe' });
      pushSpinner.succeed(chalk.green(`Push concluido para ${config.remote}/${branch}`));
    } catch (err) {
      if (err.stderr && err.stderr.includes('Everything up-to-date')) {
        pushSpinner.info(chalk.dim('Ja esta atualizado.'));
      } else {
        pushSpinner.fail(chalk.red(`Falha no push: ${err.message}`));
        process.exit(1);
      }
    }

    await autoSyncToBackup(branch);
    return;
  }

  // Step 3: Commit message
  const commitMsg = message || (await promptCommitMessage('feat: update Layer 1 content'));

  // Step 4: git commit
  const commitSpinner = ora({ text: 'Criando commit...', color: 'cyan' }).start();
  try {
    git(`commit -m "${commitMsg.replace(/"/g, '\\"')}"`, { silent: true, stdio: 'pipe' });
    commitSpinner.succeed(chalk.green('Commit criado'));
  } catch (err) {
    const output = err.stdout || err.stderr || '';
    if (output.includes('nothing to commit')) {
      commitSpinner.info(chalk.dim('Nada para commitar.'));
    } else {
      commitSpinner.fail(chalk.red(`Falha no commit: ${err.message}`));
      process.exit(1);
    }
  }

  // Step 5: git push public main
  const pushSpinner = ora({ text: `Pushing para ${config.remote}/${branch}...`, color: 'cyan' }).start();
  try {
    git(`push ${config.remote} ${branch}`);
    pushSpinner.succeed(chalk.green(`Push concluido para ${config.remote}/${branch}`));
  } catch (err) {
    pushSpinner.fail(chalk.red(`Falha no push: ${err.message}`));
    process.exit(1);
  }

  // Step 6: Ask about npm publish
  const publishNpm = await confirmAction('Publicar no npm tambem?');
  if (publishNpm) {
    const npmSpinner = ora({ text: 'Publicando no npm...', color: 'cyan' }).start();
    try {
      execSync('npm publish', { cwd: PROJECT_ROOT, stdio: 'inherit' });
      npmSpinner.succeed(chalk.green('Publicado no npm!'));
    } catch (err) {
      npmSpinner.fail(chalk.red(`Falha ao publicar no npm: ${err.message}`));
    }
  }

  // Step 7: Auto-sync to backup (Layer 3)
  await autoSyncToBackup(branch);
}

// ---------------------------------------------------------------------------
// Layer 2 Push Flow
// ---------------------------------------------------------------------------

async function pushLayer2({ dryRun, message }) {
  const config = LAYER_CONFIG[2];
  const branch = getCurrentBranch();

  // Step 1: Validate
  const spinner = ora({ text: 'Validando para Layer 2...', color: 'yellow' }).start();
  const validation = validateForLayer(2);

  if (validation.warnings.length > 0) {
    spinner.warn(chalk.yellow('Avisos de validacao:'));
    for (const w of validation.warnings) {
      console.log(`    ${chalk.yellow('!')} ${w}`);
    }
  }

  if (!validation.ok) {
    spinner.fail(chalk.red('Validacao falhou com erros:'));
    for (const e of validation.errors) {
      console.log(`    ${chalk.red('x')} ${e}`);
    }
    console.log();
    process.exit(1);
  }

  if (validation.warnings.length === 0) {
    spinner.succeed(chalk.green('Validacao OK'));
  }

  // Step 2: Read layer2-manifest.txt to get premium paths
  const manifestPaths = loadLayer2ManifestPaths();
  if (manifestPaths.length === 0) {
    console.log(chalk.red('\n  Erro: layer2-manifest.txt vazio ou nao encontrado.'));
    console.log(chalk.dim('  Verifique: .github/layer2-manifest.txt\n'));
    process.exit(1);
  }

  console.log(chalk.dim(`\n  Manifest: ${manifestPaths.length} caminhos premium definidos`));
  for (const p of manifestPaths) {
    console.log(chalk.dim(`    + ${p}`));
  }
  console.log();

  if (dryRun) {
    showDryRun(2, config, branch);
    console.log(chalk.dim('  Caminhos do manifest que seriam adicionados com git add -f:'));
    for (const p of manifestPaths) {
      const exists = existsSync(resolve(PROJECT_ROOT, p));
      console.log(`    ${exists ? chalk.green('+') : chalk.red('x')} ${p} ${!exists ? chalk.dim('(nao existe)') : ''}`);
    }
    console.log();
    return;
  }

  // Step 3: git add -f each manifest path that exists on disk
  const addSpinner = ora({ text: 'Staging caminhos premium (force add)...', color: 'yellow' }).start();
  let addedCount = 0;

  for (const manifestPath of manifestPaths) {
    const fullPath = resolve(PROJECT_ROOT, manifestPath);
    if (!existsSync(fullPath)) continue;

    try {
      git(`add -f "${manifestPath}"`, { silent: true, stdio: 'pipe' });
      addedCount++;
    } catch {
      // Some paths may fail — that's ok
    }
  }

  if (addedCount === 0) {
    addSpinner.warn(chalk.yellow('Nenhum caminho premium encontrado no disco.'));
    console.log(chalk.dim('  Verifique se o conteudo premium existe localmente.\n'));
    process.exit(1);
  }

  addSpinner.succeed(chalk.green(`${addedCount} caminhos premium staged`));

  // Step 4: Commit (bypass pre-commit hook via env var — this is a temporary commit)
  const commitMsg = message || 'feat(premium): update Layer 2 content';
  const commitSpinner = ora({ text: 'Criando commit premium...', color: 'yellow' }).start();
  try {
    git(`commit -m "${commitMsg.replace(/"/g, '\\"')}"`, { silent: true, stdio: 'pipe', env: { MEGA_BRAIN_LAYER_PUSH: 'true' } });
    commitSpinner.succeed(chalk.green('Commit premium criado'));
  } catch (err) {
    const output = (err.stdout || '') + (err.stderr || '');
    if (output.includes('nothing to commit')) {
      commitSpinner.info(chalk.dim('Nada de novo para commitar no premium.'));
      return;
    }
    commitSpinner.fail(chalk.red(`Falha no commit: ${err.message}`));
    process.exit(1);
  }

  // Step 5: git push premium main --force
  const pushSpinner = ora({ text: `Pushing para ${config.remote}/${branch} (force)...`, color: 'yellow' }).start();
  try {
    git(`push ${config.remote} ${branch} --force`);
    pushSpinner.succeed(chalk.green(`Push concluido para ${config.remote}/${branch}`));
  } catch (err) {
    pushSpinner.fail(chalk.red(`Falha no push: ${err.message}`));
    // Still try to reset even if push fails
    resetLastCommit();
    process.exit(1);
  }

  // Step 6: git reset HEAD~1 (remove Layer 2 commit from local, keep files)
  resetLastCommit();

  // Step 7: Auto-sync to backup (Layer 3)
  await autoSyncToBackup(branch);
}

// ---------------------------------------------------------------------------
// Layer 3 Push Flow
// ---------------------------------------------------------------------------

async function pushLayer3({ dryRun, message }) {
  const config = LAYER_CONFIG[3];
  const branch = getCurrentBranch();

  // No validation for Layer 3

  // Read Layer 3 manifest
  const layer3Paths = loadLayer3ManifestPaths();
  if (layer3Paths.length === 0) {
    console.log(chalk.red('\n  Erro: layer3-manifest.txt vazio ou nao encontrado.'));
    console.log(chalk.dim('  Verifique: .github/layer3-manifest.txt\n'));
    process.exit(1);
  }

  if (dryRun) {
    showDryRun(3, config, branch);
    console.log(chalk.dim('  Caminhos do manifest que seriam adicionados com git add -f:'));
    for (const p of layer3Paths) {
      const exists = existsSync(resolve(PROJECT_ROOT, p));
      console.log(`    ${exists ? chalk.green('+') : chalk.red('x')} ${p} ${!exists ? chalk.dim('(nao existe)') : ''}`);
    }
    console.log();
    return;
  }

  // Step 1: Stage tracked files normally
  const addSpinner = ora({ text: 'Staging arquivos tracked...', color: 'red' }).start();
  try {
    git('add -A', { silent: true, stdio: 'pipe' });
    addSpinner.succeed(chalk.green('Arquivos tracked staged'));
  } catch (err) {
    addSpinner.fail(chalk.red(`Falha ao fazer staging: ${err.message}`));
    process.exit(1);
  }

  // Step 2: Force-add Layer 3 content (gitignored but needed for backup)
  const forceSpinner = ora({ text: 'Staging conteudo de backup (force add)...', color: 'red' }).start();
  let addedCount = 0;

  for (const manifestPath of layer3Paths) {
    const fullPath = resolve(PROJECT_ROOT, manifestPath);
    if (!existsSync(fullPath)) continue;

    try {
      git(`add -f "${manifestPath}"`, { silent: true, stdio: 'pipe' });
      addedCount++;
    } catch {
      // Some paths may fail — that's ok
    }
  }

  forceSpinner.succeed(chalk.green(`${addedCount} caminhos de backup staged`));

  // Step 3: Safety — unstage secrets that may have been caught
  for (const secretFile of SECRET_FILES) {
    try {
      git(`reset HEAD -- "${secretFile}"`, { silent: true, stdio: 'pipe' });
    } catch {
      // File may not exist or not be staged
    }
  }

  // Check if there's anything to commit
  const staged = gitSilent('diff --cached --stat');
  if (!staged) {
    console.log(chalk.dim('\n  Nenhuma mudanca para commit. Pushing estado atual...\n'));

    const pushSpinner = ora({ text: `Pushing para ${config.remote}/${branch} (force)...`, color: 'red' }).start();
    try {
      git(`push ${config.remote} ${branch} --force`);
      pushSpinner.succeed(chalk.green(`Push concluido para ${config.remote}/${branch}`));
    } catch (err) {
      pushSpinner.fail(chalk.red(`Falha no push: ${err.message}`));
      process.exit(1);
    }
    return;
  }

  // Step 4: Commit message
  const commitMsg = message || (await promptCommitMessage('backup: full state sync'));

  // Step 5: git commit (bypass pre-commit hook via env var — this is a temporary commit)
  const commitSpinner = ora({ text: 'Criando commit de backup...', color: 'red' }).start();
  try {
    git(`commit -m "${commitMsg.replace(/"/g, '\\"')}"`, { silent: true, stdio: 'pipe', env: { MEGA_BRAIN_LAYER_PUSH: 'true' } });
    commitSpinner.succeed(chalk.green('Commit criado'));
  } catch (err) {
    const output = (err.stdout || '') + (err.stderr || '');
    if (output.includes('nothing to commit')) {
      commitSpinner.info(chalk.dim('Nada para commitar.'));
    } else {
      commitSpinner.fail(chalk.red(`Falha no commit: ${err.message}`));
      process.exit(1);
    }
  }

  // Step 6: git push backup main --force
  const pushSpinner = ora({ text: `Pushing para ${config.remote}/${branch} (force)...`, color: 'red' }).start();
  try {
    git(`push ${config.remote} ${branch} --force`);
    pushSpinner.succeed(chalk.green(`Push concluido para ${config.remote}/${branch}`));
  } catch (err) {
    pushSpinner.fail(chalk.red(`Falha no push: ${err.message}`));
    // Still try to reset
    resetLastCommit();
    process.exit(1);
  }

  // Step 7: git reset HEAD~1 (Layer 3 commit doesn't stay on local main)
  resetLastCommit();
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Reset the last commit but keep files (mixed reset).
 * Used by Layer 2 and Layer 3 to avoid polluting local main.
 */
function resetLastCommit() {
  const resetSpinner = ora({ text: 'Limpando commit local (reset HEAD~1)...', color: 'gray' }).start();
  try {
    git('reset HEAD~1', { silent: true, stdio: 'pipe' });
    resetSpinner.succeed(chalk.dim('Commit local removido (arquivos preservados)'));
  } catch (err) {
    resetSpinner.warn(chalk.yellow(`Nao foi possivel fazer reset: ${err.message}`));
  }
}

/**
 * Auto-sync current main to backup remote (Layer 3).
 */
async function autoSyncToBackup(branch) {
  const remotes = getRemotes();
  if (!remotes.backup) {
    console.log(chalk.dim('\n  Remote "backup" nao configurado. Pulando auto-sync.\n'));
    return;
  }

  const syncSpinner = ora({ text: 'Auto-sync para backup (Layer 3)...', color: 'gray' }).start();
  try {
    git(`push backup ${branch} --force`, { silent: true, stdio: 'pipe' });
    syncSpinner.succeed(chalk.dim('Auto-sync para backup concluido'));
  } catch {
    syncSpinner.warn(chalk.dim('Auto-sync para backup falhou (nao critico)'));
  }
}

/**
 * Show dry-run summary without executing.
 */
function showDryRun(layer, config, branch) {
  console.log();
  console.log(
    boxen(
      chalk.bold.yellow(' DRY RUN ') +
        chalk.white(' — Nenhuma acao sera executada\n\n') +
        chalk.white(`  Layer:   ${config.label}\n`) +
        chalk.white(`  Remote:  ${config.remote} → ${config.remoteUrl}\n`) +
        chalk.white(`  Branch:  ${branch}\n`) +
        chalk.white(`  Comando: git push ${config.remote} ${branch}`) +
        (layer !== 1 ? chalk.white(' --force') : ''),
      {
        padding: 1,
        margin: { left: 2 },
        borderStyle: 'round',
        borderColor: 'yellow',
      }
    )
  );

  if (layer === 1) {
    console.log(chalk.dim('\n  Fluxo Layer 1:'));
    console.log(chalk.dim('    1. Validar (phantom files, API keys, .env)'));
    console.log(chalk.dim('    2. git add -A (respeita .gitignore)'));
    console.log(chalk.dim('    3. Prompt para commit message'));
    console.log(chalk.dim('    4. git commit'));
    console.log(chalk.dim('    5. git push origin main'));
    console.log(chalk.dim('    6. Perguntar sobre npm publish'));
    console.log(chalk.dim('    7. Auto-sync para backup (Layer 3)'));
  } else if (layer === 2) {
    console.log(chalk.dim('\n  Fluxo Layer 2:'));
    console.log(chalk.dim('    1. Validar (personas excluidas, .env)'));
    console.log(chalk.dim('    2. Ler layer2-manifest.txt'));
    console.log(chalk.dim('    3. git add -f para cada caminho do manifest'));
    console.log(chalk.dim('    4. git commit'));
    console.log(chalk.dim('    5. git push premium main --force'));
    console.log(chalk.dim('    6. git reset HEAD~1 (limpar commit local)'));
    console.log(chalk.dim('    7. Auto-sync para backup (Layer 3)'));
  } else {
    console.log(chalk.dim('\n  Fluxo Layer 3:'));
    console.log(chalk.dim('    1. Sem validacao (tudo vai)'));
    console.log(chalk.dim('    2. git add -A (tracked files)'));
    console.log(chalk.dim('    3. git add -f para caminhos do layer3-manifest.txt'));
    console.log(chalk.dim('    4. git reset HEAD -- secrets (safety net)'));
    console.log(chalk.dim('    5. Prompt para commit message'));
    console.log(chalk.dim('    6. git commit'));
    console.log(chalk.dim('    7. git push backup main --force'));
    console.log(chalk.dim('    8. git reset HEAD~1 (limpar commit local)'));
  }

  console.log();
}

/**
 * Verify that a remote exists and show helpful error if not.
 */
function ensureRemoteExists(layer) {
  const config = LAYER_CONFIG[layer];
  const remotes = getRemotes();

  if (!remotes[config.remote]) {
    console.log();
    console.log(chalk.red(`  Erro: Remote "${config.remote}" nao esta configurado.`));
    console.log();
    console.log(chalk.white('  Para adicionar:'));
    console.log(chalk.cyan(`    git remote add ${config.remote} ${config.remoteUrl}`));
    console.log();
    console.log(chalk.dim('  Remotes atuais:'));
    for (const [name, url] of Object.entries(remotes)) {
      console.log(chalk.dim(`    ${name} → ${url}`));
    }
    console.log();
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Banner
// ---------------------------------------------------------------------------

function showBanner() {
  console.log();
  console.log(
    boxen(chalk.bold.hex('#a855f7')('  Mega Brain Push  '), {
      padding: { left: 2, right: 2, top: 0, bottom: 0 },
      margin: { left: 2 },
      borderStyle: 'round',
      borderColor: '#a855f7',
    })
  );
}

function showSuccess(layer, branch) {
  const config = LAYER_CONFIG[layer];
  console.log();
  console.log(
    boxen(
      chalk.bold.hex(config.color)(`  Push concluido!  `) +
        '\n\n' +
        chalk.white(`  Layer:  ${config.label}\n`) +
        chalk.white(`  Remote: ${config.remote}/${branch}`),
      {
        padding: 1,
        margin: { left: 2 },
        borderStyle: 'round',
        borderColor: config.color,
      }
    )
  );
  console.log();
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const opts = parseArgs(process.argv);

  showBanner();

  // Select layer
  const layer = opts.layer || (await selectLayerInteractive());
  const config = LAYER_CONFIG[layer];
  const branch = getCurrentBranch();

  // Verify remote exists (unless dry-run)
  if (!opts.dryRun) {
    ensureRemoteExists(layer);
  }

  // Show current state
  console.log();
  console.log(chalk.white(`  Layer:  `) + chalk.bold.hex(config.color)(config.label));
  console.log(chalk.white(`  Remote: `) + chalk.dim(`${config.remote}/${branch}`));

  // Show uncommitted changes warning
  const status = getStatusSummary();
  if (status) {
    console.log();
    console.log(chalk.yellow(`  ${status.total} arquivo(s) com mudancas pendentes:`));
    for (const line of status.preview) {
      console.log(chalk.dim(`    ${line}`));
    }
    if (status.hasMore) {
      console.log(chalk.dim(`    ... e mais ${status.remaining} arquivo(s)`));
    }
  }

  console.log();

  // Confirm (unless dry-run or --layer was explicit)
  if (!opts.dryRun && !opts.layer) {
    const confirmed = await confirmAction('Confirmar push?');
    if (!confirmed) {
      console.log(chalk.dim('\n  Push cancelado.\n'));
      process.exit(0);
    }
  }

  // Execute the appropriate push flow
  switch (layer) {
    case 1:
      await pushLayer1(opts);
      break;
    case 2:
      await pushLayer2(opts);
      break;
    case 3:
      await pushLayer3(opts);
      break;
  }

  showSuccess(layer, branch);
}

// ---------------------------------------------------------------------------
// Entry point — works as standalone binary AND as module import
// ---------------------------------------------------------------------------

export { pushLayer1, pushLayer2, pushLayer3, validateForLayer, loadLayer2ManifestPaths, loadLayer3ManifestPaths };

main().catch((err) => {
  console.error();
  console.error(chalk.red(`  Erro fatal: ${err.message}`));
  if (process.env.DEBUG) {
    console.error(err.stack);
  }
  console.error();
  process.exit(1);
});
