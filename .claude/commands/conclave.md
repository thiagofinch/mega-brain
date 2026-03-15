---
description: Sessao completa do Conselho (debate + CRITIC + ADVOCATE + SYNTHESIZER)
argument-hint: [decisao] - Ex: "Mudar modelo de comissao de 10% para 15%?"
---

# /conclave - Sessao do Conselho

## Descricao
Executa o fluxo completo: debate entre cargos + meta-avaliacao pelo conselho (CRITIC, DEVILS-ADVOCATE, SYNTHESIZER).

## Uso
```
/conclave [pergunta ou decisao]
```

## Argumentos
- `pergunta`: A decisao estrategica a ser avaliada

## Exemplos
```
/conclave "Mudar modelo de comissao de closers de 10% para 15%?"
/conclave "Investir R$500k em expansao de time no Q1?"
```

---

## Modo 3D (Tridimensional)

O Conclave opera em 3 dimensoes de contexto:

| Modo | Buckets | Quando Usar |
|------|---------|-------------|
| `expert-only` | B1 (External) | Perguntas teoricas / aprendizado |
| `business` | B1 + B2 (External + Workspace) | Decisoes de negocio |
| `full-3d` | B1 + B2 + B3 (Todos) | Decisoes estrategicas pessoais |
| `personal` | B3 (Personal) | Reflexao pessoal |
| `company-only` | B2 (Workspace) | Analise operacional |

### Leitura em Boxes Individuais

Cada agente convocado DEVE ler os buckets permitidos pelo modo:
- **B1 (External):** knowledge/external/dna/, knowledge/external/dossiers/, knowledge/external/playbooks/
- **B2 (Workspace):** workspace/, logs/WORKSPACE-LOG-TEMPLATE.md
- **B3 (Personal):** knowledge/personal/, logs/PERSONAL-LOG-TEMPLATE.md

Os agentes NAO podem acessar buckets fora do modo selecionado.

### Resposta com Contexto Parcial

Se um bucket NAO esta disponivel no modo selecionado:
- O agente DEVE declarar: "Sem acesso ao bucket [X] neste modo"
- Recomendar modo mais amplo se necessario: "Para esta decisao, recomendo modo `full-3d`"
- NUNCA inventar dados de buckets nao acessados

### Dados Numericos Reais

Quando em modo `business` ou `full-3d`:
- Agentes DEVEM consultar dados reais do workspace (MRR, CAC, LTV, etc.)
- Caminhos: workspace/_finance/, WORKSPACE-LOG-TEMPLATE.md
- Se dados nao existem, declarar: "Dados financeiros nao conectados"

### Secao Obrigatoria na Resposta

Toda resposta do Conclave DEVE incluir footer:

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

> **Workflow:** `core/workflows/wf-conclave.yaml`
> **Templates:** `core/templates/debates/`
> **Agents:** `agents/system/conclave/`
> **Smart Context:** `core/intelligence/query_analyzer.py` + `context_assembler.py`

### PRE-CONCLAVE: Smart Context Assembly

ANTES de iniciar qualquer fase, executar:

1. **Analise da query** via `core/intelligence/query_analyzer.py`:
   - Detectar dominios e agentes relevantes
2. **Montar contexto trimado** via `core/intelligence/context_assembler.py`:
   - MEMORY.md de cada agente: apenas secoes relevantes ao tema
   - Budget total: ~150KB (vs 1.1MB+ em full load)
3. **Reportar economia** no header do conselho

```
═══════════════════════════════════════════════════════════════════════════════
SESSAO DO CONSELHO
═══════════════════════════════════════════════════════════════════════════════

QUERY: {pergunta ou decisao}
DATA: {data atual}
VALOR EM RISCO: R$ {estimativa se possivel}
CONTEXTO: {X}KB trimado (vs {Y}KB full, reducao {Z}%)

═══════════════════════════════════════════════════════════════════════════════
FASE 0: FUNDAMENTO CONSTITUCIONAL
═══════════════════════════════════════════════════════════════════════════════

> Antes de qualquer agente opinar, a Constituição é invocada.
> Os princípios fundamentais GOVERNAM todas as deliberações.

┌─────────────────────────────────────────────────────────────────────────────┐
│  📜 CONSTITUIÇÃO BASE INVOCADA                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚖️  PRINCÍPIO 1: EMPIRISMO                                                │
│      Decisões baseadas em DADOS, não em opiniões ou intuições.             │
│      → Esta deliberação deve citar FONTES e NÚMEROS concretos.             │
│                                                                             │
│  📊 PRINCÍPIO 2: PARETO (80/20)                                            │
│      Buscar os 20% de ações que geram 80% dos resultados.                  │
│      → Qual opção tem maior alavancagem com menor esforço?                 │
│                                                                             │
│  🔄 PRINCÍPIO 3: INVERSÃO                                                  │
│      Antes de O QUE FAZER, perguntar O QUE FARIA FALHAR.                   │
│      → Os agentes devem explicitar riscos de cada opção.                   │
│                                                                             │
│  💪 PRINCÍPIO 4: ANTIFRAGILIDADE                                           │
│      Preferir opções que se BENEFICIAM de volatilidade/incerteza.          │
│      → Qual opção fica mais forte sob estresse?                            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  HIERARQUIA: CONSTITUIÇÃO > PROTOCOLOS > INSTRUÇÕES DO AGENTE              │
│  Qualquer violação dos princípios DEVE ser sinalizada.                     │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
FASE 1: DEBATE ENTRE CARGOS
═══════════════════════════════════════════════════════════════════════════════

{Executar /debate cro,cfo [mesma pergunta]}

(Incluir output completo do debate aqui)

═══════════════════════════════════════════════════════════════════════════════
FASE 2: AVALIACAO DO CRITICO
═══════════════════════════════════════════════════════════════════════════════

Carregar agents/system/conclave/critico-metodologico/AGENT.md e aplicar:

SCORE DE QUALIDADE: {0-100}/100

Breakdown:
• Premissas declaradas:      {0-20}/20
• Evidencias rastreaveis:    {0-20}/20
• Logica consistente:        {0-20}/20
• Cenarios alternativos:     {0-20}/20
• Conflitos resolvidos:      {0-20}/20

GAPS CRITICOS:
• {Gap 1 identificado}
• {Gap 2 identificado}

RECOMENDACAO: {APROVAR / REVISAR / REJEITAR}

═══════════════════════════════════════════════════════════════════════════════
FASE 3: ADVOGADO DO DIABO
═══════════════════════════════════════════════════════════════════════════════

Carregar agents/system/conclave/advogado-do-diabo/AGENT.md e aplicar:

PREMISSA MAIS FRAGIL:
{Qual e por que}

RISCO PRINCIPAL NAO DISCUTIDO:
{Descricao + probabilidade + impacto}

CENARIO DE ARREPENDIMENTO (12 meses):
{Narrativa do pior caso realista}

ALTERNATIVA IGNORADA:
{Opcao nao considerada que merece analise}

═══════════════════════════════════════════════════════════════════════════════
FASE 4: SINTESE FINAL
═══════════════════════════════════════════════════════════════════════════════

Carregar agents/system/conclave/sintetizador/AGENT.md e aplicar:

DECISAO RECOMENDADA:
{Recomendacao clara e acionavel}

MODIFICACOES APLICADAS:
{O que foi ajustado baseado no feedback do Critico e Advogado}

CONFIANCA: {0-100}%
{Justificativa do nivel de confianca}

RISCOS RESIDUAIS:
• {Risco 1}: Mitigacao: {acao}
• {Risco 2}: Mitigacao: {acao}

PROXIMOS PASSOS:
1. {Acao} - Responsavel: {quem} - Prazo: {quando}
2. {Acao} - Responsavel: {quem} - Prazo: {quando}
3. {Acao} - Responsavel: {quem} - Prazo: {quando}

CRITERIOS DE REVERSAO:
SE {condicao} ENTAO reconsiderar decisao
SE {condicao} ENTAO pausar execucao

═══════════════════════════════════════════════════════════════════════════════
```

---

## SE CONFIANCA < 60%

```
═══════════════════════════════════════════════════════════════════════════════
[CONSELHO: DECISAO INCONCLUSIVA]

⚠️ CONFIANCA: {X}% - ABAIXO DO THRESHOLD DE 60%

TIPO DE INCERTEZA:
[ ] Dados insuficientes
[ ] Conflito irresolvivel entre cargos
[ ] Fora do escopo do conhecimento disponivel

OPCOES PARA DECISAO HUMANA:

OPCAO A: {descricao}
  Trade-off: {o que ganha} vs {o que perde}
  Defendida por: {cargos}
  Evidencias: {IDs}

OPCAO B: {descricao}
  Trade-off: {o que ganha} vs {o que perde}
  Defendida por: {cargos}
  Evidencias: {IDs}

OPCAO C: Buscar mais informacoes
  O que falta: {dados necessarios}
  Como obter: {acoes}

⚠️ Este caso requer DECISAO HUMANA.
O Conselho NAO esta recomendando nenhuma opcao.
═══════════════════════════════════════════════════════════════════════════════
```

---

## NOTAS

- Conselho passa UMA vez por query (anti-loop rule)
- Se confianca < 60%, escalar para humano, nao re-rodar
- CRITIC avalia processo, nao merito
- ADVOCATE busca vulnerabilidades, nao confirma
- SYNTHESIZER integra, nao faz media
