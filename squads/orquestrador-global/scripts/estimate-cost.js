#!/usr/bin/env node
/**
 * estimate-cost.js — deterministic cost estimator
 *
 * Estimates plan execution cost in USD using pricing-snapshot.yaml.
 * Story: STORY-PA-4.2
 * Consumer: plan-architect (PA-6.1) pre-flight; PA-6.2 budget cap B1 ($150)
 */
'use strict';

const fs = require('fs');
const path = require('path');

const PRICING_PATH = path.resolve(__dirname, '../data/pricing-snapshot.yaml');

function parseArgs(argv) {
  const args = { plan: null, model_override: null, verbose: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--model') args.model_override = argv[++i];
    else if (a === '--verbose') args.verbose = true;
    else if (!args.plan) args.plan = a;
  }
  return args;
}

function parseYAML(src) {
  try { return require('js-yaml').load(src); }
  catch { /* fallback */ return null; }
}

function loadPricing() {
  const src = fs.readFileSync(PRICING_PATH, 'utf8');
  const parsed = parseYAML(src);
  if (!parsed || !parsed.models) {
    throw new Error('pricing-snapshot.yaml malformed or missing models');
  }
  return parsed;
}

// ── Token estimation per node type ────────────────────────────────────────────
const TOKEN_ESTIMATES = {
  agent: { input: 4000, output: 2000 },
  squad: { input: 8000, output: 4000 },
  workflow: { input: 5000, output: 3000 },
  task: { input: 1500, output: 800 },
  skill: { input: 6000, output: 3500 },
  template: { input: 200, output: 100 },
};

function estimateNodeTokens(node) {
  const t = node.capability_type || 'task';
  return TOKEN_ESTIMATES[t] || TOKEN_ESTIMATES.task;
}

// STORY-LC-3 / ADR-LC-002 D7 — a loop node costs its loop budget, not a single task.
const LOOP_NODE_DEFAULT_BUDGET = 200000;

function estimateNodeCost(node, pricing, defaultModel) {
  const tier = node.model_tier || defaultModel || 'sonnet';
  let tokens;
  if (node.execution_kind === 'loop') {
    // Hardening: a non-numeric / non-finite / <= 0 budget_tokens must NOT produce a NaN/negative estimate — fall back.
    const raw = node.loop_hint && node.loop_hint.budget_tokens;
    const budget = (typeof raw === 'number' && Number.isFinite(raw) && raw > 0) ? raw : LOOP_NODE_DEFAULT_BUDGET;
    tokens = { input: Math.floor(budget * 0.6), output: Math.floor(budget * 0.4), loop: true };
  } else if (node.estimated_cost_tokens) {
    tokens = { input: Math.floor(node.estimated_cost_tokens * 0.6), output: Math.floor(node.estimated_cost_tokens * 0.4) };
  } else {
    tokens = estimateNodeTokens(node);
  }
  const model = pricing.models[tier];
  if (!model) {
    return { tokens, tier, cost_usd: null, error: `unknown model tier: ${tier}` };
  }
  const cost = (tokens.input * model.input_per_1k_tokens + tokens.output * model.output_per_1k_tokens) / 1000;
  return { tokens, tier, cost_usd: cost };
}

function estimatePlan(plan, pricing, override) {
  const nodes = (plan.dag && plan.dag.nodes) || [];
  const breakdown = nodes.map(n => ({
    id: n.id,
    capability: n.capability,
    capability_type: n.capability_type,
    ...estimateNodeCost(n, pricing, override),
  }));
  const total = breakdown.reduce((s, n) => s + (n.cost_usd || 0), 0);
  return {
    plan_id: plan.plan_id || null,
    pricing_snapshot_date: pricing.snapshot_date,
    pricing_snapshot_url: pricing.anthropic_pricing_url_archive,
    nodes_count: nodes.length,
    total_cost_usd: Math.round(total * 100) / 100,
    breakdown,
  };
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.plan) {
    console.error('Usage: estimate-cost.js <plan.yaml> [--model <sonnet|opus|haiku>] [--verbose]');
    process.exit(2);
  }

  const planSrc = fs.readFileSync(args.plan, 'utf8');
  const plan = parseYAML(planSrc);
  if (!plan) { console.error('Failed to parse plan YAML'); process.exit(2); }

  const pricing = loadPricing();
  const result = estimatePlan(plan, pricing, args.model_override);

  if (args.verbose) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(JSON.stringify({
      plan_id: result.plan_id,
      pricing_snapshot_date: result.pricing_snapshot_date,
      total_cost_usd: result.total_cost_usd,
      nodes_count: result.nodes_count,
    }, null, 2));
  }
}

if (require.main === module) main();

module.exports = { estimatePlan, estimateNodeCost, loadPricing, TOKEN_ESTIMATES };
