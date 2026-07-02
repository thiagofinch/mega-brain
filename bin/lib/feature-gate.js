// bin/lib/feature-gate.js
// Central feature gate: determines what features are available based on license state.

import { readLicense, getLicenseState } from './license.js';
import { isProInstalled } from '../utils/pro-detector.js';

const FEATURES = {
  knowledge:  { name: 'Knowledge Base',   description: 'Dossiers, sources, DNAs',            tier: 'pro' },
  playbooks:  { name: 'Playbooks',        description: 'Playbooks operacionais',              tier: 'pro' },
  persons:    { name: 'Mind Clones',       description: 'agents/persons/ (Hormozi, Cole, etc.)', tier: 'pro' },
  cargo:      { name: 'C-Level Agents',    description: 'agents/cargo/ (CRO, CFO, CMO)',      tier: 'pro' },
  processing: { name: 'Processing Data',   description: 'Conteudo processado',                 tier: 'pro' },
  cli:        { name: 'CLI + Skills',      description: 'Comandos, skills, hooks, rules',      tier: 'community' },
  templates:  { name: 'Templates',         description: 'Agent templates, protocols',           tier: 'community' },
  structure:  { name: 'Structure',         description: 'Diretorios, exemplos',                tier: 'community' },
};

export function getTier() {
  const license = readLicense();
  const state = getLicenseState(license);
  if (state === 'ACTIVE' || state === 'GRACE') return 'pro';
  return 'community';
}

export function isActive() {
  const state = getLicenseState(readLicense());
  return state === 'ACTIVE' || state === 'GRACE';
}

export function canUse(featureKey) {
  const feature = FEATURES[featureKey];
  if (!feature) return false;
  if (feature.tier === 'community') return true;
  return isActive();
}

export function listFeatures() {
  const tier = getTier();
  return Object.entries(FEATURES).map(([key, feat]) => ({
    key,
    ...feat,
    available: feat.tier === 'community' || tier === 'pro',
  }));
}

export { FEATURES };
