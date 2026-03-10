# MEMORY: LISTING-OPTIMIZER

> **Versão:** 1.0.0
> **Atualizado:** 2026-03-02
> **Propósito:** Conhecimento base sobre ranking do MercadoLivre e otimização de anúncios
> **Natureza:** HÍBRIDO (CARGO)

---

## 📋 CRITÉRIOS DE RANKING DO MERCADOLIVRE

O algoritmo de ranking ML utiliza estes 4 fatores principais (por peso):

### FATOR 1: Qualidade do Anúncio (40% do peso)
**O que é:** Health Score da plataforma (0-100 pontos)

**Componentes:**
- **Título (60-80 caracteres exibidos, máx 255 cadastrado)**
  - Palavra-chave principal NO INÍCIO
  - Evitar caracteres especiais
  - Exemplo bom: "iPhone 13 128GB Preto Original A2633"
  - Exemplo ruim: "*** IMPERDÍVEL !!! MEGA OFERTA iPhone ***"

- **Imagens (6+ recomendado, mínimo 1)**
  - Resolução mínima: 1200x1200 px
  - 1ª foto: fundo branco, produto centrado
  - 2-6: ângulos diferentes, detalhe de defeitosse houver
  - Sem marcas d'água, sem logos
  - Sem fotos de estoque genéricas

- **Descrição (500+ chars, ideal 1000+)**
  - Primeiro parágrafo resume o produto em 2-3 linhas
  - Inclui benefícios principais
  - Menciona condição, defeitos, limitações
  - Links e redes sociais: EVITAR (ML penaliza)

- **Ficha Técnica (100% dos atributos obrigatórios)**
  - Variam por categoria (ver endpoint `get_category_attributes`)
  - Exemplo Eletrônicos: Marca, Modelo, Cor, Voltagem, Tipo de Bateria
  - Faltam campos = lista invisível para filtros

- **Frete (prazo confirmado)**
  - Confirmar em < 2 dias úteis
  - Usar Mercado Envios quando possível
  - Melhor score com frete sem custo

### FATOR 2: Desempenho do Vendedor (30% do peso)
**O que é:** Reputação da conta (independente do anúncio)

**Métricas (HUGOJOBS ATUAL - Power Seller Silver):**
- Taxa de cancelamento: < 2% ✅ (em dia)
- Taxa de devolução: < 5% ✅ (em dia)
- Tempo de resposta: < 12h ✅ (em dia)
- Feedback positivo: > 95% ✅ (HUGOJOBS tem 65% = ATENÇÃO)

**AÇÃO:** Campanhas para aumentar feedback positivo.

### FATOR 3: Histórico de Vendas (20% do peso)
**O que é:** Performance do PRÓPRIO anúncio

**Métricas:**
- Quantidade vendida (recência importa mais que total)
- Taxa de conversão (visualizações → compras)
- Velocidade de venda (quanto tempo entre visualizações e venda)
- Retorno de clientes

**Bootstrap:** Novos anúncios começam com score baixo → precisa de vendas rápidas para subir.

### FATOR 4: Relevância (10% do peso)
**O que é:** Alinhamento entre busca e anúncio

**Componentes:**
- Keyword matching (exato na descrição)
- Variações de termos (ex: "notebook" vs "laptop")
- Sinonímia ("celular" vs "smartphone")

---

## 📍 23 CAMPOS CRÍTICOS POR ANÚNCIO

### Bloco 1: OBRIGATÓRIOS (sem, o anúncio não publica)
1. **Título** — até 255 chars (60 exibidos em busca)
2. **Categoria** — deve ser exata (impacta atributos disponíveis)
3. **Preço** — valor numérico
4. **Estoque/Quantidade** — > 0 para publicar
5. **1ª Foto** — obrigatória para publicar
6. **Condição** — NOVO ou USADO

### Bloco 2: CRÍTICOS PARA HEALTH ALTO (impactam ranking 40%)
7. **Descrição** — mín 500 chars, ideal 1000+
8-12. **Fotos 2-6** — 5 fotos adicionais = 6 total (recomendado)
13. **Tipo de Anúncio** — Clássico vs Premium
14. **Peso do Produto** — para cálculo de frete automático
15. **Dimensões** — (L x A x P em cm)
16. **Prazo de Envio** — confirmado em dias úteis
17. **Método de Envio** — Mercado Envios vs próprio
18. **Garantia** — se aplicável

### Bloco 3: FICHA TÉCNICA (variam por categoria, via API)
19-23. **Atributos Obrigatórios da Categoria**
- Exemplo Eletrônicos: Marca, Modelo, Cor, Voltagem, Garantia
- Exemplo Roupas: Marca, Tamanho, Cor, Material, Gênero
- Exemplo Agro: Tipo, Marca, Peso, Quantidade, Safra

**OBS:** Sem estes, o anúncio fica invisível para quem filtra por atributos.

---

## 🎯 PADRÕES IDENTIFICADOS (TOP SELLERS)

### Padrão 1: Título Otimizado
- Começa com palavra-chave (ex: "iPhone")
- Inclui especificação principal (ex: "128GB")
- Inclui diferencial (ex: "Original" ou "Lacrado")
- **Exemplo:** "iPhone 13 128GB Preto Lacrado Original Nota Fiscal"

### Padrão 2: Descrição Estruturada
- 1º parágrafo: resumo executivo (3 linhas)
- 2º parágrafo: especificações técnicas completas
- 3º parágrafo: estado físico (riscos, defeitos, garantia)
- 4º parágrafo: detalhes de entrega e segurança
- Evita: "clique aqui", links, emojis excessivos

### Padrão 3: Fotos Profissionais
- 1ª foto: produto inteiro, fundo branco, sem sombra
- 2ª foto: detalhe de defeito (se houver) ou diferencial
- 3ª-6ª: ângulos diferentes, embalagem, acessórios

---

## ⚠️ RESTRIÇÕES E PENALIDADES

| Violação | Penalidade |
|----------|-----------|
| Foto pixelada ou <400x400px | Anúncio marcado como "Foto insuficiente" |
| Descrição <100 chars | Invisível em filtros de "informação completa" |
| Falta 2+ atributos obrigatórios | Invisível para filtros daquela característica |
| Título com SPAM (***!!! MEGA OFERTA) | Downrank manual |
| Link externo na descrição | Aviso de insegurança ao comprador |
| Frete confirmado >7 dias | Desfavorecido para clientes com urgência |
| Cancelamentos > 5% | Score de vendedor desce, todo anúncio afetado |

---

## 🔴 DECISÕES E RESULTADOS

### 2026-03-02 — Baseline HUGOJOBS
**Contexto:** Power Seller Silver, 942 vendas/60d, 65% feedback positivo

**Métricas Atuais:**
- Cancelamentos: ~2% ✅
- Devoluções: ~3% ✅
- Resposta: <8h ✅
- **Problema:** Feedback positivo 65% (ALVO: >95%)

**Ação:** Analisar próximos anúncios quanto a health score antes de publicar.

---

## 📅 PRÓXIMAS AÇÕES

1. Obter lista de anúncios ativos da HUGOJOBS via `get_seller_items`
2. Rodar `get_item_health` em cada um
3. Priorizar top 5 com lower health score
4. Analisar campos faltantes via `get_category_attributes`
5. Criar plano de otimização por anúncio
