---
description: Debate estruturado entre cargos com sintese de consensos e divergencias
argument-hint: [cargo1,cargo2,...] [decisao] - Ex: cro,cfo "Investir R$200k em ads?"
---

# /debate - Debate entre Cargos

## Descricao
Simula debate estruturado entre agentes de cargo, gerando sintese com consensos e divergencias.

## Uso
```
/debate [cargo1,cargo2,...] [pergunta ou decisao]
```

## Argumentos
- `cargos`: Lista de cargos separados por virgula (cro,cfo,sm)
- `pergunta`: A decisao a ser debatida

## Exemplos
```
/debate cro,cfo "Investir R$200k em ads no proximo trimestre?"
/debate cro,cfo,closer "Mudar modelo de comissao de % para fixo?"
```

---

## Modo 3D (Tridimensional)

O Debate opera em 3 dimensoes de contexto:

| Modo | Buckets | Quando Usar |
|------|---------|-------------|
| `expert-only` | B1 (External) | Perguntas teoricas / aprendizado |
| `business` | B1 + B2 (External + Workspace) | Decisoes de negocio |
| `full-3d` | B1 + B2 + B3 (Todos) | Decisoes estrategicas pessoais |
| `personal` | B3 (Personal) | Reflexao pessoal |
| `company-only` | B2 (Workspace) | Analise operacional |

### Leitura em Boxes Individuais

Cada cargo participante DEVE ler os buckets permitidos pelo modo:
- **B1 (External):** knowledge/external/dna/, knowledge/external/dossiers/, knowledge/external/playbooks/
- **B2 (Workspace):** workspace/, logs/WORKSPACE-LOG-TEMPLATE.md
- **B3 (Personal):** knowledge/personal/, logs/PERSONAL-LOG-TEMPLATE.md

Os cargos NAO podem acessar buckets fora do modo selecionado.

### Resposta com Contexto Parcial

Se um bucket NAO esta disponivel no modo selecionado:
- O cargo DEVE declarar: "Sem acesso ao bucket [X] neste modo"
- Recomendar modo mais amplo se necessario: "Para esta decisao, recomendo modo `business` ou `full-3d`"
- NUNCA inventar dados de buckets nao acessados

### Dados Numericos Reais

Quando em modo `business` ou `full-3d`:
- Cargos DEVEM consultar dados reais do workspace (MRR, CAC, LTV, etc.)
- Caminhos: workspace/_finance/, WORKSPACE-LOG-TEMPLATE.md
- Se dados nao existem, declarar: "Dados financeiros nao conectados"

### Secao Obrigatoria na Sintese

A sintese do debate (Fase 3) DEVE incluir footer:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONTEXTO UTILIZADO                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Modo: {modo selecionado}                                                   │
│  B1 (Expert):    {SIM/NAO} - {N arquivos consultados}                      │
│  B2 (Business):  {SIM/NAO} - {N arquivos consultados}                      │
│  B3 (Personal):  {SIM/NAO} - {N arquivos consultados}                      │
│  Dados reais:    {SIM/NAO} - {quais metricas}                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## INSTRUCOES DE EXECUCAO

> **Workflow:** `core/workflows/wf-conclave.yaml` (phase 1)
> **Templates:** `core/templates/debates/debate-protocol.md`
> **Agents:** `agents/cargo/` (by role)
> **Smart Context:** `core/intelligence/query_analyzer.py` + `context_assembler.py`

```
═══════════════════════════════════════════════════════════════════════════════
DEBATE: {pergunta ou decisao}
DATA: {data atual}
PARTICIPANTES: {lista de cargos}
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 0: SMART CONTEXT ASSEMBLY (pre-debate)                                 │
└─────────────────────────────────────────────────────────────────────────────┘

ANTES de carregar qualquer agente, executar analise da query:

1. ANALISAR QUERY via core/intelligence/query_analyzer.py:
   - Detectar dominios relevantes (vendas, compensation, etc.)
   - Identificar agentes mencionados explicitamente
   - Se cargos NAO foram especificados, recomendar com base nos dominios

2. MONTAR CONTEXTO TRIMADO via core/intelligence/context_assembler.py:
   - AGENT.md: primeiras 50 linhas (identidade)
   - SOUL.md: completo (voz)
   - DNA-CONFIG.yaml: completo (routing)
   - MEMORY.md: APENAS secoes relevantes aos dominios detectados
   - Budget: ~30KB por agente, ~150KB total

3. REPORTAR economia:
   "Contexto: {X}KB (vs {Y}KB full load, reducao {Z}%)"

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: POSICOES INDIVIDUAIS                                                │
└─────────────────────────────────────────────────────────────────────────────┘

PARA CADA CARGO:

1. CARREGAR (via Smart Context Assembly - JA TRIMADO):
   - BASE-CONSTITUTION.md
   - DNA-CONFIG.yaml do cargo (completo)
   - MEMORY.md do cargo (secoes relevantes apenas)

2. APLICAR REASONING-MODEL-PROTOCOL.md

3. GERAR posicao no formato:

┌─ POSICAO: {CARGO} ──────────────────────────────────────────────────────────┐
│                                                                             │
│ RECOMENDACAO:                                                               │
│ {Posicao clara em 2-3 frases}                                              │
│                                                                             │
│ RACIOCINIO:                                                                 │
│ {Camadas de DNA usadas e como}                                             │
│                                                                             │
│ EVIDENCIAS:                                                                 │
│ • {ID}: "{citacao}"                                                        │
│ • {ID}: "{citacao}"                                                        │
│                                                                             │
│ CONFIANCA: {0-100}%                                                         │
│                                                                             │
│ LIMITACOES:                                                                 │
│ • {O que nao sei}                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: REBATIDAS CRUZADAS                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

CADA CARGO agora VE as posicoes dos outros e gera:

┌─ REBATIDA: {CARGO} ─────────────────────────────────────────────────────────┐
│                                                                             │
│ CONCORDO COM:                                                               │
│ • {CARGO X} sobre {ponto}: {por que}                                       │
│                                                                             │
│ DISCORDO DE:                                                                │
│ • {CARGO Y} sobre {ponto}: {por que + evidencia propria}                   │
│                                                                             │
│ PONTO CEGO IDENTIFICADO:                                                    │
│ • {CARGO Z} nao considerou: {aspecto}                                      │
│                                                                             │
│ MANTENHO MINHA POSICAO? {Sim/Nao/Parcialmente}                             │
│ {Se mudou, explicar por que}                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: SINTESE DO DEBATE                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
PONTOS DE CONSENSO (Alta confianca para decisao)
═══════════════════════════════════════════════════════════════════════════════

• {Ponto 1 que todos concordam}
• {Ponto 2 que todos concordam}

═══════════════════════════════════════════════════════════════════════════════
PONTOS DE DIVERGENCIA
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ DIVERGENCIA 1: {tema}                                                       │
│ ─────────────────────                                                       │
│ Natureza: {dados/prioridades/timing/risco}                                 │
│                                                                             │
│ • {CARGO1} defende: {posicao}                                              │
│ • {CARGO2} defende: {posicao}                                              │
│                                                                             │
│ Impacto se nao resolvido: {consequencia}                                   │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
TENSOES PRODUTIVAS (Nao resolver - sao features)
═══════════════════════════════════════════════════════════════════════════════

• {Tensao 1}: {Por que e produtiva}

═══════════════════════════════════════════════════════════════════════════════
LACUNAS IDENTIFICADAS
═══════════════════════════════════════════════════════════════════════════════

• {Informacao que ninguem tinha e precisa ser buscada}

═══════════════════════════════════════════════════════════════════════════════
```

---

## QUANDO ESCALAR PARA CONCLAVE

```
SE qualquer das condicoes:
  • Divergencia nao resolvida em tema CRITICO
  • Confianca media < 70%
  • Valor em risco > R$100k
  • Decisao irreversivel

ENTAO:
  Sugerir ao usuario: "Recomendo /conclave para meta-avaliacao"
```

---

## NOTAS

- Cada cargo defende SUA LENTE (CRO olha revenue, CFO olha unit economics)
- Divergencia explicita > consenso artificial
- Citar evidencias de DNA sempre que possivel
