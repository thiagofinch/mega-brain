# ENFORCEMENT RULES
## Regras que Impedem Atalhos no Pipeline Jarvis v2.1

> **Versão:** 2.0.0
> **Atualizado:** 2025-12-18
> **Propósito:** Bloquear execução sem pré-requisitos + garantir integridade

---

## VISÃO GERAL

O sistema de **Enforcement** garante que o pipeline seja executado **completamente**, sem atalhos que comprometam a integridade dos dados.

---

## O PROBLEMA DOS ATALHOS

### O Que São Atalhos?

Atalhos ocorrem quando o pipeline pula fases, resultando em:

```
ATALHO (ERRADO):
Transcript → [Leitura direta] → THEMES/*.md ou DOSSIER/*.md → MEMORYs
                                         ⬇️
              SEM chunks, SEM canonical, SEM insights-state, SEM narratives

PIPELINE CORRETO:
Transcript → Chunks → Entities → Insights → Narratives → DOSSIER → MEMORYs
                ⬇️        ⬇️          ⬇️           ⬇️           ⬇️
           STATE FILE  STATE FILE  STATE FILE  STATE FILE  RASTREÁVEL
```

### Consequências dos Atalhos

| Consequência | Impacto |
|--------------|---------|
| State files vazios | Não é possível rastrear o que foi processado |
| Sem chunk_ids | Não é possível citar fontes |
| Sem canonicalização | Entidades duplicadas/inconsistentes |
| DOSSIERs incompletos | Agentes consultam informação parcial |
| MEMORYs sem referência | Conhecimento sem fonte verificável |

---

## REGRAS DE ENFORCEMENT

### REGRA 1: Bloqueio de Escrita Direta

**Antes de criar/modificar arquivos em `/knowledge/`, verificar:**

```python
def enforce_before_knowledge_write(target_path, source_id):
    """
    BLOQUEIA escrita em /knowledge/ se pipeline não foi executado
    """

    # 1. Verificar se chunks existem para este source_id
    chunks_state = load_json("/processing/chunks/CHUNKS-STATE.json")
    source_chunks = [c for c in chunks_state["chunks"] if c["meta"]["source_id"] == source_id]

    if len(source_chunks) == 0:
        raise EnforcementError(
            code="NO_CHUNKS",
            message=f"Não é possível escrever em {target_path}. "
                    f"Source {source_id} não tem chunks em CHUNKS-STATE.json. "
                    f"Execute o pipeline completo primeiro.",
            action="run /process-jarvis"
        )

    # 2. Verificar se insights existem
    insights_state = load_json("/processing/insights/INSIGHTS-STATE.json")
    has_insights = any(
        source_id in [i["source"]["id"] for i in person_insights]
        for person_insights in insights_state["insights_state"]["persons"].values()
    )

    if not has_insights:
        raise EnforcementError(
            code="NO_INSIGHTS",
            message=f"Não é possível escrever em {target_path}. "
                    f"Source {source_id} não tem insights em INSIGHTS-STATE.json. "
                    f"Execute o pipeline completo primeiro.",
            action="run /process-jarvis"
        )

    # 3. Verificar se narrativa existe (para DOSSIERs)
    if "dossiers" in target_path:
        narratives_state = load_json("/processing/narratives/NARRATIVES-STATE.json")
        person_name = extract_person_from_path(target_path)

        if person_name not in narratives_state["narratives_state"]["persons"]:
            raise EnforcementError(
                code="NO_NARRATIVE",
                message=f"Não é possível criar DOSSIER para {person_name}. "
                        f"Narrativa não existe em NARRATIVES-STATE.json. "
                        f"Execute o pipeline completo primeiro.",
                action="run /process-jarvis"
            )

    # Se passou todas as verificações, permite escrita
    return True
```

---

### REGRA 2: Checkpoints Bloqueantes

**Após cada fase crítica, verificar antes de continuar:**

```python
CHECKPOINTS = {
    "PHASE_2": {
        "verify": lambda ctx: len(ctx.new_chunks) > 0,
        "error": "Phase 2 não produziu chunks",
        "action": "EXIT"
    },
    "PHASE_3": {
        "verify": lambda ctx: ctx.source_person in ctx.canonical_map["persons"],
        "error": "SOURCE_PERSON não foi canonicalizada",
        "action": "WARN"  # Warning mas continua
    },
    "PHASE_4": {
        "verify": lambda ctx: (
            ctx.source_person in ctx.insights_state["persons"] and
            len(ctx.insights_state["persons"][ctx.source_person]) > 0
        ),
        "error": "Phase 4 não produziu insights",
        "action": "EXIT"
    },
    "PHASE_5": {
        "verify": lambda ctx: (
            ctx.source_person in ctx.narratives_state["persons"] and
            len(ctx.narratives_state["persons"][ctx.source_person]["narrative"]) > 100
        ),
        "error": "Phase 5 não produziu narrativa",
        "action": "EXIT"
    },
    "PHASE_6": {
        "verify": lambda ctx: exists(f"/knowledge/dossiers/persons/DOSSIER-{ctx.source_person}.md"),
        "error": "Phase 6 não criou DOSSIER",
        "action": "EXIT"
    },
    "PHASE_7": {
        "verify": lambda ctx: all([
            ctx.chunks_verified,
            ctx.canonical_verified,
            ctx.insights_verified,
            ctx.narratives_verified,
            ctx.dossier_verified,
            ctx.memory_verified,
            ctx.rag_verified,
            ctx.registry_verified,
            ctx.session_verified
        ]),
        "error": "Verification checklist falhou",
        "action": "EXIT"
    }
}

def run_checkpoint(phase_id, context):
    """
    Executa checkpoint e bloqueia se falhar
    """
    checkpoint = CHECKPOINTS[phase_id]

    if not checkpoint["verify"](context):
        if checkpoint["action"] == "EXIT":
            raise CheckpointError(
                phase=phase_id,
                message=checkpoint["error"],
                context=context.to_dict()
            )
        elif checkpoint["action"] == "WARN":
            log_warning(f"[{phase_id}] {checkpoint['error']}")

    log_success(f"✓ CHECKPOINT {phase_id}: OK")
```

---

### REGRA 3: Validação de Integridade dos State Files

**Antes de cada operação, verificar integridade:**

```python
def validate_state_files():
    """
    Valida que todos os state files estão íntegros e consistentes
    """
    errors = []

    # 1. CHUNKS-STATE deve ter estrutura válida
    chunks = load_json("/processing/chunks/CHUNKS-STATE.json")
    if "chunks" not in chunks and "sources" not in chunks:
        errors.append("CHUNKS-STATE.json com estrutura inválida")

    # 2. CANONICAL-MAP deve ter estrutura válida
    canonical = load_json("/processing/canonical/CANONICAL-MAP.json")
    if "entities" not in canonical:
        errors.append("CANONICAL-MAP.json com estrutura inválida")

    # 3. INSIGHTS-STATE deve ter estrutura válida
    insights = load_json("/processing/insights/INSIGHTS-STATE.json")
    if "categories" not in insights and "insights_state" not in insights:
        errors.append("INSIGHTS-STATE.json com estrutura inválida")

    # 4. NARRATIVES-STATE deve ter estrutura válida
    narratives = load_json("/processing/narratives/NARRATIVES-STATE.json")
    if "persons" not in narratives and "themes" not in narratives:
        errors.append("NARRATIVES-STATE.json com estrutura inválida")

    # 5. Cross-validation: insights devem referenciar chunks existentes
    # (implementar conforme necessidade)

    if errors:
        raise IntegrityError(errors)

    return True
```

---

### REGRA 4: Auditoria de Operações

**Toda operação deve ser logada:**

```python
AUDIT_LOG_PATH = "/logs/AUDIT/audit.jsonl"

def audit_operation(operation_type, details):
    """
    Loga toda operação para auditoria
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation_type,
        "details": details,
        "checksum": compute_checksum(details)
    }

    append_jsonl(AUDIT_LOG_PATH, entry)

# Operações auditadas
AUDITED_OPERATIONS = [
    "CHUNK_CREATE",
    "ENTITY_RESOLVE",
    "INSIGHT_EXTRACT",
    "NARRATIVE_SYNTHESIZE",
    "DOSSIER_CREATE",
    "DOSSIER_UPDATE",
    "MEMORY_UPDATE",
    "RAG_INDEX",
    "STATE_FILE_WRITE"
]
```

---

### REGRA 5: Proteção Contra Sobrescrita

**Nunca sobrescrever, sempre fazer merge incremental:**

```python
def safe_write_state_file(path, new_data, merge_strategy):
    """
    Escreve em state file com proteção contra perda de dados
    """

    # 1. Backup do estado atual
    if exists(path):
        current = load_json(path)
        backup_path = f"{path}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        write_json(backup_path, current)
    else:
        current = create_empty_state(path)

    # 2. Merge incremental (nunca substituição total)
    if merge_strategy == "APPEND":
        merged = deep_merge_append(current, new_data)
    elif merge_strategy == "UPDATE":
        merged = deep_merge_update(current, new_data)
    else:
        raise ValueError(f"Estratégia de merge inválida: {merge_strategy}")

    # 3. Atualizar metadata
    merged["meta"]["last_updated"] = datetime.now().isoformat()
    merged["meta"]["version"] = current["meta"].get("version", 0) + 1

    # 4. Validar integridade antes de escrever
    validate_state_structure(merged, path)

    # 5. Escrever
    write_json(path, merged)

    # 6. Auditar
    audit_operation("STATE_FILE_WRITE", {
        "path": path,
        "strategy": merge_strategy,
        "items_before": count_items(current),
        "items_after": count_items(merged),
        "backup": backup_path
    })

    return merged
```

---

## MATRIZ DE ENFORCEMENT

| Operação | Verificação Requerida | Ação se Falhar |
|----------|----------------------|----------------|
| Criar DOSSIER pessoa | Narrativa existe | BLOQUEAR |
| Criar DOSSIER tema | 2+ pessoas no tema | SKIP com log |
| Atualizar MEMORY | DOSSIER correspondente existe | BLOQUEAR |
| Criar arquivo em THEMES/ | Chunks existem | BLOQUEAR |
| Indexar no RAG | Arquivo foi gerado pelo pipeline | WARN |
| Avançar Phase 3→4 | Checkpoint Phase 2 passou | BLOQUEAR |
| Avançar Phase 4→5 | Checkpoint Phase 4 passou | BLOQUEAR |
| Avançar Phase 5→6 | Checkpoint Phase 5 passou | BLOQUEAR |
| Avançar Phase 6→7 | Checkpoint Phase 6 passou | BLOQUEAR |
| Finalizar pipeline | Todos os 9 itens do checklist | BLOQUEAR |

---

## MENSAGENS DE ERRO

### Formato Padrão

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ ⛔ ENFORCEMENT ERROR                                                          │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Código: {ERROR_CODE}                                                         │
│  Operação bloqueada: {OPERATION}                                              │
│                                                                               │
│  Motivo:                                                                      │
│  {DETAILED_REASON}                                                            │
│                                                                               │
│  Estado atual:                                                                │
│  {CURRENT_STATE}                                                              │
│                                                                               │
│  Para resolver:                                                               │
│  {RESOLUTION_COMMAND}                                                         │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Exemplo Real

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ ⛔ ENFORCEMENT ERROR                                                          │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Código: NO_CHUNKS                                                            │
│  Operação bloqueada: Criar DOSSIER-Jeremy-Haynes.md                           │
│                                                                               │
│  Motivo:                                                                      │
│  Não é possível criar DOSSIER para Jeremy Haynes.                             │
│  Source JH001 não tem chunks em CHUNKS-STATE.json.                            │
│  O material não passou pelas fases 2-5 do pipeline.                           │
│                                                                               │
│  Estado atual:                                                                │
│  - CHUNKS-STATE.json: 0 chunks para JH001                                     │
│  - INSIGHTS-STATE.json: Jeremy Haynes não existe                              │
│  - NARRATIVES-STATE.json: Jeremy Haynes não existe                            │
│                                                                               │
│  Para resolver:                                                               │
│  /process-jarvis inbox/JEREMY\ HAYNES/PODCASTS/recurring-high-ticket.txt   │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## BYPASS DE EMERGÊNCIA

Em casos excepcionais, o enforcement pode ser bypassado com flag explícita:

```bash
/process-jarvis arquivo.txt --bypass-enforcement --reason "Migração de dados legados"
```

**IMPORTANTE:**
- Requer flag `--reason` com justificativa
- Gera log de auditoria especial
- Marca o output como "BYPASS" para revisão posterior
- Deve ser usado APENAS em migrações ou correções

```python
def handle_bypass(reason):
    """
    Processa bypass de enforcement
    """
    if not reason or len(reason) < 10:
        raise ValueError("--reason deve ter pelo menos 10 caracteres")

    audit_operation("ENFORCEMENT_BYPASS", {
        "reason": reason,
        "user": get_current_user(),
        "timestamp": datetime.now().isoformat()
    })

    log_warning(f"⚠️ ENFORCEMENT BYPASS: {reason}")
    log_warning("Outputs serão marcados como BYPASS para revisão")

    return True
```

---

## CHECKLIST DE IMPLEMENTAÇÃO

Para implementar o enforcement, o Claude Code deve:

- [x] Adicionar verificação antes de escrever em `/knowledge/`
- [x] Implementar checkpoints após cada fase
- [x] Criar função de validação de state files
- [x] Implementar audit log
- [x] Criar proteção contra sobrescrita
- [x] Implementar mensagens de erro formatadas
- [x] Criar flag de bypass para emergências
- [x] Integrar com logs do pipeline

---

## CHANGELOG

| Versão | Data | Mudança |
|--------|------|---------|
| 2.0.0 | 2025-12-18 | Versão completa com todas as regras de enforcement |
| 1.0.0 | 2025-12-18 | Criação inicial (checkpoints básicos) |
