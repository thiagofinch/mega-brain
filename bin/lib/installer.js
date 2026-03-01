/**
 * Mega Brain - Installer Module (Interactive UX)
 *
 * Uses inquirer for arrow-key navigation, chalk for colors,
 * ora for spinners, boxen for styled boxes, gradient-string for banners.
 *
 * Handles the full installation flow:
 *   1. Edition selection (PREMIUM vs Community)
 *   2. Email validation (PREMIUM only)
 *   3. Directory setup
 *   4. File copy (shell)
 *   5. Premium content fetch (if validated)
 *   6. Post-install summary
 */

import { existsSync, mkdirSync, cpSync, writeFileSync, readFileSync, readdirSync, rmSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';
import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import boxen from 'boxen';
import gradient from 'gradient-string';
import { validateEmail, getErrorMessage, resetAttempts } from './validate-email.js';
import { writeLicense, maskEmail as maskLicenseEmail } from './license.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const TEMPLATE_ROOT = resolve(__dirname, '..', '..');

const megaGradient = gradient(['#6366f1', '#8b5cf6', '#a855f7']);
const goldGradient = gradient(['#f59e0b', '#eab308', '#fbbf24']);

function stepHeader(step, total, description) {
  console.log(`\n  ${chalk.dim(`─── Passo ${step} de ${total} ───`)} ${chalk.bold(description)}\n`);
}

/**
 * Main installer flow
 */
export async function runInstaller(version, projectName) {
  console.log();

  // ──────────────────────────────────────────────────────────
  // STEP 1: Edition Selection
  // ──────────────────────────────────────────────────────────
  stepHeader(1, 5, 'Selecione sua Edição');

  const isPremium = await selectEdition();

  // ──────────────────────────────────────────────────────────
  // STEP 2: Email Validation (PREMIUM only)
  // ──────────────────────────────────────────────────────────
  let buyerName = '';
  let buyerEmail = '';
  let premiumToken = null;

  if (isPremium) {
    stepHeader(2, 5, 'Validação de Acesso Premium');

    let validated = false;
    resetAttempts();

    while (!validated) {
      const { email } = await inquirer.prompt([{
        type: 'input',
        name: 'email',
        message: chalk.cyan('Email cadastrado no MoneyClub:'),
        validate: (input) => input.trim() ? true : chalk.red('Email não pode estar vazio.'),
      }]);

      const spinner = ora({ text: 'Verificando acesso...', color: 'cyan' }).start();
      const result = await validateEmail(email.trim());

      if (result.valid) {
        buyerName = result.name || 'Membro';
        buyerEmail = email.trim();
        premiumToken = result.premium_token || null;
        spinner.succeed(chalk.green(`Bem-vindo, ${chalk.bold(buyerName)}! Acesso PREMIUM confirmado.`));
        if (result.installCount > 1) {
          console.log(chalk.dim(`    (Instalação #${result.installCount})`));
        }
        validated = true;
      } else {
        spinner.fail(chalk.red(getErrorMessage(result.reason)));
        if (result.reason === 'max_attempts_exceeded') {
          process.exit(1);
        }
        const { retry } = await inquirer.prompt([{
          type: 'confirm',
          name: 'retry',
          message: 'Tentar novamente?',
          default: true,
        }]);
        if (!retry) {
          console.log(chalk.yellow('\n  Instalação cancelada.\n'));
          process.exit(0);
        }
      }
    }
  } else {
    stepHeader(2, 5, 'Modo Community');
    console.log(chalk.dim('  Pulando validação — instalando shell sem conteúdo premium.'));
    buyerName = 'Community User';
  }

  // ──────────────────────────────────────────────────────────
  // STEP 3: Installation Directory
  // ──────────────────────────────────────────────────────────
  stepHeader(3, 5, 'Diretório de Instalação');

  const cwd = process.cwd();
  let targetDir;

  if (projectName) {
    // Project name passed via CLI — skip interactive prompt
    targetDir = resolve(cwd, projectName);
    console.log(chalk.cyan(`  Instalando em: ${chalk.bold(targetDir)}\n`));
  } else {
    // Interactive directory selection
    const { dirChoice } = await inquirer.prompt([{
      type: 'list',
      name: 'dirChoice',
      message: chalk.cyan('Onde deseja instalar?'),
      choices: [
        { name: `Diretório atual  ${chalk.dim('(' + cwd + ')')}`, value: 'current' },
        { name: `Novo diretório   ${chalk.dim('./mega-brain')}`, value: 'new' },
        { name: 'Caminho personalizado', value: 'custom' },
      ],
    }]);

    switch (dirChoice) {
      case 'current':
        targetDir = cwd;
        break;
      case 'custom': {
        const { customPath } = await inquirer.prompt([{
          type: 'input',
          name: 'customPath',
          message: chalk.cyan('Caminho completo:'),
          validate: (input) => input.trim() ? true : chalk.red('Caminho não pode estar vazio.'),
        }]);
        targetDir = resolve(customPath.trim());
        break;
      }
      case 'new':
      default:
        targetDir = resolve(cwd, 'mega-brain');
        break;
    }
  }

  if (existsSync(join(targetDir, '.claude', 'CLAUDE.md'))) {
    const { overwrite } = await inquirer.prompt([{
      type: 'confirm',
      name: 'overwrite',
      message: chalk.yellow(`Mega Brain já existe em ${targetDir}. Sobrescrever?`),
      default: false,
    }]);
    if (!overwrite) {
      console.log(chalk.yellow('\n  Instalação cancelada.\n'));
      process.exit(0);
    }
  }

  // ──────────────────────────────────────────────────────────
  // STEP 4: Install Shell (Layer 1 — always)
  // ──────────────────────────────────────────────────────────
  stepHeader(4, 5, 'Instalando estrutura base');

  const installSpinner = ora({ text: 'Copiando arquivos do template...', color: 'cyan' }).start();

  try {
    if (!existsSync(targetDir)) {
      mkdirSync(targetDir, { recursive: true });
    }

    const excludeDirs = ['.git', 'node_modules', 'bin'];
    copyTemplateFiles(TEMPLATE_ROOT, targetDir, excludeDirs);

    installSpinner.text = 'Configurando ambiente...';

    const envTemplate = resolve(__dirname, '..', 'templates', 'env.example');
    if (existsSync(envTemplate)) {
      const envContent = readFileSync(envTemplate, 'utf-8');
      writeFileSync(join(targetDir, '.env.example'), envContent);
    }

    installSpinner.text = 'Criando diretórios...';
    ensureDirectories(targetDir);

    installSpinner.succeed(chalk.green('Estrutura base instalada!'));
  } catch (err) {
    installSpinner.fail(chalk.red(`Erro ao instalar: ${err.message}`));
    process.exit(1);
  }

  // ──────────────────────────────────────────────────────────
  // STEP 5: Fetch Premium Content (Layer 2 — PREMIUM only)
  // ──────────────────────────────────────────────────────────
  if (isPremium && premiumToken) {
    stepHeader(5, 5, 'Baixando conteúdo PREMIUM');

    const premiumSpinner = ora({ text: 'Conectando ao repositório premium...', color: 'magenta' }).start();

    try {
      await fetchPremiumContent(targetDir, premiumToken, premiumSpinner);
    } catch (err) {
      premiumSpinner.warn(chalk.yellow(`Não foi possível baixar conteúdo premium: ${err.message}`));
      console.log(chalk.dim('  Tente novamente depois com: mega-brain upgrade'));
    }
  } else {
    stepHeader(5, 5, 'Instalação Completa');
  }

  // ──────────────────────────────────────────────────────────
  // Write license.json
  // ──────────────────────────────────────────────────────────
  if (isPremium) {
    writeLicense({
      tier: 'pro',
      email: buyerEmail ? maskLicenseEmail(buyerEmail) : null,
      activated_at: new Date().toISOString(),
      validated_at: new Date().toISOString(),
      features: ['knowledge', 'playbooks', 'persons', 'cargo', 'processing'],
    });
  } else {
    writeLicense({
      tier: 'community',
      activated_at: new Date().toISOString(),
    });
  }

  // ──────────────────────────────────────────────────────────
  // Summary
  // ──────────────────────────────────────────────────────────
  console.log();
  if (isPremium) {
    showPostInstallPremium(buyerName);
  } else {
    showPostInstallCommunity();
  }
}

/**
 * Upgrade from Community to Premium
 */
export async function runUpgrade(version) {
  const { readLicense, writeLicense, maskEmail: maskUpgradeEmail } = await import('./license.js');
  const { isProInstalled } = await import('../utils/pro-detector.js');

  const license = readLicense();
  const installed = isProInstalled();

  if (installed && license?.tier === 'pro') {
    console.log(chalk.green('\n  Mega Brain Pro ja esta instalado e ativo!'));
    console.log(chalk.dim('  Use: mega-brain validate <email> para revalidar.\n'));
    return;
  }

  console.log(chalk.cyan('\n  Upgrade para PREMIUM\n'));

  // Email validation
  resetAttempts();
  let validated = false;
  let premiumToken = null;

  while (!validated) {
    const { email } = await inquirer.prompt([{
      type: 'input',
      name: 'email',
      message: chalk.cyan('Email cadastrado no MoneyClub:'),
      validate: (input) => input.trim() ? true : chalk.red('Email nao pode estar vazio.'),
    }]);

    const spinner = ora({ text: 'Verificando acesso...', color: 'cyan' }).start();
    const result = await validateEmail(email.trim());

    if (result.valid) {
      premiumToken = result.premium_token || null;
      spinner.succeed(chalk.green(`Acesso confirmado, ${result.name || 'Membro'}!`));

      writeLicense({
        tier: 'pro',
        email: maskUpgradeEmail(email.trim()),
        activated_at: new Date().toISOString(),
        validated_at: new Date().toISOString(),
        features: ['knowledge', 'playbooks', 'persons', 'cargo', 'processing'],
      });

      validated = true;
    } else {
      spinner.fail(chalk.red(getErrorMessage(result.reason)));
      if (result.reason === 'max_attempts_exceeded') process.exit(1);
      const { retry } = await inquirer.prompt([{
        type: 'confirm', name: 'retry', message: 'Tentar novamente?', default: true,
      }]);
      if (!retry) { process.exit(0); }
    }
  }

  if (premiumToken) {
    const targetDir = process.cwd();
    const premiumSpinner = ora({ text: 'Baixando conteudo premium...', color: 'magenta' }).start();
    try {
      await fetchPremiumContent(targetDir, premiumToken, premiumSpinner);
    } catch (err) {
      premiumSpinner.warn(chalk.yellow(`Erro: ${err.message}`));
    }
  }

  showPostInstallPremium('Membro');
}

/**
 * Edition selection with inquirer arrow-key list
 */
async function selectEdition() {
  const premiumLabel = goldGradient('★ PREMIUM') + chalk.white(' — Membro MoneyClub');
  const premiumDesc = [
    chalk.dim('    Sistema COMPLETO com o cérebro ligado.'),
    chalk.dim('    Mentes Clonadas, C-Levels (CRO/CFO/CMO/COO),'),
    chalk.dim('    Squad de Vendas, Conclave de Deliberação,'),
    chalk.dim('    +50 fontes pagas já processadas.'),
    chalk.dim('    Requer email cadastrado no MoneyClub.'),
  ].join('\n');

  const communityLabel = chalk.white('  COMMUNITY') + chalk.dim(' — Máquina sem Cérebro');
  const communityDesc = [
    chalk.dim('    Estrutura vazia. Comandos, skills e protocolos'),
    chalk.dim('    do JARVIS, mas SEM conteúdo processado.'),
    chalk.dim('    Você precisará alimentar tudo do zero.'),
  ].join('\n');

  const { edition } = await inquirer.prompt([{
    type: 'list',
    name: 'edition',
    message: chalk.cyan('Escolha sua edição:'),
    choices: [
      { name: premiumLabel + '\n' + premiumDesc, value: 'premium' },
      new inquirer.Separator(chalk.dim('  ─────────────────────────────────────────')),
      { name: communityLabel + '\n' + communityDesc, value: 'community' },
    ],
    loop: false,
  }]);

  return edition === 'premium';
}

/**
 * Fetch premium content from private repo using token
 *
 * LAYER 2 DESIGN:
 *   Layer 1 (npm) installs the empty shell.
 *   Layer 2 (this function) fills ONLY the premium paths defined
 *   in .github/layer2-manifest.txt — nothing else.
 *
 *   After copying, the temporary clone is deleted to save disk space.
 */
async function fetchPremiumContent(targetDir, token, spinner) {
  const tempDir = join(targetDir, '.layer-sync', 'premium-fetch');

  // Safety: ensure tempDir is strictly INSIDE targetDir
  const resolvedTemp = resolve(tempDir);
  const resolvedTarget = resolve(targetDir);
  if (!resolvedTemp.startsWith(resolvedTarget + '/') && !resolvedTemp.startsWith(resolvedTarget + '\\')) {
    throw new Error('Erro interno: caminho de download fora do diretório de instalação.');
  }

  mkdirSync(join(targetDir, '.layer-sync'), { recursive: true });

  // L-09: Validate token format to prevent injection
  const TOKEN_PATTERN = /^[a-zA-Z0-9_.\-]+$/;
  if (!TOKEN_PATTERN.test(token)) {
    throw new Error('Token contém caracteres inválidos.');
  }

  // M-04 + L-04 + L-10: Use execFileSync + http.extraheader (no token in URL/process list)
  const repoUrl = `https://github.com/${process.env.MEGA_BRAIN_GH_ORG || 'thiagofinch'}/mega-brain-premium.git`;
  const authHeader = `Authorization: Basic ${Buffer.from(`x-access-token:${token}`).toString('base64')}`;

  // --- CLONE ---
  if (!existsSync(join(tempDir, '.git'))) {
    spinner.succeed(chalk.cyan('Baixando conteúdo premium...'));
    console.log(chalk.dim('  Isso pode levar alguns minutos dependendo da sua conexão.\n'));

    try {
      execFileSync('git', [
        '-c', `http.extraheader=${authHeader}`,
        'clone', '--depth', '1', repoUrl, tempDir
      ], {
        stdio: 'inherit',
        timeout: 600000,
      });
    } catch (cloneErr) {
      throw new Error('Git clone falhou. Verifique sua conexão e tente novamente.');
    }

    console.log();
    spinner.start('Verificando download...');
  } else {
    spinner.text = 'Download anterior encontrado, reutilizando...';
  }

  if (!existsSync(tempDir) || readdirSync(tempDir).length <= 1) {
    throw new Error('Repositório premium clonado mas vazio.');
  }

  // --- READ LAYER 2 MANIFEST ---
  // The manifest lives in the Layer 1 shell (already installed).
  // It lists which paths are premium additions.
  const manifestPath = join(targetDir, '.github', 'layer2-manifest.txt');
  const layer2Paths = parseManifestPaths(manifestPath);

  if (layer2Paths.length === 0) {
    throw new Error('layer2-manifest.txt vazio ou não encontrado.');
  }

  // --- SELECTIVE COPY: only Layer 2 paths ---
  spinner.text = 'Integrando conteúdo premium (apenas Layer 2)...';
  let copied = 0;

  for (const relPath of layer2Paths) {
    const srcPath = join(tempDir, relPath);
    const destPath = join(targetDir, relPath);

    if (!existsSync(srcPath)) continue;

    mkdirSync(dirname(destPath), { recursive: true });
    cpSync(srcPath, destPath, { recursive: true, force: true });
    copied++;
  }

  if (copied === 0) {
    throw new Error('Nenhum conteúdo premium encontrado no repositório.');
  }

  spinner.text = 'Limpando arquivos temporários...';

  // --- CLEANUP: delete the clone to save disk space ---
  try {
    rmSync(join(targetDir, '.layer-sync'), { recursive: true, force: true });
  } catch {
    // Non-fatal: warn but don't fail if cleanup fails
    console.log(chalk.dim('  Aviso: não foi possível limpar .layer-sync/'));
  }

  spinner.succeed(chalk.green(`Conteúdo PREMIUM instalado! (${copied} módulos)`));
}

/**
 * Parse layer2-manifest.txt and return clean directory paths.
 * Ignores comments (#), blank lines, and LAYER 3 EXCLUSIONS section.
 */
function parseManifestPaths(manifestPath) {
  if (!existsSync(manifestPath)) return [];

  const content = readFileSync(manifestPath, 'utf-8');
  const paths = [];
  let inExclusions = false;

  for (const raw of content.split('\n')) {
    const line = raw.trim();

    // Stop parsing at Layer 3 exclusions section
    if (line.includes('LAYER 3 EXCLUSIONS')) {
      inExclusions = true;
      continue;
    }
    if (inExclusions) continue;

    // Skip comments and blanks
    if (!line || line.startsWith('#')) continue;

    // Normalize: remove trailing slash
    paths.push(line.replace(/\/+$/, ''));
  }

  return paths;
}

/**
 * Post-install message for PREMIUM users
 */
function showPostInstallPremium(name) {
  const content =
    goldGradient('  ★ Mega Brain PREMIUM instalado!') + '\n\n'
    + chalk.white(`  Bem-vindo ao sistema completo, ${chalk.bold(name)}!`) + '\n\n'
    + chalk.dim('  Próximo passo:') + '\n'
    + chalk.white('  Abra o projeto no Claude Code e o JARVIS') + '\n'
    + chalk.white('  irá se apresentar automaticamente.') + '\n\n'
    + chalk.dim('  Comandos iniciais:') + '\n'
    + chalk.cyan('    /conclave "sua pergunta"') + chalk.dim('  — Deliberação estratégica') + '\n'
    + chalk.cyan('    /ingest [URL/arquivo]') + chalk.dim('    — Alimentar o sistema') + '\n'
    + chalk.cyan('    /ask [expert]') + chalk.dim('           — Consultar clone mental');

  console.log(boxen(content, {
    padding: 1,
    margin: { left: 2 },
    borderStyle: 'round',
    borderColor: '#f59e0b',
  }));
  console.log();
}

/**
 * Post-install message for Community users
 */
function showPostInstallCommunity() {
  const content =
    megaGradient('  Mega Brain COMMUNITY instalado!') + '\n\n'
    + chalk.white('  Você tem a estrutura. Agora precisa do cérebro.') + '\n\n'
    + chalk.dim('  Para ativar o PREMIUM a qualquer momento:') + '\n'
    + chalk.cyan('    mega-brain upgrade') + '\n\n'
    + chalk.dim('  Ou comece do zero alimentando o sistema:') + '\n'
    + chalk.cyan('    /ingest [URL do YouTube]') + chalk.dim('  — Importar conteúdo') + '\n'
    + chalk.cyan('    /process-jarvis') + chalk.dim('          — Processar pipeline') + '\n\n'
    + chalk.dim('  megabrain.ai/premium — Acesse o PREMIUM completo');

  console.log(boxen(content, {
    padding: 1,
    margin: { left: 2 },
    borderStyle: 'round',
    borderColor: '#6366f1',
  }));
  console.log();
}

function copyTemplateFiles(source, target, excludeDirs) {
  if (!existsSync(source)) {
    throw new Error(`Template não encontrado: ${source}`);
  }

  const entries = readdirSync(source, { withFileTypes: true });

  if (entries.length === 0) {
    throw new Error(`Template vazio: ${source}`);
  }

  let copied = 0;
  for (const entry of entries) {
    if (excludeDirs.includes(entry.name)) continue;

    const srcPath = join(source, entry.name);
    const destPath = join(target, entry.name);

    try {
      if (entry.isDirectory()) {
        cpSync(srcPath, destPath, { recursive: true, force: true });
      } else {
        mkdirSync(dirname(destPath), { recursive: true });
        cpSync(srcPath, destPath, { force: true });
      }
      copied++;
    } catch (err) {
      console.error(`  Aviso: falha ao copiar ${entry.name}: ${err.message}`);
    }
  }

  if (copied === 0) {
    throw new Error(`Nenhum arquivo copiado. Source: ${source} (${entries.length} entries, ${excludeDirs.length} excluded)`);
  }
}

function ensureDirectories(root) {
  const dirs = [
    'inbox',
    'processing/chunks',
    'processing/canonical',
    'processing/insights',
    'processing/narratives',
    'knowledge/dossiers/persons',
    'knowledge/dossiers/themes',
    'knowledge/dossiers/system',
    'knowledge/sources',
    'knowledge/playbooks',
    'knowledge/dna',
    'logs',
    'logs/sessions',
    'logs/batches',
    'logs/decisions',
    'agents/persons',
    'agents/cargo',
    'agents/sua-empresa/org',
    'agents/sua-empresa/roles',
    'agents/sua-empresa/jds',
    'agents/sua-empresa/operations',
    'agents/sua-empresa/metrics',
    'agents/sua-empresa/memory',
    'agents/sua-empresa/sow',
  ];

  for (const dir of dirs) {
    const fullPath = join(root, dir);
    if (!existsSync(fullPath)) {
      mkdirSync(fullPath, { recursive: true });
    }
    const gitkeep = join(fullPath, '.gitkeep');
    if (!existsSync(gitkeep)) {
      writeFileSync(gitkeep, '');
    }
  }
}
