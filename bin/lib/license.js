// bin/lib/license.js
// Manages ~/.mega-brain/license.json — local cache of license state

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

const LICENSE_DIR = join(homedir(), '.mega-brain');
const LICENSE_PATH = join(LICENSE_DIR, 'license.json');
const REVALIDATION_DAYS = 7;
const GRACE_DAYS = 7;

export function readLicense() {
  if (!existsSync(LICENSE_PATH)) return null;
  try {
    return JSON.parse(readFileSync(LICENSE_PATH, 'utf-8'));
  } catch {
    return null;
  }
}

export function writeLicense(data) {
  mkdirSync(LICENSE_DIR, { recursive: true });
  writeFileSync(LICENSE_PATH, JSON.stringify(data, null, 2));
}

export function removeLicense() {
  if (existsSync(LICENSE_PATH)) {
    writeFileSync(LICENSE_PATH, JSON.stringify({ tier: 'community', deactivated_at: new Date().toISOString() }, null, 2));
  }
}

export function maskEmail(email) {
  const at = email.indexOf('@');
  if (at <= 0) return '***';
  return email[0] + '***' + email.slice(at);
}

export function getLicenseState(license) {
  if (!license) return 'NOT_FOUND';
  if (license.tier === 'community') return 'COMMUNITY';
  if (!license.validated_at) return 'INACTIVE';

  const validated = new Date(license.validated_at);
  const now = new Date();
  const daysSince = (now - validated) / (1000 * 60 * 60 * 24);

  if (daysSince <= REVALIDATION_DAYS) return 'ACTIVE';
  if (daysSince <= REVALIDATION_DAYS + GRACE_DAYS) return 'GRACE';
  return 'EXPIRED';
}

export function needsRevalidation(license) {
  if (!license || license.tier === 'community') return false;
  const state = getLicenseState(license);
  return state === 'GRACE' || state === 'EXPIRED';
}

export { LICENSE_DIR, LICENSE_PATH, REVALIDATION_DAYS, GRACE_DAYS };
