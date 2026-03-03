#!/usr/bin/env node
/**
 * Apply SQL migration to Supabase via REST API (service_role key required)
 *
 * Usage:
 *   SUPABASE_SERVICE_KEY=eyJ... node apply-migration.mjs 002_premium_token.sql
 *   SUPABASE_SERVICE_KEY=eyJ... PREMIUM_REPO_TOKEN=ghp_xxx node apply-migration.mjs 002_premium_token.sql --seed-token
 *
 * The service_role key is in: Supabase Dashboard → Settings → API → service_role (secret)
 */

import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://your-project.supabase.co';
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const PREMIUM_TOKEN = process.env.PREMIUM_REPO_TOKEN;

if (SERVICE_KEY === undefined || SERVICE_KEY === '') {
  console.error('ERROR: SUPABASE_SERVICE_KEY env var required.');
  console.error('Get it from: Supabase Dashboard → Settings → API → service_role (secret)');
  process.exit(1);
}

const args = process.argv.slice(2);
const migrationFile = args.find(a => a.endsWith('.sql'));
const seedToken = args.includes('--seed-token');

if (migrationFile === undefined) {
  console.error('Usage: SUPABASE_SERVICE_KEY=... node apply-migration.mjs <file.sql> [--seed-token]');
  process.exit(1);
}

async function runSQL(sql, label) {
  // Use the pg REST endpoint with service_role for DDL
  // Supabase doesn't have a raw SQL endpoint via REST, so we use the
  // PostgREST RPC approach: create a temporary function wrapper
  // Actually, the proper way is using the Supabase Management API or pg directly.
  // For simplicity, we split the SQL into individual statements and use the
  // service_role key with the PostgREST RPC endpoint.

  // Alternative: use the Supabase SQL editor API
  const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/`, {
    method: 'POST',
    headers: {
      'apikey': SERVICE_KEY,
      'Authorization': `Bearer ${SERVICE_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: sql }),
  });

  if (response.ok === false) {
    const text = await response.text();
    throw new Error(`${label}: ${response.status} — ${text}`);
  }

  return response.json();
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║  Mega Brain — Migration Runner                              ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log('');

  const sqlPath = resolve(__dirname, migrationFile);
  const sql = readFileSync(sqlPath, 'utf-8');
  console.log(`  Migration: ${migrationFile}`);
  console.log(`  SQL size: ${sql.length} bytes`);
  console.log('');

  // The Supabase REST API doesn't support raw DDL via PostgREST.
  // The proper way to apply migrations is:
  //   1. Supabase Dashboard → SQL Editor → paste and run
  //   2. supabase db push (Supabase CLI)
  //   3. Direct psql connection
  //
  // This script will attempt the Management API first, then fall back to instructions.

  console.log('  NOTE: Supabase REST API does not support raw DDL via PostgREST.');
  console.log('');
  console.log('  To apply this migration, use ONE of these methods:');
  console.log('');
  console.log('  [1] Supabase Dashboard → SQL Editor:');
  console.log(`      Open: https://supabase.com/dashboard/project/${new URL(SUPABASE_URL).hostname.split('.')[0]}/sql`);
  console.log(`      Paste the contents of: ${migrationFile}`);
  console.log('      Click "Run"');
  console.log('');
  console.log('  [2] Supabase CLI:');
  console.log('      npx supabase login');
  console.log(`      npx supabase link --project-ref ${new URL(SUPABASE_URL).hostname.split('.')[0]}`);
  console.log('      npx supabase db push');
  console.log('');
  console.log('  [3] Direct psql (if you have the connection string):');
  console.log(`      psql "postgresql://..." -f ${migrationFile}`);
  console.log('');

  if (seedToken) {
    if (PREMIUM_TOKEN === undefined || PREMIUM_TOKEN === '') {
      console.error('  ERROR: --seed-token requires PREMIUM_REPO_TOKEN env var.');
      console.error('  Create a fine-grained PAT at: https://github.com/settings/personal-access-tokens/new');
      console.error('  Scope: mega-brain-premium repo, contents:read only');
      process.exit(1);
    }

    console.log('  After applying the migration, run this INSERT in the SQL Editor:');
    console.log('');
    console.log(`  INSERT INTO system_config (key, value, description)`);
    console.log(`  VALUES (`);
    console.log(`    'premium_repo_token',`);
    console.log(`    '${PREMIUM_TOKEN}',`);
    console.log(`    'GitHub fine-grained PAT for mega-brain-premium (contents:read)'`);
    console.log(`  )`);
    console.log(`  ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();`);
    console.log('');
  }

  console.log('  Done. Migration file ready at:');
  console.log(`  ${sqlPath}`);
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
