# MEMORY: Especialista em MercadoLivre Ads & Vendas

> **Criação:** 2026-03-09
> **Última atualização:** 2026-03-09
> **Entradas:** 25+ padrões documentados
> **Estado:** Inicializado com Manual v2.0

---

## PADRÕES IDENTIFICADOS

### Padrão #1: Margem é mais importante que volume

**Frequência:** Aparece em todas as decisões de preço
**Contexto comum:** Novo produto, pressão de concorrência
**Resposta típica:**
- Não vender se margem < 15%
- Preferir vender menos com mais margem
- Aumentar preço antes de fazer promoção

**Aprendizado:** Um cliente com margem de 40% (vendendo 10) > um com 5% (vendendo 100)

**Fonte:** Manual #3.2, Heurística #15

---

### Padrão #2: TACOS é o gatilho para pausar

**Frequência:** Aparece sempre que anúncio está caro
**Contexto comum:** Budget crescendo, ROAS caindo
**Resposta típica:**
- Monitorar TACOS diariamente
- TACOS < 20% = manter
- TACOS 20-25% = revisar budget
- TACOS > 25% = pausar imediatamente

**Aprendizado:** Mais rápido pausar e reajustar que deixar queimar dinheiro

**Fonte:** Manual #2.1, Heurística #2

---

### Padrão #3: Conversão fraca = problema de qualidade, não tráfego

**Frequência:** Erro comum em novo produtos
**Contexto comum:** Anúncio rodando, visitantes chegando, mas não converte
**Resposta típica:**
- Verificar: foto ruim, descrição confusa, preço errado
- Melhorar qualidade ANTES de aumentar tráfego
- Testar preço menor (+5-10 BRL) como primeiro teste

**Aprendizado:** Jogar mais dinheiro em tráfego não resolve problema de qualidade

**Fonte:** Manual #3.3, Heurística #23

---

### Padrão #4: Sazonalidade não é excuse, é oportunidade

**Frequência:** Aparece todo mês com feriados, estações
**Contexto comum:** Dezembro, Carnaval, Black Friday
**Resposta típica:**
- Preparar 3 meses antes: estoque, anúncios, bundles
- Aumentar bid 2-3 semanas antes
- Ter estoque 2x o normal (logística fica lenta)

**Aprendizado:** Vender no feriado é mais fácil do que em dia normal

**Fonte:** Manual #6.1, Heurística #25

---

### Padrão #5: Bundle vende 3x mais, aumenta ticket

**Frequência:** Funciona para todos produtos
**Contexto comum:** Quando volume está caindo
**Resposta típica:**
- Criar kit com desconto 10% vs individual
- Testar com oferta relâmpago
- Resultado: +95 BRL ticket, +3x conversão

**Aprendizado:** Bundle é "cheat code" para aumentar AOV

**Fonte:** Manual #6.2, Heurística #12

---

## DECISÕES REGISTRADAS

### 2026-03-09 — Audit completo MLB5311691200 (Moletom Hugo Jobs)

**Item:** Moletom Masculino Zíper Hugo Jobs — MLB5311691200
**Categoria:** MLB108807 | **Listing:** gold_special | **Loja Oficial:** 76158
**Estado antes:** R$77,99 | 510 vendas | 4,5 estrelas (65 reviews) | 7.667 em estoque

**Variações:**
- Preto × P/M/G/GG: 387 vendas (76% do volume) — G e GG lideram
- Cinza-claro × P/M/G/GG: 82 vendas (16%) — value_id: null (cor não oficial ML)

**Decisões tomadas:**
| Ação | Decisão | Motivo |
|------|---------|--------|
| Preço | R$77,99 → R$84,99 (+9%) | CVR 2,58% sustenta. ROAS melhora automaticamente |
| Garantia | 60d → 90d | Diferencial de confiança |
| Cinza-claro fix | ABANDONADO | Bids bloqueiam PATCH. 82 vendas valem mais que filtro de cor |
| Novas cores | NÃO LANÇAR | Decisão final do usuário |

**Status:** Preço + Garantia pendentes de execução (PUT /items/MLB5311691200)

**Aprendizado:** Antes de planejar correção de atributo, verificar se há bids ativos na variation

---

### 2026-03-09 — Framework de Go/No-Go para PADS

**Contexto:** Novo produto Hugo Jobs (moletom)
**Decisão:** Ativar anúncio com 50 BRL/dia, target ROAS 3.5x
**Status:** Pendente implementação
**Aprendizado:** Começar pequeno permite testar sem risco
**Fonte:** Manual #3.2, Framework Go/No-Go

---

## RESTRIÇÕES DA ML API (CRÍTICO)

### ❌ attribute_combinations bloqueado com bids ativos
- **Endpoint:** PUT /items/{id} com payload `variations[].attribute_combinations`
- **Erro:** HTTP 400 — "You cannot change attribute combinations if the variation has bids"
- **Causa:** Product Ads ativo na variation bloqueia alteração de atributos (cor/tamanho)
- **Solução:** Pausar ads da variation → alterar → reativar
- **Detectado em:** 2026-03-09, MLB5311691200 tentativa de corrigir Cinza-claro
- **Implicação prática:** Sempre verificar se há ads ANTES de planejar correções de variação

### ✅ Campos alteráveis sem restrição (PATCH direto)
- `price` — funciona sempre
- `sale_terms` (WARRANTY_TIME) — funciona sempre
- `title`, `description` — funciona sempre
- `available_quantity` por variation — funciona sempre

---

## CVR REAL vs DECLARADO

**Fórmula:** `CVR real = sold_quantity / visits`

O ML exibe CVR diferente do real. Sempre calcular antes de decisão de preço.

Exemplo: MLB5311691200 → 510/19.765 = **2,58%** (ML declarava 3,4%)

---

## ESTRATÉGIA ROAS vs PREÇO

**Subir preço melhora ROAS automaticamente** (mesmo ad spend → mais receita por venda)

Regra prática:
- CVR 2-3%: subida de 8-10% (conservadora)
- CVR > 3%: subida de 10-15% (agressiva)
- CVR < 2%: investigar causa antes

---

## CONHECIMENTO DE HUGO JOBS

### Account Overview
- **Seller ID:** 694166791
- **Reputation:** 5 GREEN (9.142 transações)
- **Status:** Saudável
- **Official Store:** 76158
- **Listing padrão:** gold_special

### Performance (2026-03-08)
- **Vendas:** 45 pedidos
- **Faturamento:** 2.679,14 BRL
- **Ticket Médio:** 59,54 BRL
- **Margem Líquida:** 22,3%

### CMV Database (Hugo Jobs)
| Produto | CMV | Preço Atual | Margem |
|---------|-----|-------------|--------|
| Moletom Zíper MLB5311691200 | ~44,99 | R$77,99 | ~22% |
| Camiseta | [precisa atualizar] | [precisa] | [precisa] |

---

## MÉTRICAS CRÍTICAS (RASTREAMENTO)

### Targets Pessoais
- ROAS: sempre > 3.5x
- TACOS: nunca > 20%
- Margem Líquida: sempre > 25%
- Conversão: +5% acima média da categoria
- Resposta: < 30 minutos para cliente

### Score de Saúde (por conta)
Hugo Jobs:
- Margem: ✅ 22,3% (OK, pode melhorar)
- Conversão: ✅ Orgânica 100% (ótimo)
- Volume: ⚠️ 45/dia (pode 2x com ads)
- Overall: 🟡 Saudável, pronto para escalar

---

## LIÇÕES APRENDIDAS

1. **Começar pequeno com ads** — 50 BRL/dia permite testar sem risco
2. **Margem > Volume** — Sempre
3. **Pausar rápido** — TACOS > 25% = stop, não negociar
4. **Framework é ouro** — 3 Camadas de preço, Go/No-Go, Diagnóstico
5. **Bundle vende** — Sempre testar
6. **Sazonalidade é planejamento** — Preparar 3 meses antes
7. **Resposta rápida** — < 30 min é ouro no algoritmo ML
8. **Foto > Ad spend** — Melhorar qualidade antes de aumentar tráfego

---

## PRÓXIMAS AÇÕES (ROADMAP)

### Semana 1 (Atual)
- [ ] Ativar PADS Hugo Jobs (50 BRL/dia)
- [ ] Medir ROAS por 7 dias
- [ ] Preparar bundle moletom + camiseta

### Semana 2-3
- [ ] Teste de preço (67,87 → 75,99)
- [ ] Executar Framework #3 (Preço 3 Camadas)
- [ ] Revisar Minha Página

### Mês 1 Goal
- ROAS 3.5x+ ✅
- TACOS < 20% ✅
- Volume 2x (3.500 BRL/dia)

### Mês 2-3
- Escalar budget para 100+ BRL/dia
- Testar 5 novos produtos
- Documentar aprendizados em MEMORY

---

## INTEGRAÇÃO COM SISTEMA

### Consulta ao Manual do Gestor
- Sempre referir às 25 heurísticas
- Sempre usar um dos 3 frameworks principais
- Sempre documentar decisão em MEMORY

### Consulta a Ferramentas
- Dashboard: fetch_dashboard_data.py (atualizado 1x/dia)
- Ranking: update-ranking-final.py (produtos por lucro)
- Métricas: ClickUp Task 86ag0ugy0 (Manual completo)

### Escalação
- Se conflito estratégico → Conclave
- Se questão financeira → CFO
- Se questão de dados → Data Analyst

---

## VALIDAÇÃO PRÉ-RESPOSTA

Antes de responder qualquer pergunta, verificar:
- [ ] Qual framework se aplica?
- [ ] Qual heurística resolve isso?
- [ ] Tenho precedente em MEMORY?
- [ ] Posso citar o Manual?
- [ ] Resposta alinha com "Margem > Volume"?

---

**Status:** Ativo e monitorando
**Próximo sync:** 2026-03-16 (revisão semanal)
**Criado por:** JARVIS + Manual do Gestor v2.0
