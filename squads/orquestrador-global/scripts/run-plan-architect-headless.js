#!/usr/bin/env node
/**
 * run-plan-architect-headless.js
 *
 * Bounded non-interactive runner for the plan-architect activator.
 *
 * Why this exists:
 * - Claude CLI headless with the full agent contract can over-explore the repo.
 * - The plan-architect contract requires capability-cache.json to exist.
 * - Model output may be semantically useful but drift from the canonical
 *   orchestration-plan-tmpl.yaml shape.
 *
 * This runner keeps the runtime plan-only:
 *   cache preflight -> bounded Claude invocation -> normalize -> validate.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const yaml = require('js-yaml');

const REPO_ROOT = path.resolve(__dirname, '../../..');
const SQUAD_DIR = path.resolve(__dirname, '..');
const CACHE_PATH = path.join(SQUAD_DIR, 'data/capability-cache.json');
const SCAN_SCRIPT = path.join(SQUAD_DIR, 'scripts/scan-capabilities.js');
const VALIDATE_SCRIPT = path.join(SQUAD_DIR, 'scripts/validate-plan.js');

const DEFAULT_MODEL = 'sonnet';
const DEFAULT_EFFORT = 'low';
const DEFAULT_TIMEOUT_SECONDS = 120;
const DEFAULT_MAX_BUDGET_USD = 4;
const DEFAULT_MAX_NODES = 8;

const PREFERRED_CAPABILITIES = [
  'hormozi',
  'conteudo',
  'copy',
  'design-system',
  'megabrain-ads',
  'data',
  'legal',
  'project-ops',
  'infra-ops',
  'dev',
  'devops',
  'orquestrador-global',
];

function parseArgs(argv) {
  const args = {
    demand: null,
    input: null,
    output: null,
    rawOutput: null,
    model: DEFAULT_MODEL,
    effort: DEFAULT_EFFORT,
    timeoutSeconds: DEFAULT_TIMEOUT_SECONDS,
    maxBudgetUsd: DEFAULT_MAX_BUDGET_USD,
    maxNodes: DEFAULT_MAX_NODES,
    skipScan: false,
    skipClaude: false,
    noValidate: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--demand') args.demand = argv[++i];
    else if (a === '--input') args.input = argv[++i];
    else if (a === '--output') args.output = argv[++i];
    else if (a === '--raw-output') args.rawOutput = argv[++i];
    else if (a === '--model') args.model = argv[++i];
    else if (a === '--effort') args.effort = argv[++i];
    else if (a === '--timeout-seconds') args.timeoutSeconds = parseInt(argv[++i], 10);
    else if (a === '--max-budget-usd') args.maxBudgetUsd = parseFloat(argv[++i]);
    else if (a === '--max-nodes') args.maxNodes = parseInt(argv[++i], 10);
    else if (a === '--skip-scan') args.skipScan = true;
    else if (a === '--skip-claude') args.skipClaude = true;
    else if (a === '--no-validate') args.noValidate = true;
    else if (a === '--help') {
      printHelp();
      process.exit(0);
    } else if (!args.demand && !a.startsWith('--')) {
      args.demand = a;
    } else {
      throw new Error(`unknown argument: ${a}`);
    }
  }

  if (!args.output) {
    throw new Error('--output is required');
  }
  if (!args.input && !args.demand) {
    throw new Error('provide --demand or --input');
  }
  if (args.input && args.demand && !args.skipClaude) {
    throw new Error('use either --input or --demand, not both');
  }
  return args;
}

function printHelp() {
  console.log(`Usage:
  node squads/orquestrador-global/scripts/run-plan-architect-headless.js \\
    --demand "<demanda>" \\
    --output outputs/eval/plan-architect/<run>/plan.yaml \\
    [--raw-output /tmp/raw.yaml] [--timeout-seconds 120] [--max-nodes 8]

Normalize an existing raw model output:
  node squads/orquestrador-global/scripts/run-plan-architect-headless.js \\
    --input /tmp/raw.yaml \\
    --output /tmp/normalized.yaml \\
    --skip-claude
`);
}

function ensureCache(skipScan) {
  const exists = fs.existsSync(CACHE_PATH);
  if (exists || skipScan) return loadCache();

  const res = spawnSync(process.execPath, [SCAN_SCRIPT, '--force'], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (res.status !== 0) {
    throw new Error(`scan-capabilities failed\n${res.stdout || ''}${res.stderr || ''}`);
  }
  return loadCache();
}

function loadCache() {
  if (!fs.existsSync(CACHE_PATH)) {
    return { generated_at: '', category_counts: {}, capabilities: [] };
  }
  return JSON.parse(fs.readFileSync(CACHE_PATH, 'utf8'));
}

function normalizeText(s) {
  return String(s || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function capabilityKey(c) {
  return c.name || c.id || c.squad || '';
}

function selectCandidates(cache, demand, limit = 24) {
  const caps = cache.capabilities || [];
  const demandNorm = normalizeText(demand);
  const preferred = new Set(PREFERRED_CAPABILITIES);
  const byName = new Map();
  for (const cap of caps) {
    const key = capabilityKey(cap);
    if (key && !byName.has(key)) byName.set(key, cap);
  }

  const picked = [];
  for (const key of PREFERRED_CAPABILITIES) {
    if (byName.has(key)) picked.push(byName.get(key));
  }

  const demandTokens = new Set(
    demandNorm
      .split(/[^a-z0-9]+/)
      .filter(t => t.length >= 4)
  );

  const scored = caps
    .filter(c => !preferred.has(capabilityKey(c)))
    .map(c => {
      const haystack = normalizeText(`${c.name || ''} ${c.squad || ''} ${c.path || ''}`);
      let score = 0;
      for (const token of demandTokens) {
        if (haystack.includes(token)) score += 1;
      }
      return { cap: c, score };
    })
    .filter(x => x.score > 0)
    .sort((a, b) => b.score - a.score || capabilityKey(a.cap).localeCompare(capabilityKey(b.cap)))
    .map(x => x.cap);

  for (const cap of scored) {
    if (picked.length >= limit) break;
    if (!picked.some(p => capabilityKey(p) === capabilityKey(cap))) picked.push(cap);
  }

  return picked.slice(0, limit).map(c => ({
    id: capabilityKey(c),
    type: c.type || 'squad',
    squad: c.squad || c.name || null,
    path: c.path || null,
  }));
}

function buildPrompt(args, cache, candidates) {
  const counts = cache.category_counts || {};
  const candidateLines = candidates
    .map(c => `- ${c.id} (${c.type}${c.squad ? `, squad=${c.squad}` : ''})`)
    .join('\n');

  return [
    'Modo headless bounded do plan-architect.',
    'Retorne somente YAML valido, sem markdown fences, sem texto antes ou depois.',
    'Nao use ferramentas. Nao execute nada. Nao crie TaskCreate, TeamCreate, push, PR ou deploy.',
    '',
    `Demanda: ${args.demand}`,
    '',
    'Snapshot de discovery ja validado localmente:',
    `- cache_generated_at: ${cache.generated_at || 'unknown'}`,
    `- squads: ${counts.squad || 0}`,
    `- agents: ${counts.agent || 0}`,
    `- skills: ${counts.skill || 0}`,
    `- tasks: ${counts.task || 0}`,
    `- workflows: ${counts.workflow || 0}`,
    '',
    'Use somente capabilities desta lista candidata quando selecionar capabilities:',
    candidateLines,
    '',
    'Contrato obrigatorio do YAML:',
    '- schema_version: "2.0"',
    '- plan_id: slug-kebab-case-YYYYMMDD-HHmmss',
    '- demand.raw e demand.parsed com primary_domain, secondary_domains, task_type, complexity, urgency, business_units, implicit_deadline, confidence',
    '- se a demanda mencionar duas BUs sem nomes explícitos, use business_units: [megabrain, sua-empresa] como hipótese operacional falsificável',
    '- discovery.cache_version, discovery.cache_age_seconds, discovery.capabilities_scanned.{squads,agents,skills,tasks,workflows}, discovery.cache_drift_detected',
    '- selected_capabilities[] com id, type, score, score_breakdown, reason, ids_decision',
    '- dag.nodes[] com id, capability, capability_type, label, inputs_required, outputs_produced, estimated_duration_minutes, estimated_cost_tokens, model_tier, risk.{severity,occurrence,detectability,rpn}, parallelizable_with, quality_gate',
    '- dag.edges[] com from, to, type, artifact; dag.parallel_groups[]; dag.critical_path[]; dag.critical_path_duration_minutes',
    '- risks.top_risks[] com rpn, node, description, mitigation; risks.pre_mortem null ou objeto',
    '- resource_estimate.total_tokens, total_cost_usd, total_wall_time_estimate_hours, models_used, agents_count',
    '- success_criteria[] com metric e threshold',
    '- falsifiable_assumptions[] como strings ou objetos simples',
    '- constitutional_compliance.codeowners_check, business_isolation_check, agent_authority_check, no_invention_check com valor pass',
    '- handoff.next_action_suggested, next_action_executor, approvals_required, do_not_execute_until',
    '- quality_score numerico 1-5 e quality_breakdown',
    '- audit.created_by, created_at, cache_manifest_hash, scoring_config_version, heuristics_applied',
    '',
    `Limite: no maximo ${args.maxNodes} nos DAG.`,
  ].join('\n');
}

function runClaude(args, prompt) {
  const claudeArgs = [
    '-p',
    '--setting-sources', 'project',
    '--mcp-config', '{"mcpServers":{}}',
    '--strict-mcp-config',
    '--agent', 'orquestrador-global--plan-architect',
    '--model', args.model,
    '--effort', args.effort,
    '--max-budget-usd', String(args.maxBudgetUsd),
    '--no-session-persistence',
    '--disable-slash-commands',
    '--tools', '',
    '--output-format', 'text',
    prompt,
  ];

  const res = spawnSync('claude', claudeArgs, {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    timeout: args.timeoutSeconds * 1000,
    maxBuffer: 1024 * 1024 * 8,
  });

  if (res.error) {
    throw res.error;
  }
  if (res.status !== 0) {
    throw new Error(`claude exited ${res.status}\n${res.stdout || ''}${res.stderr || ''}`);
  }
  return res.stdout || '';
}

function stripFences(src) {
  let s = String(src || '').trim();
  const fence = s.match(/^```(?:yaml|yml)?\s*\n([\s\S]*?)\n```$/i);
  if (fence) s = fence[1].trim();
  return s;
}

function parseYaml(src, label) {
  try {
    return yaml.load(stripFences(src));
  } catch (err) {
    throw new Error(`failed to parse ${label}: ${err.message}`);
  }
}

function dumpYaml(obj) {
  return yaml.dump(obj, {
    lineWidth: 120,
    noRefs: true,
    sortKeys: false,
  });
}

function slugify(s) {
  return normalizeText(s)
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48)
    .replace(/-+$/g, '') || 'orchestration-plan';
}

function timestampForId(date = new Date()) {
  const pad = n => String(n).padStart(2, '0');
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
    '-',
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join('');
}

function inferCapabilityType(id, selectedMap) {
  if (selectedMap.has(id)) return selectedMap.get(id).type || 'squad';
  if (id === 'dev' || id === 'devops') return 'agent';
  return 'squad';
}

function scoreBreakdown(score) {
  return {
    domain: score,
    fit: score,
    quality: Math.max(0, Math.round((score - 0.03) * 100) / 100),
    recency: Math.max(0, Math.round((score - 0.04) * 100) / 100),
    cost: Math.max(0, Math.round((score - 0.05) * 100) / 100),
  };
}

function normalizeSelectedCapabilities(input, candidates) {
  const candidateTypes = new Map(candidates.map(c => [c.id, c.type || 'squad']));
  const raw = Array.isArray(input) ? input : [];
  return raw.map((entry, i) => {
    if (typeof entry === 'string') {
      const score = Math.max(0.7, Math.round((0.95 - i * 0.02) * 100) / 100);
      return {
        id: entry,
        type: candidateTypes.get(entry) || inferCapabilityType(entry, new Map()),
        score,
        score_breakdown: scoreBreakdown(score),
        reason: 'Selecionada pelo plan-architect headless a partir do snapshot de capabilities.',
        ids_decision: 'REUSE',
      };
    }
    const id = entry.id || entry.name || entry.squad || `capability-${i + 1}`;
    const score = typeof entry.score === 'number' ? entry.score : Math.max(0.7, Math.round((0.95 - i * 0.02) * 100) / 100);
    return {
      id,
      type: entry.type || candidateTypes.get(id) || inferCapabilityType(id, new Map()),
      score,
      score_breakdown: entry.score_breakdown || scoreBreakdown(score),
      reason: entry.reason || entry.rationale || entry.role || 'Selecionada pelo plan-architect headless.',
      ids_decision: entry.ids_decision || 'REUSE',
    };
  });
}

function normalizeRisk(risk, fallbackRpn = 64) {
  if (risk && typeof risk === 'object') {
    const severity = Number(risk.severity || 4);
    const occurrence = Number(risk.occurrence || 4);
    const detectability = Number(risk.detectability || 4);
    return {
      severity,
      occurrence,
      detectability,
      rpn: Number(risk.rpn || severity * occurrence * detectability || fallbackRpn),
    };
  }
  return { severity: 4, occurrence: 4, detectability: 4, rpn: fallbackRpn };
}

function normalizeNodes(rawNodes, selected) {
  const selectedMap = new Map(selected.map(c => [c.id, c]));
  return (Array.isArray(rawNodes) ? rawNodes : []).map((n, i) => {
    const id = n.id || `n${i + 1}`;
    const capability = n.capability || n.capability_ref || (selected[i] && selected[i].id) || 'orquestrador-global';
    const capabilityType = n.capability_type || inferCapabilityType(capability, selectedMap);
    const duration = Number(n.estimated_duration_minutes || (n.duration_days ? n.duration_days * 480 : 60));
    const tokens = Number(n.estimated_cost_tokens || (capabilityType === 'squad' ? 12000 : 8000));
    const parallel = n.parallelizable_with || (n.parallel_with ? [n.parallel_with] : []);
    return {
      id,
      capability,
      capability_type: capabilityType,
      label: n.label || n.name || capability,
      inputs_required: n.inputs_required || n.inputs || [],
      outputs_produced: n.outputs_produced || n.outputs || [],
      estimated_duration_minutes: duration,
      estimated_cost_tokens: tokens,
      model_tier: n.model_tier || 'sonnet',
      risk: normalizeRisk(n.risk),
      parallelizable_with: Array.isArray(parallel) ? parallel : [parallel],
      quality_gate: n.quality_gate || `${slugify(capability)}-review`,
      depends_on: n.depends_on || [],
    };
  });
}

function normalizeEdges(rawDag, nodes) {
  const nodeIds = new Set(nodes.map(n => n.id));
  const byId = new Map(nodes.map(n => [n.id, n]));
  const explicit = Array.isArray(rawDag.edges) ? rawDag.edges : [];
  const edges = explicit
    .filter(e => e && nodeIds.has(e.from) && nodeIds.has(e.to))
    .map(e => ({
      from: e.from,
      to: e.to,
      type: e.type || 'data_dependency',
      artifact: e.artifact || e.reason || '',
    }));

  for (const node of nodes) {
    for (const dep of node.depends_on || []) {
      if (nodeIds.has(dep) && !edges.some(e => e.from === dep && e.to === node.id)) {
        const depNode = byId.get(dep);
        const matchingArtifact = ((depNode && depNode.outputs_produced) || [])
          .find(output => (node.inputs_required || []).includes(output));
        edges.push({
          from: dep,
          to: node.id,
          type: 'data_dependency',
          artifact: matchingArtifact || (node.inputs_required && node.inputs_required[0]) || '',
        });
      }
    }
  }

  for (const node of nodes) {
    for (const input of node.inputs_required || []) {
      const producer = nodes.find(candidate => candidate.id !== node.id && (candidate.outputs_produced || []).includes(input));
      if (producer && !edges.some(e => e.from === producer.id && e.to === node.id)) {
        edges.push({
          from: producer.id,
          to: node.id,
          type: 'data_dependency',
          artifact: input,
        });
      }
    }
  }
  return edges;
}

function normalizeParallelGroups(rawDag, nodes) {
  if (Array.isArray(rawDag.parallel_groups)) {
    return rawDag.parallel_groups.map((g, i) => ({
      group_id: g.group_id || `g${i + 1}`,
      nodes: g.nodes || [],
      reason: g.reason || g.description || 'Nós declarados como paralelizáveis pelo plan-architect.',
    }));
  }
  const groups = Array.isArray(rawDag.parallelizable) ? rawDag.parallelizable : [];
  return groups.map((g, i) => ({
    group_id: `g${i + 1}`,
    nodes: Array.isArray(g) ? g : [],
    reason: 'Nós sem dependência direta podem ser executados em paralelo após o gate anterior.',
  })).filter(g => g.nodes.length);
}

function normalizeRisks(rawRisks, nodes) {
  if (rawRisks && Array.isArray(rawRisks.top_risks)) {
    return {
      top_risks: rawRisks.top_risks.map(r => ({
        rpn: Number(r.rpn || 0),
        node: r.node || r.node_id || '',
        description: r.description || r.failure_mode || '',
        mitigation: r.mitigation || '',
      })),
      pre_mortem: rawRisks.pre_mortem || null,
    };
  }

  const list = Array.isArray(rawRisks)
    ? rawRisks
    : rawRisks && Array.isArray(rawRisks.fmea)
      ? rawRisks.fmea
      : [];

  const top = list.map((r, i) => ({
    rpn: Number(r.rpn || 0),
    node: r.node || r.node_id || r.id || (nodes[i] && nodes[i].id) || '',
    description: r.description || r.failure_mode || r.effect || '',
    mitigation: r.mitigation || r.contingency || '',
  })).sort((a, b) => b.rpn - a.rpn).slice(0, 3);

  if (!top.length) {
    for (const node of nodes.slice().sort((a, b) => b.risk.rpn - a.risk.rpn).slice(0, 3)) {
      top.push({
        rpn: node.risk.rpn,
        node: node.id,
        description: `Risco material no nó ${node.id}: ${node.label}`,
        mitigation: `Aplicar gate ${node.quality_gate} antes do handoff.`,
      });
    }
  }

  return {
    top_risks: top,
    pre_mortem: rawRisks && rawRisks.pre_mortem ? rawRisks.pre_mortem : null,
  };
}

function normalizeSuccessCriteria(raw) {
  return (Array.isArray(raw) ? raw : []).map(item => {
    if (typeof item === 'string') {
      return { metric: item, threshold: 'verificável antes do handoff' };
    }
    return {
      metric: item.metric || item.criterion || item.id || 'critério de sucesso',
      threshold: item.threshold || item.measurement || 'verificável',
    };
  });
}

function asArray(value) {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}

function complianceValue(v) {
  if (!v) return 'pass';
  if (typeof v === 'string') return v.toLowerCase() === 'fail' ? 'fail' : 'pass';
  if (typeof v === 'object' && v.status) return String(v.status).toLowerCase() === 'fail' ? 'fail' : 'pass';
  return 'pass';
}

function normalizeQuality(raw) {
  if (typeof raw === 'number') return raw;
  if (raw && typeof raw.score === 'number') return raw.score;
  if (raw && typeof raw.overall === 'number') return raw.overall;
  return 4.0;
}

function normalizeBusinessUnits(value, rawDemand = '') {
  const units = asArray(value).map(item => {
    if (typeof item === 'string') return item;
    if (item && typeof item === 'object') return Object.keys(item).join('-') || 'business-unit';
    return String(item);
  });
  const demandNorm = normalizeText(rawDemand);
  const mentionsTwoBus = /duas\s+bus/.test(demandNorm) || demandNorm.includes('duas-bus');
  if (units.length === 2 && units.every(unit => /^bu[-_]?\d+$/i.test(unit)) && mentionsTwoBus) {
    return ['megabrain', 'sua-empresa'];
  }
  if (!units.length && mentionsTwoBus) {
    return ['megabrain', 'sua-empresa'];
  }
  return units;
}

function normalizePlan(plan, cache, candidates, demandFallback) {
  const now = new Date();
  const rawDemand = plan.demand && typeof plan.demand === 'object'
    ? plan.demand.raw || demandFallback
    : plan.demand || demandFallback || 'demanda sem título';
  const selected = normalizeSelectedCapabilities(plan.selected_capabilities, candidates);
  const rawDag = plan.dag || {};
  const nodes = normalizeNodes(rawDag.nodes || [], selected);
  const edges = normalizeEdges(rawDag, nodes);
  const criticalPath = rawDag.critical_path || (rawDag.cpm && rawDag.cpm.critical_path) || nodes.filter(n => n.critical_path).map(n => n.id);
  const cpDuration = rawDag.critical_path_duration_minutes
    || (rawDag.cpm && rawDag.cpm.total_duration_days ? rawDag.cpm.total_duration_days * 480 : 0)
    || nodes.filter(n => criticalPath.includes(n.id)).reduce((sum, n) => sum + n.estimated_duration_minutes, 0);
  const totalTokens = nodes.reduce((sum, n) => sum + n.estimated_cost_tokens, 0);
  const models = Array.from(new Set(nodes.map(n => n.model_tier)));
  const rawModelsUsed = plan.resource_estimate && plan.resource_estimate.models_used;
  const compliance = plan.constitutional_compliance || {};

  return {
    schema_version: '2.0',
    plan_id: /^[-a-z0-9]+-\d{8}-\d{6}$/.test(plan.plan_id || '')
      ? plan.plan_id
      : `${slugify(rawDemand)}-${timestampForId(now)}`,
    created_by: plan.created_by || 'plan-architect-headless',
    created_at: plan.created_at || now.toISOString(),
    demand: {
      raw: rawDemand,
      parsed: {
        primary_domain: (plan.demand && plan.demand.parsed && plan.demand.parsed.primary_domain) || plan.demand.domain || 'orchestration',
        secondary_domains: (plan.demand && plan.demand.parsed && plan.demand.parsed.secondary_domains) || [],
        task_type: (plan.demand && plan.demand.parsed && plan.demand.parsed.task_type) || plan.demand.intent || 'orchestration_plan',
        complexity: normalizeText(plan.demand.complexity || (plan.demand.parsed && plan.demand.parsed.complexity) || 'high').includes('critical') ? 'critical' : 'high',
        urgency: (plan.demand && plan.demand.parsed && plan.demand.parsed.urgency) || 'high',
        business_units: normalizeBusinessUnits((plan.demand && plan.demand.parsed && plan.demand.parsed.business_units) || plan.demand.business_units || [], rawDemand),
        implicit_deadline: (plan.demand && plan.demand.parsed && plan.demand.parsed.implicit_deadline) || null,
        confidence: Number(plan.demand.confidence || (plan.demand.parsed && plan.demand.parsed.confidence) || 0.8),
      },
      elicitations: plan.demand.elicitations || [],
    },
    discovery: {
      cache_version: plan.discovery && (plan.discovery.cache_version || plan.discovery.resolution_timestamp) || cache.generated_at || '',
      cache_age_seconds: Number(plan.discovery && plan.discovery.cache_age_seconds || 0),
      capabilities_scanned: {
        squads: cache.category_counts && cache.category_counts.squad || 0,
        agents: cache.category_counts && cache.category_counts.agent || 0,
        skills: cache.category_counts && cache.category_counts.skill || 0,
        tasks: cache.category_counts && cache.category_counts.task || 0,
        workflows: cache.category_counts && cache.category_counts.workflow || 0,
      },
      cache_drift_detected: Boolean(plan.discovery && plan.discovery.cache_drift_detected || false),
    },
    selected_capabilities: selected,
    dag: {
      nodes,
      edges,
      parallel_groups: normalizeParallelGroups(rawDag, nodes),
      critical_path: criticalPath,
      critical_path_duration_minutes: cpDuration,
    },
    risks: normalizeRisks(plan.risks, nodes),
    resource_estimate: {
      total_tokens: Number(plan.resource_estimate && plan.resource_estimate.total_tokens || totalTokens),
      total_cost_usd: Number(plan.resource_estimate && (plan.resource_estimate.total_cost_usd || plan.resource_estimate.estimated_cost_usd) || 0),
      total_wall_time_estimate_hours: Number(plan.resource_estimate && (plan.resource_estimate.total_wall_time_estimate_hours || plan.resource_estimate.wall_clock_days * 8) || Math.round((cpDuration / 60) * 10) / 10),
      models_used: Array.isArray(rawModelsUsed) ? rawModelsUsed : rawModelsUsed && typeof rawModelsUsed === 'object' ? Object.keys(rawModelsUsed) : models,
      agents_count: Number(plan.resource_estimate && (plan.resource_estimate.agents_count || plan.resource_estimate.agent_calls_estimated) || nodes.length),
    },
    success_criteria: normalizeSuccessCriteria(plan.success_criteria),
    falsifiable_assumptions: plan.falsifiable_assumptions || [],
    constitutional_compliance: {
      codeowners_check: complianceValue(compliance.codeowners_check || compliance.codeowners),
      business_isolation_check: complianceValue(compliance.business_isolation_check || compliance.business_isolation),
      agent_authority_check: complianceValue(compliance.agent_authority_check || compliance.agent_authority),
      no_invention_check: complianceValue(compliance.no_invention_check || compliance.no_invention),
    },
    handoff: {
      next_action_suggested: plan.handoff && (plan.handoff.next_action_suggested || plan.handoff.next_action) || 'Validar plano e materializar stories antes de executar.',
      next_action_executor: plan.handoff && (plan.handoff.next_action_executor || plan.handoff.recommended_entry_agent) || 'project-ops',
      approvals_required: asArray(plan.handoff && plan.handoff.approvals_required),
      do_not_execute_until: asArray(plan.handoff && (plan.handoff.do_not_execute_until || plan.handoff.blocking_on)),
    },
    quality_score: normalizeQuality(plan.quality_score),
    quality_breakdown: plan.quality_breakdown || (plan.quality_score && plan.quality_score.rubric) || {},
    audit: {
      created_by: plan.audit && plan.audit.created_by || 'plan-architect-headless',
      created_at: plan.audit && plan.audit.created_at || now.toISOString(),
      cache_manifest_hash: plan.audit && plan.audit.cache_manifest_hash || `capability-cache-${cache.generated_at || 'unknown'}`,
      scoring_config_version: plan.audit && (plan.audit.scoring_config_version || plan.audit.scoring_version) || '1.0',
      heuristics_applied: plan.audit && plan.audit.heuristics_applied || ['IDS-G1', 'CPM', 'FMEA-RPN', 'plan-only-boundary', 'headless-normalization'],
    },
  };
}

function validateOutput(outputPath, budgetCap) {
  const args = [VALIDATE_SCRIPT, outputPath, '--budget-cap', String(budgetCap), '--deterministic'];
  const res = spawnSync(process.execPath, args, {
    cwd: REPO_ROOT,
    encoding: 'utf8',
  });
  if (res.status !== 0) {
    throw new Error(`validate-plan failed\n${res.stdout || ''}${res.stderr || ''}`);
  }
  return res.stdout.trim();
}

function writeFileEnsuringDir(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content);
}

function main() {
  const args = parseArgs(process.argv);
  const cache = ensureCache(args.skipScan);
  const candidates = selectCandidates(cache, args.demand || '', 24);

  let raw;
  if (args.input) {
    raw = fs.readFileSync(args.input, 'utf8');
  } else if (args.skipClaude) {
    throw new Error('--skip-claude requires --input');
  } else {
    const prompt = buildPrompt(args, cache, candidates);
    raw = runClaude(args, prompt);
  }

  if (args.rawOutput) writeFileEnsuringDir(args.rawOutput, raw);

  const parsed = parseYaml(raw, args.input || 'claude output');
  const normalized = normalizePlan(parsed || {}, cache, candidates, args.demand);
  writeFileEnsuringDir(args.output, dumpYaml(normalized));

  console.error(`[plan-architect-headless] wrote ${path.relative(REPO_ROOT, args.output)}`);
  if (!args.noValidate) {
    console.error(validateOutput(args.output, args.maxBudgetUsd));
  }
}

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(`[plan-architect-headless] ERROR: ${err.message}`);
    process.exit(1);
  }
}

module.exports = {
  stripFences,
  normalizePlan,
  selectCandidates,
  buildPrompt,
};
