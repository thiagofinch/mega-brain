# SOURCES COMPILATION PROTOCOL (Prompt 4.1)

> **Versão:** 1.1.0
> **Pipeline:** Jarvis → Etapa 4.1 (Após Dossier Compilation)
> **Output:** `/knowledge/SOURCES/{PESSOA}/{TEMA}.md`
> **Protocolo de Escrita:** `NARRATIVE-METABOLISM-PROTOCOL.md` (OBRIGATÓRIO)

---

## 📖 NARRATIVE METABOLISM (OBRIGATÓRIO)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  TODO arquivo SOURCES DEVE seguir o NARRATIVE-METABOLISM-PROTOCOL.md        │
│                                                                             │
│  ESTRUTURA OBRIGATÓRIA:                                                     │
│  1. TL;DR (Em resumo: + Versão + Atualizado + Densidade)                    │
│  2. Filosofia Central (o "porquê" da fonte sobre este tema)                 │
│  3. Modus Operandi (o "como" - processos e frameworks)                      │
│  4. Arsenal Técnico (o "o quê" - táticas e números)                         │
│  5. Armadilhas (o que esta fonte diz NÃO fazer)                             │
│  6. Citações Originais (quotes preservadas com [SOURCE_ID])                 │
│  7. Metadados (fonte, chunks, insights, temas relacionados)                 │
│                                                                             │
│  VOZ: SEMPRE 1ª pessoa (voz da fonte)                                       │
│  DIAGRAMAS: ASCII (┌─┐│└┘├┤) onde framework visual ajuda                    │
│  IDIOMA: Português BR + termos técnicos em inglês                           │
│  DENSIDADE: Indicador ◯ a ◐ (1-5) obrigatório no header                     │
│                                                                             │
│  Ver: core/templates/PIPELINE/NARRATIVE-METABOLISM-PROTOCOL.md                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PRINCÍPIO FUNDAMENTAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  SOURCES = TEMA × PESSOA (consolidação uni-fonte)                          │
│                                                                             │
│  • Cada arquivo = tudo que UMA pessoa disse sobre UM tema                  │
│  • Alimentado incrementalmente por múltiplos documentos                    │
│  • Organizado por pessoa/empresa → tema                                    │
│  • Nomes sempre em MAIÚSCULAS                                              │
│                                                                             │
│  DIFERENÇA DOS DOSSIERS:                                                   │
│  • SOURCES/{PESSOA}/{TEMA}.md = 1 pessoa, 1 tema, múltiplos docs          │
│  • DOSSIERS/persons/ = 1 pessoa, TODOS os temas                           │
│  • DOSSIERS/THEMES/ = 1 tema, MÚLTIPLAS pessoas                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ESTRUTURA DE PASTAS

```
/knowledge/SOURCES/
│
├── {PESSOA-OU-EMPRESA}/              ← MAIÚSCULAS, hífen para espaços
│   ├── _INDEX.md                     ← Índice de temas desta fonte
│   ├── {TEMA-1}.md                   ← Ex: PROCESSO-VENDAS.md
│   ├── {TEMA-2}.md                   ← Ex: CLOSING.md
│   └── ...
│
├── ALEX-HORMOZI/
│   ├── _INDEX.md
│   ├── ESTRUTURA-TIME.md
│   ├── CLOSER-FRAMEWORK.md
│   └── PRICING.md
│
├── COLE-GORDON/
│   ├── _INDEX.md
│   ├── PROCESSO-VENDAS.md
│   ├── CLOSING.md
│   ├── SHOW-RATES.md
│   └── CONTRATACAO.md
│
└── ...
```

---

## NOMENCLATURA (OBRIGATÓRIO)

| Elemento | Formato | Exemplo |
|----------|---------|---------|
| Pasta pessoa/empresa | MAIÚSCULAS + hífen | `COLE-GORDON/` |
| Arquivo tema | MAIÚSCULAS + hífen + .md | `PROCESSO-VENDAS.md` |
| Índice | `_INDEX.md` | `_INDEX.md` |

---

## TEMPLATE: ARQUIVO DE TEMA POR PESSOA

```markdown
# {PESSOA}: {TEMA}

> **Fonte:** {PESSOA} (consolidação uni-fonte)
> **Tema:** {TEMA}
> **Última atualização:** {YYYY-MM-DD HH:MM}
> **Documentos fonte:** {N} | **Chunks:** {N} | **Insights:** {N}
> **Status:** 🟢 Ativo | 🟡 Incompleto | 🔴 Contradições internas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 SÍNTESE

{Parágrafo de 3-5 linhas resumindo a posição desta pessoa sobre este tema}

**Palavras-chave:** {tag1}, {tag2}, {tag3}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 POSIÇÃO CENTRAL

{Posição principal desta pessoa sobre o tema, 2-3 parágrafos}

**Nuances e condições:**
- {Condição 1}
- {Condição 2}

**Confiança:** {ALTA|MÉDIA|BAIXA} — {justificativa}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📐 FRAMEWORKS E MODELOS

### {Framework 1}

**Fonte:** [{SOURCE_ID}] {título do documento}

```
{Descrição estruturada do framework}
```

**Quando usar:** {contexto}
**Limitações:** {quando NÃO usar}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 MÉTRICAS E BENCHMARKS

| Métrica | Valor | Contexto | Chunk |
|---------|-------|----------|-------|
| {métrica} | {valor} | {contexto} | [{chunk_id}] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 💬 CITAÇÕES-CHAVE

> "{citação exata}"
> — [{chunk_id}] {contexto}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📈 HISTÓRICO DE CONTRIBUIÇÕES

| Data | Documento | Chunks | O que foi adicionado |
|------|-----------|--------|----------------------|
| {date} | [{SOURCE_ID}] {título} | {N} | {resumo} |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔗 LINKS

- **Dossiê Pessoa:** → [DOSSIER-{PESSOA}.md](/knowledge/external/dossiers/persons/DOSSIER-{PESSOA}.md)
- **Dossiê Tema:** → [DOSSIER-{TEMA}.md](/knowledge/external/dossiers/THEMES/DOSSIER-{TEMA}.md)
- **Documentos Originais:**
  - [{SOURCE_ID}] → [/inbox/{path}]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                           FIM DO ARQUIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## TEMPLATE: _INDEX.md (índice por pessoa)

```markdown
# ÍNDICE: {PESSOA}

> **Última atualização:** {YYYY-MM-DD}
> **Total de temas:** {N}
> **Total de documentos fonte:** {N}

---

## TEMAS DISPONÍVEIS

| Tema | Arquivo | Docs | Insights | Última atualização |
|------|---------|------|----------|-------------------|
| {Tema 1} | [{TEMA-1}.md](./{TEMA-1}.md) | {N} | {N} | {date} |
| {Tema 2} | [{TEMA-2}.md](./{TEMA-2}.md) | {N} | {N} | {date} |

---

## DOCUMENTOS FONTE

| ID | Título | Tipo | Temas cobertos | Path INBOX |
|----|--------|------|----------------|------------|
| {SOURCE_ID} | {título} | {tipo} | {tema1}, {tema2} | [link] |

---

## LINKS

- **Dossiê completo:** → [DOSSIER-{PESSOA}.md](/knowledge/external/dossiers/persons/DOSSIER-{PESSOA}.md)
```

---

## EXECUÇÃO AUTOMÁTICA

Este protocolo é executado pela **PHASE 6.6** do process-jarvis.md (após DOSSIER COMPILATION).

### Modo de Operação

```
FOR each PERSON in NARRATIVES_STATE.persons:

  PERSON_FOLDER = /knowledge/SOURCES/{PERSON_UPPERCASE}/

  IF folder NOT EXISTS:
    CREATE folder
    CREATE _INDEX.md from template

  FOR each THEME in person.positions_by_theme:

    THEME_FILE = {PERSON_FOLDER}/{THEME_UPPERCASE}.md

    IF file EXISTS:
      MODE = "INCREMENTAL"
      READ existing_file
      APPEND new insights from current source
      UPDATE histórico de contribuições
      UPDATE métricas e citações
    ELSE:
      MODE = "CREATE"
      GENERATE file from template
      SET initial content from current insights

    WRITE to THEME_FILE
    LOG("✅ SOURCE criado/atualizado: {THEME_FILE}")

  UPDATE _INDEX.md with new themes/documents
```

---

## REGRAS DE ATUALIZAÇÃO INCREMENTAL

| Seção | Comportamento |
|-------|---------------|
| Síntese | REFINAR se houver nova informação significativa |
| Posição Central | EXPANDIR com nuances, NUNCA contradizer sem nota |
| Frameworks | ADICIONAR novos, EXPANDIR existentes |
| Métricas | ADICIONAR novas, ATUALIZAR se valor mudou (com nota) |
| Citações | SEMPRE ADICIONAR novas |
| Histórico | SEMPRE ADICIONAR (nunca apagar) |
| Links | ATUALIZAR conforme novos docs |

---

## CHECKPOINT APÓS EXECUÇÃO

```
VALIDAR APÓS EXECUTAR:
[ ] CP-POST-6.6.A: Para cada pessoa em NARRATIVES_STATE.persons:
                   /knowledge/SOURCES/{PESSOA}/_INDEX.md existe
[ ] CP-POST-6.6.B: Para cada tema da pessoa:
                   /knowledge/SOURCES/{PESSOA}/{TEMA}.md existe
[ ] CP-POST-6.6.C: Arquivos contêm referências aos chunks fonte

Se falhar: ⚠️ WARN (não bloqueante - SOURCES é complementar aos DOSSIERS)
```

---

## INTEGRAÇÃO COM RAG

Ao salvar arquivo SOURCE, indexar no ChromaDB:

```python
{
    "id": "SOURCE-COLE-GORDON-CLOSING",
    "content": "Conteúdo do arquivo...",
    "metadata": {
        "type": "source_theme",
        "person": "Cole Gordon",
        "theme": "closing",
        "source_count": 3,
        "insight_count": 15,
        "last_updated": "2025-12-19"
    }
}
```

---

## FLUXO DE NAVEGAÇÃO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Pergunta: "O que Cole Gordon diz sobre show rates?"                       │
│                                                                             │
│  1. BUSCA RÁPIDA:                                                          │
│     → /knowledge/SOURCES/cole-gordon/SHOW-RATES.md                      │
│     (Resposta direta: tudo que Cole disse sobre show rates)                │
│                                                                             │
│  2. CONTEXTO EXPANDIDO:                                                    │
│     → /knowledge/external/dossiers/persons/DOSSIER-COLE-GORDON.md                │
│     (Visão completa de Cole, todos os temas)                               │
│                                                                             │
│  3. COMPARAÇÃO MULTI-FONTE:                                                │
│     → /knowledge/external/dossiers/THEMES/DOSSIER-SHOW-RATES.md                  │
│     (O que Cole + Jeremy + outros dizem)                                   │
│                                                                             │
│  4. DOCUMENTO ORIGINAL:                                                    │
│     → /inbox/COLE GORDON/PODCASTS/7-ways-show-rates.txt                 │
│     (Transcrição completa para contexto máximo)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PRÓXIMA ETAPA

Output complementa os DOSSIERS. Após SOURCES, o Pipeline Jarvis conclui com:
- Update de Agent MEMORYs (Phase 7)
- Indexação RAG (Phase 8)
- Registro em SESSION-STATE (Phase 9)
