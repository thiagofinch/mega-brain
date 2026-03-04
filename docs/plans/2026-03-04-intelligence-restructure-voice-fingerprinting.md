# PRD — Intelligence Module Restructure + Voice Fingerprinting System

**Tipo:** Brownfield
**Data:** 2026-03-04
**PM:** @morgan
**Status:** APROVADO — Em Implementação
**Epic ID:** EPIC-VOICE-001

---

## Problema

O `core/intelligence/` possui 28 arquivos Python em estrutura flat, dificultando manutenção e coesão semântica. Adicionalmente, o pipeline de ingestão aceita materiais sem labels de speaker, gerando dados sujos no knowledge base. Não existe mecanismo de reconhecimento de voz persistente.

---

## Solução (3 entregas em 1 epic)

### Entrega 1 — Reorganização Semântica de `core/intelligence/`

**Por quê:** 28 arquivos flat impossibilitam co-location e descoberta. Arquivos que trabalham juntos devem ficar próximos.

**Mapa de destino:**

| Subdiretório | Arquivos |
|---|---|
| `pipeline/` | `task_orchestrator.py`, `autonomous_processor.py`, `pipeline_heal.py`, `session_autosave.py`, `sync_package_files.py` |
| `entities/` | `entity_normalizer.py`, `business_model_detector.py`, `role_detector.py`, `org_chain_detector.py`, `bootstrap_registry.py` |
| `validation/` | `audit_layers.py`, `validate_layers.py`, `validate_json_integrity.py`, `verify_classifications.py` |
| `retrieval/` | `query_analyzer.py`, `context_assembler.py`, `memory_splitter.py`, `nav_map_builder.py` |
| `dossier/` | `dossier_tracer.py`, `dossier_trigger.py`, `review_dashboard.py`, `theme_analyzer.py` |
| `roles/` | `sow_generator.py`, `skill_generator.py`, `tool_discovery.py`, `viability_scorer.py` |
| `agents/` | `agent_trigger.py` |
| `speakers/` | *(novos — Entrega 2)* |

**Regras de migração:**
- `sys.path.insert(0, str(Path(__file__).parent))` → `.parent.parent` em 15 arquivos
- `entity_normalizer.py` (hub: 12 dependentes) migra para `entities/`, todos importadores atualizam path
- `core/intelligence/__init__.py` atualiza exports para novos caminhos
- `bin/validate-package.js` L67: `core/intelligence` → `core/intelligence/validation`
- `.claude/skills/pipeline-heal/SKILL.md`: atualizar path para `pipeline/pipeline_heal.py`

---

### Entrega 2 — Voice Fingerprinting System (`core/intelligence/speakers/`)

**Por quê:** Aplicativos como Plaud e Read.ai mantêm registro permanente de vozes. O Mega Brain deve auto-identificar speakers conhecidos em novos áudios/vídeos, eliminando trabalho manual repetitivo.

**Arquitetura:**

```
core/intelligence/speakers/
├── __init__.py
├── speaker_gate.py          # Valida presença de labels em transcrições de texto
├── voice_diarizer.py        # Diarização via pyannote.audio (local) + AssemblyAI (fallback)
├── voice_embedder.py        # Extrai embedding único por voz
├── voice_registry.py        # CRUD no VOICE-REGISTRY.yaml
└── speaker_labeler.py       # Interativo: mostra 5-10 frases, pergunta nome do speaker
```

**VOICE-REGISTRY.yaml** (L3 Personal — gitignored):
```yaml
version: "1.0"
speakers:
  - id: SPK-001
    name: "Pedro Valerio Lopez"
    embedding_file: "voice_embeddings/SPK-001.pkl"
    phrases_sample: ["..."]
    registered_at: "2026-03-04"
    sessions_seen: 7
```

**Fluxo para áudio/vídeo:**
1. `voice_diarizer.py` → segmentos por speaker anônimo (SPEAKER_00, SPEAKER_01...)
2. `voice_embedder.py` → embedding por segmento
3. `voice_registry.py` → match contra registry (threshold cosine > 0.85)
4. Match encontrado → auto-label. Não encontrado → `speaker_labeler.py` (interativo)
5. Novo speaker → salva embedding no registry

**Limitação documentada:** Funciona APENAS em áudio/vídeo (sinal acústico). Transcrições texto puro sem labels requerem identificação manual.

**Dependências** (já em `requirements.txt`):
- `pyannote.audio>=3.1.0`, `torch>=2.0.0`, `torchaudio>=2.0.0`
- `assemblyai>=0.28.0` (fallback cloud)
- `numpy>=1.24.0`, `scipy>=1.10.0`

---

### Entrega 3 — Speaker Gate (`phase_0: PRE_VALIDATION`)

**Por quê:** Materiais com múltiplas vozes sem labels criam conhecimento atribuído à fonte errada. A trava bloqueia ingestão prematura e apresenta 3 opções ao usuário.

**Implementação:**

`core/tasks/validate-speakers.md` — task atômica QG-SPEAKER-001:
- Detecta padrão `"Nome: texto"` ou `"[HH:MM] Nome:"` no arquivo
- Se detectado: PASS
- Se não detectado: bloqueia com 3 opções:
  1. Monólogo (prosseguir sem labels — atribui tudo à fonte)
  2. Identificar participantes manualmente (lista nomes → aplica heurística de divisão)
  3. Cancelar ingestão

`core/workflows/wf-ingest.yaml` — adicionar antes de `phase_1`:
```yaml
phases:
  - id: phase_0
    name: "PRE_VALIDATION"
    description: "Valida presença de speaker labels"
    task: "validate-speakers"
    blocking: true
    on_fail: "prompt_user_options"
```

---

## Critérios de Aceitação

- [ ] Todos os 28 arquivos nos subdirs corretos, zero broken imports
- [ ] `python3 -c "from core.intelligence import TaskOrchestrator"` passa
- [ ] `python3 -c "from core.intelligence.speakers import speaker_gate"` passa
- [ ] `wf-ingest.yaml` tem `phase_0: PRE_VALIDATION` como fase bloqueante
- [ ] Arquivos sem labels → usuário vê 3 opções (não ingere silenciosamente)
- [ ] `VOICE-REGISTRY.yaml` listado no `.gitignore` (L3 Personal)
- [ ] `bin/validate-package.js` referência atualizada

## Out of Scope

- Conexão do Phase 5 templates ao `wf-pipeline-full.yaml` (Gap 2 — próxima sessão)
- Ingestão das 9 transcrições do Pedro (aguarda gate funcionando)
- YouTube `x4T1YjJuqss` — autor desconhecido (pendente)

---

*— Morgan, planejando o futuro 📊*
