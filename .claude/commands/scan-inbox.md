# Scan INBOX Command

Scan the inbox folder and show files ready for processing.

## Usage
```
/scan-inbox
```

## PRIMEIRA AÇÃO OBRIGATÓRIA

> **ANTES de escanear, LEIA `/system/SESSION-STATE.md`**
> Para saber quais arquivos já foram processados.

---

## What It Does

1. Lista todas as **fontes** (pastas de pessoas/empresas) em `inbox/`
2. Para cada fonte, lista **tipos de conteúdo** (PODCASTS, MASTERMINDS, etc.)
3. Identifica arquivos **não processados** (comparando com `processed-files.md`)
4. Detecta temas automaticamente por keywords
5. Sugere próxima ação para cada arquivo pendente

---

## Estrutura Esperada

```
inbox/
├── ALEX HORMOZI/
│   ├── PODCASTS/
│   │   ├── VIDEO.mp4
│   │   └── VIDEO.txt
│   ├── MASTERMINDS/
│   └── BLUEPRINTS/
├── COLE GORDON/
│   └── PODCASTS/
└── _TEMPLATES/
```

---

## Output Example

```
============================================================
MEGA BRAIN - INBOX SCANNER
============================================================

📁 ALEX HORMOZI
   └── PODCASTS/
       ├── ✅ HOW I SCALED MY SALES TEAM.txt (já processado: SS001)
       └── ⏳ THE ROLE OF HR.txt (pendente)
           Detected themes: 03-contratacao, 09-gestao
           Action: /extract-knowledge "inbox/alex hormozi/PODCASTS/THE ROLE OF HR.txt"

   └── MASTERMINDS/
       └── ⏳ TAKI MOORE MASTERMIND.mp4 (sem transcrição)
           Action: /process-video "inbox/alex hormozi/MASTERMINDS/TAKI MOORE MASTERMIND.mp4"

📁 COLE GORDON
   └── PODCASTS/
       └── ✅ HIRING SALES MANAGERS.txt (já processado: CG001)

============================================================
RESUMO
============================================================
Fontes: 2
Arquivos processados: 2
Arquivos pendentes: 2
  - Transcrições prontas: 1
  - Vídeos sem transcrição: 1

PRÓXIMA AÇÃO SUGERIDA:
/extract-knowledge "inbox/alex hormozi/PODCASTS/THE ROLE OF HR.txt"
============================================================
```

---

## Theme Detection Keywords

| Tema | Keywords |
|------|----------|
| 01-ESTRUTURA-TIME | team, structure, org, bdr, sds, bc, hierarchy |
| 02-PROCESSO-VENDAS | sales, process, closing, call, pitch, closer |
| 03-CONTRATACAO | hiring, recruit, interview, onboard, farm system |
| 04-COMISSIONAMENTO | compensation, commission, ote, salary, incentive |
| 05-METRICAS | metric, kpi, conversion, rate, cac, ltv, benchmark |
| 06-FUNIL-APLICACAO | funnel, pipeline, qualification, lead |
| 07-PRICING | price, pricing, ticket, discount, offer |
| 08-FERRAMENTAS | crm, tool, software, tech stack, phone burner |
| 09-GESTAO | management, leadership, coaching, 1:1, manager |
| 10-CULTURA-GAMIFICACAO | culture, gamification, motivation, contest |

---

## Status Icons

| Icon | Significado |
|------|-------------|
| ✅ | Já processado (existe no registry) |
| ⏳ | Pendente (transcrição pronta) |
| 🎬 | Vídeo sem transcrição |
| 📄 | Documento (PDF, etc.) |

---

## Files to Check

| Arquivo | Propósito |
|---------|-----------|
| `/system/SESSION-STATE.md` | Lista de hashes processados |
| `/system/REGISTRY/processed-files.md` | Detalhes completos |
| `/agents/DISCOVERY/role-tracking.md` | Funções identificadas |

---

## Integration

Após escanear, o comando sugere automaticamente:
1. Qual arquivo processar primeiro (prioridade por tipo)
2. Qual comando usar (`/extract-knowledge` ou `/process-video`)
3. Quais temas serão provavelmente afetados
