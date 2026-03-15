# PLAYBOOK-ADS: Ad Science & DSL Framework

> **Versao:** 1.0.0
> **Criado em:** 2026-01-13
> **Fonte:** BATCH-077 (Jeremy Haynes, Jordan Stupar, Brandon Carter)
> **Elementos:** 25+ frameworks, heuristicas e metodologias de ad science

---

## RESUMO EXECUTIVO

Este playbook consolida a ciencia de anuncios pagos extraida do Jeremy Haynes Inner Circle, com foco especial na revolucao DSL (Deck Sales Letter) e metodologia cientifica de teste de anuncios.

---

## FRAMEWORK CORE: DSL (DECK SALES LETTER)

### Revolucao VSL → DSL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        A MUDANCA DE PARADIGMA                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VSL (Video Sales Letter)              DSL (Deck Sales Letter)             │
│  ├── Narrador controla o ritmo         ├── Usuario controla o ritmo        │
│  ├── 5-9% press play                   ├── 77% chegam ao slide 5           │
│  ├── $90-120 custo por call            ├── $30-80 custo por call           │
│  └── Passivo (assiste ou sai)          └── Ativo (clica para avancar)      │
│                                                                             │
│  "Consumer behavior has shifted - people are fed up with shitty VSLs"      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Estrutura do DSL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DSL FUNNEL STRUCTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HEADLINE AD → DECK (20 slides) → APPLICATION → BOOKED CALL                │
│                                                                             │
│  SLIDES CRITICOS (1-5):                                                    │
│  ├── Slide 1: Introducao + oferta                                          │
│  ├── Slide 2-3: Por que e uma boa oferta                                   │
│  ├── Slide 4-5: Perguntas frequentes                                       │
│  └── [Arrow prompt: "Press to continue"]                                   │
│                                                                             │
│  HEURISTICA: 77% drop acontece APOS slide 5                                │
│  ACAO: Colocar todo conteudo essencial nos 5 primeiros                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementacao DSL

| Passo | Acao | Detalhe |
|-------|------|---------|
| 1 | Criar deck no Google Slides | ~20 slides, Mini Webinar 2.0 template |
| 2 | Otimizar primeiros 5 slides | Offer, why good, FAQ |
| 3 | Adicionar arrow prompt | "Press to continue" → 20% → 77% |
| 4 | Envolver vendedores | Perguntar o que querem nos 5 primeiros |
| 5 | Frame corretamente | "E se criassemos um deck juntos?" |
| 6 | Exportar e embutir | Share to web → embed code |
| 7 | Versoes mobile + desktop | CSS responsivo ($50 no Upwork) |
| 8 | Deploy em paralelo | Nao substituir VSL, complementar |

**Referencia:** decksalesletter.com (exemplo ao vivo)

---

## AD SCIENCE: METODO CIENTIFICO

### Constants vs Variables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCIENTIFIC METHOD FOR AD TESTING                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ESTRUTURA DE TESTE:                                                        │
│  ┌────────────────┐                                                        │
│  │ HOOK A (var)   │──┐                                                     │
│  │ HOOK B (var)   │──┤                                                     │
│  │ HOOK C (var)   │──┼──▶ MESMO BODY (const) ──▶ MESMO CTA                │
│  │ HOOK D (var)   │──┤                                                     │
│  │ HOOK E (var)   │──┘                                                     │
│  └────────────────┘                                                        │
│                                                                             │
│  PROCESSO:                                                                  │
│  1. Testar multiplos hooks com body/CTA identico                           │
│  2. Identificar vencedor por performance isolada                           │
│  3. Criar variacoes SIMILARES ao hook vencedor                             │
│  4. Repetir ate combinacao otima                                           │
│                                                                             │
│  CASE Brandon Carter: Variacao dramatica de custo entre hooks              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Hierarquia de Elementos do Ad

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AD ELEMENT HIERARCHY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1o: VIDEO/IMAGE (mais importante - para o scroll)                         │
│  2o: HEADLINE (reitera hook ou promessa)                                   │
│  3o: PRIMARY TEXT (repete conteudo do video para nao-assistidores)         │
│                                                                             │
│  ESTRUTURA DE AD DE ALTA CONVERSAO:                                        │
│  ┌─────────────┐                                                           │
│  │    HOOK     │ ← Mais importante (parar o scroll)                        │
│  ├─────────────┤                                                           │
│  │PROMISE/TRUST│ ← O que voce ganha + por que confiar                      │
│  ├─────────────┤                                                           │
│  │ OBJECTION 1 │ ← Endereca preocupacao principal                          │
│  ├─────────────┤                                                           │
│  │ OBJECTION 2 │ ← Endereca preocupacao secundaria                         │
│  ├─────────────┤                                                           │
│  │    CTA      │ ← Call to action clara                                    │
│  └─────────────┘                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Character Expectation Triangle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHARACTER EXPECTATION TRIANGLE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        ENVIRONMENT                                          │
│                           /\                                                │
│                          /  \                                               │
│                         /    \                                              │
│                        /PERFECT\                                            │
│                       /CHARACTER\                                           │
│                      /____________\                                         │
│             APPEARANCE        CHARACTER TRAITS                              │
│             (roupa, look)     (personalidade, atitude)                      │
│                                                                             │
│  EXEMPLOS:                                                                  │
│  ├── Tai Lopez: Garagem com Lamborghini (environment)                      │
│  ├── Grant Cardone: Personalidade bold (character traits)                  │
│  └── Gary Vee: Hustle embodied nos 40-50 (appearance + traits)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## BENCHMARKS DE CTR

| Nivel | CTR | Contexto |
|-------|-----|----------|
| Aceitavel | 0.5-1% | Ainda lucrativo |
| Bom | 1-2% | Performance solida |
| Excelente | 2%+ | Standard benchmark |
| Elite | 6%+ | Tai Lopez 67 Steps level |

**HEURISTICA:** High CTR + Low page conversion = Ad nao vendeu o suficiente

---

## PROMPT ENGINEERING PARA ADS

### Estrutura de Prompt

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PROMPT ENGINEERING FOR AD COPY                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [VERDE] FRAMING: Quem o modelo esta sendo                                 │
│  "Voce e um copywriter de resposta direta que fez milhoes de dolares       │
│   mensalmente para seus clientes atraves de Facebook ads"                  │
│                                                                             │
│  [AMARELO] TASK: Instrucoes explicitas                                     │
│  "Escreva X caracteres de copy publicitario para primary text              │
│   para este cliente que vende Y para audiencia Z"                          │
│                                                                             │
│  [AZUL] QUESTIONS: Peca esclarecimentos primeiro                           │
│  "Antes de dar output, me faca perguntas para suas respostas serem         │
│   mais precisas. Voce entendeu?"                                           │
│                                                                             │
│  PRO TIPS:                                                                  │
│  ├── Use termos do treinamento do modelo ("primary text" nao "body")       │
│  ├── Chain prompts: Copy → Headlines → Scripts → Variacoes                 │
│  ├── Frame como copywriters famosos: "Voce e David Ogilvy"                 │
│  └── Input copy vencedor existente para influenciar estilo                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CUSTO POR CALL BENCHMARKS

| Mecanismo | Custo/Call | Contexto |
|-----------|------------|----------|
| VSL | $90-120 | Benchmark atual |
| DSL | $30-80 | 30-50% reducao |
| Diferenca | 30-50% | ROI do switch |

---

## CROSS-REFERENCES

- **PLAYBOOK-FOLLOW-UP.md** - Bang Angle para follow-up pos-ad
- **PLAYBOOK-YOUTUBE-ADS.md** - YouTube ads especifico
- **PAID-MEDIA-SPECIALIST/MEMORY.md** - Todos insights de paid media

---

## FONTES

- BATCH-077: Jeremy Haynes Inner Circle
- Jordan Stupar: Follow-Up Framework
- Brandon Carter: Constants vs Variables case study

---

**Gerado por:** JARVIS v3.32.0
**Timestamp:** 2026-01-13T06:40:00Z
