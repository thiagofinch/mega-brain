# /map - MMOS Mind Cloning Command

Ultra-simple entry point for creating or updating persona clones using the 8-Layer DNA Mental™ system.

> **Version:** 1.0.0
> **Backend:** `.aiox/core/workflow-engine/map_mind.py`
> **Modes:** Greenfield (new) | Brownfield (update)

---

## SINTAXE

```
/map {person_name} [OPTIONS]
```

| Option              | Descrição                                |
| ------------------- | ---------------------------------------- |
| (nenhuma)           | Auto-detect workflow type and mode       |
| `--force-mode`      | Override auto-detection with specific mode |
| `--materials-path`  | Provide path to source materials         |
| `--help`            | Show help text                           |

---

## AUTO-DETECTION

O sistema detecta automaticamente:

1. **Workflow Type** (greenfield vs brownfield)
   - Verifica se `.aiox/data/knowledge/dna/{slug}/` existe
   - Se existe + completo: brownfield (update)
   - Se não: greenfield (create new)

2. **Mode** (public vs no-public variants)
   - Se greenfield: pesquisa web rápida
     - Se encontrado: `public` mode
     - Se não: perguntar (interviews vs materials)
   - Se brownfield: usa source_type existente

---

## WORKFLOW EXECUTION

### Stage 0.5: APEX Viability Gate

```yaml
apex_gate:
  name: "APEX Viability Assessment"
  scoring:
    authority: 1-10      # Expertise recognition
    production: 1-10     # Content volume
    engagement: 1-10     # Audience interaction
    expertise: 1-10      # Demonstrable skills
  thresholds:
    auto_go: 7.5         # >= 7.5: proceed automatically
    human_review: 5.0    # 5.0-7.4: require approval
    reject: 5.0          # < 5.0: reject
```

### Stages 1-7: 8-Layer DNA Extraction

| Stage | Layers | Output Files |
|-------|--------|--------------|
| 1 | Observable Extraction | FILOSOFIAS.yaml, MODELOS-MENTAIS.yaml |
| 2 | Communication Analysis | COMUNICACAO.yaml |
| 3 | Framework Synthesis | FRAMEWORKS.yaml |
| 4 | Values Hierarchy | VALORES.yaml |
| 5 | Obsessions Mapping | OBSESSOES.yaml |
| 6 | Singularity Detection | SINGULARIDADE.yaml |
| 7 | Paradox Resolution | PARADOXAS.yaml (GOLD LAYER) |
| 8 | Identity Synthesis | SOUL.md v4.0 |

---

## VALID MODES

### Greenfield (New Clone)

| Mode | Descrição |
|------|-----------|
| `public` | Web scraping + automated research |
| `no-public-interviews` | 5-session interview protocol |
| `no-public-materials` | Process provided materials |

### Brownfield (Update Clone)

| Mode | Descrição |
|------|-----------|
| `public-update` | Update with new web sources |
| `no-public-incremental` | Add new interview data |
| `no-public-migration` | Migrate from another system |

---

## DUAL-WRITE OUTPUT

Todos os outputs são escritos em dois paths:

| MMOs Path | AIOS Path |
|-----------|-----------|
| `expansion-packs/mmos/minds/{slug}/` | `.aiox/data/knowledge/dna/{slug}/` |

---

## EXECUTION

Quando `/map {person_name}` é executado:

1. **Via Pipeline Integrator (RECOMENDADO)**
   ```python
   from workflow_engine import run_pipeline

   # One-liner para pipeline completo
   result = run_pipeline("{person_name}")

   # Verificar resultado
   if result.status == "completed":
       print(f"APEX: {result.apex_score}")
       print(f"Fidelity: {result.fidelity_score}%")
       print(f"SOUL.md: {result.outputs.get('SOUL.md')}")
   elif result.status == "human_review_required":
       print(f"APEX Score {result.apex_score} requires human approval")
   else:
       print(f"Failed: {result.errors}")
   ```

2. **Via map_mind (Legado)**
   ```python
   from workflow_engine.map_mind import map_mind

   result = map_mind(
       person_name="{person_name}",
       force_mode=None,
       materials_path=None
   )
   ```

3. **Verificar status**
   ```python
   from workflow_engine import create_adapter

   adapter = create_adapter()
   status = adapter.get_layer_status("{slug}")
   print(f"Complete: {status['complete']}")
   print(f"Missing: {status['missing']}")
   ```

---

## EXEMPLOS

```bash
# Auto-detect tudo (modo mais simples)
/map "Alex Hormozi"

# Forçar modo específico
/map "Cole Gordon" --force-mode=public

# Com materials fornecidos
/map "Jeremy Miner" --materials-path=./sources/jeremy-miner/

# Ver help
/map --help
```

---

## OUTPUT

```
═══════════════════════════════════════════════════════════════
MMOS Map Command - Mind Clone Creation
═══════════════════════════════════════════════════════════════

🔍 Auto-detecting workflow for 'Alex Hormozi'...
✅ Detected: greenfield
✅ Detected mode: public
🚀 Executing: greenfield-mind.yaml (mode: public)

📍 WORKFLOW EXECUTION CONTEXT
════════════════════════════════════════════════════════════════
Workflow: greenfield-mind.yaml
Type: greenfield
Mode: public
Slug: alex-hormozi
Person: Alex Hormozi

Detection Log:
  Web search: Found 1.2M results
  Source type: Public figure with substantial content
  Recommendation: public mode

════════════════════════════════════════════════════════════════

🚀 Starting workflow execution...

[Stage 0.5] APEX Viability Gate
  Authority: 9.5/10 (NYT bestseller, podcast host)
  Production: 9.0/10 (500+ videos, 2 books)
  Engagement: 9.2/10 (2M+ followers)
  Expertise: 9.8/10 (Multiple $100M+ companies)

  ✅ APEX Score: 9.4/10 (AUTO-GO)

[Stage 1] Observable Layer Extraction
  ✅ FILOSOFIAS.yaml created
  ✅ MODELOS-MENTAIS.yaml created

[Stage 2] Communication Analysis
  ✅ COMUNICACAO.yaml created

[Stage 3] Framework Synthesis
  ✅ FRAMEWORKS.yaml created

[Stage 4] Values Hierarchy
  ✅ VALORES.yaml created

[Stage 5] Obsessions Mapping
  ✅ OBSESSOES.yaml created

[Stage 6] Singularity Detection
  ✅ SINGULARIDADE.yaml created

[Stage 7] Paradox Resolution (GOLD LAYER)
  ✅ PARADOXAS.yaml created

[Stage 8] Identity Synthesis
  ✅ SOUL.md v4.0 generated

════════════════════════════════════════════════════════════════
                    EXECUTION COMPLETE
════════════════════════════════════════════════════════════════

📊 LAYER STATUS
  Layer 1: ✅ FILOSOFIAS
  Layer 2: ✅ MODELOS-MENTAIS
  Layer 3: ✅ COMUNICACAO
  Layer 4: ✅ FRAMEWORKS
  Layer 5: ✅ VALORES
  Layer 6: ✅ OBSESSOES
  Layer 7: ✅ SINGULARIDADE
  Layer 8: ✅ PARADOXAS (GOLD)
  Identity: ✅ SOUL.md

📁 OUTPUT PATHS
  MMOs: expansion-packs/mmos/minds/alex-hormozi/
  AIOS: .aiox/data/knowledge/dna/alex-hormozi/

✅ Workflow complete for 'Alex Hormozi'
═══════════════════════════════════════════════════════════════
```

---

## INTEGRATION WITH JARVIS

O comando `/map` é a interface principal para criação de personas. Para processamento de conteúdo bruto do INBOX, use `/process-jarvis`.

| Comando | Propósito |
|---------|-----------|
| `/map` | Criar/atualizar persona completa |
| `/process-jarvis` | Processar conteúdo bruto em chunks/insights |
| `/jarvis-briefing` | Status geral do sistema |

---

## CHANGELOG

| Versão | Data       | Mudança |
|--------|------------|---------|
| 1.0.0  | 2026-02-07 | Criação inicial - wrapper para map_mind.py |
