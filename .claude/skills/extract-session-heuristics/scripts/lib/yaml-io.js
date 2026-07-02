/**
 * yaml-io — atomic YAML read/write helpers for the extract-session-heuristics runner.
 *
 * Zero external deps beyond js-yaml (already in the repo).
 * All writes are atomic: write-to-temp + rename.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

function readYaml(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`YAML file not found: ${filePath}`);
  }
  const raw = fs.readFileSync(filePath, 'utf-8');
  try {
    return yaml.load(raw);
  } catch (err) {
    throw new Error(`YAML parse error in ${filePath}: ${err.message}`);
  }
}

function writeYaml(filePath, data, headerLines = []) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  const body = yaml.dump(data, { noRefs: true, sortKeys: false, lineWidth: 100 });
  const header = headerLines.length > 0 ? headerLines.join('\n') + '\n' : '';
  const content = header + body;
  const tmp = `${filePath}.tmp.${process.pid}`;
  fs.writeFileSync(tmp, content);
  fs.renameSync(tmp, filePath);
}

function readYamlOrNull(filePath) {
  try {
    return readYaml(filePath);
  } catch (err) {
    return null;
  }
}

/**
 * Read decision-cards.yaml — the L2 canonical file for a heuristics namespace.
 * Structure: { version, owner, id_prefix, total, last_updated, cards: [...] }
 */
function readDecisionCards(filePath) {
  const data = readYaml(filePath);
  if (!data || !Array.isArray(data.cards)) {
    throw new Error(`Invalid decision-cards.yaml structure in ${filePath}: missing cards array`);
  }
  return data;
}

/**
 * Append new cards to decision-cards.yaml preserving header/preamble.
 * Strategy: read original file as text, find the last card entry, insert new cards
 * before EOF. This preserves hand-edited comments/formatting in the header.
 */
function appendCardsToDecisionCards(filePath, newCards) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`decision-cards.yaml not found: ${filePath}`);
  }
  const original = fs.readFileSync(filePath, 'utf-8');

  // Dump only the new cards as YAML list items (no top-level wrapper)
  const fragments = newCards.map(card => {
    const block = yaml.dump([card], { noRefs: true, sortKeys: false, lineWidth: 100 });
    // yaml.dump wraps with "- id: ..." — already correct list format
    return block.trimEnd();
  });

  // Append with proper spacing
  const appendix = '\n' + fragments.map(f => '  ' + f.split('\n').join('\n  ')).join('\n\n') + '\n';

  // Sanity check via full re-parse after append
  const candidate = original.trimEnd() + appendix;
  try {
    const parsed = yaml.load(candidate);
    if (!parsed || !Array.isArray(parsed.cards)) {
      throw new Error('append produced invalid structure');
    }
  } catch (err) {
    throw new Error(`Append validation failed — YAML round-trip broken: ${err.message}`);
  }

  const tmp = `${filePath}.tmp.${process.pid}`;
  fs.writeFileSync(tmp, candidate);
  fs.renameSync(tmp, filePath);
}

module.exports = {
  readYaml,
  writeYaml,
  readYamlOrNull,
  readDecisionCards,
  appendCardsToDecisionCards,
};
