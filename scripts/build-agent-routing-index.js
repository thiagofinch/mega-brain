#!/usr/bin/env node

/**
 * Builds the ARCG agent routing index and human entrypoint catalog.
 *
 * Story: ARCG-2.1 / ARCG-2.2
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// ── Ontology bridge (SCP.W1.3): knowledge_domain DERIVADO no rebuild ─────────
// Retrofit sem edição em massa: task/candidate com taxonomy.domain ganha o
// carimbo derivado via ponte; declarado na fonte (A2 novo) tem precedência.
const BRIDGE_PATH = path.join(process.cwd(), 'squads', 'orquestrador-global', 'data', 'ontology-bridge.yaml');
let _bridgeCache = null;
function loadOntologyBridge() {
  if (_bridgeCache) return _bridgeCache;
  try {
    _bridgeCache = yaml.load(fs.readFileSync(BRIDGE_PATH, 'utf8')) || {};
  } catch { _bridgeCache = {}; }
  return _bridgeCache;
}
let _squadDomainCache = null;
function squadDomainMap() {
  // squad → taxonomy.domain, lido dos config.yaml (mesma fonte dos candidates).
  // Herança ontológica: task part_of squad => herda o domínio da squad quando
  // não declara o próprio (regra de nascimento invertida — o lar define o domínio).
  if (_squadDomainCache) return _squadDomainCache;
  _squadDomainCache = {};
  const squadsDir = path.join(process.cwd(), 'squads');
  for (const name of fs.readdirSync(squadsDir)) {
    if (name.startsWith('_') || name.startsWith('.')) continue;
    const cfg = path.join(squadsDir, name, 'config.yaml');
    if (!fs.existsSync(cfg)) continue;
    try {
      const doc = yaml.load(fs.readFileSync(cfg, 'utf8')) || {};
      const dom = doc.routing && doc.routing.taxonomy && doc.routing.taxonomy.domain;
      if (dom) _squadDomainCache[name] = String(dom);
    } catch { /* config inválido: sem herança */ }
  }
  return _squadDomainCache;
}

function stampKnowledgeDomain(routing, squadName) {
  // routing null + squad com domínio => cria bloco mínimo herdado (a task
  // sem crachá ainda ganha endereço ontológico — part_of squad define o lar)
  if (!routing) {
    const dom = squadName ? squadDomainMap()[squadName] : null;
    if (!dom) return routing;
    const b = (loadOntologyBridge().bridge || {})[dom];
    if (!b) return routing;
    return {
      version: 1,
      knowledge_domain: b.knowledge_domain,
      autonomy_dimension: b.autonomy_dimension === undefined ? null : b.autonomy_dimension,
      ontology_role: b.ontology_role || null,
      kd_source: 'inherited',
    };
  }
  const declared = routing.knowledge_domain;
  if (declared) { routing.kd_source = 'declared'; return routing; }
  // precedência: taxonomy.domain próprio > domínio herdado da squad
  let dom = routing.taxonomy && routing.taxonomy.domain;
  let source = 'derived';
  if (!dom && squadName) {
    dom = squadDomainMap()[squadName];
    source = 'inherited';
  }
  if (!dom) return routing;
  const b = (loadOntologyBridge().bridge || {})[dom];
  if (!b) return routing; // fora do mapa: NUNCA chutar (No Invention)
  routing.knowledge_domain = b.knowledge_domain;
  routing.autonomy_dimension = b.autonomy_dimension === undefined ? null : b.autonomy_dimension;
  routing.kd_source = source;
  return routing;
}
const Ajv2020 = require('ajv/dist/2020');

let addFormats = null;
try {
  addFormats = require('ajv-formats');
} catch (_) {
  addFormats = null;
}

const repoRoot = process.cwd();
const args = new Set(process.argv.slice(2));
const checkMode = args.has('--check');
const selfTestMode = args.has('--self-test');

const paths = {
  squads: path.join(repoRoot, 'squads'),
  claudeSkills: path.join(repoRoot, '.claude', 'skills'),
  schema: path.join(repoRoot, '.data', 'agent-routing-index.schema.json'),
  output: path.join(repoRoot, '.data', 'agent-routing-index.json'),
  catalog: path.join(repoRoot, 'docs', 'reference', 'agent-entrypoints.md'),
  chiefRegistry: path.join(repoRoot, 'squads', 'mega-brain', 'data', 'chief-interface-registry.yaml'),
  agentRegistry: path.join(repoRoot, 'squads', 'mega-brain', 'data', 'agent-registry.yaml'),
};

const MODE_VALUES = new Set(['CRIAR', 'RESOLVER', 'GERENCIAR', 'ENTENDER', 'VALIDAR', 'CONFIGURAR', 'PLANEJAR', 'EXPLORAR']);
const PLACEHOLDER_VALUES = new Set(['', '|', '>', 'TODO', 'TBD']);
const CORE_AGENT_IDS = new Set(['megabrain-master', 'master', 'analyst', 'architect', 'data-engineer', 'dev', 'devops', 'pm', 'po', 'qa', 'sm', 'ux-design-expert']);

const ALIAS_OVERRIDES = {
  'c-level/coo-orchestrator': ['coo'],
};

const EXCLUSIONS = {
  'workspace-governance-legacy/workspace-chief': 'workspace-chief is already the C-Level alias; legacy workspace governance must be reconciled before exposure.',
};

function rel(filePath) {
  return path.relative(repoRoot, filePath).replaceAll(path.sep, '/');
}

function posixJoin(...parts) {
  return parts.join('/').replaceAll(/\/+/g, '/');
}

function readText(filePath) {
  return fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : null;
}

function readJson(filePath) {
  const text = readText(filePath);
  return text ? JSON.parse(text) : null;
}

function readYaml(filePath) {
  const text = readText(filePath);
  if (!text) return null;
  return yaml.load(text) || null;
}

function readLooseFrontmatter(frontmatterText) {
  const out = {};
  for (const line of frontmatterText.split('\n')) {
    const match = line.match(/^\s*([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$/);
    if (!match) continue;
    const key = match[1];
    let value = match[2].replace(/\s+#.*$/, '').trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    } else if (value === 'true') {
      value = true;
    } else if (value === 'false') {
      value = false;
    } else if (/^\d+$/.test(value)) {
      value = Number(value);
    }
    out[key] = value;
  }
  return out;
}

function readFrontmatter(filePath) {
  const text = readText(filePath);
  if (!text) return {};
  const match = text.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  try {
    return yaml.load(match[1]) || {};
  } catch (_) {
    return readLooseFrontmatter(match[1]);
  }
}

function extractFirstYamlBlock(filePath) {
  const text = readText(filePath);
  if (!text) return {};
  const match = text.match(/```yaml\n([\s\S]*?)```/);
  if (!match) return {};
  try {
    return yaml.load(match[1]) || {};
  } catch (_) {
    return {};
  }
}

function walkFiles(rootDir, predicate) {
  const files = [];
  if (!fs.existsSync(rootDir)) return files;

  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile() && predicate(fullPath, entry.name)) {
        files.push(fullPath);
      }
    }
  };

  walk(rootDir);
  return files;
}

function normalizeStringArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value
      .flatMap((item) => normalizeStringArray(item))
      .filter(Boolean);
  }
  if (typeof value === 'string') return [value];
  if (typeof value === 'object') {
    if (typeof value.id === 'string') return [value.id];
    if (typeof value.name === 'string') return [value.name];
  }
  return [];
}

function normalizeModes(value) {
  return normalizeStringArray(value)
    .map((mode) => mode.toUpperCase())
    .filter((mode) => MODE_VALUES.has(mode));
}

function uniqueSorted(values) {
  return [...new Set(values.filter((value) => value !== undefined && value !== null && String(value).trim() !== '').map(String))].sort((a, b) => a.localeCompare(b));
}

function isPlaceholder(value) {
  if (value === null || value === undefined) return true;
  return PLACEHOLDER_VALUES.has(String(value).trim().toUpperCase());
}

function isGenericDescription(value) {
  if (!value || isPlaceholder(value)) return false;
  const text = String(value).trim();
  if (text.length < 32) return true;
  return /^Activate [\w-]+ from squad [\w-]+\.?$/i.test(text);
}

function candidateDescription(values) {
  const descriptions = values
    .filter((value) => !isPlaceholder(value))
    .map((value) => String(value).trim())
    .filter(Boolean);
  return descriptions.find((value) => !isGenericDescription(value)) || descriptions[0] || null;
}

function sourceRef(filePath, kind, role, fieldRefs = []) {
  return {
    path: rel(filePath),
    kind,
    role,
    field_refs: fieldRefs,
  };
}

function collectSkills() {
  const byAgent = new Map();
  const byName = new Map();
  const all = [];

  for (const skillPath of walkFiles(paths.claudeSkills, (_, name) => name === 'SKILL.md')) {
    const frontmatter = readFrontmatter(skillPath);
    const relDir = rel(path.dirname(skillPath)).replace(/^\.claude\/skills\/?/, '');
    const name = String(frontmatter.name || path.basename(path.dirname(skillPath)));
    const agent = frontmatter.agent ? String(frontmatter.agent) : null;
    const record = { path: skillPath, relDir, name, agent, frontmatter };
    all.push(record);

    if (!byName.has(name)) byName.set(name, []);
    byName.get(name).push(record);
    if (agent) {
      if (!byAgent.has(agent)) byAgent.set(agent, []);
      byAgent.get(agent).push(record);
    }
  }

  return { all, byAgent, byName };
}

const TASK_REQUIRED_FIELDS = ['id', 'name', 'verb', 'executor', 'acceptance_criteria', 'status_machine'];
// SCP.W5.2: allowlist EN+PT (red team A2: 63% verb:null com 41 verbos só-inglês)
const TASK_FILENAME_VERB_HINTS = new Set([
  // EN (originais + os que faltavam: update/delete/setup/send/etc.)
  'analyze', 'apply', 'audit', 'build', 'calculate', 'capture', 'check', 'classify', 'compile', 'compose',
  'create', 'define', 'design', 'detect', 'diagnose', 'draft', 'evaluate', 'execute', 'extract', 'generate',
  'map', 'migrate', 'monitor', 'optimize', 'plan', 'publish', 'rank', 'refine', 'render', 'research',
  'review', 'run', 'scan', 'score', 'sync', 'test', 'track', 'transform', 'translate', 'validate', 'write',
  'update', 'delete', 'setup', 'send', 'import', 'export', 'configure', 'install', 'deploy', 'merge',
  'clean', 'archive', 'register', 'resolve', 'assess', 'process', 'convert', 'fetch', 'load', 'index',
  // PT (mesma família dos default_verbs do detector + verbos reais dos filenames)
  'aplicar', 'auditar', 'analisar', 'atualizar', 'avaliar', 'calcular', 'capturar', 'classificar',
  'compilar', 'configurar', 'construir', 'criar', 'decidir', 'definir', 'desenhar', 'detectar',
  'diagnosticar', 'elaborar', 'escrever', 'executar', 'extrair', 'gerar', 'importar', 'exportar',
  'mapear', 'medir', 'migrar', 'monitorar', 'otimizar', 'planejar', 'publicar', 'qualificar',
  'validar', 'verificar', 'traduzir', 'transformar', 'testar', 'sincronizar', 'revisar', 'registrar',
]);

function firstHeading(text) {
  const match = text.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

function purposeExcerpt(text, maxChars = 280) {
  const match = text.match(/^##\s+Purpose\s*\n+([\s\S]*?)(?=\n##\s|\n---|$)/m);
  if (!match) return null;
  const excerpt = match[1].replace(/\s+/g, ' ').trim();
  return excerpt ? excerpt.slice(0, maxChars) : null;
}

function signatureFromItems(items) {
  if (!Array.isArray(items)) return [];
  return items
    .filter((item) => item && typeof item === 'object')
    .map((item) => {
      const signature = {};
      if (item.id !== undefined) signature.id = String(item.id);
      if (item.type !== undefined) signature.type = String(item.type);
      if (item.ref !== undefined) signature.ref = String(item.ref);
      return signature;
    })
    .filter((signature) => Object.keys(signature).length > 0);
}

// Routing Semantics v1 (STORY-FT-W2.1 — docs/reference/routing-semantics-spec.md):
// a fonte declara COMO quer ser encontrada. Whitelist de campos, retrocompatível
// (fonte sem routing => null, entry indexada como antes).
function normalizeRouting(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const asStrings = (v) => (Array.isArray(v) ? v.map(String).filter(Boolean) : []);
  const out = {
    version: Number(raw.version) || 1,
    // Proveniência de geração automática (STORY-W0 fix 3 — red-team 2026-07-07:
    // a whitelist apagava needs_curation, tornando o rótulo cosmético; agora a
    // flag SOBREVIVE ao índice e a query demota não-curadas).
    generated: raw.generated === true ? true : undefined,
    needs_curation: raw.needs_curation === true ? true : undefined,
    knowledge_domain: raw.knowledge_domain ? String(raw.knowledge_domain) : undefined,
    autonomy_dimension: raw.autonomy_dimension ? String(raw.autonomy_dimension) : undefined,
    ontology_role: raw.ontology_role ? String(raw.ontology_role) : undefined,
    generated_by: raw.generated_by ? String(raw.generated_by) : undefined,
    curated_by: raw.curated_by ? String(raw.curated_by) : undefined,
    curated_at: raw.curated_at ? String(raw.curated_at) : undefined,
    power_summary: raw.power_summary ? String(raw.power_summary).slice(0, 1200) : null,
    taxonomy: raw.taxonomy && typeof raw.taxonomy === 'object'
      ? { domain: raw.taxonomy.domain ? String(raw.taxonomy.domain) : null, subdomains: asStrings(raw.taxonomy.subdomains) }
      : null,
    semantic_aliases: asStrings(raw.semantic_aliases),
    verbs: asStrings(raw.verbs),
    use_when: raw.use_when ? String(raw.use_when) : null,
    not_use_when: raw.not_use_when ? String(raw.not_use_when) : null,
    ontology: raw.ontology && typeof raw.ontology === 'object'
      ? {
          entity_type: raw.ontology.entity_type ? String(raw.ontology.entity_type) : null,
          acts_on: asStrings(raw.ontology.acts_on),
          produces: asStrings(raw.ontology.produces),
          relates_to: Array.isArray(raw.ontology.relates_to)
            ? raw.ontology.relates_to
                .filter((r) => r && typeof r === 'object' && r.rel && r.target)
                .map((r) => ({ rel: String(r.rel), target: String(r.target) }))
            : [],
        }
      : null,
  };
  const hasContent = out.power_summary || out.semantic_aliases.length || out.verbs.length || out.use_when || out.taxonomy || out.ontology;
  return hasContent ? out : null;
}

function collectTasks() {
  const tasks = [];
  const seenIds = new Set();

  const taskFiles = walkFiles(paths.squads, (fullPath, name) => {
    if (!name.endsWith('.md') && !name.endsWith('.yaml') && !name.endsWith('.yml')) return false;
    if (/ \d+\.md$/.test(name)) return false; // sync duplicates ("task 2.md")
    const relPath = rel(fullPath);
    if (!/^squads\/[^/]+\/tasks\//.test(relPath)) return false;
    if (relPath.startsWith('squads/_')) return false;
    return true;
  });

  for (const taskPath of taskFiles) {
    const relPath = rel(taskPath);
    const squad = relPath.split('/')[1];
    const isYamlFile = /\.(yaml|yml)$/.test(taskPath);
    const slug = path.basename(taskPath).replace(/\.(md|yaml|yml)$/, '');
    const text = readText(taskPath) || '';
    const anatomy = isYamlFile ? (readYaml(taskPath) || {}) : extractFirstYamlBlock(taskPath);
    const hasAnatomy = anatomy && typeof anatomy === 'object' && !Array.isArray(anatomy);
    const canonical = hasAnatomy && TASK_REQUIRED_FIELDS.every((field) => anatomy[field] !== undefined && anatomy[field] !== null);

    let taskId = canonical ? String(anatomy.id) : `task_${slug.replaceAll(/[^a-z0-9]+/gi, '_').toLowerCase()}`;
    if (seenIds.has(`${squad}:${taskId}`)) continue;
    seenIds.add(`${squad}:${taskId}`);

    const filenameVerb = slug.split(/[-_]/)[0].toLowerCase();
    const executor = canonical && anatomy.executor && typeof anatomy.executor === 'object'
      ? {
          type: anatomy.executor.type ? String(anatomy.executor.type) : null,
          role: anatomy.executor.role ? String(anatomy.executor.role) : null,
          id: anatomy.executor.id ? String(anatomy.executor.id) : null,
        }
      : null;

    tasks.push({
      task_id: taskId,
      name: (canonical && anatomy.name ? String(anatomy.name) : firstHeading(text)) || slug,
      squad,
      source_path: relPath,
      grade: canonical ? 'canonical' : 'legacy',
      verb: canonical && anatomy.verb
        ? String(anatomy.verb)
        : (TASK_FILENAME_VERB_HINTS.has(filenameVerb) ? filenameVerb
          // SCP.W5.2 fallback 2: primeira palavra do H1/name (ex.: "Audit Landing Page")
          : (() => {
              const nameVerb = String((firstHeading(text) || '')).toLowerCase().split(/[\s:—-]+/)[0];
              return TASK_FILENAME_VERB_HINTS.has(nameVerb) ? nameVerb : null;
            })()),
      description: purposeExcerpt(text),
      executor,
      inputs_signature: canonical ? signatureFromItems(anatomy.inputs) : [],
      outputs_signature: canonical ? signatureFromItems(anatomy.outputs) : [],
      acceptance_criteria_count: canonical && Array.isArray(anatomy.acceptance_criteria) ? anatomy.acceptance_criteria.length : 0,
      depends_on: canonical && Array.isArray(anatomy.depends_on) ? anatomy.depends_on.map(String) : [],
      routing: stampKnowledgeDomain(normalizeRouting(anatomy.routing), squad),
      quality_signals: {
        has_anatomy_block: Boolean(hasAnatomy),
        has_pre_checklist: Boolean(canonical && Array.isArray(anatomy.pre_checklist) && anatomy.pre_checklist.length > 0),
        has_post_checklist: Boolean(canonical && Array.isArray(anatomy.post_checklist) && anatomy.post_checklist.length > 0),
        has_failure_handling: Boolean(canonical && anatomy.failure_handling),
        has_artifact_template: Boolean(canonical && anatomy.artifact_template),
        has_purpose_section: Boolean(purposeExcerpt(text)),
      },
    });
  }

  tasks.sort((a, b) => `${a.squad}/${a.task_id}`.localeCompare(`${b.squad}/${b.task_id}`));

  // STORY-MB-011 AC3: twin-flag para pares divergentes copy/megabrain-copy (mesma slug,
  // conteúdo diferente — dedup silencioso seria desonesto; flag para curadoria).
  const TWIN_SQUADS = [['copy', 'megabrain-copy']];
  for (const [a, b] of TWIN_SQUADS) {
    const bySlug = new Map();
    for (const task of tasks) {
      if (task.squad !== a && task.squad !== b) continue;
      const slug = path.basename(task.source_path).replace(/\.(md|yaml|yml)$/, '');
      if (!bySlug.has(slug)) bySlug.set(slug, []);
      bySlug.get(slug).push(task);
    }
    for (const group of bySlug.values()) {
      if (group.length > 1) {
        for (const task of group) {
          task.twin_of = group.filter((g) => g !== task).map((g) => `${g.squad}/${g.task_id}`);
        }
      }
    }
  }
  return tasks;
}


// STORY-MB-011 AC1 (SOT R3): tools no closed-world do índice.
// Fonte 1: services/tool-capability-registry.yaml (26 capabilities semânticas → tool oficial)
// Fonte 2: .mcp.json (servers MCP registrados)
function collectTools() {
  const tools = [];
  const registryPath = path.join(repoRoot, 'services', 'tool-capability-registry.yaml');
  const reg = readYaml(registryPath);
  if (reg && reg.capabilities) {
    for (const [id, cap] of Object.entries(reg.capabilities)) {
      tools.push({
        tool_id: `capability:${id}`,
        kind: 'tool_capability',
        name: id,
        official: cap.official || null,
        description: cap.description || null,
        source_path: 'services/tool-capability-registry.yaml',
        routing: normalizeRouting({
          semantic_aliases: cap.semantic_aliases || [],
          use_when: cap.description || null,
          taxonomy: { domain: 'tools', subdomains: [] },
          ontology: { entity_type: 'tool_capability', acts_on: [], produces: [] },
        }),
        providers: Object.keys(cap.providers || {}),
      });
    }
  }
  const mcpPath = path.join(repoRoot, '.mcp.json');
  if (fs.existsSync(mcpPath)) {
    try {
      const mcp = JSON.parse(fs.readFileSync(mcpPath, 'utf8'));
      for (const server of Object.keys(mcp.mcpServers || {})) {
        tools.push({
          tool_id: `mcp:${server}`,
          kind: 'mcp_server',
          name: server,
          official: server,
          description: null,
          source_path: '.mcp.json',
          routing: null,
          providers: [],
        });
      }
    } catch (_) { /* mcp.json ilegível => sem tools mcp */ }
  }
  tools.sort((a, b) => a.tool_id.localeCompare(b.tool_id));
  return tools;
}

function collectSquads() {
  const configs = [];
  if (!fs.existsSync(paths.squads)) return configs;

  for (const squad of fs.readdirSync(paths.squads).sort()) {
    const configPath = path.join(paths.squads, squad, 'config.yaml');
    const config = readYaml(configPath);
    if (!config) continue;
    configs.push({ squad, configPath, config });
  }

  return configs;
}

function collectAgentIds(config) {
  const ids = new Set();
  const add = (value) => {
    if (!value) return;
    if (typeof value === 'string') {
      ids.add(value);
      return;
    }
    if (Array.isArray(value)) {
      for (const item of value) add(item);
      return;
    }
    if (typeof value === 'object') {
      if (typeof value.id === 'string') ids.add(value.id);
      if (typeof value.agent === 'string') ids.add(value.agent);
      for (const nested of Object.values(value)) {
        if (Array.isArray(nested)) add(nested);
      }
    }
  };
  const addRoleValue = (value) => {
    if (!value) return;
    if (typeof value === 'string') {
      ids.add(value);
      return;
    }
    if (Array.isArray(value)) {
      for (const item of value) addRoleValue(item);
      return;
    }
    if (typeof value === 'object') {
      if (typeof value.id === 'string') ids.add(value.id);
      if (typeof value.agent === 'string') ids.add(value.agent);
      for (const nested of Object.values(value)) {
        if (Array.isArray(nested)) addRoleValue(nested);
      }
    }
  };
  const addRolesMap = (roles) => {
    if (!roles || typeof roles !== 'object') return;
    for (const roleValue of Object.values(roles)) {
      if (typeof roleValue === 'string' || Array.isArray(roleValue)) {
        addRoleValue(roleValue);
      } else if (roleValue && typeof roleValue === 'object') {
        if (typeof roleValue.id === 'string' || typeof roleValue.agent === 'string') {
          addRoleValue(roleValue);
        }
      }
    }
  };

  add(config.agents);
  addRolesMap(config.agents_by_role);
  return uniqueSorted([...ids]);
}

function collectAgentFileIds(squad) {
  const agentsDir = path.join(paths.squads, squad, 'agents');
  return walkFiles(agentsDir, (_, name) => name.endsWith('.md'))
    .map((filePath) => path.basename(filePath, '.md'));
}

function collectChiefs() {
  const registry = readYaml(paths.chiefRegistry) || {};
  const entries = Array.isArray(registry.entries) ? registry.entries : [];
  const byId = new Map();
  for (const entry of entries) {
    if (entry && entry.id) byId.set(String(entry.id), entry);
  }
  return { count: entries.length, byId };
}

function collectAgentRegistry() {
  const registry = readYaml(paths.agentRegistry) || {};
  const agents = Array.isArray(registry.agents) ? registry.agents : [];
  const byId = new Map();
  for (const agent of agents) {
    if (agent && agent.id) byId.set(String(agent.id), agent);
  }
  return { count: agents.length, byId, agents };
}

function findSkillsForAgent(skills, squad, agentId) {
  const key = `${squad}/${agentId}`;
  const names = uniqueSorted([
    agentId,
    `${squad}--${agentId}`,
    `${squad}-${agentId}`,
    agentId.replace(`${squad}-`, ''),
    ...(ALIAS_OVERRIDES[key] || []),
  ]);

  const matches = [];
  for (const name of names) {
    const byName = skills.byName.get(name) || [];
    matches.push(...byName);
  }
  matches.push(...(skills.byAgent.get(agentId) || []));

  const seen = new Set();
  return matches.filter((skill) => {
    if (seen.has(skill.path)) return false;
    seen.add(skill.path);
    return true;
  });
}

function descriptionFromAgent(agentPath) {
  const block = extractFirstYamlBlock(agentPath);
  const agent = block.agent || {};
  return candidateDescription([
    block.whenToUse,
    block.description,
    agent.whenToUse,
    agent.description,
    block.title,
    agent.title,
    block.name,
    agent.name,
  ]);
}

function domainFromConfig(config, squad) {
  return String(config.domain || config.metadata?.domain || config.metadata?.category || config.pack?.name || squad);
}

function buildFieldSources(baseSources) {
  const fieldSources = {};
  const keys = [
    'agent_id',
    'squad',
    'entrypoint',
    'source_paths',
    'domain',
    'description',
    'supported_modes',
    'user_invocable',
    'visibility_status',
    'routing_status',
    'chief_interface_compliant',
    'quality_signals',
    'exclusion_reason',
  ];
  for (const key of keys) fieldSources[key] = baseSources;
  return fieldSources;
}

function score(value) {
  if (value === null || value === undefined) return null;
  return Math.max(0, Math.min(1, Number(value)));
}

function buildCandidate({
  agentId,
  displayName,
  squad,
  config,
  configPath,
  agentPath,
  skills,
  entrypoint,
  excludedReason,
  sourceKind,
  chiefEntry,
  registryEntry,
}) {
  const skillAliases = skills.map((skill) => skill.name);
  const visibleSkill = skills.find((skill) => skill.frontmatter['user-invocable'] === true && skill.frontmatter['disable-model-invocation'] !== true);
  const directSkill = skills.find((skill) => skill.name === agentId || skill.relDir === agentId);
  const sourcePaths = [];

  if (configPath) sourcePaths.push(sourceRef(configPath, 'squad_config', 'sot', ['entry_agent', 'agents']));
  if (agentPath && fs.existsSync(agentPath)) sourcePaths.push(sourceRef(agentPath, 'agent_card', 'sot', ['id', 'description']));
  for (const skill of skills) sourcePaths.push(sourceRef(skill.path, 'skill', 'evidence', ['name', 'agent', 'user-invocable']));
  if (registryEntry && registryEntry.location) sourcePaths.push(sourceRef(path.join(repoRoot, registryEntry.location), 'agent_registry', 'derived', ['agents']));
  if (chiefEntry) sourcePaths.push(sourceRef(paths.chiefRegistry, 'chief_registry', 'derived', ['entries']));

  const missingSource = Boolean(agentPath && !fs.existsSync(agentPath));
  const explicitExcluded = Boolean(excludedReason || missingSource);
  const publicSkillDescriptions = skills
    .filter((skill) => skill.frontmatter['user-invocable'] === true && skill.frontmatter['disable-model-invocation'] !== true)
    .map((skill) => skill.frontmatter.description);
  const description = candidateDescription([
    visibleSkill && visibleSkill.frontmatter.description,
    ...publicSkillDescriptions,
    ...skills.map((skill) => skill.frontmatter.description),
    descriptionFromAgent(agentPath),
    config?.description,
    config?.pack?.description,
    registryEntry?.name,
  ]);
  const descriptionPlaceholder = isPlaceholder(description);
  const issues = [];

  if (descriptionPlaceholder) {
    issues.push({
      code: 'description_placeholder',
      severity: 'warning',
      message: 'Description is missing or placeholder and cannot be used as competence evidence.',
    });
  }
  if (missingSource) {
    issues.push({
      code: 'missing_source',
      severity: 'blocker',
      message: `Agent source is missing at ${rel(agentPath)}.`,
    });
  }
  if (excludedReason) {
    issues.push({
      code: excludedReason.includes('ide_sync.enabled: false') ? 'ide_sync_disabled' : 'explicit_exclusion',
      severity: 'blocker',
      message: excludedReason,
    });
  }
  if (!entrypoint) {
    issues.push({
      code: 'internal_specialist',
      severity: 'info',
      message: 'Route through a public chief or visible skill unless a workflow explicitly requests this specialist.',
    });
  }

  let visibilityStatus = 'unknown';
  let routingStatus = 'unknown';
  if (explicitExcluded) {
    visibilityStatus = 'excluded';
    routingStatus = 'excluded';
  } else if (sourceKind === 'core') {
    visibilityStatus = 'visible';
    routingStatus = 'core_authority';
  } else if (!entrypoint) {
    visibilityStatus = 'internal_only';
    routingStatus = 'internal_specialist';
  } else if (visibleSkill && directSkill) {
    visibilityStatus = 'visible';
    routingStatus = 'public_entrypoint';
  } else if (visibleSkill) {
    visibilityStatus = 'covered_by_alias';
    routingStatus = 'legacy_alias';
  } else {
    visibilityStatus = 'not_visible';
    routingStatus = 'unknown';
    issues.push({
      code: 'not_visible',
      severity: 'warning',
      message: 'Entrypoint has no visible public skill or alias in .claude/skills.',
    });
  }

  const baseSources = sourcePaths.length > 0 ? sourcePaths : [sourceRef(paths.agentRegistry, 'agent_registry', 'derived', ['agents'])];
  const userInvocable = Boolean(visibleSkill && !explicitExcluded);
  const domain = domainFromConfig(config || {}, squad || registryEntry?.squad || 'core');
  const primaryDomain = sourceKind === 'core' ? ['core', agentId.replace(/^@/, '')] : [domain];
  const supportedModes = uniqueSorted([...normalizeModes(config?.modes), ...normalizeModes(config?.supported_modes)]);

  return {
    agent_id: sourceKind === 'core' && !agentId.startsWith('@') ? `@${agentId}` : agentId,
    display_name: displayName || registryEntry?.name || agentId,
    squad: squad || registryEntry?.squad || null,
    entrypoint: Boolean(entrypoint || sourceKind === 'core'),
    aliases: uniqueSorted(skillAliases),
    source_paths: baseSources,
    domain: {
      primary: primaryDomain,
      secondary: uniqueSorted([config?.metadata?.category, config?.pack?.name].filter(Boolean)),
    },
    description: descriptionPlaceholder ? null : String(description),
    routing: stampKnowledgeDomain(normalizeRouting((config && config.routing) || (visibleSkill && visibleSkill.frontmatter && visibleSkill.frontmatter.routing) || null), null),
    supported_modes: supportedModes,
    user_invocable: userInvocable || sourceKind === 'core',
    visibility_status: visibilityStatus,
    routing_status: routingStatus,
    chief_interface_compliant: sourceKind === 'core' ? null : Boolean(chiefEntry),
    quality_signals: {
      description_placeholder: descriptionPlaceholder,
      metadata_advisories: issues.filter((issue) => issue.severity !== 'info').length,
      readiness_status: 'unknown',
      issues,
    },
    confidence_inputs: {
      authority_fit: score(sourceKind === 'core' ? 1 : chiefEntry ? 0.8 : 0.5),
      entrypoint_fit: score(entrypoint ? 1 : sourceKind === 'core' ? 0.8 : 0),
      domain_fit: score(domain ? 0.8 : 0.4),
      metadata_quality: score(descriptionPlaceholder ? 0.2 : missingSource ? 0.1 : 0.75),
      visibility_fit: score(userInvocable || sourceKind === 'core' ? 1 : explicitExcluded ? 0 : 0.2),
    },
    exclusion_reason: missingSource ? `Agent source is missing at ${rel(agentPath)}.` : excludedReason || null,
    field_sources: buildFieldSources(baseSources),
  };
}

function buildIndex(generatedAt) {
  const skills = collectSkills();
  const squads = collectSquads();
  const chiefs = collectChiefs();
  const agentRegistry = collectAgentRegistry();
  const tasks = collectTasks();
  const tools = collectTools();
  const candidates = [];
  const seen = new Set();

  function pushCandidate(candidate) {
    const key = `${candidate.squad || 'core'}:${candidate.agent_id}`;
    if (seen.has(key)) return;
    seen.add(key);
    candidates.push(candidate);
  }

  for (const registryEntry of agentRegistry.agents) {
    if (!registryEntry || !CORE_AGENT_IDS.has(String(registryEntry.id))) continue;
    const agentId = String(registryEntry.id);
    const location = registryEntry.location ? path.join(repoRoot, registryEntry.location) : null;
    pushCandidate(buildCandidate({
      agentId,
      displayName: registryEntry.name,
      squad: null,
      config: null,
      configPath: null,
      agentPath: location,
      skills: [],
      entrypoint: true,
      excludedReason: null,
      sourceKind: 'core',
      chiefEntry: null,
      registryEntry,
    }));
  }

  for (const squadConfig of squads) {
    const { squad, configPath, config } = squadConfig;
    const entryAgent = config.entry_agent || config.pack?.entry_agent || config.squad?.entry_agent || config.primary_agent;
    const declaredAgentIds = collectAgentIds(config);
    const fileAgentIds = collectAgentFileIds(squad);
    const agentIds = uniqueSorted([
      ...fileAgentIds,
      ...declaredAgentIds.filter((agentId) => fs.existsSync(path.join(paths.squads, squad, 'agents', `${agentId}.md`))),
      ...(entryAgent ? [entryAgent] : []),
    ]);

    for (const agentId of uniqueSorted(agentIds)) {
      const key = `${squad}/${agentId}`;
      const entrypoint = agentId === entryAgent;
      const agentPath = path.join(paths.squads, squad, 'agents', `${agentId}.md`);
      const matchingSkills = findSkillsForAgent(skills, squad, agentId);
      const ideSyncDisabled = config.ide_sync && config.ide_sync.enabled === false;
      const excludedReason =
        EXCLUSIONS[key] ||
        (ideSyncDisabled && entrypoint ? `${rel(configPath)} declares ide_sync.enabled: false.` : null);

      pushCandidate(buildCandidate({
        agentId,
        displayName: agentId,
        squad,
        config,
        configPath,
        agentPath,
        skills: matchingSkills,
        entrypoint,
        excludedReason,
        sourceKind: 'squad',
        chiefEntry: chiefs.byId.get(agentId) || null,
        registryEntry: agentRegistry.byId.get(agentId) || null,
      }));
    }
  }

  candidates.sort((a, b) => {
    const statusA = a.routing_status.localeCompare(b.routing_status);
    if (statusA !== 0) return statusA;
    return `${a.squad || ''}/${a.agent_id}`.localeCompare(`${b.squad || ''}/${b.agent_id}`);
  });

  return {
    schema_version: '1.0.0',
    generated_at: generatedAt,
    generator: {
      name: 'build-agent-routing-index',
      story_id: 'ARCG-2.1',
      command: 'npm run build:agent-routing-index',
    },
    source_summary: {
      squad_configs: squads.length,
      skill_sources: skills.all.length,
      chief_registry: chiefs.count,
      agent_registry: agentRegistry.count,
      codex_agents: walkFiles(path.join(repoRoot, '.codex', 'agents'), (_, name) => name.endsWith('.toml')).length,
      task_definitions: tasks.length,
      tool_entries: tools.length,
    },
    candidates,
    tasks,
    tools,
  };
}

function escapeCell(value) {
  const text = value === null || value === undefined || value === '' ? '-' : String(value);
  return text.replaceAll('|', '\\|').replaceAll('\n', ' ');
}

function primarySource(candidate) {
  const source = candidate.source_paths[0];
  return source ? source.path : '-';
}

function notes(candidate) {
  const issueSummary = candidate.quality_signals.issues
    .map((issue) => `${issue.code}:${issue.severity}`)
    .join(', ');
  return candidate.exclusion_reason || issueSummary || '-';
}

function candidateRow(candidate) {
  return [
    candidate.squad || 'core',
    candidate.agent_id,
    candidate.aliases.join(', ') || '-',
    candidate.visibility_status,
    candidate.domain.primary.join(', '),
    candidate.supported_modes.join(', ') || '-',
    candidate.description || '(sem descricao valida)',
    primarySource(candidate),
    notes(candidate),
  ].map(escapeCell).join(' | ');
}

function renderSection(title, candidates) {
  const header = [
    `## ${title}`,
    '',
    `Total: ${candidates.length}`,
    '',
    '| squad | entry agent | skill/alias | status | dominio | modos | descricao | fonte | observacoes |',
    '|---|---|---|---|---|---|---|---|---|',
  ];
  const rows = candidates.map((candidate) => `| ${candidateRow(candidate)} |`);
  return [...header, ...rows, ''].join('\n');
}

function renderCatalog(index) {
  const publicCandidates = index.candidates.filter((candidate) => ['public_entrypoint', 'core_authority', 'legacy_alias'].includes(candidate.routing_status));
  const internalCandidates = index.candidates.filter((candidate) => candidate.routing_status === 'internal_specialist');
  const excludedCandidates = index.candidates.filter((candidate) => candidate.routing_status === 'excluded' || candidate.visibility_status === 'not_visible');

  return [
    '# Agent Entrypoints Catalog',
    '',
    '> GENERATED FILE. Do not edit manually.',
    '>',
    '> Update with: `npm run build:agent-routing-index`.',
    '',
    `Generated at: ${index.generated_at}`,
    `Source: \`.data/agent-routing-index.json\``,
    '',
    '## Summary',
    '',
    `- Public/core/alias candidates: ${publicCandidates.length}`,
    `- Internal specialists: ${internalCandidates.length}`,
    `- Excluded or not visible: ${excludedCandidates.length}`,
    `- Source squad configs: ${index.source_summary.squad_configs}`,
    `- Source skills: ${index.source_summary.skill_sources}`,
    `- Chief registry entries: ${index.source_summary.chief_registry}`,
    `- Agent registry entries: ${index.source_summary.agent_registry}`,
    '',
    renderSection('Public Entrypoints And Core Authorities', publicCandidates),
    renderSection('Excluded Or Not Visible', excludedCandidates),
    renderSection('Internal Specialists', internalCandidates),
  ].join('\n');
}

function stableJson(value) {
  return `${JSON.stringify(value)}\n`;
}

function validateIndex(index) {
  const schema = readJson(paths.schema);
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  if (addFormats) addFormats(ajv);
  const validate = ajv.compile(schema);
  if (!validate(index)) {
    const errors = JSON.stringify(validate.errors, null, 2);
    throw new Error(`agent-routing-index schema validation failed:\n${errors}`);
  }
}

function runSelfTest() {
  const idsFromArray = collectAgentIds({ agents: ['chief', { id: 'worker' }] });
  const idsFromMap = collectAgentIds({ agents_by_role: { orchestrator: 'chief', specialists: [{ id: 'specialist' }] } });
  if (!idsFromArray.includes('chief') || !idsFromArray.includes('worker')) {
    throw new Error('self-test failed: config agents array parsing');
  }
  if (!idsFromMap.includes('chief') || !idsFromMap.includes('specialist')) {
    throw new Error('self-test failed: config agents_by_role map parsing');
  }
  console.log('build-agent-routing-index self-test PASS');
}

function compareFile(filePath, expected) {
  const current = readText(filePath);
  return current === expected;
}

function main() {
  if (selfTestMode) {
    runSelfTest();
    return;
  }

  const existing = readJson(paths.output);
  const generatedAt = checkMode && existing && existing.generated_at ? existing.generated_at : new Date().toISOString();
  const index = buildIndex(generatedAt);
  validateIndex(index);

  const indexText = stableJson(index);
  const catalogText = renderCatalog(index);

  if (checkMode) {
    const indexOk = compareFile(paths.output, indexText);
    const catalogOk = compareFile(paths.catalog, catalogText);
    if (!indexOk || !catalogOk) {
      if (!indexOk) console.error(`[STALE] ${rel(paths.output)} is out of date.`);
      if (!catalogOk) console.error(`[STALE] ${rel(paths.catalog)} is out of date.`);
      console.error('Run: npm run build:agent-routing-index');
      process.exit(1);
    }
    console.log('agent-routing-index check PASS');
    return;
  }

  fs.mkdirSync(path.dirname(paths.output), { recursive: true });
  fs.mkdirSync(path.dirname(paths.catalog), { recursive: true });
  fs.writeFileSync(paths.output, indexText);
  fs.writeFileSync(paths.catalog, catalogText);
  const canonicalTasks = index.tasks.filter((task) => task.grade === 'canonical').length;
  console.log(`Wrote ${rel(paths.output)} (${index.candidates.length} candidates, ${index.tasks.length} tasks [${canonicalTasks} canonical])`);
  console.log(`Wrote ${rel(paths.catalog)}`);
}

main();
