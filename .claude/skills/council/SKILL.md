---
name: council
version: 1.0.0
description: Sessao completa do Conselho (debate + CRITIC + ADVOCATE + SYNTHESIZER)
triggers:
  - conselho
  - council
  - debate
  - decisao
  - war room
  - multiplas perspectivas
user_invocable: true
---

# SKILL: Council - Conselho de Especialistas

## Proposito

Ativar o Conselho de Especialistas para decisoes estrategicas de alta complexidade. Aplica processo estruturado de debate, critica metodologica, advocacia do diabo e sintese final.

## Quando Usar

- Decisoes de alto impacto (R$ > 100K)
- Mudancas estrategicas significativas
- Trade-offs complexos sem resposta obvia
- Validacao de hipoteses criticas
- Analise de riscos multi-dimensional
- Quando multiplas perspectivas sao necessarias

## Contexto Obrigatorio

Antes de responder, CARREGAR:

```
OBRIGATORIO:
1. /system/protocols/conclave/CONCLAVE-PROTOCOL.md
2. /system/protocols/conclave/DEBATE-PROTOCOL.md
3. /system/protocols/conclave/DEBATE-DYNAMICS-PROTOCOL.md
4. /[sua-empresa]/[SUA EMPRESA]-CONTEXT.md (contexto operacional)

AGENTES DO CONSELHO:
- /agents/council/critico-metodologico/AGENT.md
- /agents/council/advogado-do-diabo/AGENT.md
- /agents/council/sintetizador/AGENT.md

OPCIONAL (se decisao envolve):
- /[sua-empresa]/agents/AGENT-FINANCE.md (decisoes financeiras)
- /[sua-empresa]/agents/AGENT-TALENT.md (decisoes de contratacao)
```

## Fluxo de Execucao

### Fase 0: Invocar Constituicao

```
ANTES de qualquer agente opinar, exibir os 4 principios:
1. EMPIRISMO - Decisoes baseadas em DADOS
2. PARETO (80/20) - Buscar alavancagem maxima
3. INVERSAO - Perguntar o que faria FALHAR
4. ANTIFRAGILIDADE - Preferir opcoes que se fortalecem sob estresse
```

### Fase 1: Debate entre Cargos

```
Identificar cargos relevantes para a decisao:
- CRO (vendas)
- CFO (financas)
- CMO (marketing)
- COO (operacoes)
- CTO (tech)

Cada cargo apresenta posicao + evidencias
Rodadas de rebatidas cruzadas
Sintese de consensos e divergencias
```

### Fase 2: Critico Avalia

```
Score de Qualidade (0-100):
- Premissas declaradas: 0-20
- Evidencias rastreaveis: 0-20
- Logica consistente: 0-20
- Cenarios alternativos: 0-20
- Conflitos resolvidos: 0-20

Recomendacao: APROVAR / REVISAR / REJEITAR
```

### Fase 3: Advogado do Diabo

```
4 questoes obrigatorias:
1. Premissa mais fragil?
2. Risco nao discutido?
3. Cenario de arrependimento (12 meses)?
4. Alternativa ignorada?
```

### Fase 4: Sintese Final

```
- Decisao recomendada (clara, acionavel)
- Modificacoes baseadas no feedback
- Confianca: 0-100%
- Riscos residuais + mitigacoes
- Proximos passos com responsavel/prazo
- Criterios de reversao
```

### Fase 5: Threshold de Confianca

```
>= 70%: Emitir decisao final
50-69%: Emitir com ressalvas (CONFIANCA MEDIA)
< 50%: NAO emitir, escalar para humano
```

## Principios Inviolaveis

1. **Constituicao Primeiro** - Principios governam tudo
2. **Conselho NAO tem DNA de dominio** - Avalia processo, nao merito
3. **Critico avalia PROCESSO** - Nao diz se esta "certo"
4. **Advocate NAO confirma** - Funcao e ATACAR
5. **Synthesizer INTEGRA** - Nao faz media, escolhe caminho
6. **Fallback < 50%** - Escalar para humano

## Exemplo de Uso

**Usuario:** "/conclave Devemos pivotar de infoproduto para SaaS?"

**JARVIS (ativando CONCLAVE):**

```
=======================================================================
SESSAO DO CONSELHO
=======================================================================

QUERY: Pivotar de infoproduto para SaaS?
DATA: 2026-01-11
VALOR EM RISCO: R$ XXXk MRR + custos de transicao

=======================================================================
FASE 0: FUNDAMENTO CONSTITUCIONAL
=======================================================================

[Exibe os 4 principios]

=======================================================================
FASE 1: DEBATE ENTRE CARGOS
=======================================================================

[CRO opina sobre impacto em vendas]
[CFO opina sobre unit economics]
[CTO opina sobre viabilidade tecnica]

=======================================================================
FASE 2: AVALIACAO DO CRITICO
=======================================================================

SCORE: 72/100

Breakdown:
- Premissas declaradas: 18/20
- Evidencias rastreaveis: 14/20 (gap: dados de churn)
...

=======================================================================
FASE 3: ADVOGADO DO DIABO
=======================================================================

PREMISSA MAIS FRAGIL:
"Assumimos que mercado SaaS absorvera clientes atuais"

RISCO NAO DISCUTIDO:
Competidores ja estabelecidos no SaaS...

=======================================================================
FASE 4: SINTESE FINAL
=======================================================================

DECISAO RECOMENDADA:
Pivotar em 2 fases com validacao intermediaria...

CONFIANCA: 68% (MEDIA)

RISCOS RESIDUAIS:
1. Perda de base durante transicao
2. ...

PROXIMOS PASSOS:
1. MVP SaaS em 60 dias - Andre (CTO)
2. Validar com 50 clientes - [Head Comercial]
...
```

## Integracao com Outros Agentes

```
COUNCIL pode convocar:
- AGENT-FINANCE: Para analise financeira detalhada
- AGENT-TALENT: Para avaliar impacto em time
- PERSON Agents: Para perspectivas de especialistas (Jeremy Haynes, etc.)
```

---

**Ultima Atualizacao:** 2026-01-11
**User Story:** US-025
