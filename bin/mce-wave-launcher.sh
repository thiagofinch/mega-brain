#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# MCE Wave Launcher — Full Pipeline Orchestration
# ============================================================================
# Executes 4 waves:
#   Wave 0: Hygiene (Python, deterministic)
#   Wave 1: Batch creation (Python, deterministic)
#   Wave 2: MCE extraction (claude -p headless, parallel per entity)
#   Wave 3: Merge & validate (Python, deterministic)
#
# Usage:
#   bash bin/mce-wave-launcher.sh --all                    # Run all waves
#   bash bin/mce-wave-launcher.sh --wave 0                 # Hygiene only
#   bash bin/mce-wave-launcher.sh --wave 2 --max-parallel 5
#   bash bin/mce-wave-launcher.sh --wave 2 --batch 1       # Specific batch
#   bash bin/mce-wave-launcher.sh --status                 # Show status
#   bash bin/mce-wave-launcher.sh --dry-run --all          # Preview all
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs/wave-mce"
STATE_FILE="${ROOT_DIR}/.claude/mission-control/WAVE-STATE.json"
MANIFEST="${ROOT_DIR}/bin/mce-entity-manifest.yaml"

# Defaults
WAVE=""
RUN_ALL=0
DRY_RUN=0
SHOW_STATUS=0
MAX_PARALLEL=3
BATCH_NUM=""
MODEL="sonnet"

usage() {
  cat <<'EOF'
MCE Wave Launcher — Full Pipeline Orchestration

Usage:
  bash bin/mce-wave-launcher.sh [OPTIONS]

Options:
  --all                 Run all waves sequentially (0 → 1 → 2 → 3)
  --wave N              Run specific wave (0, 1, 2, or 3)
  --batch N             Wave 2 only: run specific batch from manifest (1-4)
  --max-parallel N      Wave 2 only: max concurrent claude sessions (default: 3)
  --model MODEL         Wave 2 only: claude model (default: sonnet)
  --dry-run             Preview actions without executing
  --status              Show status of all waves and entities
  -h, --help            Show this help

Waves:
  0  Hygiene — dedup, reclassify, consolidate, clean
  1  Batch creation — scan inboxes, create processing batches
  2  MCE extraction — headless claude sessions per entity
  3  Merge & validate — consolidate artifacts, rebuild indexes

Examples:
  bash bin/mce-wave-launcher.sh --all
  bash bin/mce-wave-launcher.sh --wave 2 --max-parallel 5
  bash bin/mce-wave-launcher.sh --wave 2 --batch 1 --dry-run
  bash bin/mce-wave-launcher.sh --status
EOF
}

# ============================================================================
# Parse arguments
# ============================================================================
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)        RUN_ALL=1; shift ;;
    --wave)       WAVE="${2:-}"; shift 2 ;;
    --batch)      BATCH_NUM="${2:-}"; shift 2 ;;
    --max-parallel) MAX_PARALLEL="${2:-3}"; shift 2 ;;
    --model)      MODEL="${2:-sonnet}"; shift 2 ;;
    --dry-run)    DRY_RUN=1; shift ;;
    --status)     SHOW_STATUS=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *)            echo "Error: unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "${RUN_ALL}" -eq 0 && -z "${WAVE}" && "${SHOW_STATUS}" -eq 0 ]]; then
  echo "Error: specify --all, --wave N, or --status" >&2
  usage
  exit 1
fi

# ============================================================================
# Prerequisites
# ============================================================================
ensure_prereqs() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 not found in PATH" >&2
    exit 1
  fi

  if [[ "${WAVE}" == "2" || "${RUN_ALL}" -eq 1 ]]; then
    if [[ "${DRY_RUN}" -eq 0 ]]; then
      if ! command -v claude >/dev/null 2>&1; then
        echo "Error: 'claude' CLI not found in PATH" >&2
        exit 1
      fi
      if ! command -v tmux >/dev/null 2>&1; then
        echo "Error: tmux not found. Install: brew install tmux" >&2
        exit 1
      fi
    fi
  fi
}

# ============================================================================
# Logging
# ============================================================================
mkdir -p "${LOG_DIR}"

log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  echo "${msg}" | tee -a "${LOG_DIR}/launcher.log"
}

# ============================================================================
# State management
# ============================================================================
update_wave_status() {
  local wave_num="$1"
  local status="$2"
  python3 -c "
import json, sys
from pathlib import Path
from datetime import datetime, timezone

sf = Path('${STATE_FILE}')
sf.parent.mkdir(parents=True, exist_ok=True)
state = json.loads(sf.read_text()) if sf.exists() else {'waves': {}}
w = state.setdefault('waves', {}).setdefault('${wave_num}', {})
w['status'] = '${status}'
w['updated'] = datetime.now(timezone.utc).isoformat()
if '${status}' == 'running':
    w['started'] = w['updated']
if '${status}' in ('complete', 'failed'):
    w['completed'] = w['updated']
state['updated'] = datetime.now(timezone.utc).isoformat()
sf.write_text(json.dumps(state, indent=2, ensure_ascii=False))
"
}

# ============================================================================
# WAVE 0: Hygiene
# ============================================================================
run_wave_0() {
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "  WAVE 0 — HYGIENE"
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  update_wave_status "0" "running"

  local dry_flag=""
  [[ "${DRY_RUN}" -eq 1 ]] && dry_flag="--dry-run"

  if python3 "${ROOT_DIR}/bin/wave-0-hygiene.py" ${dry_flag} 2>&1 | tee -a "${LOG_DIR}/wave-0.log"; then
    update_wave_status "0" "complete"
    log "WAVE 0: COMPLETE"
  else
    update_wave_status "0" "failed"
    log "WAVE 0: FAILED"
    return 1
  fi
}

# ============================================================================
# WAVE 1: Batch creation
# ============================================================================
run_wave_1() {
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "  WAVE 1 — BATCH CREATION"
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  update_wave_status "1" "running"

  local dry_flag=""
  [[ "${DRY_RUN}" -eq 1 ]] && dry_flag="--dry-run"

  cd "${ROOT_DIR}"

  if python3 -c "
import sys
sys.path.insert(0, '.')
from core.intelligence.pipeline.batch_auto_creator import scan_and_create
result = scan_and_create(dry_run=$([[ "${DRY_RUN}" -eq 1 ]] && echo "True" || echo "False"))
print(f'Batches created: {result.batches_created}')
print(f'Files scanned: {result.files_scanned}')
print(f'Files below threshold: {result.files_below_threshold}')
" 2>&1 | tee -a "${LOG_DIR}/wave-1.log"; then
    update_wave_status "1" "complete"
    log "WAVE 1: COMPLETE"
  else
    update_wave_status "1" "failed"
    log "WAVE 1: FAILED"
    return 1
  fi
}

# ============================================================================
# WAVE 2: MCE Extraction (Headless Claude Sessions)
# ============================================================================

# Parse entity manifest to get entities for a batch
get_batch_entities() {
  local batch="$1"
  python3 -c "
import yaml, sys
from pathlib import Path

manifest = yaml.safe_load(Path('${MANIFEST}').read_text())
batches = manifest.get('execution_batches', [])

if ${batch} < 1 or ${batch} > len(batches):
    print('ERROR: batch ${batch} not found (valid: 1-' + str(len(batches)) + ')', file=sys.stderr)
    sys.exit(1)

b = batches[${batch} - 1]
for entity in b['entities']:
    print(entity)
"
}

# Get all pending entities across all batches
get_all_pending_entities() {
  python3 -c "
import yaml
from pathlib import Path

manifest = yaml.safe_load(Path('${MANIFEST}').read_text())
for tier in manifest.get('tiers', []):
    for entity in tier.get('entities', []):
        if entity.get('status', 'pending') == 'pending':
            print(entity['slug'])
"
}

# Write the runner script for a single entity
write_entity_runner() {
  local slug="$1"
  local runner="${LOG_DIR}/run-${slug}.sh"
  local logf="${LOG_DIR}/${slug}.log"

  cat > "${runner}" <<RUNNER_EOF
#!/usr/bin/env bash
set -euo pipefail
unset CLAUDECODE
cd "${ROOT_DIR}"

echo "[start] MCE pipeline for ${slug} at \$(date)" | tee -a "${logf}"

claude -p --dangerously-skip-permissions --model ${MODEL} "$(cat <<'PROMPT_EOF'
Execute /pipeline-mce SLUG_PLACEHOLDER.

MODO AUTONOMO — REGRAS OBRIGATORIAS:
1. Auto-approve identity checkpoint (Step 9). NAO pause, NAO pergunte.
2. Execute TODOS os 12 steps ate o final sem interrupção.
3. Escreva artifacts em artifacts/mce/SLUG_PLACEHOLDER/ em vez dos paths globais:
   - artifacts/mce/SLUG_PLACEHOLDER/CHUNKS-STATE.json
   - artifacts/mce/SLUG_PLACEHOLDER/CANONICAL-MAP.json
   - artifacts/mce/SLUG_PLACEHOLDER/INSIGHTS-STATE.json
4. DNA YAMLs, dossiers e agent files vão nos paths normais (per-entity, safe).
5. Se falhar, salve estado e termine com mensagem de erro.
6. NO final, escreva um arquivo artifacts/mce/SLUG_PLACEHOLDER/COMPLETION.json com:
   {"slug": "SLUG_PLACEHOLDER", "status": "complete", "steps_completed": 12, "timestamp": "ISO"}
PROMPT_EOF
)" 2>&1 | tee -a "${logf}"

EXIT_CODE=\${PIPESTATUS[0]}
echo "[end] MCE pipeline for ${slug} exit=\${EXIT_CODE} at \$(date)" | tee -a "${logf}"
exit \${EXIT_CODE}
RUNNER_EOF

  # Replace placeholder with actual slug
  sed -i '' "s/SLUG_PLACEHOLDER/${slug}/g" "${runner}"
  chmod +x "${runner}"
  echo "${runner}"
}

run_wave_2() {
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "  WAVE 2 — MCE EXTRACTION (Headless)"
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  update_wave_status "2" "running"

  # Determine which entities to process
  local entities=()
  if [[ -n "${BATCH_NUM}" ]]; then
    while IFS= read -r e; do
      [[ -n "$e" ]] && entities+=("$e")
    done < <(get_batch_entities "${BATCH_NUM}")
    log "Processing batch ${BATCH_NUM}: ${entities[*]}"
  else
    while IFS= read -r e; do
      [[ -n "$e" ]] && entities+=("$e")
    done < <(get_all_pending_entities)
    log "Processing all pending entities: ${entities[*]}"
  fi

  if [[ "${#entities[@]}" -eq 0 ]]; then
    log "No pending entities found."
    update_wave_status "2" "complete"
    return 0
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "[DRY RUN] Would launch ${#entities[@]} sessions (max ${MAX_PARALLEL} parallel):"
    for e in "${entities[@]}"; do
      log "  - ${e}"
    done
    return 0
  fi

  # Create MCE artifact dirs
  for e in "${entities[@]}"; do
    mkdir -p "${ROOT_DIR}/artifacts/mce/${e}"
  done

  # Process in groups of MAX_PARALLEL
  local total=${#entities[@]}
  local processed=0
  local group_num=0

  while [[ "${processed}" -lt "${total}" ]]; do
    group_num=$((group_num + 1))
    local group=()
    local count=0

    # Collect up to MAX_PARALLEL entities
    while [[ "${count}" -lt "${MAX_PARALLEL}" && "${processed}" -lt "${total}" ]]; do
      group+=("${entities[${processed}]}")
      processed=$((processed + 1))
      count=$((count + 1))
    done

    local session="mce-wave-2-g${group_num}"

    log ""
    log "  GROUP ${group_num}: ${group[*]} (${count} sessions)"
    log "  tmux session: ${session}"

    # Check if session already exists
    if tmux has-session -t "${session}" 2>/dev/null; then
      log "  WARNING: session ${session} already exists. Skipping group."
      continue
    fi

    # Launch tmux session with panes
    local first=1
    for slug in "${group[@]}"; do
      local runner
      runner="$(write_entity_runner "${slug}")"
      log "  Launching: ${slug} → ${runner}"

      if [[ "${first}" -eq 1 ]]; then
        tmux new-session -d -s "${session}" -n "mce" "bash '${runner}'"
        first=0
      else
        tmux split-window -t "${session}:0" -v "bash '${runner}'"
        tmux select-layout -t "${session}:0" tiled >/dev/null 2>&1 || true
      fi
    done

    log "  Attach: tmux attach -t ${session}"
    log "  Waiting for group ${group_num} to complete..."

    # Wait for all sessions in this group to finish
    # Check every 30 seconds if tmux session still exists
    while tmux has-session -t "${session}" 2>/dev/null; do
      sleep 30
      # Check if all panes are done (tmux session auto-closes when all panes exit)
      local alive
      alive=$(tmux list-panes -t "${session}" 2>/dev/null | wc -l || echo "0")
      if [[ "${alive}" -eq 0 ]]; then
        break
      fi
    done

    log "  Group ${group_num} complete."

    # Check completion status for each entity in this group
    for slug in "${group[@]}"; do
      local completion="${ROOT_DIR}/artifacts/mce/${slug}/COMPLETION.json"
      if [[ -f "${completion}" ]]; then
        log "  ● ${slug}: COMPLETE"
      else
        log "  ✗ ${slug}: INCOMPLETE (check logs/wave-mce/${slug}.log)"
      fi
    done
  done

  # Final status
  local complete_count=0
  for e in "${entities[@]}"; do
    if [[ -f "${ROOT_DIR}/artifacts/mce/${e}/COMPLETION.json" ]]; then
      complete_count=$((complete_count + 1))
    fi
  done

  log ""
  log "Wave 2 Summary: ${complete_count}/${total} entities completed"

  if [[ "${complete_count}" -eq "${total}" ]]; then
    update_wave_status "2" "complete"
    log "WAVE 2: COMPLETE"
  else
    update_wave_status "2" "partial"
    log "WAVE 2: PARTIAL (${complete_count}/${total})"
  fi
}

# ============================================================================
# WAVE 3: Merge & Validate
# ============================================================================
run_wave_3() {
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "  WAVE 3 — MERGE & VALIDATE"
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  update_wave_status "3" "running"

  cd "${ROOT_DIR}"

  if python3 "${ROOT_DIR}/bin/wave-3-merge.py" $([[ "${DRY_RUN}" -eq 1 ]] && echo "--dry-run") 2>&1 | tee -a "${LOG_DIR}/wave-3.log"; then
    update_wave_status "3" "complete"
    log "WAVE 3: COMPLETE"
  else
    update_wave_status "3" "failed"
    log "WAVE 3: FAILED"
    return 1
  fi
}

# ============================================================================
# Status display
# ============================================================================
show_status() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  MCE WAVE STATUS"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ -f "${STATE_FILE}" ]]; then
    python3 -c "
import json
from pathlib import Path

state = json.loads(Path('${STATE_FILE}').read_text())
waves = state.get('waves', {})

wave_names = {'0': 'Hygiene', '1': 'Batch Creation', '2': 'MCE Extraction', '3': 'Merge & Validate'}

for num in ['0', '1', '2', '3']:
    w = waves.get(num, {})
    status = w.get('status', 'pending')
    icon = {'pending': '○', 'running': '~', 'complete': '●', 'failed': '✗', 'partial': '◐'}.get(status, '?')
    started = w.get('started', '-')[:19] if w.get('started') else '-'
    print(f'  [{icon}] Wave {num} — {wave_names[num]}: {status}  (started: {started})')

print()
"
  else
    echo "  No state file found. Run --wave 0 to start."
  fi

  # Check tmux sessions
  echo "  Active tmux sessions:"
  if command -v tmux >/dev/null 2>&1; then
    tmux list-sessions 2>/dev/null | grep "mce-wave" | sed 's/^/    /' || echo "    (none)"
  else
    echo "    tmux not installed"
  fi

  # Check completion files
  echo ""
  echo "  Entity completion:"
  if [[ -d "${ROOT_DIR}/artifacts/mce" ]]; then
    local found_any=0
    for comp in "${ROOT_DIR}"/artifacts/mce/*/COMPLETION.json; do
      if [[ -f "${comp}" ]]; then
        local slug
        slug="$(basename "$(dirname "${comp}")")"
        echo "    ● ${slug}"
        found_any=1
      fi
    done
    [[ "${found_any}" -eq 0 ]] && echo "    (no entities completed yet)"
  else
    echo "    (no entities processed yet)"
  fi

  echo ""
  echo "  Logs: ${LOG_DIR}/"
  echo "  State: ${STATE_FILE}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ============================================================================
# Main execution
# ============================================================================
ensure_prereqs

if [[ "${SHOW_STATUS}" -eq 1 ]]; then
  show_status
  exit 0
fi

if [[ "${RUN_ALL}" -eq 1 ]]; then
  log "Starting FULL PIPELINE (Waves 0 → 1 → 2 → 3)"
  run_wave_0
  run_wave_1
  run_wave_2
  run_wave_3
  log ""
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "  ALL WAVES COMPLETE"
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  show_status
  exit 0
fi

case "${WAVE}" in
  0) run_wave_0 ;;
  1) run_wave_1 ;;
  2) run_wave_2 ;;
  3) run_wave_3 ;;
  *)
    echo "Error: invalid wave number: ${WAVE} (valid: 0, 1, 2, 3)" >&2
    exit 1
    ;;
esac
