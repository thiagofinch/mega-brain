#!/usr/bin/env node

/**
 * Mega Brain CLI (v2) — CLI Entry Point
 *
 * Unified CLI with consistent UX across all commands.
 * Run: node bin/mega-brain.js [command]
 */

import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import { readFileSync, existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load .env (Node 21+ native)
const envPath = resolve(__dirname, '..', '.env');
if (existsSync(envPath)) {
  try { process.loadEnvFile(envPath); } catch {}
}

const pkg = JSON.parse(readFileSync(resolve(__dirname, '..', 'package.json'), 'utf-8'));
const args = process.argv.slice(2);
const command = args[0];

// Comandos de conhecimento/pipeline (search, ingest, conclave, ...) rodam como
// slash commands no Claude Code ou pelos scripts em engine/ e scripts/.
// Esta CLI cobre apenas o ciclo de vida da instalação.
const SLASH_ONLY_COMMANDS = [
  'search', 'buckets', 'preflight', 'health', 'ingest', 'index', 'conclave',
  'dossier', 'governance', 'workspace-health', 'scheduler', 'operations', 'dispatch',
];

async function main() {
  const { showBanner, showHelp } = await import('./lib/ascii-art.js');

  showBanner(pkg.version);

  // ── Help / No command ─────────────────────────────────────
  if (!command || command === '--help' || command === '-h') {
    showHelp(pkg.version);
    process.exit(0);
  }

  // ── Auto-setup if .env missing (skip for install/setup/push)
  if (!['install', 'setup', 'push', 'update'].includes(command)) {
    const projectEnv = resolve(process.cwd(), '.env');
    if (!existsSync(projectEnv)) {
      const boxen = (await import('boxen')).default;
      const chalk = (await import('chalk')).default;
      console.log(boxen(
        chalk.cyan('  Primeira vez? Vamos configurar.\n') +
        chalk.dim('  Executando setup wizard...\n\n') +
        chalk.dim('  (Rode a qualquer momento: npx @thiagofinch/mega-brain@latest setup)'),
        { padding: 1, borderColor: 'cyan', borderStyle: 'round' }
      ));
      const { runSetup } = await import('./lib/setup-wizard.js');
      await runSetup();
      process.exit(0);
    }
  }

  // ── Command Router ────────────────────────────────────────
  // Comandos disponíveis: install, update, status, features, setup, push
  switch (command) {
    case 'install': {
      const { runInstaller } = await import('./lib/installer.js');
      await runInstaller(pkg.version, args[1]);
      break;
    }

    case 'update': {
      const { runUpdate } = await import('./lib/installer.js');
      await runUpdate(pkg.version);
      break;
    }

    case 'status': {
      const { getProStatus } = await import('./utils/pro-detector.js');
      const { getLicenseState } = await import('./lib/license.js');
      const { showStatusBox } = await import('./lib/ascii-art.js');
      const status = getProStatus();
      showStatusBox({
        state: getLicenseState(status.license),
        email: status.email,
        activatedAt: status.activatedAt,
      }, status.installed);
      break;
    }

    case 'features': {
      const { listFeatures } = await import('./lib/feature-gate.js');
      const { showFeatureTable } = await import('./lib/ascii-art.js');
      showFeatureTable(listFeatures());
      break;
    }

    case 'setup': {
      const { runSetup } = await import('./lib/setup-wizard.js');
      await runSetup();
      break;
    }

    case 'push': {
      await import('./push.js');
      break;
    }

    default: {
      const chalk = (await import('chalk')).default;
      if (SLASH_ONLY_COMMANDS.includes(command)) {
        console.error(chalk.yellow(`\n  O comando '${command}' não está disponível nesta CLI.`));
        console.error(chalk.dim('  Use os slash commands no Claude Code (/ingest, /jarvis-briefing, /conclave) ou os scripts em engine/ e scripts/.'));
        console.error(chalk.dim('  Comandos disponíveis aqui: install, update, status, features, setup, push.\n'));
        process.exit(1);
      }
      console.error(chalk.red(`\n  Comando desconhecido: ${command}`));
      showHelp(pkg.version);
      process.exit(1);
    }
  }
}

main().catch((err) => {
  console.error(`\n  Erro: ${err.message}`);
  setTimeout(() => process.exit(1), 100);
});
