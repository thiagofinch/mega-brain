# /system-digest - Diagnóstico Completo do Sistema

## PROPÓSITO

Comando de diagnóstico que mostra o **estado completo** do sistema Mega Brain, incluindo:
- O que foi processado
- O que está pendente
- Inconsistências detectadas
- Ações recomendadas

## USO

```bash
/system-digest [--verbose] [--fix]
```

### Flags

| Flag | Descrição |
|------|-----------|
| (nenhuma) | Mostra digest padrão |
| `--verbose` | Inclui detalhes de cada arquivo/dossier |
| `--fix` | Sugere comandos para corrigir inconsistências |

---

## O QUE O COMANDO FAZ

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                         /system-digest                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  1. LÊ TODOS OS STATE FILES                                                   │
│     ├─ /processing/chunks/CHUNKS-STATE.json                                │
│     ├─ /processing/canonical/CANONICAL-MAP.json                            │
│     ├─ /processing/insights/INSIGHTS-STATE.json                            │
│     └─ /processing/narratives/NARRATIVES-STATE.json                        │
│                                                                               │
│  2. ESCANEIA DIRETÓRIOS                                                       │
│     ├─ /inbox/ → Lista arquivos não processados                            │
│     ├─ /knowledge/dossiers/ → Lista dossiers existentes                    │
│     └─ /agents/ → Lista agents e status de MEMORYs                         │
│                                                                               │
│  3. DETECTA INCONSISTÊNCIAS                                                   │
│     ├─ Dossiers sem narrativa correspondente                                  │
│     ├─ MEMORYs sem dossier correspondente                                     │
│     ├─ State files desatualizados                                             │
│     └─ Arquivos processados por atalho                                        │
│                                                                               │
│  4. GERA RECOMENDAÇÕES                                                        │
│     ├─ Materiais para reprocessar                                             │
│     ├─ Agentes para criar                                                     │
│     └─ Arquivos pendentes no inbox                                            │
│                                                                               │
│  5. EXIBE RELATÓRIO FORMATADO                                                 │
│     └─ LOG 2: SYSTEM DIGEST (ver LOG-TEMPLATES.md)                            │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## EXECUÇÃO

Ao receber este comando, execute as seguintes etapas:

### ETAPA 1: Carregar State Files

```
READ /processing/chunks/CHUNKS-STATE.json
READ /processing/canonical/CANONICAL-MAP.json
READ /processing/insights/INSIGHTS-STATE.json
READ /processing/narratives/NARRATIVES-STATE.json
```

### ETAPA 2: Escanear Diretórios

```
SCAN /inbox/ recursivamente para arquivos .txt e .md
SCAN /knowledge/dossiers/persons/ para DOSSIERs
SCAN /knowledge/dossiers/THEMES/ para DOSSIERs temáticos
SCAN /agents/*/MEMORY-*.md para status de MEMORYs
```

### ETAPA 3: Detectar Inconsistências

Para cada tipo de inconsistência:

#### DOSSIER_SEM_NARRATIVA
```python
for dossier in list_files("/knowledge/dossiers/persons/"):
    person_name = extract_person_from_dossier(dossier)
    if person_name not in narratives_state["persons"]:
        report_inconsistency("DOSSIER_SEM_NARRATIVA", dossier, person_name)
```

#### MEMORY_SEM_DOSSIER
```python
for memory in list_files("/agents/*/MEMORY-*.md"):
    persons_mentioned = extract_persons_from_memory(memory)
    for person in persons_mentioned:
        if not exists(f"/knowledge/dossiers/persons/DOSSIER-{person}.md"):
            report_inconsistency("MEMORY_SEM_DOSSIER", memory, person)
```

#### CHUNKS_ZERO
```python
if chunks_state["sources"] > 0 and chunks_state["total_chunks"] == 0:
    report_inconsistency("CHUNKS_ZERO", "Pipeline não executou Phase 2")
```

### ETAPA 4: Calcular Métricas

| Métrica | Descrição |
|---------|-----------|
| `inbox_pending_count` | Arquivos aguardando no inbox |
| `chunks_total` | Total de chunks criados |
| `canonical_coverage` | % de pessoas com entidade canônica |
| `insights_total` | Total de insights extraídos |
| `dossiers_complete` | Dossiers criados via pipeline |
| `dossiers_partial` | Dossiers criados por atalho |
| `agents_updated` | Agents com MEMORY atualizada |
| `agents_stale` | Agents com MEMORY desatualizada |
| `inconsistencies_count` | Total de inconsistências |
| `health_score` | Score de saúde do sistema (0-100) |

### ETAPA 5: Calcular Health Score

```python
def calculate_health_score():
    score = 100

    # Penalidades
    score -= inconsistencies_count * 5
    score -= inbox_pending_count * 2
    score -= agents_stale * 3

    # Bônus
    if chunks_total > 0:
        score += 10
    if canonical_coverage > 0.9:
        score += 5

    return max(0, min(100, score))
```

### ETAPA 6: Gerar Relatório

Usar template do LOG 2: SYSTEM DIGEST de `/agents/protocols/LOG-TEMPLATES.md`

---

## OUTPUT ESPERADO

### Digest Padrão

```
┌───────────────────────────────────────────────────────────────────────────────┐
                              SYSTEM DIGEST
                         2024-12-18 14:30:00
───────────────────────────────────────────────────────────────────────────────

📥 INBOX: 3 arquivos aguardando processamento

📦 STATE FILES:
   CHUNKS-STATE:     10 sources, 96 chunks ✓
   CANONICAL-MAP:    15 entidades
   INSIGHTS-STATE:   42 insights (3 pessoas)
   NARRATIVES-STATE: 3 pessoas com narrativa

⚠️ INCONSISTÊNCIAS: 2 detectadas
   1. DOSSIER-Cole-Gordon.md sem narrativa
   2. MEMORY-CRO.md menciona pessoa sem dossier

📁 DOSSIERS:
   PERSONS: 3 (1 via atalho, 2 via pipeline)
   THEMES: 2 (parciais)

🤖 AGENTS:
   Com MEMORY atualizada: 8
   Com MEMORY desatualizada: 2

🔧 AÇÕES RECOMENDADAS:
   1. Reprocessar: Cole Gordon
   2. Processar inbox: 3 arquivos
   3. Criar agente: HR Director (threshold atingido)

📊 HEALTH SCORE: 75/100

└───────────────────────────────────────────────────────────────────────────────┘
```

### Com --fix

Adiciona comandos sugeridos:

```
🔧 COMANDOS PARA CORREÇÃO:

# Reprocessar materiais inconsistentes
/process-jarvis inbox/COLE\ GORDON/PODCASTS/CG001.txt

# Processar inbox pendente
/process-jarvis inbox/ALEX\ HORMOZI/MASTERCLASS/new-video.txt

# Criar agente sugerido
# (criar manualmente: /agents/SALES/AGENT-HR-DIRECTOR.md)
```

---

## ALERTAS AUTOMÁTICOS

Se Health Score < 50:

```
🚨 ALERTA CRÍTICO: Health Score abaixo de 50
   Score atual: 35/100
   Principais problemas:
   - 10 inconsistências detectadas
   - 0 chunks criados (pipeline não executado)
   - 5 arquivos no inbox há mais de 7 dias

   Recomendação: Executar correção imediata
   Comando: /system-digest --fix
```

---

## INTEGRAÇÃO

O `/system-digest` pode ser chamado:

1. **Manualmente** - A qualquer momento para verificar estado
2. **Automaticamente** - Após erros no pipeline
3. **No início de sessão** - Para verificar estado antes de trabalhar

---

## SALVAMENTO

Salvar output em: `/logs/DIGEST/digest-{TIMESTAMP}.md`
