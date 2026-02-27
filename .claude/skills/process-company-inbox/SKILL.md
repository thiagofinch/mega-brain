---
name: process-[sua-empresa]-inbox
description: "Processa arquivos no INBOX [SUA EMPRESA], classifica, extrai insights, e move para pasta destino. Use quando: novos arquivos em inbox, processar conteúdo [SUA EMPRESA], atualizar contexto da empresa."
---

# Process [SUA EMPRESA] Inbox

Pipeline de processamento de conteúdo interno da [SUA EMPRESA].

---

## Quando Usar

- Novos arquivos adicionados em `/[sua-empresa]/inbox/`
- Atualização de contexto da empresa necessária
- Processamento de calls, planilhas, documentos internos

---

## O Que Faz

1. **Escaneia** `/[sua-empresa]/inbox/` por arquivos não processados
2. **Classifica** cada arquivo por tipo e categoria
3. **Extrai** CHUNKS e INSIGHTS relevantes
4. **Move** para pasta destino apropriada
5. **Indexa** em `_INDEX.md` e `[SUA EMPRESA]-STATE.json`

---

## Fluxo de Processamento

```
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 1: SCAN                                                              │
├────────────────────────────────────────────────────────────────────────────┤
│  1. Listar arquivos em /[sua-empresa]/inbox/                                │
│  2. Ignorar README.md                                                       │
│  3. Para cada arquivo:                                                      │
│     - Detectar extensão                                                     │
│     - Ler conteúdo                                                          │
│     - Classificar tipo                                                      │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 2: CLASSIFICAÇÃO                                                     │
├────────────────────────────────────────────────────────────────────────────┤
│  Detectar tipo baseado em:                                                  │
│  - Nome do arquivo (call-, planilha-, contrato-)                           │
│  - Extensão (.txt, .csv, .pdf, .md)                                        │
│  - Conteúdo (keywords: "transcrição", "reunião", "KPI", etc.)              │
│                                                                             │
│  TIPOS:                                                                     │
│  - CALL_MENTOR: Calls com mentores externos                                │
│  - CALL_TEAM: Reuniões internas                                            │
│  - CALL_CLIENT: Calls com clientes                                         │
│  - FINANCE: Planilhas financeiras                                          │
│  - CONTRACT: Contratos                                                      │
│  - TEAM: Documentos de time                                                │
│  - STRATEGY: Documentos estratégicos                                       │
│  - PRODUCT: Documentação de produto                                        │
│  - MARKETING: Material de marketing                                         │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 3: EXTRAÇÃO (por tipo)                                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CALL_MENTOR:                                                               │
│  - Extrair DNA 5 camadas ([FILOSOFIA], [MODELO-MENTAL], [HEURISTICA],      │
│    [FRAMEWORK], [METODOLOGIA])                                              │
│  - Gerar INSIGHTS-[NOME-MENTOR].md em /07-STRATEGY/                        │
│  - Criar CHUNKS indexados                                                   │
│                                                                             │
│  CALL_TEAM:                                                                 │
│  - Extrair DECISÕES tomadas                                                │
│  - Extrair ACTION ITEMS com responsáveis                                   │
│  - Gerar resumo executivo                                                  │
│                                                                             │
│  FINANCE:                                                                   │
│  - Extrair métricas-chave (MRR, CAC, LTV, etc.)                           │
│  - Atualizar DAILY-SNAPSHOT.yaml                                           │
│  - Detectar thresholds críticos                                            │
│                                                                             │
│  STRATEGY:                                                                  │
│  - Indexar decisões                                                         │
│  - Vincular com contexto existente                                         │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 4: MOVIMENTAÇÃO                                                      │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DESTINOS:                                                                  │
│  - CALL_MENTOR → /[sua-empresa]/calls/MENTORS/                             │
│  - CALL_TEAM → /[sua-empresa]/calls/TEAM/                                  │
│  - CALL_CLIENT → /[sua-empresa]/calls/CLIENTS/                             │
│  - FINANCE → /[sua-empresa]/02-FINANCE/                                       │
│  - CONTRACT → /[sua-empresa]/03-CONTRACTS/                                    │
│  - TEAM → /[sua-empresa]/team/                                             │
│  - MARKETING → /[sua-empresa]/05-MARKETING/                                   │
│  - PRODUCT → /[sua-empresa]/06-PRODUCTS/                                      │
│  - STRATEGY → /[sua-empresa]/07-STRATEGY/                                     │
│                                                                             │
│  AÇÕES:                                                                     │
│  - Renomear com prefixo [[SUA EMPRESA]]                                           │
│  - Mover para pasta destino                                                 │
│  - Criar backup em inbox/PROCESSED/ se necessário                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 5: INDEXAÇÃO                                                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Atualizar /[sua-empresa]/_INDEX.md:                                        │
│     - Adicionar entrada com link                                            │
│     - Atualizar contadores                                                  │
│     - Registrar data de processamento                                       │
│                                                                             │
│  2. Atualizar /[sua-empresa]/[SUA EMPRESA]-STATE.json:                               │
│     - Incrementar contadores por categoria                                  │
│     - Atualizar last_processed_at                                          │
│     - Registrar arquivo processado                                          │
│                                                                             │
│  3. Gerar LOG em /logs/[SUA EMPRESA]-PIPELINE/:                               │
│     - PROCESS-YYYY-MM-DD-HHmm.md                                           │
│     - Detalhes de cada arquivo processado                                   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Output

Após processamento, entregar relatório:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    [SUA EMPRESA] INBOX PROCESSING - COMPLETE                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Data: YYYY-MM-DD HH:MM                                                      ║
║  Arquivos processados: N                                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│  ARQUIVOS PROCESSADOS                                                       │
├────────────────────────────────────┬────────────┬───────────────────────────┤
│  ARQUIVO                           │ TIPO       │ DESTINO                   │
├────────────────────────────────────┼────────────┼───────────────────────────┤
│  [arquivo1.txt]                    │ CALL_MENTOR│ /calls/MENTORS/        │
│  [arquivo2.csv]                    │ FINANCE    │ /02-FINANCE/              │
└────────────────────────────────────┴────────────┴───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  INSIGHTS EXTRAÍDOS                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Lista de insights principais]                                             │
└─────────────────────────────────────────────────────────────────────────────┘

✅ _INDEX.md atualizado
✅ [SUA EMPRESA]-STATE.json atualizado
✅ Log salvo em /logs/[SUA EMPRESA]-PIPELINE/
```

---

## Regras

- **NUNCA** deletar arquivos originais sem backup
- **SEMPRE** atualizar _INDEX.md após processamento
- **SEMPRE** gerar log de processamento
- **SEMPRE** aplicar marcação [[SUA EMPRESA]] nos arquivos movidos

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-11
