# /jarvis-briefing — MCE Pipeline Status Briefing

Display compiled MCE pipeline status for a persona using the Chronicler Design System v3.0.

## Uso

```
/jarvis-briefing {slug}              # Status completo de uma persona
/jarvis-briefing alex-hormozi        # Exemplo
/jarvis-briefing --all               # Overview de todas as personas
```

## Execução

### 0. Health Score (Story MCE-11.12)

Sempre exibir o Health Score holístico no topo do briefing antes de qualquer outra secao:

```python
from pathlib import Path
from engine.intelligence.health.health_scorer import HealthScorer, render_health_box

ROOT = Path(".")  # project root
scorer = HealthScorer(ROOT)
result = scorer.compute()
print(render_health_box(result))
```

Formato esperado do gauge:

```
┌─────────────────────────────────────────┐
│  HEALTH SCORE: 78/100 — BOM             │
│  ████████████████░░░░  78%              │
│                                         │
│  State Files  ████████████  20/20 ✓    │
│  Agents       ███████████░  15/20 ↑    │
│  Dossiers     ███████████░  15/20 ↑    │
│  Inbox        ████████████  20/20 ✓    │
│  Pipeline     ████████░░░░  13/20 ↓    │
└─────────────────────────────────────────┘
```

Grades:
- EXCELENTE: 85-100
- BOM: 70-84
- ATENCAO: 50-69
- CRITICO: <50

HEALTH-STATE.json e gerado em `.data/artifacts/HEALTH-STATE.json` a cada chamada.

---

### 1. Carregar Step Results

```python
# Ler todos step_result files do slug
step_results_dir = ".claude/mission-control/mce/{slug}/step_results/"

# Para cada step_NN_result.json encontrado:
from core.intelligence.pipeline.mce.step_result import StepResult
import json, dataclasses

results = []
for f in sorted(step_results_dir.glob("step_*_result.json")):
    data = json.loads(f.read_text())
    # Reconstruct StepResult from dict
    results.append(data)
```

### 2. Carregar Pipeline State

```python
# Estado da FSM
pipeline_state = ".claude/mission-control/mce/{slug}/pipeline_state.yaml"
# Metadata
metadata = ".claude/mission-control/mce/{slug}/metadata.yaml"
# Metrics
metrics = ".claude/mission-control/mce/{slug}/metrics.yaml"
```

### 3. Renderizar Briefing

**Se step_results existem:**

```python
from core.intelligence.pipeline.mce.step_log_renderer import render_briefing

session_data = {
    "slugs_processed": [slug],
    "active_buckets": ["external"],
    "total_steps": len(results),
    "duration_seconds": sum(r.get("duration_seconds", 0) for r in results),
}

output = render_briefing(session_data, results)
print(output)
```

**Se NÃO existem step_results:**

Exibir status mínimo a partir de pipeline_state.yaml e metadata.yaml:

```
======================================================================
  JARVIS BRIEFING — {slug}
======================================================================

  Pipeline State: {current_state}
  Started: {started_at}
  Updated: {updated_at}
  Phases Completed: {list}

  DNA Layers (10):
    L1 FILOSOFIAS:          {exists? ✅/❌}
    L2 MODELOS-MENTAIS:     {exists? ✅/❌}
    L3 HEURISTICAS:         {exists? ✅/❌}
    L4 FRAMEWORKS:          {exists? ✅/❌}
    L5 METODOLOGIAS:        {exists? ✅/❌}
    L6 BEHAVIORAL-PATTERNS: {exists? ✅/❌}
    L7 VALUES-HIERARCHY:    {exists? ✅/❌}
    L8 VOICE-DNA:           {exists? ✅/❌}
    L9 OBSESSIONS:          {exists? ✅/❌}
    L10 PARADOXES:          {exists? ✅/❌}

  Agent Files:
    AGENT.md:       {exists? ✅/❌}
    SOUL.md:        {exists? ✅/❌}
    MEMORY.md:      {exists? ✅/❌}
    DNA-CONFIG.yaml: {exists? ✅/❌}
    ACTIVATION.yaml: {exists? ✅/❌}

  Nenhum step result disponível — rode a pipeline para dados detalhados.
======================================================================
```

### 4. Verificar DNA Layers

Para cada slug, verificar existência dos 10 YAML files:

```
knowledge/external/dna/persons/{slug}/FILOSOFIAS.yaml          (L1)
knowledge/external/dna/persons/{slug}/MODELOS-MENTAIS.yaml     (L2)
knowledge/external/dna/persons/{slug}/HEURISTICAS.yaml         (L3)
knowledge/external/dna/persons/{slug}/FRAMEWORKS.yaml          (L4)
knowledge/external/dna/persons/{slug}/METODOLOGIAS.yaml        (L5)
knowledge/external/dna/persons/{slug}/BEHAVIORAL-PATTERNS.yaml (L6)
knowledge/external/dna/persons/{slug}/VALUES-HIERARCHY.yaml    (L7)
knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml           (L8)
knowledge/external/dna/persons/{slug}/OBSESSIONS.yaml          (L9)
knowledge/external/dna/persons/{slug}/PARADOXES.yaml           (L10)
```

### 5. Propagation Status Table (Story MCE-11.4)

Read `.data/artifacts/PROPAGATION-GAPS.json` and render the last 5 processed
sources as a table.  If the file does not exist, print "(no propagation data
yet — run the pipeline to generate)".

```python
import json
from pathlib import Path

gaps_file = Path(".data/artifacts/PROPAGATION-GAPS.json")
if not gaps_file.exists():
    print("  Propagation Status: (no data yet)")
else:
    data = json.loads(gaps_file.read_text(encoding="utf-8"))
    sources = data.get("sources", {})
    # Sort by processed_at descending; show last 5
    sorted_entries = sorted(
        sources.values(),
        key=lambda e: e.get("processed_at", ""),
        reverse=True,
    )[:5]

    print()
    print("  Propagation Status (last 5 sources):")
    print(f"  {'Source ID':<12} {'Slug':<20} {'Status':<12} {'Gaps'}")
    print(f"  {'-'*12} {'-'*20} {'-'*12} {'-'*4}")
    for entry in sorted_entries:
        src_id  = (entry.get("source_id") or entry.get("slug", "?"))[:12]
        slug_   = entry.get("slug", "?")[:20]
        overall = entry.get("overall", "UNKNOWN")[:12]
        gaps_   = str(entry.get("gap_count", "?"))
        print(f"  {src_id:<12} {slug_:<20} {overall:<12} {gaps_}")
```

Expected output format:

```
  Propagation Status (last 5 sources):
  Source ID    Slug                 Status       Gaps
  ------------ -------------------- ------------ ----
  AH-YT005     alex-hormozi         COMPLETE     0
  LO-0003      liam-ottley          INCOMPLETE   2
```

## Argumentos

| Arg | Required | Descrição |
|-----|----------|-----------|
| slug | Sim | Person slug (e.g., alex-hormozi) |
| --all | Não | Overview de todas as personas com DNA |
| --compact | Não | Versão resumida (só status e DNA layers) |

### 6. Role Tracker Section (Story MCE-11.8)

Read `.data/artifacts/ROLE-TRACKING-CARGO.json` and render roles with CRITICAL or
IMPORTANT priority. If the file does not exist, print "(no role tracking data yet —
run the pipeline to generate)".

```python
import json
from pathlib import Path

cargo_file = Path(".data/artifacts/ROLE-TRACKING-CARGO.json")
if not cargo_file.exists():
    print("  Role Tracker: (no data yet — run pipeline to generate)")
else:
    data = json.loads(cargo_file.read_text(encoding="utf-8"))
    roles = data.get("roles", {})
    # Filter to CRITICAL and IMPORTANT only
    visible = {
        k: v for k, v in roles.items()
        if v.get("priority") in ("CRITICAL", "IMPORTANT")
    }
    if not visible:
        print("  Role Tracker: no CRITICAL or IMPORTANT roles detected yet")
    else:
        print()
        print("  Role Tracker (CRITICAL / IMPORTANT roles):")
        print(f"  {'Role':<16} {'Mentions':>8} {'Priority':<12} {'Agent Exists'}")
        print(f"  {'-'*16} {'-'*8} {'-'*12} {'-'*30}")
        for role_name, entry in sorted(
            visible.items(),
            key=lambda x: -x[1].get("mention_count", 0),
        ):
            mentions = str(entry.get("mention_count", "?"))
            priority = entry.get("priority", "?")
            agent_exists = entry.get("agent_exists", False)
            agent_status = (
                f"YES — {entry.get('agent_path', '?')}"
                if agent_exists
                else "NO — pendente criacao"
            )
            print(f"  {role_name:<16} {mentions:>8} {priority:<12} {agent_status}")
    print(f"  Last updated: {data.get('last_updated', '?')}")
```

Expected output format:

```
  Role Tracker (CRITICAL / IMPORTANT roles):
  Role             Mentions Priority     Agent Exists
  ---------------- -------- ------------ ------------------------------
  Closer                 42 CRITICAL     YES — agents/external/cargo/sales/closer/
  Head of Ops            11 CRITICAL     NO — pendente criacao
  BDR                     7 IMPORTANT   NO — pendente criacao
  Last updated: 2026-05-27T12:00:00+00:00
```

### 7. Últimos Batches — Cross-Batch Summary (Story MCE-11.11)

Read `.data/artifacts/BATCH-HISTORY.json` and render the last 5 batches as a
summary table. Highlight anomalies. If the file does not exist, print "(sem
histórico de batches — rode a pipeline para gerar)".

```python
import json
from pathlib import Path

history_file = Path(".data/artifacts/BATCH-HISTORY.json")
if not history_file.exists():
    print("  Últimos Batches: (sem histórico — rode a pipeline para gerar)")
else:
    history = json.loads(history_file.read_text(encoding="utf-8"))
    if not history:
        print("  Últimos Batches: (arquivo existe mas está vazio)")
    else:
        last_5 = history[-5:]  # last 5 entries
        print()
        print("  Últimos Batches (cross-batch analysis):")
        print(f"  {'Batch ID':<22} {'Slug':<20} {'Chunks':>6} {'Insights':>8} {'HIGH':>5} {'Health':<10} {'Anomalias'}")
        print(f"  {'-'*22} {'-'*20} {'-'*6} {'-'*8} {'-'*5} {'-'*10} {'-'*9}")
        for entry in reversed(last_5):  # most recent first
            if not isinstance(entry, dict):
                continue
            batch_id = entry.get("batch_id", "?")[:22]
            slug_col  = entry.get("source_person", entry.get("slug", "?"))[:20]
            m         = entry.get("metrics", {})
            chunks_   = str(m.get("chunks", "?"))
            insights_ = str(m.get("insights_total", "?"))
            high_     = str(m.get("insights_high", "?"))
            health_   = entry.get("health_status", "?")[:10]
            anomalies_= entry.get("anomalies", [])
            anom_col  = f"{len(anomalies_)} anomalia(s)" if anomalies_ else "ok"
            print(f"  {batch_id:<22} {slug_col:<20} {chunks_:>6} {insights_:>8} {high_:>5} {health_:<10} {anom_col}")
        # If last batch has anomalies, show detail
        last = last_5[-1] if last_5 else {}
        last_anomalies = last.get("anomalies", [])
        if last_anomalies:
            print()
            print("  Anomalias no ultimo batch:")
            for a in last_anomalies:
                print(f"    - {a.get('flag', str(a))}")
        # Briefing path hint
        print()
        print("  Executive briefings: logs/executive-briefings/")
```

Expected output format:

```
  Últimos Batches (cross-batch analysis):
  Batch ID               Slug                 Chunks Insights  HIGH Health     Anomalias
  ---------------------- -------------------- ------ -------- ----- ---------- ---------
  BATCH-20260527-002     alex-hormozi             12       10     2  CRITICO    1 anomalia(s)
  BATCH-20260527-001     liam-ottley              45       38    12  BOM        ok

  Anomalias no ultimo batch:
    - chunks 73% abaixo da média — possível vídeo curto

  Executive briefings: logs/executive-briefings/
```

## Notas

- Este é um comando READ-ONLY — não modifica nenhum arquivo
- Graceful degradation: funciona com dados parciais
- Mostra status de todos 10 DNA layers (L1-L10)
- Integrado com Chronicler Design System v3.0 quando step_results disponíveis
- Seção "Propagation Status" lê `.data/artifacts/PROPAGATION-GAPS.json` (Story MCE-11.4)
- Seção "Role Tracker" lê `.data/artifacts/ROLE-TRACKING-CARGO.json` (Story MCE-11.8)
- Seção "Últimos Batches" lê `.data/artifacts/BATCH-HISTORY.json` (Story MCE-11.11)
