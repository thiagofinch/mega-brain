#!/usr/bin/env node

/**
 * Mega Brain - AI Knowledge Management System
 * CLI Entry Point
 *
 * Usage:
 *   npx mega-brain-ai install [name] - Install Mega Brain (optional project name)
 *   npx mega-brain-ai validate   - Validate MoneyClub email
 *   npx mega-brain-ai push       - Push to Layer 1/2/3 remote
 *   npx mega-brain-ai upgrade    - Upgrade Community to Premium
 *   npx mega-brain-ai status     - Show Pro license status
 *   npx mega-brain-ai features   - List available vs locked features
 *   npx mega-brain-ai --help     - Show help
 */

import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import { readFileSync, existsSync } from 'fs';

// Load .env from project root (Node.js 21+ native, no dependencies)
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const envPath = resolve(__dirname, '..', '.env');
if (existsSync(envPath)) {
  try { process.loadEnvFile(envPath); } catch {}
}

const require = createRequire(import.meta.url);

const pkg = JSON.parse(readFileSync(resolve(__dirname, '..', 'package.json'), 'utf-8'));

const args = process.argv.slice(2);
const command = args[0];

async function main() {
  const { showBanner } = await import('./lib/ascii-art.js');

  showBanner(pkg.version);

  if (!command || command === '--help' || command === '-h') {
    showHelp();
    process.exit(0);
  }

  if (command === 'install') {
    const { runInstaller } = await import('./lib/installer.js');
    await runInstaller(pkg.version, args[1]);
  } else if (command === 'validate') {
    const { validateEmail } = await import('./lib/validate-email.js');
    const email = args[1];
    if (!email) {
      console.error('\n  Uso: mega-brain validate <email>\n');
      process.exit(1);
    }
    const result = await validateEmail(email);
    console.log(result.valid ? `\n  Email válido: ${result.name}` : `\n  Email inválido: ${result.reason}`);
    setTimeout(() => process.exit(result.valid ? 0 : 1), 100);
  } else if (command === 'push') {
    // Dynamic import of push module
    await import('./push.js');
  } else if (command === 'upgrade') {
    const { runUpgrade } = await import('./lib/installer.js');
    if (typeof runUpgrade === 'function') {
      await runUpgrade(pkg.version);
    } else {
      console.log('\n  Funcionalidade de upgrade será disponibilizada em breve.');
      console.log('  Por enquanto, reinstale com: mega-brain install\n');
    }
  } else if (command === 'status') {
    const { showStatus } = await import('./lib/pro-commands.js');
    showStatus();
  } else if (command === 'features') {
    const { showFeatures } = await import('./lib/pro-commands.js');
    showFeatures();
  } else {
    console.error(`\n  Comando desconhecido: ${command}`);
    showHelp();
    process.exit(1);
  }
}

function showHelp() {
  console.log(`
  Mega Brain v${pkg.version}
  AI Knowledge Management System

  Comandos:
    install [nome]  Instalar Mega Brain (PREMIUM ou Community)
    validate    Validar email MoneyClub (mega-brain validate <email>)
    push        Push para Layer 1/2/3 (mega-brain push [--layer N])
    upgrade     Atualizar Community para Premium
    status      Mostrar status da licenca Pro
    features    Listar features disponiveis vs bloqueadas
    --help      Mostrar esta mensagem

  Layers:
    Layer 1     Community (público) — shell sem conteúdo
    Layer 2     Premium (MoneyClub) — shell + cérebro
    Layer 3     Full Backup (pessoal) — tudo incluindo dados sensíveis

  Exemplos:
    npx mega-brain-ai install
    npx mega-brain-ai install meu-projeto
    npx mega-brain-ai push --layer 1
    npx mega-brain-ai push
`);
}

main().catch((err) => {
  console.error('\n  Erro inesperado:', err.message);
  setTimeout(() => process.exit(1), 100);
});
