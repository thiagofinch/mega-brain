#!/usr/bin/env node
/**
 * plan-to-sdc.js — materialize a governed orchestration plan into an SDC package.
 *
 * Story: OG-88.9
 * Output: outputs/sdc/{plan_id}/manifest.yaml + SOP/epic/stories/handoffs.
 *
 * This script never executes downstream agents. It emits Draft material only.
 */
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const REPO_ROOT = path.resolve(__dirname, '../../..');
const DEFAULT_OUTPUT_ROOT = path.join(REPO_ROOT, 'outputs/sdc');

function parseArgs(argv) {
  const args = {
    plan: null,
    out: null,
    createdAt: new Date().toISOString(),
    force: false,
    dryRun: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--out') args.out = path.resolve(argv[++i]);
    else if (arg === '--created-at') args.createdAt = argv[++i];
    else if (arg === '--force') args.force = true;
    else if (arg === '--dry-run') args.dryRun = true;
    else if (!args.plan) args.plan = path.resolve(arg);
    else throw new Error(`Unexpected argument: ${arg}`);
  }

  if (!args.plan) {
    throw new Error('Usage: plan-to-sdc.js <plan.yaml|plan.json> [--out <dir>] [--created-at <iso>] [--force] [--dry-run]');
  }

  return args;
}

function loadStructuredFile(filePath) {
  const src = fs.readFileSync(filePath, 'utf8');
  if (filePath.endsWith('.json')) return { src, data: JSON.parse(src) };
  return { src, data: yaml.load(src) };
}

function slugify(value) {
  return String(value || 'item')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-') || 'item';
}

function hashContent(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function selectedCapabilityById(plan) {
  return new Map((plan.selected_capabilities || []).map((capability) => [capability.id, capability]));
}

function getNodeWorkflowIds(plan) {
  const selected = selectedCapabilityById(plan);
  const workflowIds = [];
  for (const node of ((plan.dag || {}).nodes || [])) {
    if (node.source_workflow) workflowIds.push(node.source_workflow);
    const capability = selected.get(node.capability) || selected.get(node.capability_ref);
    if (capability && capability.type === 'workflow') workflowIds.push(capability.id);
  }
  return unique(workflowIds);
}

function classifyMode(plan) {
  const nodes = ((plan.dag || {}).nodes || []);
  const workflowIds = getNodeWorkflowIds(plan);
  if (nodes.length <= 1) {
    return {
      mode: 'task_solo',
      workflow_ids: workflowIds,
      rationale: 'Plano possui um único node executável; materializar uma unidade SDC draft.',
    };
  }
  if (workflowIds.length === 1) {
    return {
      mode: 'workflow_slice',
      workflow_ids: workflowIds,
      rationale: 'Plano possui múltiplos nodes rastreados ao mesmo workflow de origem; materializar slice SDC preservando dependências.',
    };
  }
  return {
    mode: 'workflow_synthesis',
    workflow_ids: workflowIds,
    rationale: 'Plano possui múltiplos nodes e capabilities de workflows distintos; materializar síntese SDC sem executar downstream.',
  };
}

function storyIdFor(planSlug, index) {
  return `SDC-${planSlug.toUpperCase()}-${String(index + 1).padStart(2, '0')}`;
}

function executorForNode(node) {
  const capability = String(node.capability || node.capability_ref || '');
  const label = String(node.label || '').toLowerCase();
  if (/push|pull request|deploy|release/.test(label)) return '@devops';
  if (/qa|validar|review|auditar|audit/.test(label)) return '@qa';
  if (/arquitet|architecture|schema|contrato|contract/.test(label)) return '@architect';
  if (/tracking|pixel|utm|campanha|campaign|copy|landing|implementar|configurar|escrever|preparar/.test(label) || capability) {
    return '@dev';
  }
  return '@dev';
}

function adapterForNode(node, modeClassification) {
  if (executorForNode(node) === '@devops') return 'manual';
  if (modeClassification.mode === 'task_solo') return 'megabrain-example-squad';
  return 'codex-subagents';
}

function buildDependencyMap(plan, nodeToStoryId) {
  const dependencies = new Map();
  for (const node of ((plan.dag || {}).nodes || [])) dependencies.set(node.id, []);
  for (const edge of ((plan.dag || {}).edges || [])) {
    if (!dependencies.has(edge.to)) dependencies.set(edge.to, []);
    const fromStory = nodeToStoryId.get(edge.from);
    if (fromStory) dependencies.get(edge.to).push(fromStory);
  }
  return dependencies;
}

function buildUnits(plan, packageRoot, modeClassification) {
  const planSlug = slugify(plan.plan_id);
  const nodes = ((plan.dag || {}).nodes || []);
  const nodeToStoryId = new Map(nodes.map((node, index) => [node.id, storyIdFor(planSlug, index)]));
  const dependencies = buildDependencyMap(plan, nodeToStoryId);

  return nodes.map((node, index) => {
    const storyId = nodeToStoryId.get(node.id);
    const storyPath = path.join(packageRoot, 'stories', `${String(index + 1).padStart(2, '0')}-${slugify(node.label)}.md`);
    const handoffPath = path.join(packageRoot, 'handoffs', `${String(index + 1).padStart(2, '0')}-${slugify(node.label)}-handoff.yaml`);
    return {
      story_id: storyId,
      node_id: node.id,
      title: node.label || `Executar node ${node.id}`,
      status: 'Draft',
      executor: executorForNode(node),
      qa_gate: '@qa',
      adapter_candidate: adapterForNode(node, modeClassification),
      depends_on: unique(dependencies.get(node.id) || []),
      source_capability: node.capability || node.capability_ref || 'unknown',
      story_path: path.relative(REPO_ROOT, storyPath),
      handoff_path: path.relative(REPO_ROOT, handoffPath),
      _node: node,
    };
  });
}

function markdownList(items, fallback = '- N/A') {
  if (!items || items.length === 0) return fallback;
  return items.map((item) => `- ${item}`).join('\n');
}

function renderIdeaSop(plan, manifest) {
  return `# Idea SOP — ${plan.plan_id}

## Demand

${plan.demand && plan.demand.raw ? plan.demand.raw : 'N/A'}

## Mode

- Mode: ${manifest.mode_classification.mode}
- Rationale: ${manifest.mode_classification.rationale}

## Execution Boundary

- Auto execute: ${manifest.execution_policy.auto_execute}
- Approval required: ${manifest.execution_policy.approval_required}
- Do not execute until:
${markdownList(manifest.execution_policy.do_not_execute_until)}

## DAG Summary

- Nodes: ${manifest.audit.node_count}
- Edges: ${manifest.audit.edge_count}
- Critical path: ${(((plan.dag || {}).critical_path) || []).join(' -> ') || 'N/A'}

## SDC Units

${manifest.sdc_units.map((unit) => `### ${unit.story_id} — ${unit.title}

- Node: ${unit.node_id}
- Executor: ${unit.executor}
- QA gate: ${unit.qa_gate}
- Adapter candidate: ${unit.adapter_candidate}
- Depends on: ${unit.depends_on.length ? unit.depends_on.join(', ') : 'none'}
- Source capability: ${unit.source_capability}
`).join('\n')}
`;
}

function renderEpic(plan, manifest) {
  return `# Epic Draft — ${plan.plan_id}

## Objective

Materializar o plano ${plan.plan_id} em unidades SDC revisáveis antes de execução.

## Scope

${plan.demand && plan.demand.raw ? plan.demand.raw : 'N/A'}

## Stories

${manifest.sdc_units.map((unit) => `- ${unit.story_id}: ${unit.title} (${unit.status})`).join('\n')}

## Governance

- Generated by: ${manifest.created_by}
- Execution is blocked until explicit approval.
- This draft must be reviewed by @po before promotion to canonical docs/stories.
`;
}

function renderStory(plan, unit) {
  const node = unit._node;
  return `# ${unit.story_id}: ${unit.title}

## Metadata

\`\`\`yaml
story_id: "${unit.story_id}"
source_plan_id: "${plan.plan_id}"
source_node_id: "${unit.node_id}"
status: Draft
priority: HIGH
complexity: STANDARD
executor: "${unit.executor}"
qa_gate: "${unit.qa_gate}"
deploy_type: none
adapter_candidate: "${unit.adapter_candidate}"
depends_on: ${JSON.stringify(unit.depends_on)}
\`\`\`

## Objetivo

Executar o node \`${unit.node_id}\` do plano \`${plan.plan_id}\`: ${unit.title}.

## Contexto

- Source capability: \`${unit.source_capability}\`
- Capability type: \`${node.capability_type || 'unknown'}\`
- Quality gate: \`${node.quality_gate || 'default-qa'}\`

## Acceptance Criteria

- [ ] AC1: Inputs requeridos estão disponíveis: ${((node.inputs_required || []).join(', ') || 'none')}.
- [ ] AC2: Outputs esperados foram produzidos: ${((node.outputs_produced || []).join(', ') || 'none')}.
- [ ] AC3: Quality gate \`${node.quality_gate || 'default-qa'}\` passou.
- [ ] AC4: Evidências foram registradas antes de qualquer handoff downstream.

## Tasks

- [ ] Validar inputs e constraints do node.
- [ ] Executar a unidade com o executor indicado.
- [ ] Produzir outputs declarados.
- [ ] Rodar QA gate e anexar evidência.

## File List

- [ ] TBD by executor

## Dev Notes

Esta story foi gerada como Draft por \`plan-to-sdc.js\`. Não executar antes de revisão PO.
`;
}

function renderHandoff(plan, unit) {
  return {
    schema_version: '1.0',
    handoff_id: `${slugify(unit.story_id)}-handoff`,
    plan_id: plan.plan_id,
    story_id: unit.story_id,
    node_id: unit.node_id,
    created_by: 'plan-to-sdc',
    executor_agent: unit.executor,
    adapter_candidate: unit.adapter_candidate,
    dag_slice: {
      nodes_to_execute: [unit.node_id],
      scope: 'partial',
      rationale: `Executar somente o node ${unit.node_id} depois dos gates SDC.`,
    },
    authorization: {
      approved_by: null,
      approved_at: null,
      approval_signal: null,
    },
    constraints: [
      {
        type: 'execution',
        rule: 'Do not execute from plan-to-sdc output without PO approval.',
        enforcement: 'blocking',
      },
    ],
    post_execution_action: {
      report_to: '@po',
      artifact_to_produce: 'execution evidence for execution-registry',
      next_handoff: null,
    },
  };
}

function buildManifest(plan, planPath, planSrc, packageRoot, createdAt) {
  const modeClassification = classifyMode(plan);
  const units = buildUnits(plan, packageRoot, modeClassification);
  const packageRootRel = path.relative(REPO_ROOT, packageRoot);
  const manifestRel = path.join(packageRootRel, 'manifest.yaml');

  const publicUnits = units.map(({ _node, ...unit }) => unit);
  const storyRefs = publicUnits.map((unit) => ({
    node_id: unit.node_id,
    story_id: unit.story_id,
    path: unit.story_path,
  }));
  const handoffRefs = publicUnits.map((unit) => ({
    node_id: unit.node_id,
    story_id: unit.story_id,
    path: unit.handoff_path,
  }));

  return {
    schema_version: '1.0',
    package_id: `${slugify(plan.plan_id)}-sdc-package`,
    plan_id: plan.plan_id,
    source_plan_path: path.relative(REPO_ROOT, planPath),
    created_by: 'plan-to-sdc',
    created_at: createdAt,
    mode_classification: modeClassification,
    outputs: {
      root: packageRootRel,
      manifest: manifestRel,
      idea_sop: path.join(packageRootRel, 'idea-sop.md'),
      epic: path.join(packageRootRel, 'epic.md'),
      stories: storyRefs,
      handoffs: handoffRefs,
    },
    sdc_units: publicUnits,
    execution_policy: {
      auto_execute: false,
      approval_required: true,
      allowed_adapters: unique(publicUnits.map((unit) => unit.adapter_candidate).concat(['manual'])),
      do_not_execute_until: [
        'PO approves the generated SDC package',
        'Executor validates each generated story draft',
        'Execution adapter is selected from execution-adapter-registry',
      ],
    },
    audit: {
      source_plan_hash: hashContent(planSrc),
      node_count: ((plan.dag || {}).nodes || []).length,
      edge_count: ((plan.dag || {}).edges || []).length,
      heuristics_applied: ['PLAN-TO-SDC', 'DAG-NODE-TO-STORY', 'NO-AUTO-EXECUTE'],
    },
    _units_with_nodes: units,
  };
}

function assertWritableOutput(packageRoot, force) {
  if (fs.existsSync(packageRoot) && !force) {
    throw new Error(`Output directory already exists. Use --force to overwrite: ${packageRoot}`);
  }
}

function writePackage(plan, manifestWithInternals, packageRoot, dryRun) {
  const { _units_with_nodes: unitsWithNodes, ...manifest } = manifestWithInternals;
  const files = [
    { path: path.join(packageRoot, 'manifest.yaml'), content: yaml.dump(manifest, { lineWidth: 120 }) },
    { path: path.join(packageRoot, 'idea-sop.md'), content: renderIdeaSop(plan, manifest) },
    { path: path.join(packageRoot, 'epic.md'), content: renderEpic(plan, manifest) },
  ];

  for (const unit of unitsWithNodes) {
    files.push({
      path: path.resolve(REPO_ROOT, unit.story_path),
      content: renderStory(plan, unit),
    });
    files.push({
      path: path.resolve(REPO_ROOT, unit.handoff_path),
      content: yaml.dump(renderHandoff(plan, unit), { lineWidth: 120 }),
    });
  }

  if (!dryRun) {
    fs.rmSync(packageRoot, { recursive: true, force: true });
    for (const file of files) {
      fs.mkdirSync(path.dirname(file.path), { recursive: true });
      fs.writeFileSync(file.path, file.content);
    }
  }

  return { manifest, files: files.map((file) => path.relative(REPO_ROOT, file.path)) };
}

function materialize(args) {
  const { src, data: plan } = loadStructuredFile(args.plan);
  if (!plan || !plan.plan_id) throw new Error('Input plan must include plan_id.');
  if (!((plan.dag || {}).nodes || []).length) throw new Error('Input plan must include at least one dag node.');

  const packageRoot = args.out || path.join(DEFAULT_OUTPUT_ROOT, slugify(plan.plan_id));
  assertWritableOutput(packageRoot, args.force || args.dryRun);
  const manifest = buildManifest(plan, args.plan, src, packageRoot, args.createdAt);
  const result = writePackage(plan, manifest, packageRoot, args.dryRun);

  return {
    ok: true,
    dry_run: args.dryRun,
    package_id: result.manifest.package_id,
    manifest_path: result.manifest.outputs.manifest,
    files: result.files,
  };
}

function main() {
  try {
    const result = materialize(parseArgs(process.argv));
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
    process.exit(1);
  }
}

if (require.main === module) main();

module.exports = {
  parseArgs,
  slugify,
  classifyMode,
  buildManifest,
  materialize,
};
