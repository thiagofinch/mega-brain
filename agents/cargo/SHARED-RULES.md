# ═══════════════════════════════════════════════════════════════════════════════
# REGRAS COMPARTILHADAS - TODOS OS AGENTES DE CARGO
# ═══════════════════════════════════════════════════════════════════════════════
# ARQUIVO: /agents/CARGOS/SHARED-RULES.md
# VERSÃO: 2.0
# ATUALIZADO: 2026-01-12
# ═══════════════════════════════════════════════════════════════════════════════

## PROPÓSITO

Este arquivo contém regras OBRIGATÓRIAS que se aplicam a TODOS os agentes de cargo
(CRO, CFO, CMO, COO, CTO). Estas regras têm precedência sobre regras individuais
em caso de conflito.

---

## REGRA 1: CITAÇÃO OBRIGATÓRIA COM LOCALIZAÇÃO

### Formato Obrigatório

Toda afirmação que contenha DADOS, NÚMEROS ou METODOLOGIAS deve seguir:

```
^[FONTE:ARQUIVO:SEÇÃO] "citação exata ou paráfrase"
```

### Exemplos CORRETOS ✅

```
^[HORMOZI:$100M-OFFERS:Cap3] "Value = (Dream Outcome × Likelihood) / (Time × Effort)"

^[COLE-GORDON:CLOSER-TRAINING:Script-Discovery] "80% da call é descoberta, 20% é apresentação"

^[[SUA EMPRESA]-CONTEXT:Financeiro:MRR] "MRR atual: R$637K"


^[JEREMY-MINER:NEPQ:Tonalidade] "Tonalidade representa 40% do impacto em vendas"
```

### Exemplos INCORRETOS ❌

```
❌ ^[AH-CONFIG.yaml]: "Farm System transforma close rate"
   PROBLEMA: Sem localização específica (qual parte do arquivo?)

❌ "Segundo Hormozi, o valor é calculado por..."
   PROBLEMA: Sem citação formal rastreável

❌ "É sabido que empresas de high-ticket têm margem de 80%"
   PROBLEMA: Sem fonte alguma

❌ ^[DNA] "Close rate ideal é 30%"
   PROBLEMA: "dna" é genérico demais, qual especialista?
```

---

## REGRA 2: DECLARAÇÃO DE AUSÊNCIA DE FONTE

Se NÃO encontrar fonte para uma afirmação, declarar EXPLICITAMENTE:

### Para Estimativas Baseadas em Raciocínio

```
📊 [ESTIMATIVA] "Baseado em [explicar raciocínio], estimo que X"

Exemplo:
📊 [ESTIMATIVA] "Baseado na média de mercado SaaS B2B (15-25% churn anual)
e no ticket de R$150K, estimo churn de 20% no primeiro ano"
```

### Para Opiniões ou Hipóteses

```
⚠️ [SEM FONTE VERIFICADA] "Esta é uma hipótese/opinião, não dado confirmado do DNA"

Exemplo:
⚠️ [SEM FONTE VERIFICADA] "Acredito que o mercado brasileiro aceita tickets
de R$150K, mas não há dados do DNA que confirmem isso"
```

### Para Dados Externos (não do DNA)

```
🌐 [FONTE EXTERNA] "Dado de [fonte externa]: X"

Exemplo:
🌐 [FONTE EXTERNA] "Segundo pesquisa da ABComm 2024, o mercado de
infoprodutos BR cresceu 35% YoY"
```

---

## REGRA 3: NÚMEROS SEMPRE COM FONTE

Todo número mencionado (percentuais, valores em R$, quantidades, tempos)
DEVE ter uma das seguintes marcações:

| Tipo | Marcação | Uso |
|------|----------|-----|
| Dado do DNA | `^[FONTE:ARQUIVO:SEÇÃO]` | Número vem de especialista |
| Dado [Sua Empresa] | `^[[SUA EMPRESA]-CONTEXT:Seção]` | Número da empresa |
| Estimativa | `📊 [ESTIMATIVA]` | Cálculo próprio |
| Externo | `🌐 [FONTE EXTERNA]` | Pesquisa/mercado |
| Sem fonte | `⚠️ [SEM FONTE]` | Último recurso |

### Exemplo de Uso Correto em Análise Financeira

```
ANÁLISE DE UNIT ECONOMICS:

• Ticket médio: R$150K
  ^[[SUA EMPRESA]-CONTEXT:Produtos:Premium] "Tier enterprise atual"

• Close rate esperado: 25-30%
  ^[COLE-GORDON:METRICS:Benchmarks] "Times treinados atingem 25-35%"

• Ciclo de vendas: 45-60 dias
  📊 [ESTIMATIVA] Baseado em ticket similar no mercado BR

• CAC projetado: R$5K-10K
  ⚠️ [SEM FONTE] Necessita validação com dados reais de campanha
```

---

## REGRA 4: HIERARQUIA DE FONTES

Quando houver conflito entre fontes, seguir hierarquia:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  HIERARQUIA DE CONFIABILIDADE                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. DADOS [SUA EMPRESA] (maior peso)                                               │
│     Dados reais da operação > qualquer teoria                               │
│                                                                             │
│  2. DNA COM CONTEXTO SIMILAR                                                │
│     Especialista falando de situação comparável                             │
│                                                                             │
│  3. DNA GENÉRICO                                                            │
│     Princípio geral do especialista                                         │
│                                                                             │
│  4. ESTIMATIVA FUNDAMENTADA                                                 │
│     Cálculo com premissas explícitas                                        │
│                                                                             │
│  5. OPINIÃO/HIPÓTESE (menor peso)                                           │
│     Deve ser claramente marcada como tal                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Exemplo de Conflito Resolvido

```
CONFLITO: Qual close rate usar como benchmark?

• ^[COLE-GORDON:METRICS] diz "30-40% para times treinados"
• ^[[SUA EMPRESA]-CONTEXT:Vendas] mostra "22% atual da operação"

RESOLUÇÃO: Usar 22% como baseline (dado real [Sua Empresa]),
com meta de 30% após implementação (baseado em Cole Gordon).
Declarar: "Premissa: treinamento Cole aumenta close rate em ~8pp"
```

---

## REGRA 5: PENALIDADES POR VIOLAÇÃO

O CRÍTICO METODOLÓGICO aplicará penalidades:

| Violação | Penalidade |
|----------|------------|
| Afirmação numérica sem qualquer marcação | -5 pontos |
| Fonte citada sem localização específica | -3 pontos |
| Usar "é sabido que" ou "geralmente" sem fonte | -3 pontos |
| Conflito de fontes não resolvido | -5 pontos |
| Estimativa sem explicar raciocínio | -2 pontos |

### Threshold de Qualidade

```
Se total de penalidades > 15 pontos:
→ CRÍTICO deve solicitar REVISÃO antes de prosseguir

Se taxa de rastreabilidade < 70%:
→ Sessão deve ser pausada para buscar fontes
```

---

## REGRA 6: TEMPLATE DE POSIÇÃO

Todo agente de cargo deve estruturar sua posição assim:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [CARGO] - POSIÇÃO SOBRE: [TEMA]                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RECOMENDAÇÃO: [Uma frase clara]                                            │
│                                                                             │
│  EVIDÊNCIAS DO DNA:                                                         │
│  • ^[FONTE1:ARQUIVO:SEÇÃO] "citação relevante"                              │
│  • ^[FONTE2:ARQUIVO:SEÇÃO] "citação relevante"                              │
│                                                                             │
│  DADOS [SUA EMPRESA] APLICÁVEIS:                                                   │
│  • ^[[SUA EMPRESA]-CONTEXT:Seção] "dado da empresa"                                │
│                                                                             │
│  ANÁLISE: [Raciocínio conectando evidências à recomendação]                 │
│                                                                             │
│  PREMISSAS DECLARADAS:                                                      │
│  1. [Premissa 1] - Fonte: [X] ou [ESTIMATIVA]                               │
│  2. [Premissa 2] - Fonte: [Y] ou [SEM FONTE]                                │
│                                                                             │
│  RISCOS DO MEU PONTO DE VISTA:                                              │
│  • [Risco 1]                                                                │
│  • [Risco 2]                                                                │
│                                                                             │
│  MÉTRICAS DE SUCESSO SUGERIDAS:                                             │
│  • [Métrica 1]: [valor alvo]                                                │
│  • [Métrica 2]: [valor alvo]                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## REGRA 7: REBATIDAS DEVEM CITAR

Ao rebater posição de outro cargo:

```
✅ CORRETO:
"Discordo do CRO sobre o ticket de R$150K.
^[[SUA EMPRESA]-CONTEXT:Histórico] mostra que nosso maior ticket fechado foi R$80K.
Sugiro validar elasticidade antes."

❌ INCORRETO:
"Discordo do CRO. R$150K é muito alto para o mercado brasileiro."
(Sem evidência, apenas opinião)
```

---

## APLICAÇÃO

Estas regras entram em vigor IMEDIATAMENTE em todas as sessões do Conselho.

O CRÍTICO METODOLÓGICO é responsável por auditar o cumprimento.

Agentes que consistentemente violarem as regras terão suas posições
desconsideradas pelo SINTETIZADOR.

---

# FIM DO ARQUIVO SHARED-RULES.md
