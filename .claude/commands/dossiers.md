---
description: Exibe status dos dossiers de pessoas e temas com narrativa Mordomo e box ASCII rico
allowed-tools: Bash(find:*), Bash(python3:*), Bash(grep:*)
argument-hint: [--persons] [--themes] [--incomplete] [--person "Name"]
---

# /dossiers — Mordomo Dossier Inspector (v2.0.0)

> **Versao:** 2.0.0 [Story MCE-10.0 — Mordomo restoration]
> **Pipeline:** Mega Brain MCE — Inspecao de dossiers
> **Arquivo anterior:** `.claude/commands/_archive/dossiers-v1.0.0-pre-mordomo.md`

---

## Identidade deste slash

Este slash e **DESCRITIVO** — instrui Claude a executar N bashes separados com narrativa JARVIS entre eles.
Claude inspeciona os dossiers existentes, verifica integridade, e entrega um relatorio rico.

Flags suportadas:

| Flag | Efeito |
|------|--------|
| (nenhuma) | Lista todos os dossiers |
| `--persons` | Apenas dossiers de pessoas |
| `--themes` | Apenas dossiers de temas |
| `--incomplete` | Dossiers sem rastreabilidade completa |
| `--person "Nome"` | Dossier especifico de uma pessoa |

---

## Tom JARVIS — Mordomo

Claude narra em PT-BR, tom mordomo elegante, conciso, sem floreio.

Exemplos corretos:
- `"Senhor. Verificando o estado dos dossiers agora."`
- `"Encontrei 7 dossiers de pessoas e 3 de temas. Verificando integridade..."`
- `"Cole Gordon: 4 fontes, 23 insights, dossier completo e rastreaevel."`
- `"2 dossiers apresentam gaps de rastreabilidade. Detalhando recomendacoes."`

---

## FASE 1 — Escanear Dossiers

JARVIS anuncia: `"Senhor. Mapeando dossiers disponiveis."`

### D1 — Contar dossiers de pessoas

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
find knowledge/external/dossiers/persons -name "DOSSIER-*.md" 2>/dev/null | sort
```

Timeout sugerido: 10s.
Narre: numero de dossiers de pessoas encontrados + lista de nomes.

### D2 — Contar dossiers de temas

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
find knowledge/external/dossiers/THEMES -name "DOSSIER-*.md" 2>/dev/null | sort
```

Timeout sugerido: 10s.
Narre: numero de dossiers de temas encontrados + lista de temas.

Se ambos D1 e D2 retornarem vazios: narrar `"Nenhum dossier encontrado, Senhor. A knowledge base esta vazia."` e ir para box final.

---

## FASE 2 — Verificar Integridade

JARVIS anuncia: `"Verificando rastreabilidade e integridade de cada dossier."`

### D3 — Verificar chunk_ids inline

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
for f in knowledge/external/dossiers/persons/DOSSIER-*.md knowledge/external/dossiers/THEMES/DOSSIER-*.md; do
  [ -f "$f" ] || continue
  basename "$f"
  grep -c '\[.*_[0-9]\{3\}\]' "$f" 2>/dev/null && echo "HAS_REFS" || echo "NO_REFS"
  grep -c '^**Sources:**\|Sources:' "$f" 2>/dev/null | xargs echo "SOURCES_LINE:"
done
```

Timeout sugerido: 15s.
Apos D3, identificar:
- Dossiers com `NO_REFS`: incompletos (sem rastreabilidade chunk_id)
- Contar fontes por dossier

Se `--incomplete` presente: filtrar apenas os dossiers sem rastreabilidade para mostrar no report.
Se `--person "Nome"` presente: filtrar apenas o dossier da pessoa especificada.

---

## FASE 3 — Metadados por Dossier

JARVIS anuncia: `"Extraindo metadados detalhados dos dossiers."`

### D4 — Extrair metadados de cada dossier

Para cada dossier relevante (conforme flags), ler o header e extrair:
- Versao (campo `**Versao:**` ou `version:`)
- Ultima atualizacao
- Fontes listadas
- Numero de secoes

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
for f in knowledge/external/dossiers/persons/DOSSIER-*.md; do
  [ -f "$f" ] || continue
  echo "=== $(basename $f) ==="
  head -20 "$f" | grep -E 'Version|Versao|Sources|Updated|Fontes|Data'
  wc -l < "$f" | xargs echo "LINES:"
done
```

Timeout sugerido: 15s.
Narre: resumo por dossier (versao, fontes, status).

---

## DOSSIERS REPORT ASCII — sempre renderizar ao final

Apos todas as fases, Claude renderiza:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           DOSSIERS REPORT                                     ║
║                          <ISO timestamp>                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─ 📁  DOSSIERS ──────────────────────────────────────────────────────────────┐
│                                                                              │
│   Pessoas:    <N> dossiers                                                   │
│   Temas:      <N> dossiers                                                   │
│   Total:      <N> dossiers                                                   │
│                                                                              │
│   ┌──────────────────────┬─────────┬─────────┬───────────────────────┐       │
│   │ Dossier              │ Fontes  │ Linhas  │ Status                │       │
│   ├──────────────────────┼─────────┼─────────┼───────────────────────┤       │
│   │ <DOSSIER-pessoa-1>   │ <N>     │ <N>     │ ✅ COMPLETO           │       │
│   │ <DOSSIER-pessoa-2>   │ <N>     │ <N>     │ ✅ COMPLETO           │       │
│   │ <DOSSIER-tema-1>     │ <N>     │ <N>     │ ⚠️ SEM CHUNK REFS    │       │
│   └──────────────────────┴─────────┴─────────┴───────────────────────┘       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📊  COBERTURA ──────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────┬──────────────────────────────────────────────┐        │
│   │ Com chunk_refs   │ <N> (<N>% do total)                          │        │
│   │ Sem chunk_refs   │ <N> dossiers incompletos                     │        │
│   │ Ultima atualizac │ <data do dossier mais recente>               │        │
│   │ Mais desatualiz. │ <data do mais antigo>                        │        │
│   └──────────────────┴──────────────────────────────────────────────┘        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ ⚠️  GAPS ───────────────────────────────────────────────────────────────────┐
│                                                                              │
│   <Se houver gaps: listar dossiers com problemas e o tipo de gap>            │
│   <Se nenhum gap: "Todos os dossiers estao integros, Senhor.">               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ ⭐  RECOMENDACAO ───────────────────────────────────────────────────────────┐
│                                                                              │
│   <narrativa em 1-2 linhas da acao mais urgente ou proximo passo>            │
│                                                                              │
│   ⚙  <comando exato recomendado>                                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Regras de renderizacao:**
- Campos preenchidos com dados REAIS dos outputs das fases.
- Se `--incomplete`: mostrar apenas dossiers com gaps na tabela principal.
- Se `--person "Nome"`: mostrar apenas o dossier da pessoa, com metadados expandidos.
- Omitir secao de GAPS se nenhum gap detectado.

---

## OUTPUT EXPANDIDO com --person "Nome"

Se `--person "Nome"` presente, apos o box principal Claude adiciona:

```
┌─ 📄  DOSSIER: {NOME} ──────────────────────────────────────────────────────┐
│                                                                              │
│   Arquivo:    knowledge/external/dossiers/persons/DOSSIER-{NOME}.md         │
│   Versao:     v{N}                                                           │
│   Atualizado: <data>                                                         │
│   Fontes:     <lista de SOURCE_IDs>                                          │
│                                                                              │
│   Insights:   <N> total (<N> HIGH, <N> MEDIUM, <N> LOW)                     │
│   Frameworks: <N>                                                            │
│   Tensoes:    <N>                                                            │
│   Open loops: <N>                                                            │
│   Chunk refs: <N> validos                                                    │
│                                                                              │
│   Agentes com este conhecimento:                                             │
│   <lista de agentes que referenciam este dossier>                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Pergunta JARVIS de encerramento

Apos o box ASCII, Claude encerra com 1 pergunta concisa. Exemplos:
- `"Dossiers mapeados, Senhor. Deseja que eu reprocesse os que estao sem rastreabilidade agora?"`
- `"Cobertura completa identificada. Posso compilar um briefing executivo dos dossiers agora?"`
- `"Dossier de {PESSOA} disponivel. Quer que eu execute uma busca RAG com base neste dossier, Senhor?"`

---

## References

- Dossiers de pessoas: `knowledge/external/dossiers/persons/DOSSIER-*.md`
- Dossiers de temas: `knowledge/external/dossiers/THEMES/DOSSIER-*.md`
- NAVIGATION-MAP: `knowledge/NAVIGATION-MAP.json`
- Story origem: `docs/stories/epic-mce-port-jarvis-v2.1/STORY-MCE-10.0-mordomo-multi-slash.md`
- Constitution: Art. XII (Pipeline MCE Integrity), Art. XIII (Bucket Isolation)
