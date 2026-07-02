#!/usr/bin/env node
/**
 * audit-capability-fidelity.js — compare squad config declarations against filesystem reality.
 *
 * Purpose:
 *   Prevent orchestration from trusting shallow or stale config.yaml capability lists.
 *
 * Story: OG-88.8-V2
 */
'use strict';

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const REPO_ROOT = path.resolve(__dirname, '../../..');
const SQUADS_DIR = path.join(REPO_ROOT, 'squads');

function parseArgs(argv) {
  const args = {
    limit: 15,
    format: 'json',
    output: null,
    minAbsGap: 1,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--limit') args.limit = parseInt(argv[++i], 10);
    else if (arg === '--format') args.format = argv[++i];
    else if (arg === '--output') args.output = path.resolve(argv[++i]);
    else if (arg === '--min-abs-gap') args.minAbsGap = parseInt(argv[++i], 10);
  }

  return args;
}

function safeReadYaml(filePath) {
  try {
    return yaml.load(fs.readFileSync(filePath, 'utf8')) || {};
  } catch {
    return {};
  }
}

function listDir(dir) {
  try {
    return fs.readdirSync(dir);
  } catch {
    return [];
  }
}

function stat(filePath) {
  try {
    return fs.statSync(filePath);
  } catch {
    return null;
  }
}

function* walk(dir, depth = 0, maxDepth = 5) {
  if (depth > maxDepth) return;
  for (const name of listDir(dir)) {
    if (name.startsWith('.') || name === 'node_modules') continue;
    const full = path.join(dir, name);
    const st = stat(full);
    if (!st) continue;
    if (st.isDirectory()) yield* walk(full, depth + 1, maxDepth);
    else yield full;
  }
}

function stripExt(filePath) {
  return path.basename(filePath).replace(/\.(md|yaml|yml|json|sh|js|mjs|cjs)$/, '');
}

function actualItems(squadDir, subdir, extensions) {
  const dir = path.join(squadDir, subdir);
  if (!stat(dir)) return [];
  const extPattern = new RegExp(`\\.(${extensions.join('|')})$`);
  return [...walk(dir)]
    .filter((filePath) => extPattern.test(filePath))
    .map((filePath) => ({
      id: stripExt(filePath),
      path: path.relative(REPO_ROOT, filePath),
    }))
    .sort((a, b) => a.path.localeCompare(b.path));
}

function declaredList(config, key) {
  if (config.components && Array.isArray(config.components[key])) return config.components[key].map(String);
  if (Array.isArray(config[key])) return config[key].map((item) => {
    if (typeof item === 'string') return item;
    if (item && typeof item === 'object' && item.id) return String(item.id);
    if (item && typeof item === 'object' && item.name) return String(item.name);
    return JSON.stringify(item);
  });
  return [];
}

function declaredStats(config, key) {
  const candidates = [
    config.stats && config.stats[key],
    config.metadata && config.metadata.base_stats && config.metadata.base_stats[key],
    config.metadata && config.metadata.stats && config.metadata.stats[key],
  ];
  for (const value of candidates) {
    if (typeof value === 'number') return value;
  }
  return null;
}

function classifyGap(declaredCount, actualCount) {
  const gap = declaredCount - actualCount;
  if (gap === 0) return { gap, status: 'aligned' };
  if (gap < 0) return { gap, status: 'underdeclared' };
  return { gap, status: 'overdeclared' };
}

function compareCapability(config, squadDir, key, subdir, extensions) {
  const declared = declaredList(config, key);
  const stats = declaredStats(config, key);
  const actual = actualItems(squadDir, subdir, extensions);
  const declaredCount = declared.length > 0 ? declared.length : (stats || 0);
  const source = declared.length > 0 ? `components.${key}` : (stats !== null ? 'stats' : 'none');
  const actualIds = new Set(actual.map((item) => item.id));
  const declaredIds = new Set(declared);
  const missingFromConfig = actual.filter((item) => !declaredIds.has(item.id)).map((item) => item.path);
  const phantomInConfig = declared.filter((id) => !actualIds.has(id));
  return {
    declared_count: declaredCount,
    declared_source: source,
    actual_count: actual.length,
    ...classifyGap(declaredCount, actual.length),
    missing_from_config: missingFromConfig.slice(0, 25),
    phantom_in_config: phantomInConfig.slice(0, 25),
  };
}

function auditSquad(squadName) {
  const squadDir = path.join(SQUADS_DIR, squadName);
  const configPath = path.join(squadDir, 'config.yaml');
  const config = safeReadYaml(configPath);

  return {
    squad: squadName,
    config_path: path.relative(REPO_ROOT, configPath),
    tasks: compareCapability(config, squadDir, 'tasks', 'tasks', ['md', 'yaml', 'yml']),
    workflows: compareCapability(config, squadDir, 'workflows', 'workflows', ['md', 'yaml', 'yml', 'json', 'sh']),
    agents: compareCapability(config, squadDir, 'agents', 'agents', ['md']),
    templates: compareCapability(config, squadDir, 'templates', 'templates', ['md', 'yaml', 'yml', 'json']),
  };
}

function sortFindings(findings) {
  return findings.sort((a, b) => {
    const aMax = Math.max(
      Math.abs(a.tasks.gap),
      Math.abs(a.workflows.gap),
      Math.abs(a.agents.gap),
      Math.abs(a.templates.gap),
    );
    const bMax = Math.max(
      Math.abs(b.tasks.gap),
      Math.abs(b.workflows.gap),
      Math.abs(b.agents.gap),
      Math.abs(b.templates.gap),
    );
    return bMax - aMax || a.squad.localeCompare(b.squad);
  });
}

function buildAudit(args) {
  const squads = listDir(SQUADS_DIR)
    .filter((name) => !name.startsWith('.') && stat(path.join(SQUADS_DIR, name, 'config.yaml')));
  const audited = sortFindings(squads.map(auditSquad));
  const findings = audited.filter((item) => {
    return ['tasks', 'workflows', 'agents', 'templates'].some((key) => Math.abs(item[key].gap) >= args.minAbsGap);
  });
  return {
    schema_version: '1.0',
    generated_at: new Date().toISOString(),
    repo_root: '.',
    total_squads_scanned: audited.length,
    total_squads_with_gaps: findings.length,
    thresholds: {
      min_abs_gap: args.minAbsGap,
    },
    top_findings: findings.slice(0, args.limit),
    summary: {
      underdeclared_tasks: findings.filter((item) => item.tasks.status === 'underdeclared').length,
      overdeclared_tasks: findings.filter((item) => item.tasks.status === 'overdeclared').length,
      underdeclared_workflows: findings.filter((item) => item.workflows.status === 'underdeclared').length,
      overdeclared_workflows: findings.filter((item) => item.workflows.status === 'overdeclared').length,
    },
  };
}

function toMarkdown(audit) {
  const lines = [];
  lines.push('# Capability Fidelity Audit');
  lines.push('');
  lines.push(`Generated: ${audit.generated_at}`);
  lines.push(`Squads scanned: ${audit.total_squads_scanned}`);
  lines.push(`Squads with gaps: ${audit.total_squads_with_gaps}`);
  lines.push('');
  lines.push('## Summary');
  lines.push('');
  lines.push('| Metric | Count |');
  lines.push('|---|---:|');
  lines.push(`| Underdeclared tasks | ${audit.summary.underdeclared_tasks} |`);
  lines.push(`| Overdeclared tasks | ${audit.summary.overdeclared_tasks} |`);
  lines.push(`| Underdeclared workflows | ${audit.summary.underdeclared_workflows} |`);
  lines.push(`| Overdeclared workflows | ${audit.summary.overdeclared_workflows} |`);
  lines.push('');
  lines.push('## Top Findings');
  lines.push('');
  lines.push('| Squad | Tasks declared/actual/gap | Workflows declared/actual/gap | Agents declared/actual/gap | Templates declared/actual/gap |');
  lines.push('|---|---:|---:|---:|---:|');
  for (const item of audit.top_findings) {
    lines.push(`| ${item.squad} | ${item.tasks.declared_count}/${item.tasks.actual_count}/${item.tasks.gap} | ${item.workflows.declared_count}/${item.workflows.actual_count}/${item.workflows.gap} | ${item.agents.declared_count}/${item.agents.actual_count}/${item.agents.gap} | ${item.templates.declared_count}/${item.templates.actual_count}/${item.templates.gap} |`);
  }
  lines.push('');
  lines.push('## Interpretation');
  lines.push('');
  lines.push('- Negative gap means config underdeclares what exists on disk.');
  lines.push('- Positive gap means config overdeclares capabilities not found on disk.');
  lines.push('- `orquestrador-global` must prefer filesystem-backed capability discovery and treat stale config as advisory.');
  lines.push('- Before multi-agent swarm execution, every selected squad should pass this audit or emit a blocker.');
  return `${lines.join('\n')}\n`;
}

function main() {
  const args = parseArgs(process.argv);
  const audit = buildAudit(args);
  const rendered = args.format === 'md' ? toMarkdown(audit) : `${JSON.stringify(audit, null, 2)}\n`;

  if (args.output) {
    fs.mkdirSync(path.dirname(args.output), { recursive: true });
    fs.writeFileSync(args.output, rendered, 'utf8');
  }

  process.stdout.write(rendered);
}

if (require.main === module) main();

module.exports = {
  parseArgs,
  buildAudit,
  toMarkdown,
};
