#!/bin/bash
# Ralph Cascateamento - Loop autônomo para FASE 5.7
# MISSION-2026-001 - Cascateamento Retroativo de 78 Batches
#
# USO:
#   ./ralph-cascateamento.sh              # Executa até completar todos os batches
#   ./ralph-cascateamento.sh 5            # Executa no máximo 5 iterações
#   ./ralph-cascateamento.sh 10 --resume  # Retoma de onde parou
#
# REQUISITOS:
#   - Claude Code CLI instalado (`claude` command)
#   - prd-batches-cascateamento.json no mesmo diretório
#   - prompt-batches.md no mesmo diretório

set -e

MAX_ITERATIONS=${1:-100}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd-batches-cascateamento.json"
PROMPT_FILE="$SCRIPT_DIR/prompt-batches.md"
PROGRESS_FILE="$SCRIPT_DIR/progress-batches.txt"
AUDIT_LOG="$SCRIPT_DIR/audit-cascateamento.jsonl"
DASHBOARD_FILE="$SCRIPT_DIR/cascading-dashboard.md"
LOCK_FILE="$SCRIPT_DIR/.ralph-cascateamento.lock"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║   ██████╗  █████╗ ██╗     ██████╗ ██╗  ██╗                                   ║"
echo "║   ██╔══██╗██╔══██╗██║     ██╔══██╗██║  ██║                                   ║"
echo "║   ██████╔╝███████║██║     ██████╔╝███████║                                   ║"
echo "║   ██╔══██╗██╔══██║██║     ██╔═══╝ ██╔══██║                                   ║"
echo "║   ██║  ██║██║  ██║███████╗██║     ██║  ██║                                   ║"
echo "║   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝                                   ║"
echo "║                                                                              ║"
echo "║                    CASCATEAMENTO AUTOMÁTICO                                  ║"
echo "║                         FASE 5.7                                             ║"
echo "╠══════════════════════════════════════════════════════════════════════════════╣"
echo "║  MISSÃO:     MISSION-2026-001                                                ║"
echo "║  TOTAL:      78 batches                                                      ║"
echo "║  MAX ITER:   $MAX_ITERATIONS                                                         ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for lock file (prevent multiple instances)
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${RED}ERRO: Ralph já está rodando (PID: $PID)${NC}"
        echo "Se isso é um erro, remova: $LOCK_FILE"
        exit 1
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# Check prerequisites
if ! command -v claude &> /dev/null; then
    echo -e "${RED}ERRO: Claude Code CLI não encontrado.${NC}"
    echo "Instale com: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

if [ ! -f "$PRD_FILE" ]; then
    echo -e "${RED}ERRO: PRD não encontrado: $PRD_FILE${NC}"
    exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo -e "${RED}ERRO: Prompt não encontrado: $PROMPT_FILE${NC}"
    exit 1
fi

# Function to get current progress
get_progress() {
    local completed=$(jq '[.userStories[] | select(.passes == true)] | length' "$PRD_FILE")
    local total=$(jq '.userStories | length' "$PRD_FILE")
    local next=$(jq -r '[.userStories[] | select(.passes == false)] | sort_by(.priority) | .[0].id // "NONE"' "$PRD_FILE")
    echo "$completed $total $next"
}

# Function to log iteration
log_iteration() {
    local iteration=$1
    local batch_id=$2
    local status=$3
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Iteration $iteration - $batch_id - $status${NC}"
    echo -e "${BLUE}  Timestamp: $timestamp${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

# Initialize progress file if needed
if [ ! -f "$PROGRESS_FILE" ]; then
    echo "# Ralph Cascateamento Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "Mission: MISSION-2026-001 - FASE 5.7" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
fi

echo ""
echo -e "${GREEN}Iniciando Ralph Cascateamento...${NC}"
echo ""

# Get initial progress
read completed total next <<< $(get_progress)
echo -e "Progresso inicial: ${YELLOW}$completed/$total${NC} batches completos"
echo -e "Próximo batch: ${CYAN}$next${NC}"
echo ""

# Main loop
for i in $(seq 1 $MAX_ITERATIONS); do
    # Get current state
    read completed total next <<< $(get_progress)

    # Check if all done
    if [ "$next" == "NONE" ]; then
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                                              ║${NC}"
        echo -e "${GREEN}║                    ✅ TODOS OS BATCHES COMPLETOS!                           ║${NC}"
        echo -e "${GREEN}║                                                                              ║${NC}"
        echo -e "${GREEN}║  Total processados: $completed/$total                                              ║${NC}"
        echo -e "${GREEN}║  Iterações usadas: $i                                                        ║${NC}"
        echo -e "${GREEN}║                                                                              ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

        # Final timestamp
        echo "" >> "$PROGRESS_FILE"
        echo "## COMPLETE - $(date)" >> "$PROGRESS_FILE"
        echo "All 78 batches processed successfully." >> "$PROGRESS_FILE"
        echo "Total iterations: $i" >> "$PROGRESS_FILE"

        exit 0
    fi

    log_iteration "$i" "$next" "STARTING"

    # Show progress bar
    percent=$((completed * 100 / total))
    bars=$((completed * 40 / total))
    printf "Progress: ["
    for ((j=0; j<bars; j++)); do printf "█"; done
    for ((j=bars; j<40; j++)); do printf "░"; done
    printf "] %d%% (%d/%d)\n" "$percent" "$completed" "$total"
    echo ""

    # Run Claude with the cascateamento prompt
    echo -e "${YELLOW}Executando Claude para $next...${NC}"
    echo ""

    # Create a specific prompt for this iteration
    ITERATION_PROMPT="MODO: EXECUÇÃO AUTÔNOMA (NÃO INTERATIVO)

Você é JARVIS executando FASE 5.7 - Cascateamento Retroativo em modo BATCH AUTOMÁTICO.

⚠️ REGRAS CRÍTICAS PARA ESTE MODO:
- NÃO PERGUNTE se deve continuar - EXECUTE
- NÃO PEÇA confirmação - EXECUTE
- NÃO SUGIRA próximos passos - APENAS EXECUTE ESTE BATCH
- Após completar o batch, ENCERRE IMEDIATAMENTE
- Este é um processo automatizado sem input humano

CONTEXTO:
- Iteração: $i de $MAX_ITERATIONS
- Batches completos: $completed de $total
- Próximo batch: $next

INSTRUÇÕES:
1. Leia o PRD em prd-batches-cascateamento.json
2. Leia os learnings em progress-batches.txt
3. Processe o batch $next seguindo o protocolo em prompt-batches.md
4. Execute o cascateamento completo COM AUDITORIA
5. Marque passes: true no PRD após completar
6. Responda com resumo do que foi feito e ENCERRE

Se todos os batches estiverem completos, responda: <promise>COMPLETE</promise>

EXECUTE AGORA o batch $next. Ao finalizar, mostre apenas o resumo e ENCERRE."

    # Execute Claude
    OUTPUT=$(echo "$ITERATION_PROMPT" | claude --dangerously-skip-permissions 2>&1 | tee /dev/stderr) || true

    # Check for completion signal
    if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
        echo ""
        echo -e "${GREEN}Ralph completou todas as tarefas!${NC}"
        exit 0
    fi

    # Check if batch was processed
    read new_completed new_total new_next <<< $(get_progress)

    if [ "$new_completed" -gt "$completed" ]; then
        echo ""
        echo -e "${GREEN}✅ $next processado com sucesso!${NC}"
        log_iteration "$i" "$next" "COMPLETED"
    else
        echo ""
        echo -e "${YELLOW}⚠️ $next pode não ter sido completado. Verificando...${NC}"
    fi

    # Small pause between iterations
    echo ""
    echo -e "${CYAN}Aguardando 3 segundos antes da próxima iteração...${NC}"
    sleep 3
done

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║                                                                              ║${NC}"
echo -e "${YELLOW}║  ⚠️ Ralph atingiu máximo de iterações ($MAX_ITERATIONS)                              ║${NC}"
echo -e "${YELLOW}║                                                                              ║${NC}"
echo -e "${YELLOW}║  Batches completos: $completed/$total                                              ║${NC}"
echo -e "${YELLOW}║  Execute novamente para continuar.                                           ║${NC}"
echo -e "${YELLOW}║                                                                              ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 1
