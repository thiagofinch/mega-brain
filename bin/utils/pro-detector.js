// bin/utils/pro-detector.js
// Detects if Pro content is installed in the current project directory
// and whether the license is active.

import { existsSync, readdirSync } from 'fs';
import { join } from 'path';
import { readLicense, getLicenseState } from '../lib/license.js';

// Premium directories from layer2-manifest.txt
const PRO_INDICATORS = [
  'knowledge/dossiers/persons',
  'knowledge/playbooks',
  'knowledge/dna',
  'agents/persons',
  'agents/cargo',
];

export function isProInstalled(projectRoot = process.cwd()) {
  let foundCount = 0;
  for (const indicator of PRO_INDICATORS) {
    const dirPath = join(projectRoot, indicator);
    if (!existsSync(dirPath)) continue;
    try {
      const entries = readdirSync(dirPath);
      // Directory exists and has more than just .gitkeep
      if (entries.some(e => e !== '.gitkeep')) {
        foundCount++;
      }
    } catch {
      // ignore
    }
  }
  return foundCount >= 2; // At least 2 populated premium dirs
}

export function getProStatus(projectRoot = process.cwd()) {
  const installed = isProInstalled(projectRoot);
  const license = readLicense();
  const state = getLicenseState(license);

  return {
    installed,
    license,
    state,
    tier: license?.tier || 'community',
    email: license?.email || null,
    activatedAt: license?.activated_at || null,
    validatedAt: license?.validated_at || null,
  };
}
