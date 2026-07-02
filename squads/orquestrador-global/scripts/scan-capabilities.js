#!/usr/bin/env node
/**
 * scan-capabilities.js — Filesystem capability scanner for plan-architect
 *
 * Consumer: capability-cartographer (PA-1.2), plan-architect agent (PA-6.1)
 * Produces: data/capability-cache.json + data/capability-manifest.yaml
 *
 * Deterministic, zero LLM, zero external deps (uses only node stdlib).
 * Story: STORY-PA-1.1
 */
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ── Config ─────────────────────────────────────────────────────────────────────
const REPO_ROOT = process.env.REPO_ROOT || path.resolve(__dirname, '../../..');
const SQUAD_DATA_DIR = path.resolve(__dirname, '../data');
const CACHE_PATH = path.join(SQUAD_DATA_DIR, 'capability-cache.json');
const MANIFEST_PATH = path.join(SQUAD_DATA_DIR, 'capability-manifest.yaml');
const DEFAULT_TTL_SECONDS = 3600;

// ── CLI args ───────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = { ttl: DEFAULT_TTL_SECONDS, force: false, dryRun: false, subset: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--force') args.force = true;
    else if (a === '--dry-run') args.dryRun = true;
    else if (a === '--ttl') args.ttl = parseInt(argv[++i], 10);
    else if (a === '--subset') args.subset = argv[++i];
    else if (a === '--help') {
      console.log(`Usage: scan-capabilities.js [--force] [--dry-run] [--ttl <sec>] [--subset <name>]

  --force         bypass TTL, always re-scan
  --dry-run       print summary without writing cache files
  --ttl <sec>     cache TTL in seconds (default: 3600)
  --subset <name> scan only one category (e.g., 'squads-config' for PoC mode)`);
      process.exit(0);
    }
  }
  return args;
}

// ── Filesystem helpers ─────────────────────────────────────────────────────────
function md5(filePath) {
  const buf = fs.readFileSync(filePath);
  return crypto.createHash('md5').update(buf).digest('hex');
}

function safeStat(p) {
  try { return fs.statSync(p); } catch { return null; }
}

function listDir(dir) {
  try { return fs.readdirSync(dir); } catch { return []; }
}

function* walk(dir, maxDepth = 3, depth = 0) {
  if (depth > maxDepth) return;
  for (const name of listDir(dir)) {
    if (name.startsWith('.') && name !== '.mcp.json') continue;
    if (name === 'node_modules' || name === '.git') continue;
    const full = path.join(dir, name);
    const st = safeStat(full);
    if (!st) continue;
    if (st.isDirectory()) yield* walk(full, maxDepth, depth + 1);
    else yield { full, name, mtime: st.mtimeMs, size: st.size };
  }
}

// ── Scanners (one per capability category) ─────────────────────────────────────
function scanSquads(rootSquads) {
  const out = [];
  for (const squad of listDir(rootSquads)) {
    if (squad.startsWith('_') || squad.startsWith('.')) continue;
    const cfg = path.join(rootSquads, squad, 'config.yaml');
    const st = safeStat(cfg);
    if (!st) continue;
    out.push({
      type: 'squad',
      name: squad,
      squad: squad,
      path: path.relative(REPO_ROOT, cfg),
      mtime: st.mtimeMs,
      hash: md5(cfg),
    });
  }
  return out;
}

function scanSquadAgents(rootSquads) {
  const out = [];
  for (const squad of listDir(rootSquads)) {
    if (squad.startsWith('_') || squad.startsWith('.')) continue;
    const agentsDir = path.join(rootSquads, squad, 'agents');
    if (!safeStat(agentsDir)) continue;
    for (const f of listDir(agentsDir)) {
      if (!f.endsWith('.md')) continue;
      const full = path.join(agentsDir, f);
      const st = safeStat(full); if (!st) continue;
      out.push({
        type: 'agent',
        name: f.replace(/\.md$/, ''),
        squad,
        path: path.relative(REPO_ROOT, full),
        mtime: st.mtimeMs,
        hash: md5(full),
      });
    }
  }
  return out;
}

function scanSquadTasks(rootSquads) {
  const out = [];
  for (const squad of listDir(rootSquads)) {
    if (squad.startsWith('_') || squad.startsWith('.')) continue;
    const dir = path.join(rootSquads, squad, 'tasks');
    if (!safeStat(dir)) continue;
    for (const f of listDir(dir)) {
      if (!f.match(/\.(md|yaml|yml)$/)) continue;
      const full = path.join(dir, f);
      const st = safeStat(full); if (!st) continue;
      out.push({
        type: 'task',
        name: f.replace(/\.(md|yaml|yml)$/, ''),
        squad,
        path: path.relative(REPO_ROOT, full),
        mtime: st.mtimeMs,
        hash: md5(full),
      });
    }
  }
  return out;
}

function scanSquadWorkflows(rootSquads) {
  const out = [];
  for (const squad of listDir(rootSquads)) {
    if (squad.startsWith('_') || squad.startsWith('.')) continue;
    const dir = path.join(rootSquads, squad, 'workflows');
    if (!safeStat(dir)) continue;
    for (const item of walk(dir, 2)) {
      if (!item.name.match(/\.(md|yaml|yml|json|sh)$/)) continue;
      out.push({
        type: 'workflow',
        name: item.name.replace(/\.(md|yaml|yml|json|sh)$/, ''),
        squad,
        path: path.relative(REPO_ROOT, item.full),
        mtime: item.mtime,
        hash: md5(item.full),
      });
    }
  }
  return out;
}

function scanSquadTemplates(rootSquads) {
  const out = [];
  for (const squad of listDir(rootSquads)) {
    if (squad.startsWith('_') || squad.startsWith('.')) continue;
    const dir = path.join(rootSquads, squad, 'templates');
    if (!safeStat(dir)) continue;
    for (const item of walk(dir, 2)) {
      if (!item.name.match(/\.(md|yaml|yml|json)$/)) continue;
      out.push({
        type: 'template',
        name: item.name,
        squad,
        path: path.relative(REPO_ROOT, item.full),
        mtime: item.mtime,
        hash: md5(item.full),
      });
    }
  }
  return out;
}

function scanSkills(claudeDir) {
  const out = [];
  const skillsDir = path.join(claudeDir, 'skills');
  if (!safeStat(skillsDir)) return out;
  for (const skill of listDir(skillsDir)) {
    const skillFile = path.join(skillsDir, skill, 'SKILL.md');
    const st = safeStat(skillFile);
    if (!st) continue;
    out.push({
      type: 'skill',
      name: skill,
      squad: null,
      path: path.relative(REPO_ROOT, skillFile),
      mtime: st.mtimeMs,
      hash: md5(skillFile),
    });
  }
  return out;
}

function scanClaudeAgents(claudeDir) {
  const out = [];
  const agentsDir = path.join(claudeDir, 'agents');
  if (!safeStat(agentsDir)) return out;
  for (const f of listDir(agentsDir)) {
    if (!f.endsWith('.md')) continue;
    const full = path.join(agentsDir, f);
    const st = safeStat(full); if (!st) continue;
    out.push({
      type: 'agent',
      name: f.replace(/\.md$/, ''),
      squad: null,
      path: path.relative(REPO_ROOT, full),
      mtime: st.mtimeMs,
      hash: md5(full),
      surface: 'claude-code',
    });
  }
  return out;
}

function scanHooks(claudeDir) {
  const out = [];
  const hooksDir = path.join(claudeDir, 'hooks');
  if (!safeStat(hooksDir)) return out;
  for (const f of listDir(hooksDir)) {
    if (!f.match(/\.(sh|cjs|js)$/)) continue;
    const full = path.join(hooksDir, f);
    const st = safeStat(full); if (!st) continue;
    out.push({
      type: 'hook',
      name: f,
      squad: null,
      path: path.relative(REPO_ROOT, full),
      mtime: st.mtimeMs,
      hash: md5(full),
    });
  }
  return out;
}

function scanMcps(repoRoot) {
  const out = [];
  const mcpFile = path.join(repoRoot, '.mcp.json');
  const st = safeStat(mcpFile);
  if (!st) return out;
  let parsed = null;
  try { parsed = JSON.parse(fs.readFileSync(mcpFile, 'utf8')); }
  catch { return out; }
  const servers = parsed.mcpServers || parsed.servers || {};
  for (const [name, _conf] of Object.entries(servers)) {
    out.push({
      type: 'mcp',
      name,
      squad: null,
      path: path.relative(REPO_ROOT, mcpFile),
      mtime: st.mtimeMs,
      hash: md5(mcpFile),
    });
  }
  return out;
}

function scanPackages(repoRoot) {
  const out = [];
  const dir = path.join(repoRoot, 'packages');
  if (!safeStat(dir)) return out;
  for (const pkg of listDir(dir)) {
    const pkgJson = path.join(dir, pkg, 'package.json');
    const st = safeStat(pkgJson);
    if (!st) continue;
    out.push({
      type: 'package',
      name: pkg,
      squad: null,
      path: path.relative(REPO_ROOT, pkgJson),
      mtime: st.mtimeMs,
      hash: md5(pkgJson),
    });
  }
  return out;
}

function scanServices(repoRoot) {
  const out = [];
  const dir = path.join(repoRoot, 'services');
  if (!safeStat(dir)) return out;
  for (const svc of listDir(dir)) {
    const svcDir = path.join(dir, svc);
    const st = safeStat(svcDir);
    if (!st || !st.isDirectory()) continue;
    out.push({
      type: 'service',
      name: svc,
      squad: null,
      path: path.relative(REPO_ROOT, svcDir),
      mtime: st.mtimeMs,
      hash: crypto.createHash('md5').update(svc + st.mtimeMs).digest('hex'),
    });
  }
  return out;
}

function scanApps(repoRoot) {
  const out = [];
  const dir = path.join(repoRoot, 'apps');
  if (!safeStat(dir)) return out;
  for (const app of listDir(dir)) {
    const appDir = path.join(dir, app);
    const st = safeStat(appDir);
    if (!st || !st.isDirectory()) continue;
    out.push({
      type: 'app',
      name: app,
      squad: null,
      path: path.relative(REPO_ROOT, appDir),
      mtime: st.mtimeMs,
      hash: crypto.createHash('md5').update(app + st.mtimeMs).digest('hex'),
    });
  }
  return out;
}

// ── Orchestration ──────────────────────────────────────────────────────────────
function fullScan(opts) {
  const t0 = Date.now();
  const rootSquads = path.join(REPO_ROOT, 'squads');
  const claudeDir = path.join(REPO_ROOT, '.claude');

  const all = [];
  if (opts.subset === 'squads-config') {
    all.push(...scanSquads(rootSquads));
  } else {
    all.push(...scanSquads(rootSquads));
    all.push(...scanSquadAgents(rootSquads));
    all.push(...scanSquadTasks(rootSquads));
    all.push(...scanSquadWorkflows(rootSquads));
    all.push(...scanSquadTemplates(rootSquads));
    all.push(...scanSkills(claudeDir));
    all.push(...scanClaudeAgents(claudeDir));
    all.push(...scanHooks(claudeDir));
    all.push(...scanMcps(REPO_ROOT));
    all.push(...scanPackages(REPO_ROOT));
    all.push(...scanServices(REPO_ROOT));
    all.push(...scanApps(REPO_ROOT));
  }

  const counts = {};
  for (const c of all) counts[c.type] = (counts[c.type] || 0) + 1;

  return {
    elapsed_ms: Date.now() - t0,
    capabilities: all,
    category_counts: counts,
  };
}

function buildCache(scan, opts) {
  return {
    version: '1.0',
    schema_version: '1.0',
    generated_at: new Date().toISOString(),
    ttl_seconds: opts.ttl,
    repo_root: REPO_ROOT,
    elapsed_ms: scan.elapsed_ms,
    capabilities: scan.capabilities,
    category_counts: scan.category_counts,
    total: scan.capabilities.length,
  };
}

function buildManifest(scan, opts) {
  const fileHashes = {};
  for (const c of scan.capabilities) {
    fileHashes[c.path] = {
      hash: c.hash,
      mtime: c.mtime,
      type: c.type,
      last_seen_at: new Date().toISOString(),
    };
  }
  // Minimal YAML emitter (no external deps)
  const lines = [
    '# Capability manifest — produced by scan-capabilities.js',
    '# Tracks hash+mtime per file for incremental drift detection',
    `version: "1.0"`,
    `generated_at: "${new Date().toISOString()}"`,
    `ttl_seconds: ${opts.ttl}`,
    `total_files: ${Object.keys(fileHashes).length}`,
    'file_hashes:',
  ];
  for (const [p, info] of Object.entries(fileHashes).sort()) {
    lines.push(`  "${p}":`);
    lines.push(`    hash: "${info.hash}"`);
    lines.push(`    mtime: ${info.mtime}`);
    lines.push(`    type: "${info.type}"`);
    lines.push(`    last_seen_at: "${info.last_seen_at}"`);
  }
  return lines.join('\n') + '\n';
}

// ── Main ───────────────────────────────────────────────────────────────────────
function main() {
  const opts = parseArgs(process.argv);

  // TTL check (skip if --force)
  if (!opts.force && !opts.dryRun) {
    const cacheStat = safeStat(CACHE_PATH);
    if (cacheStat) {
      const ageSec = (Date.now() - cacheStat.mtimeMs) / 1000;
      if (ageSec < opts.ttl) {
        console.log(`Cache is fresh (age ${Math.floor(ageSec)}s < TTL ${opts.ttl}s). Use --force to re-scan.`);
        return;
      }
    }
  }

  const scan = fullScan(opts);

  // Print summary
  console.log(`Scan complete in ${scan.elapsed_ms}ms`);
  console.log(`Total capabilities: ${scan.capabilities.length}`);
  console.log('Category counts:');
  for (const [k, v] of Object.entries(scan.category_counts).sort()) {
    console.log(`  ${k.padEnd(12)} ${v}`);
  }

  if (opts.dryRun) {
    console.log('\n(dry-run: cache files NOT written)');
    return;
  }

  // Ensure data dir exists
  fs.mkdirSync(SQUAD_DATA_DIR, { recursive: true });

  const cache = buildCache(scan, opts);
  fs.writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2));
  console.log(`Cache written: ${path.relative(REPO_ROOT, CACHE_PATH)} (${cache.total} entries)`);

  const manifest = buildManifest(scan, opts);
  fs.writeFileSync(MANIFEST_PATH, manifest);
  console.log(`Manifest written: ${path.relative(REPO_ROOT, MANIFEST_PATH)}`);
}

if (require.main === module) main();

module.exports = { fullScan, buildCache, buildManifest, parseArgs };
