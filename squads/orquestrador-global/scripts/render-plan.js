#!/usr/bin/env node
/**
 * render-plan.js — deterministic plan renderer
 *
 * Transforms plan YAML to: md (narrative), mermaid (DAG diagram), json (canonical).
 * Pure function: same input → same output.
 *
 * Story: STORY-PA-4.2
 * Consumer: plan-architect (PA-6.1) handoff; humanos (review)
 */
'use strict';

const fs = require('fs');


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
  catch { return null; }
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

function render(plan, format) {
  switch (format) {
    case 'md': return renderMarkdown(plan);
    case 'mermaid': return renderMermaid(plan);
    case 'json': return renderJSON(plan);
    default: throw new Error(`unknown format: ${format}`);
  }
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.plan) {
    console.error('Usage: render-plan.js <plan.yaml> [--format md|mermaid|json] [--output <path>]');
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

module.exports = { render, renderMarkdown, renderMermaid, renderJSON };
