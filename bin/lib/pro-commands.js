// bin/lib/pro-commands.js
// CLI commands for Pro license management: status, features

import chalk from 'chalk';
import boxen from 'boxen';
import { readLicense, getLicenseState, maskEmail } from './license.js';
import { isProInstalled } from '../utils/pro-detector.js';
import { listFeatures } from './feature-gate.js';

export function showStatus() {
  const license = readLicense();
  const state = getLicenseState(license);
  const installed = isProInstalled();

  const stateColors = {
    NOT_FOUND: chalk.dim('Nao encontrado'),
    COMMUNITY: chalk.blue('Community'),
    INACTIVE: chalk.yellow('Inativo'),
    ACTIVE: chalk.green('Ativo'),
    GRACE: chalk.yellow('Periodo de graca'),
    EXPIRED: chalk.red('Expirado'),
  };

  const lines = [
    `  ${chalk.bold('Mega Brain Pro Status')}`,
    '',
    `  Tier:       ${stateColors[state]}`,
    `  Conteudo:   ${installed ? chalk.green('Instalado') : chalk.dim('Nao instalado')}`,
  ];

  if (license && license.email) {
    lines.push(`  Email:      ${maskEmail(license.email)}`);
  }
  if (license && license.activated_at) {
    lines.push(`  Ativado em: ${new Date(license.activated_at).toLocaleDateString('pt-BR')}`);
  }
  if (license && license.validated_at) {
    lines.push(`  Validado:   ${new Date(license.validated_at).toLocaleDateString('pt-BR')}`);
  }

  if (state === 'GRACE') {
    lines.push('');
    lines.push(chalk.yellow('  Revalidacao necessaria. Execute: mega-brain validate <email>'));
  }
  if (state === 'EXPIRED') {
    lines.push('');
    lines.push(chalk.red('  Licenca expirada. Execute: mega-brain validate <email>'));
  }
  if (state === 'COMMUNITY' || state === 'NOT_FOUND') {
    lines.push('');
    lines.push(chalk.dim('  Upgrade: mega-brain upgrade'));
  }

  console.log(boxen(lines.join('\n'), {
    padding: 1,
    margin: { left: 2 },
    borderStyle: 'round',
    borderColor: state === 'ACTIVE' ? '#22c55e' : state === 'GRACE' ? '#f59e0b' : '#6366f1',
  }));
}

export function showFeatures() {
  const features = listFeatures();
  console.log(`\n  ${chalk.bold('Features disponiveis:')}\n`);

  for (const feat of features) {
    const icon = feat.available ? chalk.green('[+]') : chalk.red('[-]');
    const name = feat.available ? chalk.white(feat.name) : chalk.dim(feat.name);
    const desc = chalk.dim(feat.description);
    console.log(`  ${icon} ${name}  ${desc}`);
  }

  const available = features.filter(f => f.available).length;
  console.log(`\n  ${available}/${features.length} features ativas\n`);
}
