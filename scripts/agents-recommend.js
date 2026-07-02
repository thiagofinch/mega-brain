#!/usr/bin/env node

/**
 * Recommends public agent entrypoints from the ARCG routing index.
 *
 * Story: ARCG-4.1
 */

const fs = require('fs');
const path = require('path');

const repoRoot = process.cwd();
const indexPath = path.join(repoRoot, '.data', 'agent-routing-index.json');
const args = process.argv.slice(2);

const STOP_WORDS = new Set([
  'a', 'as', 'o', 'os', 'e', 'de', 'do', 'da', 'dos', 'das', 'para', 'por', 'com',
  'em', 'um', 'uma', 'uns', 'umas', 'quais', 'qual', 'que', 'quem', 'me', 'pra',
  'sem', 'sobre', 'conhecido', 'este', 'esta', 'isso', 'isto',
  'the', 'and', 'or', 'to', 'for', 'of', 'in', 'on', 'with',
]);

const PUBLIC_STATUSES = new Set(['public_entrypoint', 'legacy_alias', 'core_authority']);
const CORE_FALLBACK_ORDER = new Map([
  ['@analyst', 0],
  ['@architect', 1],
  ['@megabrain-master', 2],
  ['@pm', 3],
  ['@po', 4],
  ['@qa', 5],
  ['@sm', 6],
]);
const AUTHORITY_RULES = [
  {
    id: 'devops-exclusive',
    agent_id: '@devops',
    triggers: ['push', 'abrir pr', 'criar pr', 'fazer pr', 'pull request', 'merge', 'release', 'deploy', 'publicar', 'subir', 'mcp'],
    label: 'Operação exclusiva de @devops.',
  },
  {
    id: 'architecture-authority',
    agent_id: '@architect',
    triggers: ['arquitetura', 'architecture', 'adr', 'decisão técnica', 'design técnico'],
    label: 'Decisão de arquitetura pertence a @architect.',
  },
  {
    id: 'story-validation-authority',
    agent_id: '@po',
    triggers: ['validar story', 'validar história', 'acceptance criteria', 'critérios de aceite'],
    label: 'Validação de story pertence a @po.',
  },
  {
    id: 'story-breakdown-authority',
    agent_id: '@sm',
    triggers: ['quebrar', 'quebrar em stories', 'epic em stories', 'épico em stories', 'criar story', 'story draft', 'story drafting', 'sprint', 'scrum', 'backlog de stories'],
    label: 'Criação e quebra operacional de stories pertence a @sm.',
  },
  {
    id: 'quality-authority',
    agent_id: '@qa',
    triggers: ['quality gate', 'teste', 'testes', 'qa', 'validar qualidade'],
    label: 'Quality gate pertence a @qa.',
  },
];

const DOMAIN_RULES = [
  {
    id: 'methodology-framework',
    triggers: ['metodologia', 'metodologias', 'framework', 'frameworks', 'cognitive', 'cognitivo', 'quality checks'],
    prefer: ['tools-squad/tools-orchestrator', 'mega-brain/megabrain-chief', 'squad-creator/squad-chief'],
    fallback: '@architect',
    reason: 'Demanda fala de criação, validação ou governança de metodologias/frameworks.',
  },
  {
    id: 'process-method',
    triggers: ['processo', 'processos', 'workflow', 'sop', 'procedimento', 'mapeamento'],
    prefer: ['mega-brain/megabrain-chief', 'megabrain-sop/sop-chief', 'tools-squad/tools-orchestrator'],
    fallback: '@architect',
    reason: 'Demanda parece envolver mapeamento ou formalização de processo.',
  },
  {
    id: 'agent-squad-creation',
    triggers: ['criar agente', 'criação de agente', 'criacao de agente', 'novo agente', 'criar squad', 'novo squad', 'skill', 'skills', 'orquestração'],
    prefer: ['squad-creator/squad-chief', 'tools-squad/tools-orchestrator'],
    fallback: '@architect',
    reason: 'Demanda envolve criação ou governança de agentes/squads/skills.',
  },
  {
    id: 'design-system',
    triggers: [
      'design system', 'design-system', 'ui', 'ux', 'interface', 'componentes', 'visual',
      'landing', 'landing page', 'página', 'pagina', 'dashboard', 'tela', 'telas',
      'desenhar', 'layout', 'wireframe', 'protótipo', 'prototipo', 'mockup',
    ],
    prefer: ['design-system/design-chief', 'design-ops/design-chief'],
    fallback: '@ux-design-expert',
    reason: 'Demanda aponta para design system, UX/UI, landing page, dashboard ou componentes visuais.',
  },
  {
    id: 'research',
    triggers: ['pesquisa', 'research', 'mercado', 'benchmark', 'competitive', 'intelligence', 'osint', 'evidência', 'evidencia'],
    prefer: ['deep-research/dr-orchestrator', 'intelligence-pipeline/intel-chief', 'spy/spy', '@analyst'],
    fallback: '@analyst',
    reason: 'Demanda pede pesquisa, inteligência ou síntese de evidências.',
  },
  {
    // Copywriting — carta de vendas, copy, VSL, headline, oferta. Distinto de brand (estratégia)
    // e content (conteúdo editorial). PT-BR natural de copy não casava com triggers genéricos.
    id: 'copywriting',
    triggers: [
      'copy', 'copywriting', 'carta de vendas', 'carta de venda', 'sales letter',
      'headline', 'oferta', 'vsl', 'video sales letter', 'persuasiva', 'persuasivo',
      'big idea', 'lead de vendas', 'email de vendas', 'página de vendas', 'pagina de vendas',
    ],
    prefer: ['copy/copy-chief', 'megabrain-copy/copy-chief', 'vsl-factory/vsl-chief'],
    fallback: '@pm',
    reason: 'Demanda pede copywriting (carta de vendas, VSL, headline, oferta persuasiva).',
  },
  {
    id: 'brand',
    triggers: ['marca', 'brand', 'branding', 'posicionamento', 'naming', 'arquétipo', 'arquetipo'],
    prefer: ['brand/brand-chief'],
    fallback: '@pm',
    reason: 'Demanda aponta para estratégia de marca.',
  },
  {
    id: 'code-analysis',
    triggers: ['código', 'codigo', 'code', 'repo', 'repositório', 'repositorio', 'brownfield', 'arquitetura de código'],
    prefer: ['domain-decoder/decoder-chief', 'code-anatomist/decoder-chief', '@architect'],
    fallback: '@architect',
    reason: 'Demanda pede análise de código, domínio ou brownfield.',
  },
  {
    // Investigação DIAGNÓSTICA (caçar incongruência/causa-raiz) — distinta de code-analysis (brownfield/arquitetura).
    // A intenção vem do VERBO diagnóstico + SINTOMA de discrepância, nunca de substantivo técnico genérico
    // (ex: "pipeline", "código") que pertence à construção. Por isso triggers exigem sinal investigativo explícito.
    id: 'code-investigation',
    triggers: [
      'investigar', 'investigação', 'investigacao', 'incongruência', 'incongruencia',
      'discrepância', 'discrepancia', 'inconsistência', 'inconsistencia', 'divergência', 'divergencia',
      'rastrear bug', 'caçar bug', 'cacar bug', 'diagnosticar bug', 'root cause', 'causa raiz',
      'por que está', 'por que esta', 'porque está', 'porque esta', 'não bate', 'nao bate', 'deveria bater',
    ],
    prefer: ['@megabrain-master', '@dev', 'data/data-chief', '@architect'],
    fallback: '@megabrain-master',
    reason: 'Demanda é investigação diagnóstica de sistema técnico — caçar incongruência/causa-raiz via varredura de código/dados (fan-out de subagentes). @megabrain-master orquestra investigadores paralelos; @dev/@data-chief para o domínio específico.',
  },
  {
    // Autonomia de agente — gate de fidelidade, ciclo autônomo, auditoria de agente, freios anti-delírio.
    // Camada de autonomia do bundle de autonomia (autonomy-gate, pipeline-cycle, agent-autonomy squad).
    id: 'agent-autonomy',
    triggers: [
      'autonomia', 'autonomia de agente', 'autonomy', 'gate de autonomia', 'autonomy-gate',
      'fidelidade', 'fidelity', 'truth-gate', 'anti-alucinação', 'anti-alucinacao', 'anti-delírio', 'anti-delirio',
      'ciclo autônomo', 'ciclo autonomo', 'pipeline-cycle', 'idea to done', 'auditar agente', 'auditoria de agente',
      'hard-stop', 'freios', 'no-omission', 'no-invention',
    ],
    prefer: ['agent-autonomy/autonomy-chief'],
    fallback: '@architect',
    reason: 'Demanda envolve autonomia de agente, gate de fidelidade (anti-delírio), ciclo autônomo idea→done ou auditoria de agente. autonomy-chief tria e roteia para o especialista de autonomia.',
  },
  {
    // Implementação/construção de software — distinta de code-analysis (entender) e code-investigation (diagnosticar).
    // Verbos de construção (construir, implementar, desenvolver) + alvo técnico (backend, frontend, API, feature).
    id: 'development',
    triggers: [
      'construir', 'implementar', 'desenvolver', 'codar', 'programar', 'build', 'implement',
      'backend', 'frontend', 'front-end', 'back-end', 'api', 'endpoint', 'feature', 'funcionalidade',
      'autenticação', 'autenticacao', 'auth', 'integração', 'integracao', 'refatorar', 'refactor',
    ],
    prefer: ['@dev', '@architect', '@megabrain-master'],
    fallback: '@dev',
    reason: 'Demanda envolve implementação/construção de software (backend, frontend, API, feature). @dev implementa; @architect decide trade-offs estruturais.',
  },
  {
    // Data engineering — schema, banco, multi-tenant, RLS, migração. Distinto de research (negócio) e analytics.
    id: 'data-engineering',
    triggers: [
      'banco de dados', 'database', 'schema', 'esquema', 'rls', 'row level security',
      'multi-tenant', 'multitenant', 'migração', 'migracao', 'migration', 'supabase',
      'postgres', 'postgresql', 'sql', 'modelar dados', 'modelagem de dados', 'query',
    ],
    prefer: ['@data-engineer', 'db-sage/db-sage', 'data/data-chief'],
    fallback: '@data-engineer',
    reason: 'Demanda envolve modelagem de dados, schema, RLS, multi-tenant ou migração de banco. @data-engineer/db-sage detêm autoridade de migrations e RLS.',
  },
  {
    id: 'ip-protection',
    triggers: ['proteção', 'protecao', 'ip', 'cópia', 'copia', 'engenharia reversa', 'prompt extraction'],
    prefer: ['ip-shield-squad/shield-chief'],
    fallback: '@architect',
    reason: 'Demanda envolve proteção de propriedade intelectual ou sistemas de IA.',
  },
];

const MODE_RULES = [
  { mode: 'CRIAR', triggers: ['criar', 'gerar', 'desenhar', 'construir', 'materializar', 'create', 'build'] },
  { mode: 'VALIDAR', triggers: ['validar', 'auditar', 'revisar', 'testar', 'avaliar', 'validate', 'audit', 'review'] },
  { mode: 'PLANEJAR', triggers: ['planejar', 'plano', 'roadmap', 'estratégia', 'estrategia', 'plan'] },
  { mode: 'ENTENDER', triggers: ['entender', 'explicar', 'analisar', 'diagnosticar', 'understand', 'analyze'] },
  { mode: 'CONFIGURAR', triggers: ['configurar', 'setup', 'instalar', 'configure'] },
  { mode: 'GERENCIAR', triggers: ['gerenciar', 'operar', 'gestão', 'gestao', 'manage'] },
  { mode: 'RESOLVER', triggers: ['resolver', 'corrigir', 'debug', 'fix'] },
  { mode: 'EXPLORAR', triggers: ['explorar', 'descobrir', 'investigar', 'explore'] },
];

function usage() {
  return [
    'Usage: npm run agents:recommend -- [--json] [--top N] "<demanda>"',
    '',
    'Examples:',
    '  npm run agents:recommend -- "validar metodologia de framework"',
    '  npm run agents:recommend -- --json "criar PR e fazer push"',
  ].join('\n');
}

function parseArgs(rawArgs) {
  const parsed = { json: false, top: 5, queryParts: [] };
  for (let i = 0; i < rawArgs.length; i += 1) {
    const arg = rawArgs[i];
    if (arg === '--json') {
      parsed.json = true;
    } else if (arg === '--top') {
      const value = Number(rawArgs[i + 1]);
      if (!Number.isInteger(value) || value < 1) throw new Error('--top requires a positive integer.');
      parsed.top = value;
      i += 1;
    } else if (arg === '--help' || arg === '-h') {
      parsed.help = true;
    } else {
      parsed.queryParts.push(arg);
    }
  }
  parsed.query = parsed.queryParts.join(' ').trim();
  return parsed;
}

function rel(filePath) {
  return path.relative(repoRoot, filePath).replaceAll(path.sep, '/');
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function normalize(text) {
  return String(text || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function tokenize(text) {
  return normalize(text)
    .split(/[^a-z0-9@-]+/i)
    .map((token) => token.trim())
    .filter((token) => token.length >= 2 && !STOP_WORDS.has(token));
}

function includesAny(text, triggers) {
  const normalized = normalize(text);
  const tokens = tokenize(text);
  return triggers.some((trigger) => {
    const normalizedTrigger = normalize(trigger);
    if (normalizedTrigger.includes(' ')) return normalized.includes(normalizedTrigger);
    return tokens.some((token) => token === normalizedTrigger || (normalizedTrigger.length >= 4 && token.startsWith(normalizedTrigger)));
  });
}

function candidateKey(candidate) {
  return candidate.squad ? `${candidate.squad}/${candidate.agent_id}` : candidate.agent_id;
}

function publicCandidate(candidate) {
  return PUBLIC_STATUSES.has(candidate.routing_status) && candidate.user_invocable && candidate.visibility_status !== 'excluded';
}

function candidateText(candidate) {
  return [
    candidate.agent_id,
    candidate.display_name,
    candidate.squad,
    ...(candidate.aliases || []),
    ...(candidate.domain?.primary || []),
    ...(candidate.domain?.secondary || []),
    candidate.description,
    ...(candidate.supported_modes || []),
  ].filter(Boolean).join(' ');
}

function coreFallbackPriority(candidate) {
  if (candidate.routing_status !== 'core_authority') return 999;
  return CORE_FALLBACK_ORDER.has(candidate.agent_id) ? CORE_FALLBACK_ORDER.get(candidate.agent_id) : 500;
}

function sourceSummary(candidate) {
  return (candidate.source_paths || []).slice(0, 3).map((source) => source.path);
}

function detectModes(query) {
  return MODE_RULES
    .filter((rule) => includesAny(query, rule.triggers))
    .map((rule) => rule.mode);
}

function detectAuthority(query) {
  return AUTHORITY_RULES.filter((rule) => includesAny(query, rule.triggers));
}

function detectDomains(query) {
  return DOMAIN_RULES.filter((rule) => includesAny(query, rule.triggers));
}

function metadataGaps(candidate) {
  const gaps = [];
  if (candidate.quality_signals?.description_placeholder) gaps.push('descrição ausente ou placeholder');
  if (candidate.quality_signals?.metadata_advisories > 0) gaps.push(`${candidate.quality_signals.metadata_advisories} advisory(s) de metadados`);
  if (!candidate.description) gaps.push('sem descrição útil para evidência de competência');
  return gaps;
}

function confidenceLabel(score, gaps) {
  if (score >= 75 && gaps.length === 0) return 'High';
  if (score >= 48) return 'Medium';
  return 'Low';
}

function scoreCandidate(candidate, context) {
  const key = candidateKey(candidate);
  const text = normalize(candidateText(candidate));
  const queryTokens = tokenize(context.query);
  const reasons = [];
  const gaps = metadataGaps(candidate);
  let domainPriority = 999;
  let hasRelevance = false;

  let score = 0;
  if (PUBLIC_STATUSES.has(candidate.routing_status)) score += 14;
  if (candidate.user_invocable) score += 12;
  if (candidate.entrypoint) score += 10;
  if (candidate.chief_interface_compliant || candidate.routing_status === 'core_authority') score += 9;
  if (candidate.description && !candidate.quality_signals?.description_placeholder) score += 10;

  const authorityMatch = context.authorityRules.find((rule) => rule.agent_id === candidate.agent_id);
  if (authorityMatch) {
    hasRelevance = true;
    score += 42;
    reasons.push(authorityMatch.label);
  }

  for (const domainRule of context.domainRules) {
    if (domainRule.prefer.includes(key) || domainRule.prefer.includes(candidate.agent_id)) {
      const position = domainRule.prefer.includes(key) ? domainRule.prefer.indexOf(key) : domainRule.prefer.indexOf(candidate.agent_id);
      domainPriority = Math.min(domainPriority, position);
      hasRelevance = true;
      score += 32 + ((domainRule.prefer.length - position) * 8);
      reasons.push(domainRule.reason);
    } else if (domainRule.fallback === candidate.agent_id) {
      hasRelevance = true;
      score += 16;
      reasons.push(`Fallback seguro: ${domainRule.fallback}.`);
    }
  }

  const supportedModes = new Set(candidate.supported_modes || []);
  const modeMatches = context.modes.filter((mode) => supportedModes.has(mode));
  if (modeMatches.length > 0) {
    hasRelevance = true;
    score += Math.min(12, modeMatches.length * 6);
    reasons.push(`Modos compatíveis: ${modeMatches.join(', ')}.`);
  }

  const tokenMatches = queryTokens.filter((token) => text.includes(token));
  if (tokenMatches.length > 0) {
    hasRelevance = true;
    score += Math.min(20, tokenMatches.length * 4);
    reasons.push(`Termos batem com catálogo: ${tokenMatches.slice(0, 5).join(', ')}.`);
  }

  // Domain-primary boost: quando a query bate com o domínio canônico ou o nome do
  // squad de um chief PÚBLICO, dá força ao roteamento por catálogo. Cobre os chiefs
  // de negócio que não têm domain rule explícita (auto-escalável aos squads do repo).
  if (candidate.routing_status === 'public_entrypoint') {
    const domainTokens = new Set([
      ...(candidate.domain?.primary || []),
      ...(candidate.domain?.secondary || []),
      candidate.squad,
    ].filter(Boolean).flatMap((d) => tokenize(String(d))));
    const domainHits = queryTokens.filter((token) => domainTokens.has(token));
    if (domainHits.length > 0) {
      hasRelevance = true;
      score += Math.min(30, 18 + (domainHits.length - 1) * 6);
      reasons.push(`Domínio do catálogo bate: ${domainHits.slice(0, 4).join(', ')}.`);
    }
  }

  if (candidate.routing_status === 'core_authority' && context.domainRules.length > 0 && !authorityMatch) {
    score -= 10;
    reasons.push('Core agent tratado como fallback porque há entrypoint especializado plausível.');
  }
  if (candidate.quality_signals?.description_placeholder) score -= 18;
  if (candidate.quality_signals?.metadata_advisories > 0) score -= Math.min(12, candidate.quality_signals.metadata_advisories * 4);
  if (candidate.routing_status === 'legacy_alias') score -= 3;
  if (!hasRelevance) score = Math.min(score, 35);

  const boundedScore = Math.max(0, Math.min(100, Math.round(score)));
  return {
    candidate,
    score: boundedScore,
    confidence: confidenceLabel(boundedScore, gaps),
    domainPriority,
    reasons: reasons.length > 0 ? reasons : ['Roteamento por entrypoint público e metadados do catálogo.'],
    gaps,
    sources: sourceSummary(candidate),
  };
}

function fallbackFor(context, recommendations) {
  const explicit = context.domainRules.find((rule) => rule.fallback)?.fallback;
  if (explicit) return explicit;
  if (context.authorityRules.length > 0) return context.authorityRules[0].agent_id;
  if (recommendations.some((rec) => rec.candidate.routing_status !== 'core_authority')) return '@architect';
  return '@analyst';
}

function buildRecommendation(index, query, top) {
  const context = {
    query,
    modes: detectModes(query),
    authorityRules: detectAuthority(query),
    domainRules: detectDomains(query),
  };

  const gated = [];
  for (const candidate of index.candidates || []) {
    if (candidate.routing_status === 'excluded') {
      gated.push({
        candidate: candidateKey(candidate),
        gate: 'excluded',
        reason: candidate.exclusion_reason || 'Candidate is excluded from public recommendation.',
      });
    } else if (candidate.routing_status === 'internal_specialist') {
      gated.push({
        candidate: candidateKey(candidate),
        gate: 'internal/manual-only',
        reason: 'Internal specialist; route through a public chief or visible skill.',
      });
    } else if (candidate.quality_signals?.issues?.some((issue) => issue.code === 'missing_source')) {
      gated.push({
        candidate: candidateKey(candidate),
        gate: 'missing_source',
        reason: candidate.exclusion_reason || 'Missing source file.',
      });
    }
  }

  const scored = (index.candidates || [])
    .filter(publicCandidate)
    .map((candidate) => scoreCandidate(candidate, context))
    .filter((rec) => rec.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      if (a.domainPriority !== b.domainPriority) return a.domainPriority - b.domainPriority;
      const corePriority = coreFallbackPriority(a.candidate) - coreFallbackPriority(b.candidate);
      if (corePriority !== 0) return corePriority;
      return candidateKey(a.candidate).localeCompare(candidateKey(b.candidate));
    });

  let recommendations = scored.slice(0, top);
  if (context.authorityRules.some((rule) => rule.id === 'devops-exclusive')) {
    const devops = scored.find((rec) => rec.candidate.agent_id === '@devops');
    recommendations = devops ? [devops] : recommendations;
  }

  const lowConfidence = recommendations.length === 0 || recommendations[0].confidence === 'Low';
  const fallback = fallbackFor(context, recommendations);
  return {
    schema_version: '1.0.0',
    story_id: 'ARCG-4.1',
    generated_at: new Date().toISOString(),
    advisory_only: true,
    query,
    objective: summarizeObjective(query, context),
    detected_modes: context.modes,
    detected_authority_rules: context.authorityRules.map((rule) => ({ id: rule.id, route: rule.agent_id, reason: rule.label })),
    detected_domain_rules: context.domainRules.map((rule) => ({ id: rule.id, reason: rule.reason })),
    low_confidence: lowConfidence,
    fallback,
    recommendations: recommendations.map((rec, index) => ({
      rank: index + 1,
      agent: rec.candidate.agent_id,
      squad: rec.candidate.squad || 'core',
      role: rec.candidate.routing_status,
      aliases: rec.candidate.aliases || [],
      confidence: rec.confidence,
      score: rec.score,
      reasons: rec.reasons,
      metadata_gaps: rec.gaps,
      sources: rec.sources,
      fallback,
    })),
    gated_summary: {
      excluded: gated.filter((item) => item.gate === 'excluded').length,
      internal_manual_only: gated.filter((item) => item.gate === 'internal/manual-only').length,
      missing_source: gated.filter((item) => item.gate === 'missing_source').length,
    },
  };
}

function summarizeObjective(query, context) {
  if (context.authorityRules.length > 0) return `Aplicar autoridade correta para: ${query}`;
  if (context.domainRules.length > 0) return context.domainRules.map((rule) => rule.id).join(' + ');
  return query;
}

function renderText(report) {
  const lines = [
    'agent recommendation advisory',
    `Objetivo: ${report.objective}`,
    `Demanda: ${report.query}`,
    `Modo(s): ${report.detected_modes.join(', ') || 'não detectado'}`,
    `Fallback: ${report.fallback}`,
    '',
    'Agentes/squads recomendados:',
  ];

  if (report.recommendations.length === 0) {
    lines.push('- Nenhum entrypoint público com confiança suficiente.');
  }

  for (const item of report.recommendations) {
    lines.push(`${item.rank}. ${item.squad}/${item.agent}`);
    lines.push(`   Papel: ${item.role}`);
    lines.push(`   Confiança: ${item.confidence} (${item.score}/100)`);
    lines.push(`   Motivo: ${item.reasons.join(' ')}`);
    lines.push(`   Fontes: ${item.sources.join(', ') || 'sem fonte registrada'}`);
    lines.push(`   Lacunas: ${item.metadata_gaps.join('; ') || 'nenhuma crítica'}`);
    lines.push(`   Fallback: ${item.fallback}`);
  }

  if (report.detected_authority_rules.length > 0) {
    lines.push('', 'Authority gate:');
    for (const rule of report.detected_authority_rules) {
      lines.push(`- ${rule.route}: ${rule.reason}`);
    }
  }

  if (report.low_confidence) {
    lines.push('', 'Confiança baixa: confirme o domínio ou leia os agent cards antes de ativar workflow.');
  }

  lines.push('', 'Hard gates aplicados:');
  lines.push(`- excluded: ${report.gated_summary.excluded}`);
  lines.push(`- internal/manual-only: ${report.gated_summary.internal_manual_only}`);
  lines.push(`- missing_source: ${report.gated_summary.missing_source}`);
  lines.push('', 'Aviso: advisory de catálogo; não executa agentes nem substitui EPIC-ASI runtime routing.');
  return `${lines.join('\n')}\n`;
}

function main() {
  let options;
  try {
    options = parseArgs(args);
  } catch (error) {
    console.error(error.message);
    console.error(usage());
    process.exit(1);
  }

  if (options.help) {
    console.log(usage());
    return;
  }
  if (!options.query) {
    console.error('Missing demand text.');
    console.error(usage());
    process.exit(1);
  }
  if (!fs.existsSync(indexPath)) {
    console.error(`Missing index: ${rel(indexPath)}. Run npm run build:agent-routing-index first.`);
    process.exit(1);
  }

  const index = readJson(indexPath);
  const report = buildRecommendation(index, options.query, options.top);
  if (options.json) console.log(JSON.stringify(report, null, 2));
  else process.stdout.write(renderText(report));
}

main();
