/**
 * Mega Brain - Unified Installer (v2)
 *
 * Single, unified flow:
 *   1. Dependency check (Python, Node, Git)
 *   2. Directory setup + file copy (scaffold from this repo)
 *   3. Post-install config (.env + API keys)
 *   4. Post-install summary
 *
 * The buyer already has the complete product (private repo clone), so there is
 * no edition selection, no email validation, and no premium content fetch.
 */

import { existsSync, mkdirSync, cpSync, writeFileSync, readFileSync, readdirSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import boxen from 'boxen';
import { theme, stepHeader, showPostInstallCommunity, showDependencyTable } from './ascii-art.js';
import { writeLicense } from './license.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const TEMPLATE_ROOT = resolve(__dirname, '..', '..');

// ── Helpers ───────────────────────────────────────────────────

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

// ── Python Auto-Install ───────────────────────────────────────

function detectOS() {
  const platform = process.platform;
  if (platform === 'win32') return 'windows';
  if (platform === 'darwin') return 'mac';
  return 'linux';
}

function checkPythonAfterInstall() {
  for (const cmd of ['python3 --version', 'python --version', 'py -3 --version']) {
    const out = runCmd(cmd);
    if (out && out.toLowerCase().includes('python 3')) {
      return { cmd: cmd.replace(' --version', '').trim(), version: parseVersion(out) };
    }
  }
  return null;
}

async function installPythonFlow() {
  const os = detectOS();

  console.log();
  console.log(chalk.yellow('    ⚠ Python 3 é necessário para os hooks funcionarem.'));
  console.log(chalk.dim('      Sem ele, o sistema funciona mas sem automações.\n'));

  const { action } = await inquirer.prompt([{
    type: 'list',
    name: 'action',
    message: chalk.cyan('Como instalar Python 3?'),
    choices: [
      {
        name: `${chalk.white('Automático')}  ${chalk.dim('— Instalo para você agora')}`,
        value: 'auto',
      },
      {
        name: `${chalk.white('Guia passo-a-passo')}  ${chalk.dim('— Mostro como fazer')}`,
        value: 'guide',
      },
      {
        name: `${chalk.dim('Pular')}  ${chalk.dim('— Instalo depois (hooks desativados)')}`,
        value: 'skip',
      },
    ],
  }]);

  if (action === 'skip') {
    console.log(chalk.dim('    Pulando. Hooks Python ficarão desativados.\n'));
    return { installed: false };
  }

  if (action === 'guide') {
    return await showPythonGuide(os);
  }

  // Auto install
  return await autoInstallPython(os);
}

async function autoInstallPython(os) {
  const spinner = ora({ text: 'Instalando Python 3...', indent: 4, color: 'yellow' }).start();

  try {
    if (os === 'windows') {
      // Use winget (Windows 10+) — most reliable silent install
      const hasWinget = runCmd('winget --version');
      if (hasWinget) {
        spinner.text = 'Instalando via winget (pode pedir permissão de admin)...';
        execSync('winget install Python.Python.3.13 --accept-source-agreements --accept-package-agreements', {
          stdio: 'pipe',
          timeout: 120000,
        });
      } else {
        // Fallback: download and run installer
        spinner.text = 'Baixando instalador do python.org...';
        const url = 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe';
        const tempPath = resolve(process.env.TEMP || 'C:\\Temp', 'python-installer.exe');
        execSync(`powershell -Command "Invoke-WebRequest -Uri '${url}' -OutFile '${tempPath}'"`, {
          stdio: 'pipe',
          timeout: 60000,
        });
        spinner.text = 'Executando instalador (silencioso)...';
        execSync(`"${tempPath}" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1`, {
          stdio: 'pipe',
          timeout: 120000,
        });
      }
    } else if (os === 'mac') {
      // Try brew first, then xcode-select
      const hasBrew = runCmd('brew --version');
      if (hasBrew) {
        spinner.text = 'Instalando via Homebrew...';
        execSync('brew install python3', { stdio: 'pipe', timeout: 120000 });
      } else {
        spinner.fail(chalk.yellow('Homebrew não encontrado.'));
        return await showPythonGuide(os);
      }
    } else {
      // Linux
      const hasApt = runCmd('which apt');
      const hasYum = runCmd('which yum');
      const hasDnf = runCmd('which dnf');
      const hasPacman = runCmd('which pacman');

      if (hasApt) {
        spinner.text = 'Instalando via apt...';
        execSync('sudo apt update -qq && sudo apt install -y python3 python3-pip', {
          stdio: 'pipe', timeout: 120000
        });
      } else if (hasDnf) {
        spinner.text = 'Instalando via dnf...';
        execSync('sudo dnf install -y python3 python3-pip', { stdio: 'pipe', timeout: 120000 });
      } else if (hasYum) {
        spinner.text = 'Instalando via yum...';
        execSync('sudo yum install -y python3 python3-pip', { stdio: 'pipe', timeout: 120000 });
      } else if (hasPacman) {
        spinner.text = 'Instalando via pacman...';
        execSync('sudo pacman -S --noconfirm python python-pip', { stdio: 'pipe', timeout: 120000 });
      } else {
        spinner.fail(chalk.yellow('Gerenciador de pacotes não detectado.'));
        return await showPythonGuide(os);
      }
    }

    // Verify installation
    const result = checkPythonAfterInstall();
    if (result) {
      spinner.succeed(chalk.green('Python 3 instalado com sucesso'));
      return { installed: true, cmd: result.cmd, version: result.version };
    } else {
      spinner.warn(chalk.yellow('Instalação concluída mas Python não encontrado no PATH.'));
      console.log(chalk.dim('      Feche e reabra o terminal, depois rode o install novamente.\n'));
      return { installed: false };
    }
  } catch (err) {
    spinner.fail(chalk.yellow('Não foi possível instalar automaticamente.'));
    console.log(chalk.dim(`      Erro: ${err.message?.slice(0, 80)}\n`));
    return await showPythonGuide(os);
  }
}

async function showPythonGuide(os) {
  console.log();
  console.log(chalk.cyan('    ┌─────────────────────────────────────────────┐'));
  console.log(chalk.cyan('    │  Guia de Instalação — Python 3              │'));
  console.log(chalk.cyan('    └─────────────────────────────────────────────┘'));
  console.log();

  if (os === 'windows') {
    console.log(chalk.white('    Opção 1 (Recomendada):'));
    console.log(chalk.dim('    Abra o PowerShell e rode:'));
    console.log(chalk.green('    winget install Python.Python.3.13'));
    console.log();
    console.log(chalk.white('    Opção 2 (Manual):'));
    console.log(chalk.dim('    1. Acesse python.org/downloads'));
    console.log(chalk.dim('    2. Baixe o instalador para Windows'));
    console.log(chalk.dim('    3. Execute e marque "Add Python to PATH" ✓'));
    console.log(chalk.dim('    4. Clique "Install Now"'));
  } else if (os === 'mac') {
    console.log(chalk.white('    Opção 1 (Com Homebrew):'));
    console.log(chalk.green('    brew install python3'));
    console.log();
    console.log(chalk.white('    Opção 2 (Sem Homebrew):'));
    console.log(chalk.dim('    1. Acesse python.org/downloads'));
    console.log(chalk.dim('    2. Baixe o instalador para macOS'));
    console.log(chalk.dim('    3. Execute o .pkg'));
  } else {
    console.log(chalk.white('    Ubuntu/Debian:'));
    console.log(chalk.green('    sudo apt install python3 python3-pip'));
    console.log();
    console.log(chalk.white('    Fedora/RHEL:'));
    console.log(chalk.green('    sudo dnf install python3 python3-pip'));
    console.log();
    console.log(chalk.white('    Arch:'));
    console.log(chalk.green('    sudo pacman -S python python-pip'));
  }

  console.log();
  console.log(chalk.dim('    Após instalar, feche e reabra o terminal.'));
  console.log();

  const { retry } = await inquirer.prompt([{
    type: 'list',
    name: 'retry',
    message: chalk.cyan('O que fazer agora?'),
    choices: [
      { name: `${chalk.white('Já instalei')} ${chalk.dim('— verificar novamente')}`, value: 'retry' },
      { name: `${chalk.dim('Continuar sem Python')} ${chalk.dim('— hooks desativados')}`, value: 'skip' },
    ],
  }]);

  if (retry === 'retry') {
    const result = checkPythonAfterInstall();
    if (result) {
      console.log(`\n    ${chalk.green('✓')} Python 3 detectado ${chalk.dim(`(${result.version.raw})`)}\n`);
      return { installed: true, cmd: result.cmd, version: result.version };
    } else {
      console.log(chalk.yellow('\n    Python ainda não detectado. Continuando sem hooks.\n'));
      return { installed: false };
    }
  }

  console.log(chalk.dim('    Continuando sem Python. Hooks desativados.\n'));
  return { installed: false };
}

// ── Step 1: Dependency Check ──────────────────────────────────

async function checkDependencies() {
  stepHeader(1, 3, 'Verificando dependências');

  const spinner = ora({ text: 'Detectando ferramentas...', indent: 4 }).start();

  // Python (try python3, python, py -3 for cross-platform)
  let pythonCmd = null;
  let pythonVer = null;
  for (const cmd of ['python3 --version', 'python --version', 'py -3 --version']) {
    const out = runCmd(cmd);
    if (out && out.toLowerCase().includes('python 3')) {
      pythonCmd = cmd.replace(' --version', '').trim();
      pythonVer = parseVersion(out);
      break;
    }
  }

  // Node
  const nodeOut = runCmd('node --version');
  const nodeVer = parseVersion(nodeOut?.replace('v', ''));

  // Git
  const gitOut = runCmd('git --version');
  const gitVer = parseVersion(gitOut);

  spinner.stop();

  const deps = [
    {
      name: 'Python 3',
      ok: !!pythonVer && pythonVer.major >= 3,
      warn: !pythonVer,
      version: pythonVer?.raw,
      hint: pythonVer ? null : 'Não encontrado — necessário para hooks',
    },
    {
      name: 'Node.js',
      ok: !!nodeVer && nodeVer.major >= 18,
      version: nodeVer?.raw,
      hint: 'Atualize em nodejs.org (mínimo v18)',
    },
    {
      name: 'Git',
      ok: !!gitVer,
      warn: !gitVer,
      version: gitVer?.raw,
      hint: 'Instale em git-scm.com (recomendado)',
    },
  ];

  showDependencyTable(deps);

  const critical = deps.filter(d => !d.ok && d.name === 'Node.js');
  if (critical.length > 0) {
    console.log(chalk.red('  Node.js 18+ é obrigatório. Instale e tente novamente.\n'));
    process.exit(1);
  }

  // Auto-install Python if missing
  if (!pythonVer) {
    const result = await installPythonFlow();
    if (result.installed) {
      pythonCmd = result.cmd;
      pythonVer = result.version;
      console.log(`    ${chalk.green('✓')} Python 3 instalado ${chalk.dim(`(${pythonVer.raw})`)}\n`);
    }
  }

  return { pythonCmd, pythonVer, nodeVer, gitVer, gitOk: !!gitVer };
}

// ── Step 2: Directory + Files ─────────────────────────────────

async function chooseDirectory(projectName) {
  const cwd = process.cwd();
  const folderName = 'mega-brain';

  if (projectName) {
    return resolve(cwd, projectName);
  }

  const choices = [
    { name: `Diretório atual  ${chalk.dim(cwd)}`, value: 'current' },
    { name: `Nova pasta       ${chalk.dim('./' + folderName)}`, value: 'new' },
    { name: 'Caminho personalizado', value: 'custom' },
  ];

  const { choice } = await inquirer.prompt([{
    type: 'list',
    name: 'choice',
    message: chalk.cyan('Onde instalar?'),
    choices,
  }]);

  if (choice === 'current') return cwd;
  if (choice === 'new') return resolve(cwd, folderName);

  const { path } = await inquirer.prompt([{
    type: 'input',
    name: 'path',
    message: chalk.cyan('Caminho:'),
    validate: (v) => v.trim() ? true : chalk.red('Obrigatório.'),
  }]);
  return resolve(path.trim());
}

function installShell(targetDir) {
  if (!existsSync(targetDir)) {
    mkdirSync(targetDir, { recursive: true });
  }

  const excludeDirs = ['.git', 'node_modules', 'bin'];
  const entries = readdirSync(TEMPLATE_ROOT, { withFileTypes: true });
  let copied = 0;

  for (const entry of entries) {
    if (excludeDirs.includes(entry.name)) continue;
    const src = join(TEMPLATE_ROOT, entry.name);
    const dest = join(targetDir, entry.name);
    try {
      if (entry.isDirectory()) {
        cpSync(src, dest, { recursive: true, force: true });
      } else {
        mkdirSync(dirname(dest), { recursive: true });
        cpSync(src, dest, { force: true });
      }
      copied++;
    } catch (err) {
      console.error(chalk.dim(`    Aviso: ${entry.name}: ${err.message}`));
    }
  }

  if (copied === 0) throw new Error('Nenhum arquivo copiado.');

  // .env.example
  const envTemplate = resolve(__dirname, '..', 'templates', 'env.example');
  if (existsSync(envTemplate)) {
    writeFileSync(join(targetDir, '.env.example'), readFileSync(envTemplate, 'utf-8'));
  }

  // Ensure required directories (matching current architecture)
  const dirs = [
    'knowledge/external/inbox',
    'knowledge/external/dna/persons',
    'knowledge/external/dossiers/persons',
    'knowledge/external/dossiers/themes',
    'knowledge/external/sources',
    'knowledge/external/playbooks',
    'knowledge/business/inbox',
    'knowledge/business/people',
    'knowledge/business/dossiers',
    'knowledge/business/insights',
    'knowledge/business/sops',
    'knowledge/personal/inbox',
    'knowledge/personal/calls',
    'knowledge/personal/cognitive',
    'workspace/inbox',
    'workspace/businesses',
    'workspace/_templates',
    'processing',
    'agents/external',
    'agents/business',
    'agents/personal',
    'agents/cargo',
    'agents/system',
    'agents/sua-empresa/sow',
    'agents/_templates',
    'artifacts/audit',
    'logs/batches',
    'logs/sessions',
    '.data',
  ];

  for (const dir of dirs) {
    const full = join(targetDir, dir);
    if (!existsSync(full)) {
      mkdirSync(full, { recursive: true });
      writeFileSync(join(full, '.gitkeep'), '');
    }
  }

  return copied;
}

// ── Step 3: Post-Install Config ───────────────────────────────

async function postInstallConfig(targetDir, pythonCmd) {
  stepHeader(3, 3, 'Configuração inicial');

  const { configure } = await inquirer.prompt([{
    type: 'confirm',
    name: 'configure',
    message: chalk.cyan('Deseja configurar API keys agora?'),
    default: true,
  }]);

  if (!configure) {
    console.log(chalk.dim('    Pulando. Rode a qualquer momento:'));
    console.log(chalk.cyan('    npx @thiagofinch/mega-brain@latest setup\n'));
    return;
  }

  console.log();
  console.log(chalk.dim('    Chaves são salvas em .env (nunca commitadas no git).'));
  console.log();

  const keys = {};

  // OpenAI (RECOMMENDED — Whisper only)
  console.log(
    `    ${chalk.yellow.bold('RECOMMENDED')} ${chalk.bold('OPENAI_API_KEY')}`
  );
  console.log(chalk.dim('    Transcrição de vídeo/áudio via Whisper.'));
  console.log(chalk.dim('    Se já tem transcrições .txt/.docx, pode pular.'));
  console.log(chalk.dim('    https://platform.openai.com/api-keys'));
  const { openai } = await inquirer.prompt([{
    type: 'input',
    name: 'openai',
    message: chalk.cyan('    OpenAI API Key (Enter para pular):'),
    validate: (v) => {
      if (v && !v.startsWith('sk-')) return chalk.yellow('Chaves OpenAI começam com sk-');
      return true;
    },
  }]);
  keys.OPENAI_API_KEY = openai || '';
  console.log();

  // Voyage (OPTIONAL — RAG embeddings)
  console.log(
    `    ${chalk.dim.bold('OPTIONAL')} ${chalk.bold('VOYAGE_API_KEY')}`
  );
  console.log(chalk.dim('    Embeddings semânticos para busca RAG.'));
  console.log(chalk.dim('    https://dash.voyageai.com/api-keys'));
  const { voyage } = await inquirer.prompt([{
    type: 'input',
    name: 'voyage',
    message: chalk.cyan('    Voyage API Key (Enter para pular):'),
  }]);
  keys.VOYAGE_API_KEY = voyage || '';
  console.log();

  // Write .env
  const envExamplePath = resolve(__dirname, '..', 'templates', 'env.example');
  const envTargetPath = join(targetDir, '.env');

  let envContent;
  if (existsSync(envExamplePath)) {
    envContent = readFileSync(envExamplePath, 'utf-8');
  } else {
    envContent = [
      '# Mega Brain - Environment Configuration',
      '# Generated by installer',
      '',
      'OPENAI_API_KEY=',
      'VOYAGE_API_KEY=',
      'GOOGLE_CLIENT_ID=',
      'GOOGLE_CLIENT_SECRET=',
      '',
    ].join('\n');
  }

  if (keys.OPENAI_API_KEY) {
    envContent = envContent.replace(/^OPENAI_API_KEY=.*$/m, `OPENAI_API_KEY=${keys.OPENAI_API_KEY}`);
  }
  if (keys.VOYAGE_API_KEY) {
    envContent = envContent.replace(/^VOYAGE_API_KEY=.*$/m, `VOYAGE_API_KEY=${keys.VOYAGE_API_KEY}`);
  }

  let wrote = false;
  if (existsSync(envTargetPath)) {
    const { overwrite } = await inquirer.prompt([{
      type: 'confirm',
      name: 'overwrite',
      message: chalk.yellow('    .env já existe. Sobrescrever?'),
      default: false,
    }]);
    if (overwrite) {
      writeFileSync(envTargetPath, envContent, 'utf-8');
      wrote = true;
    }
  } else {
    writeFileSync(envTargetPath, envContent, 'utf-8');
    wrote = true;
  }

  if (wrote) {
    console.log(chalk.green('    .env criado com sucesso'));
  } else {
    console.log(chalk.dim('    .env mantido sem alteração'));
  }

  // Quick summary
  const icon = (v) => v ? chalk.green('✓') : chalk.dim('—');
  console.log();
  console.log(`    ${icon(keys.OPENAI_API_KEY)} OpenAI   ${icon(keys.VOYAGE_API_KEY)} Voyage   ${wrote ? chalk.green('✓ .env') : chalk.dim('— .env')}`);
  console.log();

  if (!keys.OPENAI_API_KEY) {
    console.log(chalk.dim('    Sem OpenAI: importe transcrições .txt/.docx diretamente no inbox.'));
    console.log();
  }
}

// ── Main: Install ─────────────────────────────────────────────

export async function runInstaller(version, projectName) {
  console.log();

  // Step 1: Dependencies
  const { pythonCmd } = await checkDependencies();

  // Step 2: Install
  stepHeader(2, 3, 'Instalando');

  const targetDir = await chooseDirectory(projectName);

  if (existsSync(join(targetDir, '.claude', 'CLAUDE.md'))) {
    const { overwrite } = await inquirer.prompt([{
      type: 'confirm',
      name: 'overwrite',
      message: chalk.yellow('Mega Brain já existe nesse diretório. Sobrescrever?'),
      default: false,
    }]);
    if (!overwrite) {
      console.log(chalk.yellow('\n  Instalação cancelada.\n'));
      process.exit(0);
    }
  }

  const spinner = ora({ text: 'Copiando arquivos...', indent: 4, color: 'cyan' }).start();
  try {
    const count = installShell(targetDir);
    spinner.succeed(chalk.green(`Estrutura base instalada (${count} itens)`));
  } catch (err) {
    spinner.fail(chalk.red(err.message));
    process.exit(1);
  }

  // Install Python deps if available
  if (pythonCmd) {
    const reqPath = resolve(TEMPLATE_ROOT, 'requirements.txt');
    if (existsSync(reqPath)) {
      const pipSpinner = ora({ text: 'Instalando dependências Python...', indent: 4 }).start();
      try {
        execSync(`${pythonCmd} -m pip install -r "${reqPath}" --quiet`, { stdio: 'pipe', timeout: 60000 });
        pipSpinner.succeed(chalk.green('Dependências Python instaladas'));
      } catch {
        pipSpinner.warn(chalk.yellow('Falha ao instalar deps Python (rode pip install -r requirements.txt)'));
      }
    }
  }

  // Step 3: Post-install config
  await postInstallConfig(targetDir, pythonCmd);

  // License (local, single tier)
  writeLicense({
    tier: 'community',
    activated_at: new Date().toISOString(),
  });

  // Summary
  console.log();
  showPostInstallCommunity(version);

  // Next steps: cd + claude hint (when installed in a different dir)
  if (targetDir !== process.cwd()) {
    console.log(chalk.dim('  Próximo passo:'));
    console.log(chalk.cyan(`  cd ${targetDir}`));
    console.log(chalk.cyan('  claude'));
    console.log();
  }
}

// ── Main: Update (safe — never touches user data) ─────────

/**
 * Protected paths: NEVER overwritten during update.
 * These contain user data, personal config, and runtime state.
 */
const PROTECTED_PATHS = [
  'knowledge',
  'workspace',
  '.env',
  '.data',
  'logs',
  'processing',
  'artifacts',
  'research',
  '.claude/sessions',
  '.claude/mission-control',
  '.claude/jarvis/JARVIS-STATE.json',
  '.claude/jarvis/JARVIS-MEMORY.md',
  'agents/external',
  'agents/business',
  'agents/personal',
  'agents/discovery',
];

function isProtected(relPath) {
  return PROTECTED_PATHS.some(p =>
    relPath === p || relPath.startsWith(p + '/') || relPath.startsWith(p + '\\')
  );
}

function copyWithProtection(source, target, excludeDirs, relBase = '') {
  const entries = readdirSync(source, { withFileTypes: true });
  let updated = 0;
  let skipped = 0;

  for (const entry of entries) {
    if (excludeDirs.includes(entry.name)) continue;

    const relPath = relBase ? `${relBase}/${entry.name}` : entry.name;
    const srcPath = join(source, entry.name);
    const destPath = join(target, entry.name);

    if (isProtected(relPath)) {
      skipped++;
      continue;
    }

    try {
      if (entry.isDirectory()) {
        mkdirSync(destPath, { recursive: true });
        const sub = copyWithProtection(srcPath, destPath, excludeDirs, relPath);
        updated += sub.updated;
        skipped += sub.skipped;
      } else {
        mkdirSync(dirname(destPath), { recursive: true });
        cpSync(srcPath, destPath, { force: true });
        updated++;
      }
    } catch {
      // skip individual file errors
    }
  }

  return { updated, skipped };
}

export async function runUpdate(version) {
  console.log();
  stepHeader(1, 3, 'Verificando projeto');

  const targetDir = process.cwd();

  // Check if this is a mega-brain project
  if (!existsSync(join(targetDir, '.claude', 'CLAUDE.md'))) {
    console.log(chalk.red('    Nenhum projeto Mega Brain encontrado neste diretório.'));
    console.log(chalk.dim('    Rode este comando de dentro da pasta do seu projeto.\n'));
    process.exit(1);
  }

  // Show current version
  let currentVersion = 'desconhecida';
  const localPkg = join(targetDir, 'package.json');
  if (existsSync(localPkg)) {
    try {
      const pkg = JSON.parse(readFileSync(localPkg, 'utf-8'));
      currentVersion = pkg.version || 'desconhecida';
    } catch {}
  }

  console.log(`    Projeto:  ${chalk.white(targetDir)}`);
  console.log(`    Atual:    ${chalk.dim('v' + currentVersion)}`);
  console.log(`    Nova:     ${chalk.green('v' + version)}`);
  console.log();

  // Show what will be protected
  stepHeader(2, 3, 'Dados protegidos');

  console.log(chalk.dim('    Os seguintes dados NUNCA serão alterados:'));
  console.log();
  const protectedLabels = {
    'knowledge': 'Knowledge base (expert, business, personal)',
    'workspace': 'Workspace (operações, estratégia)',
    '.env': 'Credenciais e API keys',
    '.data': 'Índices RAG e embeddings',
    'logs': 'Logs de sessão e batches',
    'agents/external': 'Mind clones de especialistas',
    'agents/business': 'Clones de colaboradores',
    'agents/personal': 'Clone do founder',
  };

  for (const [path, label] of Object.entries(protectedLabels)) {
    const exists = existsSync(join(targetDir, path));
    const icon = exists ? chalk.green('✓') : chalk.dim('—');
    console.log(`    ${icon} ${chalk.dim(path.padEnd(20))} ${chalk.dim(label)}`);
  }
  console.log();

  // Confirm
  const { proceed } = await inquirer.prompt([{
    type: 'confirm',
    name: 'proceed',
    message: chalk.cyan('Atualizar arquivos de sistema? (seus dados ficam intactos)'),
    default: true,
  }]);

  if (!proceed) {
    console.log(chalk.yellow('\n  Update cancelado.\n'));
    process.exit(0);
  }

  // Step 3: Copy with protection
  stepHeader(3, 3, 'Atualizando');

  const spinner = ora({ text: 'Copiando arquivos de sistema...', indent: 4, color: 'cyan' }).start();

  try {
    const excludeDirs = ['.git', 'node_modules', 'bin'];
    const { updated, skipped } = copyWithProtection(TEMPLATE_ROOT, targetDir, excludeDirs);

    // Also update bin templates (env.example)
    const envTemplate = resolve(__dirname, '..', 'templates', 'env.example');
    if (existsSync(envTemplate)) {
      writeFileSync(join(targetDir, '.env.example'), readFileSync(envTemplate, 'utf-8'));
    }

    spinner.succeed(chalk.green(`Atualizado! (${updated} arquivos atualizados, ${skipped} protegidos)`));
  } catch (err) {
    spinner.fail(chalk.red(err.message));
    process.exit(1);
  }

  // Summary
  console.log();
  const content = [
    theme.success('  Mega Brain atualizado para v' + version),
    '',
    chalk.dim('  Sistema atualizado. Seus dados estão intactos.'),
    '',
    chalk.bold('  O que foi atualizado:'),
    `  ${chalk.dim('engine/')}          Engine, templates, workflows`,
    `  ${chalk.dim('.claude/')}       Skills, hooks, rules, commands`,
    `  ${chalk.dim('agents/cargo/')} Agentes de cargo (C-Levels, Squad)`,
    `  ${chalk.dim('agents/system/')} Conclave, JARVIS`,
    '',
    chalk.bold('  O que NÃO foi tocado:'),
    `  ${chalk.dim('knowledge/')}    Seu knowledge base`,
    `  ${chalk.dim('workspace/')}    Suas operações`,
    `  ${chalk.dim('.env')}           Suas credenciais`,
    `  ${chalk.dim('agents/external/')} Seus mind clones`,
  ].join('\n');

  console.log(boxen(content, {
    padding: 1,
    margin: { left: 2 },
    borderStyle: 'round',
    borderColor: '#22c55e',
  }));
  console.log();
}
