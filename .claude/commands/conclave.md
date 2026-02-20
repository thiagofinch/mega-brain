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

## INSTRUCOES DE EXECUCAO

Seguir /system/protocols/conclave/CONCLAVE-PROTOCOL.md

```
═══════════════════════════════════════════════════════════════════════════════
SESSAO DO CONSELHO
═══════════════════════════════════════════════════════════════════════════════

QUERY: {pergunta ou decisao}
DATA: {data atual}
VALOR EM RISCO: R$ {estimativa se possivel}

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

Carregar /agents/council/CRITIC.md e aplicar:

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

Carregar /agents/council/DEVILS-ADVOCATE.md e aplicar:

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

Carregar /agents/council/SYNTHESIZER.md e aplicar:

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
