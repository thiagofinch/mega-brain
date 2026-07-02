/**
 * Mega Brain - ASCII Art & Visual Elements (v2)
 * Unified visual system — single source of truth for all CLI visuals.
 */

import chalk from 'chalk';
import gradient from 'gradient-string';
import boxen from 'boxen';

// ── Shared Gradients ──────────────────────────────────────────
export const theme = {
  brand:   gradient(['#6366f1', '#8b5cf6', '#a855f7']),
  gold:    gradient(['#f59e0b', '#eab308', '#fbbf24']),
  success: gradient(['#22c55e', '#10b981']),
  info:    gradient(['#06b6d4', '#3b82f6']),
};

// ── Main Banner ───────────────────────────────────────────────
export function showBanner(version) {
  const art = `
  ███╗   ███╗███████╗ ██████╗  █████╗
  ████╗ ████║██╔════╝██╔════╝ ██╔══██╗
  ██╔████╔██║█████╗  ██║  ███╗███████║
  ██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║
  ██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║
  ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝

  ██████╗ ██████╗  █████╗ ██╗███╗   ██╗
  ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║
  ██████╔╝██████╔╝███████║██║██╔██╗ ██║
  ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║
  ██████╔╝██║  ██║██║  ██║██║██║ ╚████║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝`;

  console.log(theme.brand(art));
  console.log();
  console.log(chalk.dim(`  Powered by JARVIS AI Orchestration  ·  v${version}`));
  console.log();
}

// ── Step Header ───────────────────────────────────────────────
export function stepHeader(step, total, title) {
  const progress = '●'.repeat(step) + '○'.repeat(total - step);
  console.log();
  console.log(`  ${chalk.dim(progress)}  ${chalk.bold(title)}`);
  console.log(chalk.dim('  ' + '─'.repeat(50)));
}

// ── Divider ───────────────────────────────────────────────────
export function divider(label) {
  if (label) {
    const line = '─'.repeat(Math.max(0, 48 - label.length));
    console.log(chalk.dim(`\n  ── ${label} ${line}`));
  } else {
    console.log(chalk.dim('\n  ' + '─'.repeat(52)));
  }
}

// ── Post-Install ──────────────────────────────────────────────
export function showPostInstallCommunity(version) {
  const content = [
    theme.brand('  MEGA BRAIN'),
    '',
    chalk.white('  Estrutura instalada. Hora de alimentar o cérebro.'),
    chalk.dim(`  v${version}`),
    '',
    chalk.bold('  Primeiros comandos:'),
    `  ${chalk.cyan('/ingest [URL]')}      ${chalk.dim('─── Importar conteúdo')}`,
    `  ${chalk.cyan('/process-jarvis')}    ${chalk.dim('─── Pipeline de 5 fases')}`,
    `  ${chalk.cyan('/conclave')}          ${chalk.dim('─── Deliberação estratégica')}`,
  ].join('\n');

  console.log(boxen(content, {
    padding: 1,
    margin: { left: 2 },
    borderStyle: 'round',
    borderColor: '#6366f1',
  }));
  console.log();
}

// ── Help Screen ───────────────────────────────────────────────
export function showHelp(version) {
  const content = [
    chalk.bold(`  Mega Brain v${version}`),
    chalk.dim('  AI Knowledge Management System'),
    '',
    chalk.bold('  Sistema:'),
    `    ${chalk.cyan('install')} ${chalk.dim('[nome]')}       Instalar o sistema`,
    `    ${chalk.cyan('setup')}                Configurar API keys (wizard)`,
    `    ${chalk.cyan('update')}               Atualizar sistema sem perder seus dados`,
    `    ${chalk.cyan('status')}               Status da instalacao`,
    `    ${chalk.cyan('features')}             Features disponiveis`,
    `    ${chalk.cyan('push')}                 Push para repositorio por layer`,
    '',
    chalk.bold('  Knowledge:'),
    `    ${chalk.cyan('search')} ${chalk.dim('<query>')}      Buscar no knowledge base (RAG)`,
    `    ${chalk.cyan('buckets')}              Status dos buckets de conhecimento`,
    `    ${chalk.cyan('ingest')} ${chalk.dim('<path>')}       Ingerir novo material`,
    `    ${chalk.cyan('index')} ${chalk.dim('[bucket]')}      Rebuild do indice RAG`,
    `    ${chalk.cyan('dossier')} ${chalk.dim('<persona>')}   Compilar dossier de persona`,
    `    ${chalk.cyan('conclave')} ${chalk.dim('<topic>')}    Sessao multi-agente`,
    '',
    chalk.bold('  Engine:'),
    `    ${chalk.cyan('preflight')}            Checagem pre-pipeline`,
    `    ${chalk.cyan('health')} ${chalk.dim('[agent-id]')}   Health check de agente(s)`,
    `    ${chalk.cyan('governance')}           Validar governance engine`,
    `    ${chalk.cyan('workspace-health')}     Validar workspace e TTLs`,
    `    ${chalk.cyan('scheduler')}            Rodar pipeline autonomo`,
    '',
    chalk.bold('  Dispatch (acesso generico a todas as 34 operacoes):'),
    `    ${chalk.cyan('operations')}           Listar todas as operacoes registradas`,
    `    ${chalk.cyan('dispatch')} ${chalk.dim('<op> [args]')}  Executar qualquer operacao por nome`,
    '',
    chalk.bold('  Exemplos:'),
    chalk.dim('    mega-brain search "offer creation" --bucket external'),
    chalk.dim('    mega-brain operations --category pipeline'),
    chalk.dim('    mega-brain dispatch build_aggregation --json \'{"persona":"hormozi"}\''),
    chalk.dim('    mega-brain dispatch hash_content content="test string"'),
  ].join('\n');

  console.log(boxen(content, {
    padding: 1,
    margin: { left: 2 },
    borderStyle: 'round',
    borderColor: '#6366f1',
  }));
  console.log();
}

// ── Dependency Check Table ────────────────────────────────────
export function showDependencyTable(deps) {
  console.log();
  for (const dep of deps) {
    const icon = dep.ok
      ? chalk.green('✓')
      : dep.warn
        ? chalk.yellow('!')
        : chalk.red('✗');
    const version = dep.version
      ? chalk.dim(`(${dep.version})`)
      : chalk.dim('não encontrado');
    const hint = dep.hint && !dep.ok
      ? `\n      ${chalk.dim(dep.hint)}`
      : '';
    console.log(`    ${icon} ${chalk.white(dep.name)} ${version}${hint}`);
  }
  console.log();
}

// ── Feature Table ─────────────────────────────────────────────
export function showFeatureTable(features) {
  console.log();
  for (const feat of features) {
    const icon = feat.available ? chalk.green('✓') : chalk.red('✗');
    const name = feat.available ? chalk.white(feat.name) : chalk.dim(feat.name);
    console.log(`    ${icon} ${name}  ${chalk.dim(feat.description)}`);
  }
  const active = features.filter(f => f.available).length;
  console.log(chalk.dim(`\n    ${active}/${features.length} features ativas`));
  console.log();
}

// ── Status Box ────────────────────────────────────────────────
export function showStatusBox(license, installed) {
  const stateMap = {
    NOT_FOUND:  chalk.dim('Não encontrado'),
    COMMUNITY:  chalk.blue('Community'),
    INACTIVE:   chalk.yellow('Inativo'),
    ACTIVE:     chalk.green('● Ativo'),
    GRACE:      chalk.yellow('● Período de graça'),
    EXPIRED:    chalk.red('● Expirado'),
  };

  const lines = [
    chalk.bold('  Mega Brain — Status'),
    '',
    `  Tier:      ${stateMap[license.state] || chalk.dim('desconhecido')}`,
    `  Conteúdo:  ${installed ? chalk.green('Instalado') : chalk.dim('Não instalado')}`,
  ];

  if (license.email) lines.push(`  Email:     ${chalk.dim(license.email)}`);
  if (license.activatedAt) lines.push(`  Ativado:   ${chalk.dim(new Date(license.activatedAt).toLocaleDateString('pt-BR'))}`);

  const borderColor = license.state === 'ACTIVE' ? '#22c55e'
    : license.state === 'GRACE' ? '#f59e0b'
    : '#6366f1';

  console.log(boxen(lines.join('\n'), {
    padding: 1,
    margin: { left: 2 },
    borderStyle: 'round',
    borderColor,
  }));
}
