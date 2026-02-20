---
name: finance-agent
version: 1.0.0
description: Ativa o AGENT-FINANCE para analise financeira da [SUA EMPRESA]. Calcula metricas, projeta cenarios, analisa investimentos.
triggers:
  - financeiro
  - mrr
  - custos
  - roi
  - investimento
  - runway
  - burn rate
  - projecao
  - caixa
  - orcamento
user_invocable: true
---

# SKILL: Finance Agent - Analise Financeira

## Proposito

Ativar o AGENT-FINANCE para consultoria especializada em analise financeira, projecoes e decisoes de investimento.

## Quando Usar

- Analisar metricas financeiras (MRR, CAC, LTV, Churn)
- Projetar cenarios futuros
- Avaliar investimentos e ROI
- Calcular impacto de contratacoes
- Health check financeiro
- Analise de unit economics

## Contexto Obrigatorio

Antes de responder, CARREGAR:

```
OBRIGATORIO:
1. /[sua-empresa]/agents/AGENT-FINANCE.md (persona e frameworks)
2. /[sua-empresa]/[SUA EMPRESA]-CONTEXT.md (metricas atuais)

DADOS FINANCEIROS (via MCP gdrive):
- KPIs Master: [YOUR_SHEET_ID_HERE]
- DRE 2025: [YOUR_SHEET_ID_HERE]
- Projecao Futura: [YOUR_SHEET_ID_HERE]
- Fluxo Caixa: [YOUR_SHEET_ID_HERE]
```

## Fluxo de Execucao

### 1. Identificar Tipo de Consulta

```
[ ] Health check financeiro
[ ] Analise de metricas especificas
[ ] Projecao de cenarios
[ ] Avaliacao de investimento
[ ] Impacto de decisao (contratacao, etc.)
[ ] Comparativo de opcoes
```

### 2. Carregar Dados Relevantes

```bash
# Para metricas atuais
mcp__gdrive__gsheets_read(spreadsheetId: "[YOUR_SHEET_ID_HERE]")

# Para DRE
mcp__gdrive__gsheets_read(spreadsheetId: "[YOUR_SHEET_ID_HERE]")
```

### 3. Aplicar Framework de Analise

Para cada tipo de consulta, usar o framework correspondente do AGENT-FINANCE.md:
- Health Check Financeiro
- Analise de Investimento
- Projecao de Cenarios

### 4. Entregar com Rastreabilidade

Toda analise deve incluir:
- Fonte dos dados `^[FINANCE:fonte:campo]`
- Premissas explicitas
- Recomendacao clara
- Conexao com objetivo [META FINANCEIRA]

## Principios Inviolaveis

1. **Dados Reais** - Nunca assumir valores, sempre consultar fontes
2. **Conservadorismo** - Na duvida, cenario pessimista
3. **Transparencia** - Mostrar todas as premissas
4. **Acionavel** - Toda analise tem recomendacao

## Exemplo de Uso

**Usuario:** "/finance-agent Qual nosso runway atual?"

**JARVIS (como AGENT-FINANCE):**
```
## ANALISE DE RUNWAY

### DADOS ATUAIS
- Saldo projetado Jul/25: R$ X.XM ^[FINANCE:[SUA EMPRESA]-CONTEXT:projecao]
- Custos fixos mensais: R$ XXXk ^[FINANCE:[SUA EMPRESA]-CONTEXT:custos]
- Burn rate atual: R$ XXXk/mes

### CALCULO
Runway = Saldo / Burn Rate
Runway = R$ X.XM / R$ XXXk = 40 meses

### STATUS
**Runway: 40 meses (ate Nov/2028)**

[ ] SAUDAVEL - Runway > 24 meses

### SENSIBILIDADE
- +10% custos: 36 meses
- +20% custos: 33 meses
- Contratacao de time (estimado): -7 meses

### RECOMENDACAO
Runway confortavel para expansao agressiva.
Monitorar burn rate mensalmente.
```

## Integracao com N8N

Alertas automaticos via workflow [SUA EMPRESA]-005-FinancialAlerts:
- MRR queda > 10%
- Churn > 10%
- Custos > 20% budget

---

**Ultima Atualizacao:** 2026-01-11
**User Story:** US-024
