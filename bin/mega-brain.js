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

// ── 3-Mode Dispatch via engine/operations.py (Story W1-001.5, AC2) ──
// Modes: subprocess (default) | mcp | api
// CLI commands that map to Python operations go through this dispatcher.
// JS-native commands (install, setup, upgrade, etc.) stay in Node.
const DISPATCH_MODE = process.env.MEGABRAIN_DISPATCH_MODE || 'subprocess';

/**
 * Dispatch a command to engine/operations.py using the configured mode.
 *
 * @param {string} operation - Operation name (key in OPERATIONS_REGISTRY)
 * @param {object} kwargs - Keyword arguments as JSON
 * @returns {Promise<object>} Parsed JSON result from Python
 */
async function dispatchOperation(operation, kwargs = {}) {
  if (DISPATCH_MODE === 'subprocess') {
    // Mode 1: Direct Python call via subprocess (default)
    const { execFileSync } = await import('child_process');
    const projectRoot = resolve(__dirname, '..');
    const script = `
import json, sys
sys.path.insert(0, ${JSON.stringify(projectRoot)})
from engine.operations import dispatch
result = dispatch(${JSON.stringify(operation)}, **json.loads(sys.argv[1]))
print(json.dumps(result, default=str))
`;
    const result = execFileSync('python3', ['-c', script, JSON.stringify(kwargs)], {
      cwd: projectRoot,
      encoding: 'utf-8',
      env: { ...process.env, PYTHONPATH: projectRoot },
    });
    return JSON.parse(result.trim() || 'null');
  }

  if (DISPATCH_MODE === 'mcp') {
    // Mode 2: JSON-RPC via MCP (future -- requires MCP server running)
    throw new Error('MCP dispatch mode not yet implemented. Use subprocess (default).');
  }

  if (DISPATCH_MODE === 'api') {
    // Mode 3: REST API (future -- requires API server running)
    throw new Error('API dispatch mode not yet implemented. Use subprocess (default).');
  }

  throw new Error(`Unknown dispatch mode: ${DISPATCH_MODE}. Valid: subprocess, mcp, api`);
}

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
  // JS-native commands (cannot go through Python):
  // install, update, status, features, setup, push
  //
  // Python-dispatched commands (via engine/operations.py):
  // search, ingest, preflight, health, buckets, index, conclave, etc.
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

    // ── Python-dispatched commands (via engine/operations.py) ──
    // Named shortcuts for commonly-used operations:
    case 'search': {
      const query = args[1];
      if (!query) {
        const chalk = (await import('chalk')).default;
        console.error(chalk.red('\n  Uso: mega-brain search <query> [--bucket external|business|personal]\n'));
        process.exit(1);
      }
      const bucketFlag = args.indexOf('--bucket');
      const buckets = bucketFlag !== -1 && args[bucketFlag + 1] ? [args[bucketFlag + 1]] : null;
      const result = await dispatchOperation('search_knowledge', { query, buckets });
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'buckets': {
      const result = await dispatchOperation('available_buckets');
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'preflight': {
      const result = await dispatchOperation('run_preflight');
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'health': {
      const agentId = args[1] || null;
      const result = await dispatchOperation('check_agent_health', { agent_id: agentId });
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'ingest': {
      const sourcePath = args[1];
      if (!sourcePath) {
        const chalk = (await import('chalk')).default;
        console.error(chalk.red('\n  Uso: mega-brain ingest <source-path> [--bucket external|business|personal]\n'));
        process.exit(1);
      }
      const ingestBucketFlag = args.indexOf('--bucket');
      const ingestBucket = ingestBucketFlag !== -1 ? args[ingestBucketFlag + 1] : null;
      const result = await dispatchOperation('ingest', { source_path: sourcePath, bucket: ingestBucket });
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'index': {
      const indexBucket = args[1] || null;
      const result = await dispatchOperation('build_index', { bucket_name: indexBucket });
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'conclave': {
      const topic = args[1];
      if (!topic) {
        const chalk = (await import('chalk')).default;
        console.error(chalk.red('\n  Uso: mega-brain conclave <topic> [--agents agent1,agent2,...]\n'));
        process.exit(1);
      }
      const agentsFlag = args.indexOf('--agents');
      const agents = agentsFlag !== -1 && args[agentsFlag + 1] ? args[agentsFlag + 1].split(',') : null;
      const result = await dispatchOperation('run_conclave', { topic, agents });
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'dossier': {
      const persona = args[1];
      if (!persona) {
        const chalk = (await import('chalk')).default;
        console.error(chalk.red('\n  Uso: mega-brain dossier <persona>\n'));
        process.exit(1);
      }
      const result = await dispatchOperation('compile_dossier', { persona });
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'governance': {
      const result = await dispatchOperation('validate_governance');
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'workspace-health': {
      const result = await dispatchOperation('check_workspace_health');
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case 'scheduler': {
      const result = await dispatchOperation('run_autonomous_pipeline');
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    // ── Generic operation listing and dispatch ──
    case 'operations': {
      const catFlag = args.indexOf('--category');
      const category = catFlag !== -1 ? args[catFlag + 1] : null;
      const result = await dispatchOperation('list_operations', category ? { category } : {});
      const chalk = (await import('chalk')).default;
      console.log();
      console.log(chalk.bold('  Registered Operations'));
      console.log(chalk.dim('  ' + '─'.repeat(58)));
      const entries = Object.entries(result);
      const categories = {};
      for (const [name, info] of entries) {
        const cat = info.category || 'other';
        if (!categories[cat]) categories[cat] = [];
        categories[cat].push({ name, description: info.description });
      }
      for (const [cat, ops] of Object.entries(categories).sort()) {
        console.log();
        console.log(`  ${chalk.cyan(cat.toUpperCase())}`);
        for (const op of ops) {
          console.log(`    ${chalk.white(op.name.padEnd(28))} ${chalk.dim(op.description)}`);
        }
      }
      console.log();
      console.log(chalk.dim(`  Total: ${entries.length} operations`));
      console.log(chalk.dim('  Run any operation: mega-brain dispatch <operation> [--json \'{"key":"value"}\']'));
      console.log();
      break;
    }

    case 'dispatch': {
      const opName = args[1];
      if (!opName) {
        const chalk = (await import('chalk')).default;
        console.error(chalk.red('\n  Uso: mega-brain dispatch <operation> [--json \'{"key":"value"}\']\n'));
        console.error(chalk.dim('  Run "mega-brain operations" to see all available operations.\n'));
        process.exit(1);
      }
      const jsonFlag = args.indexOf('--json');
      let kwargs = {};
      if (jsonFlag !== -1 && args[jsonFlag + 1]) {
        try {
          kwargs = JSON.parse(args[jsonFlag + 1]);
        } catch (e) {
          const chalk = (await import('chalk')).default;
          console.error(chalk.red(`\n  JSON parse error: ${e.message}\n`));
          process.exit(1);
        }
      }
      // Also support positional key=value pairs after operation name
      for (let i = 2; i < args.length; i++) {
        if (args[i] === '--json') { i++; continue; }
        const eqIdx = args[i].indexOf('=');
        if (eqIdx > 0) {
          kwargs[args[i].slice(0, eqIdx)] = args[i].slice(eqIdx + 1);
        }
      }
      const result = await dispatchOperation(opName, kwargs);
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    default: {
      const chalk = (await import('chalk')).default;
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
