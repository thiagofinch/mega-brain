#!/usr/bin/env node
// SYN-14: Boot time captured before ANY require — measures hook cold start
const _BOOT_TIME = process.hrtime.bigint();
'use strict';

/**
 * SYNAPSE Hook Entry Point — UserPromptSubmit
 *
 * Thin wrapper that reads JSON from stdin, delegates to SynapseEngine,
 * and writes <synapse-rules> context to stdout.
 *
 * - Silent exit on missing .synapse/ directory
 * - Silent exit on any error (never blocks the user prompt)
 * - All errors logged to stderr with [synapse-hook] prefix
 * - 5s safety timeout as defense-in-depth
 *
 * @module synapse-engine-hook
 */

const path = require('path');
const { resolveHookRuntime, buildHookOutput, finalizeHookSession, detectActivationSkill, runActivationPipeline } = require(
  path.join(__dirname, '..', '..', 'mega-brain-core', 'core', 'synapse', 'runtime', 'hook-runtime.js'),
);

/** Safety timeout (ms) — defense-in-depth; Claude Code also manages hook timeout. */
const HOOK_TIMEOUT_MS = 5000;

/**
 * Read all data from stdin as a JSON object.
 * @returns {Promise<object>} Parsed JSON input
 */
function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('error', (e) => reject(e));
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => {
      try { resolve(JSON.parse(data)); }
      catch (e) { reject(e); }
    });
  });
}

/** Main hook execution pipeline. */
async function main() {
  const input = await readStdin();
  const runtime = resolveHookRuntime(input);
  if (!runtime) return;

  const result = await runtime.engine.process(input.prompt, runtime.session, { _hookBootTime: _BOOT_TIME });
  finalizeHookSession(runtime, input, result);

  // Story 117.3: Deterministic Agent Activation — run pipeline IN the hook
  // CRITICAL: activation data MUST come BEFORE synapse-rules in the output.
  // Claude Code truncates hook output at 10,000 chars — activation context
  // must be in the first 5KB to survive truncation.
  let xml = '';
  const skill = detectActivationSkill(input.prompt, input.cwd, runtime.bridgeData);
  if (skill) {
    const activationXml = await runActivationPipeline(skill.agentId, input.cwd);
    if (activationXml) {
      xml = activationXml;
    }
  }
  // Append synapse-rules AFTER activation data
  if (result.xml) {
    xml = xml ? `${xml}\n${result.xml}` : result.xml;
  }

  process.stdout.write(JSON.stringify(buildHookOutput(xml)));
}

/**
 * Safely exit the process — no-op inside Jest workers to prevent worker crashes.
 * @param {number} code - Exit code
 */
function safeExit(code) {
  if (process.env.JEST_WORKER_ID) return;
  process.exit(code);
}

/** Entry point runner — sets safety timeout and executes main(). */
function run() {
  const timer = setTimeout(() => safeExit(0), HOOK_TIMEOUT_MS);
  timer.unref();
  main().catch((err) => {
    console.error(`[synapse-hook] ${err.message}`);
    safeExit(0);
  });
}

if (require.main === module) run();

module.exports = { readStdin, main, run, HOOK_TIMEOUT_MS };
