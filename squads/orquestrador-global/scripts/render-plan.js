#!/usr/bin/env node
/**
 * render-plan.js — deterministic plan renderer
 *
 * Transforms plan YAML to: md (narrative), mermaid (DAG diagram), json (canonical),
 * and html (standalone visual report).
 * Pure function: same input → same output.
 *
 * Story: STORY-PA-4.2
 * Consumer: plan-architect (PA-6.1) handoff; humanos (review)
 */
'use strict';

const fs = require('fs');
const report = require('./html-report-primitives');

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[char]);
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function numberOrDash(value, suffix = '') {
  return typeof value === 'number' && Number.isFinite(value) ? `${value}${suffix}` : '-';
}

function compactList(items, fallback = '-') {
  const list = asArray(items).filter(Boolean);
  return list.length ? list.map(escapeHtml).join(', ') : fallback;
}

function riskClass(rpn) {
  if (rpn >= 150) return 'risk-high';
  if (rpn >= 90) return 'risk-medium';
  return 'risk-low';
}

function gateClass(gate) {
  const normalized = String(gate || '').toLowerCase();
  if (normalized === 'pass' || normalized === 'go') return 'ok';
  if (normalized === 'fail' || normalized === 'hold') return 'bad';
  return 'neutral';
}

function wrapSvgText(value, maxChars = 30, maxLines = 3) {
  const words = String(value || '').trim().split(/\s+/).filter(Boolean);
  const lines = [];

  for (const word of words.length ? words : ['-']) {
    const chunks = [];
    for (let i = 0; i < word.length; i += maxChars) {
      chunks.push(word.slice(i, i + maxChars));
    }
    for (const chunk of chunks) {
      if (!lines.length) {
        lines.push(chunk);
        continue;
      }
      const current = lines[lines.length - 1];
      const next = current ? `${current} ${chunk}` : chunk;
      if (next.length <= maxChars) {
        lines[lines.length - 1] = next;
      } else {
        lines.push(chunk);
      }
      if (lines.length > maxLines) {
        lines.length = maxLines;
        lines[maxLines - 1] = `${lines[maxLines - 1].slice(0, Math.max(0, maxChars - 3))}...`;
        return lines;
      }
    }
  }

  return lines.slice(0, maxLines);
}

function computeDagLayout(nodes, edges) {
  const levels = new Map(nodes.map((node) => [node.id, 0]));
  const knownEdges = edges.filter((edge) => levels.has(edge.from) && levels.has(edge.to));

  for (let i = 0; i < nodes.length; i++) {
    let changed = false;
    for (const edge of knownEdges) {
      const nextLevel = (levels.get(edge.from) || 0) + 1;
      if (nextLevel > (levels.get(edge.to) || 0)) {
        levels.set(edge.to, nextLevel);
        changed = true;
      }
    }
    if (!changed) break;
  }

  const columns = [];
  for (const node of nodes) {
    const level = levels.get(node.id) || 0;
    if (!columns[level]) columns[level] = [];
    columns[level].push(node);
  }

  return columns.filter(Boolean);
}

function svgTextLines(lines, x, y, className) {
  return `<text class="${className}" x="${x}" y="${y}">${lines.map((line, index) => (
    `<tspan x="${x}" dy="${index === 0 ? 0 : 16}">${escapeHtml(line)}</tspan>`
  )).join('')}</text>`;
}

function renderDagSvg(plan) {
  const nodes = asArray(plan.dag && plan.dag.nodes);
  const edges = asArray(plan.dag && plan.dag.edges);
  if (!nodes.length) {
    return '<p class="muted">Nenhum nó DAG declarado.</p>';
  }

  const criticalPath = new Set(asArray(plan.dag && plan.dag.critical_path));
  const columns = computeDagLayout(nodes, edges);
  const boxWidth = 230;
  const boxHeight = 92;
  const colGap = 76;
  const rowGap = 34;
  const padding = 34;
  const maxRows = Math.max(...columns.map((column) => column.length), 1);
  const contentHeight = maxRows * boxHeight + Math.max(0, maxRows - 1) * rowGap;
  const width = Math.max(680, padding * 2 + columns.length * boxWidth + Math.max(0, columns.length - 1) * colGap);
  const height = padding * 2 + contentHeight;
  const positions = new Map();

  columns.forEach((column, columnIndex) => {
    const columnHeight = column.length * boxHeight + Math.max(0, column.length - 1) * rowGap;
    const yStart = padding + (contentHeight - columnHeight) / 2;
    column.forEach((node, rowIndex) => {
      positions.set(node.id, {
        x: padding + columnIndex * (boxWidth + colGap),
        y: yStart + rowIndex * (boxHeight + rowGap),
      });
    });
  });

  const edgePaths = edges.map((edge, index) => {
    const from = positions.get(edge.from);
    const to = positions.get(edge.to);
    if (!from || !to) return '';
    const startX = from.x + boxWidth;
    const startY = from.y + boxHeight / 2;
    const endX = to.x;
    const endY = to.y + boxHeight / 2;
    const midX = startX + Math.max(34, (endX - startX) / 2);
    const path = `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
    const label = edge.type || edge.artifact || '';
    const labelX = startX + (endX - startX) / 2;
    const labelY = startY + (endY - startY) / 2 - 8;
    return `
      <g class="dag-edge">
        <path d="${path}" marker-end="url(#dag-arrow)" />
        ${label ? `<text x="${labelX}" y="${labelY}" class="dag-edge-label">${escapeHtml(label)}</text>` : ''}
      </g>`;
  }).join('\n');

  const nodeGroups = nodes.map((node) => {
    const pos = positions.get(node.id);
    if (!pos) return '';
    const label = node.label || node.capability || node.id || '';
    const meta = [
      node.routing_primary_executor,
      node.estimated_duration_minutes ? `${node.estimated_duration_minutes}min` : '',
    ].filter(Boolean).join(' · ');
    return `
      <g class="dag-node ${criticalPath.has(node.id) ? 'critical' : ''}">
        <rect x="${pos.x}" y="${pos.y}" width="${boxWidth}" height="${boxHeight}" rx="8" />
        <text class="dag-node-id" x="${pos.x + 14}" y="${pos.y + 22}">${escapeHtml(node.id || '')}</text>
        ${svgTextLines(wrapSvgText(label, 30, 2), pos.x + 14, pos.y + 45, 'dag-node-label')}
        <text class="dag-node-meta" x="${pos.x + 14}" y="${pos.y + 78}">${escapeHtml(meta || node.quality_gate || '')}</text>
      </g>`;
  }).join('\n');

  return `<svg class="dag-svg" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="dag-title dag-desc">
    <title id="dag-title">Diagrama DAG renderizado</title>
    <desc id="dag-desc">Visualização SVG standalone gerada a partir do Mermaid do plano.</desc>
    <defs>
      <marker id="dag-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#d1ff00" />
      </marker>
    </defs>
    <style>
      .dag-edge path { fill: none; stroke: rgba(209,255,0,0.42); stroke-width: 2; }
      .dag-edge-label { fill: #d1ff00; font: 800 11px "Geist Mono", ui-monospace, monospace; text-anchor: middle; paint-order: stroke; stroke: #090b0a; stroke-width: 4px; letter-spacing: 0; }
      .dag-node rect { fill: #161a15; stroke: rgba(255,255,255,0.18); stroke-width: 1.5; }
      .dag-node.critical rect { fill: #202717; stroke: #d1ff00; stroke-width: 2.5; }
      .dag-node-id { fill: #d1ff00; font: 900 12px "Geist Mono", ui-monospace, monospace; letter-spacing: 0; }
      .dag-node-label { fill: #f7ffe6; font: 800 13px "Geist", system-ui, sans-serif; letter-spacing: 0; }
      .dag-node-meta { fill: #a8ad9d; font: 700 11px "Geist Mono", ui-monospace, monospace; letter-spacing: 0; }
    </style>
    ${edgePaths}
    ${nodeGroups}
  </svg>`;
}


function parseArgs(argv) {
  const args = { plan: null, format: 'md', output: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--format') args.format = argv[++i];
    else if (a === '--output') args.output = argv[++i];
    else if (a === '--deterministic') { /* no-op: render is already deterministic */ }
    else if (!args.plan) args.plan = a;
  }
  return args;
}

function parseYAML(src) {
  try { return require('js-yaml').load(src); }
  catch {
    try { return JSON.parse(src); }
    catch { return null; }
  }
}

// ── Renderers ─────────────────────────────────────────────────────────────────
function renderMermaid(plan) {
  const nodes = (plan.dag && plan.dag.nodes) || [];
  const edges = (plan.dag && plan.dag.edges) || [];
  const criticalPath = new Set((plan.dag && plan.dag.critical_path) || []);
  const lines = ['```mermaid', 'graph TD'];
  for (const n of nodes) {
    const label = (n.label || n.capability || n.id).replace(/"/g, '');
    const dur = n.estimated_duration_minutes ? ` — ${n.estimated_duration_minutes}min` : '';
    lines.push(`    ${n.id}["${label}${dur}"]`);
  }
  for (const e of edges) {
    lines.push(`    ${e.from} --> ${e.to}`);
  }
  for (const n of nodes) {
    if (criticalPath.has(n.id)) {
      lines.push(`    style ${n.id} fill:#f66`);
    }
  }
  lines.push('```');
  return lines.join('\n');
}

function renderMarkdown(plan) {
  const out = [];
  const planId = plan.plan_id || 'unknown';
  const demand = plan.demand && plan.demand.raw || '';
  const score = plan.quality_score || 'N/A';
  const cost = (plan.resource_estimate && plan.resource_estimate.total_cost_usd) || 0;

  out.push(`# Plano de Orquestração — \`${planId}\``);
  out.push('');
  out.push(`> **Demanda:** ${demand}`);
  out.push(`> **Score:** ${score}/5 · **Custo:** $${cost} · **Criado:** ${plan.created_at || ''}`);
  out.push('');

  // Executive summary
  out.push('## Resumo Executivo');
  out.push('');
  const parsed = (plan.demand && plan.demand.parsed) || {};
  out.push(`- **Domain:** ${parsed.primary_domain || ''} · **Complexity:** ${parsed.complexity || ''} · **Urgency:** ${parsed.urgency || ''}`);
  out.push(`- **Capabilities:** ${(plan.selected_capabilities || []).length} selecionadas · **Nós DAG:** ${(plan.dag && plan.dag.nodes || []).length}`);
  if (plan.routing_summary) {
    out.push(`- **Routing:** ${plan.routing_summary.engine || 'unchecked'} · decisions: ${plan.routing_summary.decisions_count || 0} · blockers: ${(plan.routing_summary.blocked_nodes || []).length} · fallbacks: ${(plan.routing_summary.fallback_nodes || []).length}`);
  }
  if (plan.handoff && plan.handoff.next_action_suggested) {
    out.push(`- **Próxima ação:** \`${plan.handoff.next_action_suggested}\` (executor: ${plan.handoff.next_action_executor || 'TBD'})`);
  }
  out.push('');

  // DAG diagram
  out.push('## DAG');
  out.push('');
  out.push(renderMermaid(plan));
  out.push('');

  // Capabilities table
  out.push('## Capabilities Selecionadas');
  out.push('');
  out.push('| # | ID | Tipo | Score | IDS | Route | Executor | Band |');
  out.push('|---|---|---|---|---|---|---|---|');
  for (const [i, c] of (plan.selected_capabilities || []).entries()) {
    const routing = c.routing || {};
    out.push(`| ${i + 1} | ${c.id || ''} | ${c.type || ''} | ${c.score || ''} | ${c.ids_decision || ''} | ${routing.decision_id || c.routing_decision_id || ''} | ${routing.primary_executor || ''} | ${routing.confidence_band || ''} |`);
  }
  out.push('');

  const blockedNodes = ((plan.dag && plan.dag.nodes) || []).filter(n => n.routing_blocked);
  if (blockedNodes.length) {
    out.push('## Routing Blockers');
    out.push('');
    out.push('| Nó | Route | Gates |');
    out.push('|---|---|---|');
    for (const n of blockedNodes) {
      out.push(`| ${n.id || ''} | ${n.routing_decision_id || ''} | ${(n.routing_hard_gates || []).join(', ')} |`);
    }
    out.push('');
  }

  // Risks
  if (plan.risks && plan.risks.top_risks && plan.risks.top_risks.length) {
    out.push('## Top Riscos');
    out.push('');
    out.push('| RPN | Nó | Descrição | Mitigação |');
    out.push('|---|---|---|---|');
    for (const r of plan.risks.top_risks) {
      out.push(`| ${r.rpn} | ${r.node} | ${r.description} | ${r.mitigation} |`);
    }
    out.push('');
  }

  // Success criteria
  if (plan.success_criteria && plan.success_criteria.length) {
    out.push('## Success Criteria');
    out.push('');
    for (const s of plan.success_criteria) {
      out.push(`- [ ] ${s.metric} — threshold: ${s.threshold}`);
    }
    out.push('');
  }

  // Compliance
  out.push('## Constitutional Compliance');
  out.push('');
  const cc = plan.constitutional_compliance || {};
  out.push(`- CODEOWNERS: \`${cc.codeowners_check || 'unchecked'}\``);
  out.push(`- Business Isolation: \`${cc.business_isolation_check || 'unchecked'}\``);
  out.push(`- Agent Authority: \`${cc.agent_authority_check || 'unchecked'}\``);
  out.push(`- No-Invention: \`${cc.no_invention_check || 'unchecked'}\``);

  return out.join('\n');
}

function renderJSON(plan) {
  return JSON.stringify(plan, null, 2);
}

// Chave snake_case → título legível ("cli_first" → "Cli First").
function titleizeKey(key) {
  return String(key).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

// Score de qualidade: escala honesta (design pass 2026-07-02).
// quality_score ≤ 1 é fração → renderiza como % ; > 1 assume escala /5 legada.
function formatScore(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  if (value <= 1) return `${Math.round(value * 100)}%`;
  return `${value}/5`;
}

// Seção que se esconde quando o conteúdo é vazio — nunca esqueleto de traços.
function sectionIf(title, content) {
  if (!content || !String(content).trim()) return '';
  return `\n    <section>\n      <h2>${escapeHtml(title)}</h2>\n      ${content}\n    </section>`;
}

function renderHtml(plan) {
  const planId = plan.plan_id || 'unknown';
  const demand = (plan.demand && plan.demand.raw) || '';
  const parsed = (plan.demand && plan.demand.parsed) || {};
  const nodes = asArray(plan.dag && plan.dag.nodes);
  const edges = asArray(plan.dag && plan.dag.edges);
  const criticalPathIds = asArray(plan.dag && plan.dag.critical_path);
  const criticalPath = new Set(criticalPathIds);
  const capabilities = asArray(plan.selected_capabilities);
  // Tolerância de schema: aceita top_risks (canônico) e top (variante de campo).
  const risks = asArray((plan.risks && (plan.risks.top_risks || plan.risks.top)));
  const criteria = asArray(plan.success_criteria);
  const assumptions = asArray(plan.falsifiable_assumptions);
  const elicitations = asArray(plan.demand && plan.demand.elicitations);
  const parallelGroups = asArray(plan.dag && plan.dag.parallel_groups);
  const compliance = plan.constitutional_compliance || {};
  const handoff = plan.handoff || {};
  const discovery = plan.discovery || {};
  const scanned = discovery.capabilities_scanned || {};
  const resource = plan.resource_estimate || {};
  const routing = plan.routing_summary || {};
  const quality = plan.quality_breakdown || {};
  const audit = plan.audit || {};
  const preMortem = plan.risks && plan.risks.pre_mortem;
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const criticalNodes = criticalPathIds.map((id) => nodeById.get(id)).filter(Boolean);
  const dagSvg = renderDagSvg(plan);

  const demandConfidence = typeof parsed.confidence === 'number' ? parsed.confidence
    : (typeof (plan.demand && plan.demand.confidence) === 'number' ? plan.demand.confidence : null);
  const demandGrid = report.renderDefinitionList([
    { label: 'Domínio primário', value: parsed.primary_domain || null },
    { label: 'Domínios secundários', value: asArray(parsed.secondary_domains).length ? compactList(parsed.secondary_domains) : null, html: true },
    { label: 'Tipo de tarefa', value: parsed.task_type || null },
    { label: 'Complexidade', value: parsed.complexity || (plan.demand && plan.demand.mode) || null },
    { label: 'Urgência', value: parsed.urgency || null },
    { label: 'Business units', value: asArray(parsed.business_units).length ? compactList(parsed.business_units) : null, html: true },
    { label: 'Deadline implícito', value: parsed.implicit_deadline || null },
    { label: 'Confiança', value: demandConfidence !== null ? report.renderBar(demandConfidence, 1, demandConfidence.toFixed(2)) : null, html: true },
    { label: 'Evidência', value: (plan.demand && plan.demand.evidence) || null },
  ]);

  const discoveryGrid = report.renderKeyValueGrid([
    { label: 'Cache version', value: discovery.cache_version || null },
    { label: 'Cache age', value: discovery.cache_age_seconds ?? null },
    { label: 'Squads', value: scanned.squads ?? null },
    { label: 'Agents', value: scanned.agents ?? null },
    { label: 'Skills', value: scanned.skills ?? null },
    { label: 'Tasks', value: scanned.tasks ?? null },
    { label: 'Workflows', value: scanned.workflows ?? null },
    { label: 'Drift', value: discovery.cache_drift_detected === undefined ? null : report.renderPill(discovery.cache_drift_detected ? 'detected' : 'none', discovery.cache_drift_detected ? 'bad' : 'ok'), html: true },
  ]);
  const discoveryNote = discovery.note ? `<p class="muted">${escapeHtml(discovery.note)}</p>` : '';
  const discoverySources = asArray(discovery.sources).length
    ? `<p class="muted">Fontes: ${compactList(discovery.sources)}</p>` : '';

  const elicitationTable = report.renderTable([
    { label: 'Pergunta', field: 'q' },
    { label: 'Resposta', field: 'a' },
    { label: 'Dimensão', field: 'dimension' },
    { label: 'Info gain', field: 'info_gain' },
  ], elicitations, 'Nenhuma elicitação declarada.');

  const nodeCards = nodes.map((node) => {
    const risk = node.risk || {};
    const rpn = Number(risk.rpn || 0);
    return `
      <article class="node-card ${criticalPath.has(node.id) ? 'critical' : ''}">
        <div class="node-head">
          <span class="node-id">${escapeHtml(node.id || '')}</span>
          <span class="pill ${riskClass(rpn)}">RPN ${numberOrDash(rpn)}</span>
        </div>
        <h3>${escapeHtml(node.label || node.capability || node.id || '')}</h3>
        <dl>
          <div><dt>Executor</dt><dd>${escapeHtml(node.routing_primary_executor || '')}</dd></div>
          <div><dt>Capability</dt><dd>${escapeHtml(node.capability || '')}</dd></div>
          <div><dt>Duração</dt><dd>${numberOrDash(node.estimated_duration_minutes, 'min')}</dd></div>
          <div><dt>Gate</dt><dd>${escapeHtml(node.quality_gate || '')}</dd></div>
        </dl>
        <p class="muted">Outputs: ${compactList(node.outputs_produced)}</p>
      </article>`;
  }).join('\n');

  // Dependências: dropEmptyColumns mata as colunas Tipo/Artefato quando as
  // edges só carregam from/to (caso comum).
  const edgeTable = report.renderTable([
    { label: 'De', field: 'from' },
    { label: 'Para', field: 'to' },
    { label: 'Tipo', field: 'type' },
    { label: 'Artefato', field: 'artifact' },
  ], edges, 'Nenhuma dependência declarada.', { dropEmptyColumns: true });

  // Capabilities: tabela COMPACTA e adaptativa. Colunas 100% vazias caem
  // (dropEmptyColumns) — antes: cada capability sem routing rico virava um
  // bloco de ~330px de traços empilhados.
  const capabilityTable = report.renderTable([
    { label: '#', html: true, value: (_, index) => String(index + 1) },
    { label: 'ID', field: 'id' },
    { label: 'Papel', html: true, value: (capability) => escapeHtml(capability.role || capability.reason || '') },
    { label: 'Tipo', field: 'type' },
    { label: 'IDS', html: true, value: (capability) => capability.ids_decision ? report.renderPill(capability.ids_decision, capability.ids_decision === 'CREATE' ? 'bad' : 'ok') : '' },
    { label: 'Score', html: true, value: (capability) => typeof capability.score === 'number' ? report.renderBar(capability.score, 1, capability.score.toFixed(2)) : '' },
    { label: 'Executor', html: true, value: (capability) => escapeHtml((capability.routing && capability.routing.primary_executor) || '') },
    { label: 'Gate', html: true, value: (capability) => escapeHtml((capability.routing && capability.routing.quality_gate_agent) || '') },
    { label: 'Confiança', html: true, value: (capability) => {
      const c = capability.routing && capability.routing.confidence;
      return typeof c === 'number' ? report.renderBar(c, 1, c.toFixed(2)) : '';
    } },
  ], capabilities, 'Nenhuma capability selecionada.', { dropEmptyColumns: true });

  // Detalhe dos Nós: dieta de colunas (design pass 2026-07-02). Antes: ~15
  // colunas esmagadas em células de 20px. Inputs/outputs/routing detalhado já
  // vivem nos CARDS "Nós do DAG" — a tabela carrega só o comparável.
  const nodeDetailTable = report.renderTable([
    { label: 'Nó', field: 'id' },
    { label: 'Label', field: 'label' },
    { label: 'Executor', html: true, value: (node) => escapeHtml(node.routing_primary_executor || '') },
    { label: 'Quality gate', html: true, value: (node) => escapeHtml(node.quality_gate || node.routing_quality_gate_agent || '') },
    { label: 'Duração', html: true, value: (node) => node.estimated_duration_minutes ? `${node.estimated_duration_minutes}min` : '' },
    { label: 'Tokens', html: true, value: (node) => node.estimated_cost_tokens ? Number(node.estimated_cost_tokens).toLocaleString('pt-BR') : '' },
    { label: 'Modelo', field: 'model_tier' },
    { label: 'Confiança', html: true, value: (node) => typeof node.routing_confidence === 'number' ? report.renderBar(node.routing_confidence, 1, node.routing_confidence.toFixed(2)) : '' },
    { label: 'RPN', html: true, value: (node) => {
      const rpn = node.risk && node.risk.rpn;
      return rpn ? report.renderPill(rpn, riskClass(Number(rpn))) : '';
    } },
    { label: 'Hard gates', html: true, value: (node) => asArray(node.routing_hard_gates).length ? compactList(node.routing_hard_gates) : '' },
  ], nodes, 'Nenhum nó declarado.', { dropEmptyColumns: true });

  // Grupos paralelos: tolerância de schema (QA CONCERNS 2026-07-02) — aceita
  // AMBAS as formas vivas: objeto {group_id, nodes, reason} OU array puro de
  // node-ids (a forma do plan.json canônico). Sem isso, array-rows viravam a
  // cascata de '-' que o honest-empty existe para matar.
  const normalizedGroups = parallelGroups.map((group, index) => {
    if (Array.isArray(group)) return { group_id: `G${index + 1}`, nodes: group, reason: '' };
    return group || {};
  });
  const parallelGroupTable = report.renderTable([
    { label: 'Grupo', field: 'group_id' },
    { label: 'Nós', html: true, value: (group) => compactList(group.nodes) },
    { label: 'Motivo', field: 'reason' },
  ], normalizedGroups, 'Nenhum grupo paralelo declarado.', { dropEmptyColumns: true });

  const riskRows = risks.map((risk) => `
    <tr>
      <td><span class="pill ${riskClass(Number(risk.rpn || 0))}">${escapeHtml(risk.rpn ?? '')}</span></td>
      <td>${escapeHtml(risk.node || '')}</td>
      <td>${escapeHtml(risk.description || risk.risk || '')}</td>
      <td>${escapeHtml(risk.mitigation || '')}</td>
    </tr>`).join('\n');

  // Critérios: aceita objetos {metric, threshold} OU strings simples.
  const criteriaItems = criteria.map((item) => {
    if (typeof item === 'string') return `\n    <li><strong>${escapeHtml(item)}</strong></li>`;
    return `\n    <li>\n      <strong>${escapeHtml(item.metric || '')}</strong>\n      <span>${escapeHtml(item.threshold || '')}</span>\n    </li>`;
  }).join('\n');

  const criticalPathItems = criticalNodes.map((node, index) => `
    <li>
      <span class="step-index">${index + 1}</span>
      <span>${escapeHtml(node.label || node.id || '')}</span>
      <small>${numberOrDash(node.estimated_duration_minutes, 'min')}</small>
    </li>`).join('\n');

  // Breakdown de qualidade: escala honesta — valores ≤1 são frações → %.
  const qualityRows = Object.entries(quality).map(([key, value]) => {
    const num = Number(value) || 0;
    const isFraction = num <= 1;
    const label = isFraction ? `${Math.round(num * 100)}%` : `${value}/5`;
    return `
    <div class="metric-row">
      <span>${escapeHtml(key.replace(/_/g, ' '))}</span>
      <strong>${report.renderBar(num, isFraction ? 1 : 5, label)}</strong>
    </div>`;
  }).join('\n');

  // Recursos: tolerância de schema (total_tokens|total_tokens_estimate;
  // wall time em horas OU estimate textual) + campos ausentes se escondem.
  const totalTokens = resource.total_tokens ?? resource.total_tokens_estimate ?? null;
  const wallTime = resource.total_wall_time_estimate_hours != null
    ? `${resource.total_wall_time_estimate_hours}h`
    : (resource.wall_clock_estimate || null);
  const resourceGrid = report.renderKeyValueGrid([
    { label: 'Tokens totais', value: totalTokens != null ? Number(totalTokens).toLocaleString('pt-BR') : null },
    { label: 'Custo USD', value: resource.total_cost_usd != null ? `$${resource.total_cost_usd}` : null },
    { label: 'Wall time', value: wallTime },
    { label: 'Modelos', value: asArray(resource.models_used).length ? compactList(resource.models_used) : null, html: true },
    { label: 'Agents', value: resource.agents_count ?? null },
    { label: 'Time', value: resource.team || null },
    { label: 'Duração crítica', value: (plan.dag && plan.dag.critical_path_duration_minutes) ? `${plan.dag.critical_path_duration_minutes}min` : null },
  ]);

  const preMortemContent = preMortem
    ? `${report.renderDefinitionList([
      { label: 'Ativado', value: preMortem.activated ? 'sim' : 'não' },
      { label: 'Trigger', value: preMortem.trigger || '-' },
    ])}${report.renderTable([
      { label: 'ID', field: 'id' },
      { label: 'Cenário', field: 'scenario' },
      { label: 'Mitigação', field: 'mitigation' },
    ], asArray(preMortem.failure_scenarios), 'Nenhum cenário de falha declarado.')}`
    : '<p class="muted">Pre-mortem não ativado.</p>';

  // Handoff: tolerância de schema (next_action_suggested | next_action).
  const nextAction = handoff.next_action_suggested || handoff.next_action || null;
  const handoffDetails = report.renderDefinitionList([
    { label: 'Próxima ação', value: nextAction },
    { label: 'Executor', value: handoff.next_action_executor || null },
    { label: 'Aprovações', value: asArray(handoff.approvals_required).length ? compactList(handoff.approvals_required) : null, html: true },
    { label: 'Não executar até', value: asArray(handoff.do_not_execute_until).length ? compactList(handoff.do_not_execute_until) : null, html: true },
    { label: 'Handoffs relacionados', value: asArray(handoff.related_handoffs).length ? compactList(handoff.related_handoffs) : null, html: true },
    { label: 'Evidências', value: handoff.evidence_dir || null },
  ]);

  const auditDetails = report.renderDefinitionList([
    { label: 'Criado por', value: audit.created_by || plan.created_by || '-' },
    { label: 'Criado em', value: audit.created_at || plan.created_at || '-' },
    { label: 'Cache hash', value: audit.cache_manifest_hash || '-' },
    { label: 'Scoring config', value: audit.scoring_config_version || '-' },
    { label: 'Heurísticas', value: compactList(audit.heuristics_applied), html: true },
  ]);

  return `<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Ccircle cx='8' cy='8' r='7' fill='%23b5ff00'/%3E%3C/svg%3E">
  <title>Plano de Orquestração - ${escapeHtml(planId)}</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --surface: #ffffff;
      --surface-soft: #f1f5f9;
      --text: #18202f;
      --muted: #64748b;
      --line: #d7dde8;
      --blue: #2563eb;
      --green: #047857;
      --amber: #b45309;
      --red: #b91c1c;
      --violet: #6d28d9;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main { max-width: 1180px; margin: 0 auto; padding: 28px 20px 48px; }
    header {
      display: grid;
      gap: 16px;
      padding: 28px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    h1, h2, h3 { margin: 0; line-height: 1.2; }
    h1 { font-size: 28px; }
    h2 { font-size: 18px; margin-bottom: 14px; }
    h3 { font-size: 15px; }
    section { margin-top: 18px; padding: 22px; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0; white-space: nowrap; }
    /* Design pass 2026-07-02: tabelas largas rolam horizontalmente em vez de
       esmagar colunas em células de 20px quebrando letra a letra. */
    .table-wrap { overflow-x: auto; }
    .table-wrap table { min-width: 640px; }
    .table-wrap td { min-width: 72px; }
    code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    pre { overflow: auto; padding: 14px; background: #0f172a; color: #e2e8f0; border-radius: 8px; }
    .muted { color: var(--muted); }
    .summary-grid, .metric-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
    .kv-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
    .summary-card, .metric-row {
      padding: 14px;
      background: var(--surface-soft);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .kv-card {
      padding: 12px;
      background: var(--surface-soft);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
    }
    .kv-card span, .detail-list dt { display: block; color: var(--muted); font-size: 12px; }
    .kv-card strong { display: block; margin-top: 4px; overflow-wrap: anywhere; }
    .summary-card span, .metric-row span { display: block; color: var(--muted); font-size: 12px; }
    .summary-card strong, .metric-row strong { display: block; margin-top: 4px; font-size: 18px; }
    .detail-list { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); margin: 0; }
    .detail-list div { min-width: 0; }
    .detail-list dd { margin: 2px 0 0; overflow-wrap: anywhere; }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: var(--surface-soft);
      color: var(--muted);
      border: 1px solid var(--line);
    }
    .ok { color: var(--green); background: #ecfdf5; border-color: #a7f3d0; }
    .bad { color: var(--red); background: #fef2f2; border-color: #fecaca; }
    .neutral { color: var(--muted); }
    .risk-low { color: var(--green); background: #ecfdf5; border-color: #a7f3d0; }
    .risk-medium { color: var(--amber); background: #fffbeb; border-color: #fde68a; }
    .risk-high { color: var(--red); background: #fef2f2; border-color: #fecaca; }
    .bar { position: relative; display: block; min-width: 96px; height: 22px; overflow: hidden; border-radius: 999px; background: #e2e8f0; border: 1px solid #cbd5e1; }
    .bar span { position: absolute; inset: 0 auto 0 0; display: block; background: #93c5fd; }
    .bar em { position: relative; z-index: 1; display: grid; place-items: center; height: 100%; font-style: normal; font-size: 12px; font-weight: 800; color: #172033; }
    .score-stack { display: grid; gap: 6px; min-width: 150px; }
    .score-row { display: grid; grid-template-columns: 82px 1fr; gap: 8px; align-items: center; }
    .score-row > span { color: var(--muted); font-size: 12px; }
    .rich-list { display: grid; gap: 8px; margin: 0; padding-left: 18px; }
    .json-appendix { margin-top: 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-soft); }
    .json-appendix summary { cursor: pointer; padding: 12px 14px; font-weight: 800; }
    .json-appendix pre { margin: 0; border-radius: 0 0 8px 8px; }
    .dag-svg-wrap { overflow-x: auto; padding: 12px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 8px; }
    .dag-svg { display: block; width: 100%; min-width: 680px; height: auto; }
    .node-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
    .node-card { padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
    .node-card.critical { border-color: #93c5fd; box-shadow: inset 4px 0 0 var(--blue); }
    .node-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
    .node-id { font-weight: 800; color: var(--blue); }
    dl { display: grid; gap: 8px; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 12px 0; }
    dt { color: var(--muted); font-size: 12px; }
    dd { margin: 2px 0 0; overflow-wrap: anywhere; }
    .path { list-style: none; display: grid; gap: 10px; margin: 0; padding: 0; }
    .path li { display: grid; grid-template-columns: 32px 1fr auto; gap: 10px; align-items: center; padding: 10px; background: var(--surface-soft); border-radius: 8px; }
    .step-index { display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: var(--blue); color: white; font-weight: 800; }
    .criteria { display: grid; gap: 10px; margin: 0; padding-left: 18px; }
    .criteria span { display: block; color: var(--muted); }
    .footer-note { margin-top: 20px; color: var(--muted); font-size: 12px; }
    @media (max-width: 720px) {
      main { padding: 16px 12px 32px; }
      header, section { padding: 16px; }
      h1 { font-size: 22px; }
      table { display: block; overflow-x: auto; }
      dl { grid-template-columns: 1fr; }
      .path li { grid-template-columns: 32px 1fr; }
      .path small { grid-column: 2; }
    }
    ${report.renderMegabrainNeelStyles()}
  </style>
</head>
<body class="megabrain-report plan-report" data-visual-contract="megabrain-neel-offline">
  <main>
    <header class="report-hero">
      <div class="hero-content">
        <p class="hero-kicker">MEGABRAIN DS / Orquestrador Global / Offline HTML</p>
        <h1>${escapeHtml(planId)}</h1>
        <p class="hero-lead">${escapeHtml(demand)}</p>
      </div>
      ${(() => {
        // KPIs do hero: só renderiza cards com dado REAL (honest-empty).
        const signals = [
          { label: 'Próxima ação', value: nextAction },
          { label: 'Executor', value: handoff.next_action_executor },
          { label: 'Caminho crítico', value: criticalPathIds.length ? `${criticalPathIds.length} nós${(plan.dag && plan.dag.critical_path_duration_minutes) ? ` · ${plan.dag.critical_path_duration_minutes}min` : ''}` : null },
          { label: 'Routing', value: routing.engine ? `${routing.engine} · ${asArray(routing.blocked_nodes).length} blockers` : (routing.strategy || null) },
        ].filter((s) => s.value);
        const summary = [
          { label: 'Domínio', value: parsed.primary_domain },
          { label: 'Modo', value: (plan.demand && plan.demand.mode) || parsed.complexity },
          { label: 'Score', value: formatScore(plan.quality_score) },
          { label: 'Custo estimado', value: resource.total_cost_usd != null ? `$${resource.total_cost_usd}` : null },
          { label: 'Wall time', value: wallTime },
          { label: 'Nós', value: nodes.length ? String(nodes.length) : null },
        ].filter((s) => s.value);
        const card = (cls) => (s) => `<div class="${cls}"><span>${escapeHtml(s.label)}</span><strong>${escapeHtml(String(s.value))}</strong></div>`;
        return `${signals.length ? `<div class="hero-signal-grid">${signals.map(card('signal-card')).join('\n        ')}</div>` : ''}
      ${summary.length ? `<div class="summary-grid">${summary.map(card('summary-card')).join('\n        ')}</div>` : ''}`;
      })()}
    </header>

    ${sectionIf('Demanda Parseada', [demandGrid, elicitations.length ? `<h3>Elicitações</h3>${elicitationTable}` : ''].filter(Boolean).join('\n      '))}

    ${sectionIf('Discovery de Capabilities', [discoveryGrid, discoveryNote, discoverySources].filter(Boolean).join('\n      '))}

    ${sectionIf('Próxima Ação', nextAction ? `<p><strong>${escapeHtml(nextAction)}</strong></p>${handoff.next_action_executor ? `<p class="muted">Executor: ${escapeHtml(handoff.next_action_executor)}</p>` : ''}` : '')}

    <section>
      <h2>Caminho Crítico</h2>
      <ol class="path">${criticalPathItems || '<li><span class="step-index">-</span><span>Nenhum caminho crítico declarado.</span></li>'}</ol>
    </section>

    <section>
      <h2>Diagrama do DAG</h2>
      <div class="dag-svg-wrap">${dagSvg}</div>
    </section>

    <section>
      <h2>Nós do DAG</h2>
      <div class="node-grid">${nodeCards}</div>
    </section>

    <section>
      <h2>Detalhe dos Nós</h2>
      ${nodeDetailTable}
    </section>

    ${sectionIf('Dependências', edgeTable)}

    <section>
      <h2>Grupos Paralelos</h2>
      ${parallelGroupTable}
    </section>

    <section>
      <h2>Capabilities Selecionadas</h2>
      ${capabilityTable}
    </section>

    <section>
      <h2>Recursos e Custo</h2>
      ${resourceGrid}
    </section>

    <section>
      <h2>Riscos Principais</h2>
      <table>
        <thead><tr><th>RPN</th><th>Nó</th><th>Descrição</th><th>Mitigação</th></tr></thead>
        <tbody>${riskRows || '<tr><td colspan="4">Nenhum risco principal declarado.</td></tr>'}</tbody>
      </table>
    </section>

    <section>
      <h2>Pre-Mortem</h2>
      ${preMortemContent}
    </section>

    <section>
      <h2>Critérios de Sucesso</h2>
      <ul class="criteria">${criteriaItems}</ul>
    </section>

    <section>
      <h2>Hipóteses Refutáveis</h2>
      ${report.renderList(assumptions, 'Nenhuma hipótese refutável declarada.')}
    </section>

    ${sectionIf('Governança', (() => {
      // Adaptativo: itera as chaves REAIS do constitutional_compliance —
      // valores booleanos viram pass/fail, strings entram como estão.
      const entries = Object.entries(compliance);
      if (!entries.length) return '';
      const cards = entries.map(([key, value]) => {
        const text = typeof value === 'boolean' ? (value ? 'pass' : 'fail') : String(value);
        const cls = typeof value === 'boolean' ? (value ? 'ok' : 'bad') : gateClass(value);
        return `<div class="summary-card"><span>${escapeHtml(titleizeKey(key))}</span><strong class="pill ${cls}">${escapeHtml(text)}</strong></div>`;
      });
      return `<div class="summary-grid">${cards.join('\n        ')}</div>`;
    })())}

    ${sectionIf('Qualidade e Routing', (() => {
      const rows = [qualityRows];
      if (routing.engine) rows.push(`<div class="metric-row"><span>Routing Engine</span><strong>${escapeHtml(routing.engine)}</strong></div>`);
      if (routing.strategy) rows.push(`<div class="metric-row"><span>Estratégia</span><strong>${escapeHtml(routing.strategy)}</strong></div>`);
      if (asArray(routing.blocked_nodes).length) rows.push(`<div class="metric-row"><span>Blockers</span><strong>${asArray(routing.blocked_nodes).length}</strong></div>`);
      const body = rows.filter(Boolean).join('\n        ');
      return body.trim() ? `<div class="metric-grid">${body}</div>` : '';
    })())}

    ${sectionIf('Handoff Completo', handoffDetails)}

    ${sectionIf('Auditoria', (() => {
      // Adaptativo: renderiza as chaves reais do audit (arrays viram lista).
      const entries = Object.entries(audit).filter(([, v]) => v !== null && v !== undefined && v !== '');
      const base = entries.map(([key, value]) => ({
        label: titleizeKey(key),
        value: Array.isArray(value) ? value.join(', ') : (typeof value === 'object' ? JSON.stringify(value) : String(value)),
      }));
      if (plan.created_by) base.push({ label: 'Criado por', value: plan.created_by });
      if (plan.created_at) base.push({ label: 'Criado em', value: plan.created_at });
      return report.renderDefinitionList(base);
    })())}

    <section>
      <h2>Mermaid Fonte</h2>
      <pre>${escapeHtml(renderMermaid(plan))}</pre>
    </section>

    <section>
      <h2>Apêndice Bruto</h2>
      ${report.renderJsonDetails('Abrir plan.json completo', plan)}
    </section>

    <p class="footer-note">Gerado por render-plan.js. HTML standalone, sem assets externos.<br>${report.renderMegabrainFooterTag()}</p>
  </main>
</body>
</html>
`.replace(/[ \t]+$/gm, '');
}

function render(plan, format) {
  switch (format) {
    case 'md': return renderMarkdown(plan);
    case 'mermaid': return renderMermaid(plan);
    case 'json': return renderJSON(plan);
    case 'html': return renderHtml(plan);
    default: throw new Error(`unknown format: ${format}`);
  }
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.plan) {
    console.error('Usage: render-plan.js <plan.yaml> [--format md|mermaid|json|html] [--output <path>]');
    process.exit(2);
  }

  const planSrc = fs.readFileSync(args.plan, 'utf8');
  const plan = parseYAML(planSrc);
  if (!plan) { console.error('Failed to parse plan YAML'); process.exit(2); }

  const out = render(plan, args.format);
  if (args.output) {
    fs.writeFileSync(args.output, out);
    console.error(`Wrote ${args.output}`);
  } else {
    process.stdout.write(out);
    if (!out.endsWith('\n')) process.stdout.write('\n');
  }
}

if (require.main === module) main();

module.exports = { render, renderMarkdown, renderMermaid, renderJSON, renderHtml, renderDagSvg, escapeHtml };
