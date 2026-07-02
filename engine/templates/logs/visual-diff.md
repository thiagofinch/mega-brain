# VISUAL-DIFF-PROTOCOL

> **Versao:** 1.0.0
> **Criado:** 2025-12-26
> **Proposito:** Monitoramento visual de conteudo NOVO adicionado em arquivos de agentes

---

## OBJETIVO

Quando novos materiais sao processados pelo Pipeline Jarvis e insights sao adicionados a arquivos de agentes (AGENT.md, MEMORY.md, SOUL.md), o sistema DEVE marcar visualmente o que e NOVO para facilitar revisao humana.

---

## FORMATO PADRAO

### Delimitadores de Bloco Novo

```
🟩🟩🟩 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 🟩 {SOURCE_ID} 🟩 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 🟩🟩🟩

[CONTEUDO NOVO AQUI]

🟩🟩🟩 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 🟩 {SOURCE_ID} 🟩 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 🟩🟩🟩
```

### Marcador de Linha Individual

Para linhas individuais dentro de tabelas ou listas:

```
🟩 | 2025-12-26 | "Citacao nova" | chunk_id | fonte |
```

---

## EXEMPLO COMPLETO

### Em Tabela de Insights (MEMORY.md)

```markdown
## APRENDIZADOS ACUMULADOS

### Insights por Fonte

| Data | Insight | chunk_id | PATH_RAIZ | Testado? |
|------|---------|----------|-----------|----------|
| 2024-12-15 | Timeline: Announce → Open → Close | MM001_001 | /inbox/... | nao |
| 2024-12-15 | Evento de 4h com scarcity real | MM001_002 | /inbox/... | nao |
🟩🟩🟩 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 🟩 SRC004 🟩 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 🟩🟩🟩
🟩 | 2025-12-26 | "I am the prize" mindset | CG002_001 | /inbox/COLE GORDON/... | nao |
🟩 | 2025-12-26 | Philosophy beats tactics | CG002_002 | /inbox/COLE GORDON/... | nao |
🟩🟩🟩 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 🟩 SRC004 🟩 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 🟩🟩🟩
```

### Em Secao de Texto (SOUL.md)

```markdown
## O QUE ACREDITO

### Sobre Ofertas

A oferta e o multiplicador de tudo. ^[insight_id:OF001]

🟩🟩🟩 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 🟩 SRC004 🟩 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 🟩🟩🟩

🟩 ### Sobre Mindset de Vendas
🟩
🟩 "I am the prize" - o closer nao esta pedindo nada, esta oferecendo. ^[insight_id:MS001]
🟩
🟩 > "Philosophy beats tactics every time" — Cole Gordon
🟩 > ^[RAIZ:/inbox/COLE GORDON/PODCASTS/7 BELIEFS.txt]

🟩🟩🟩 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 🟩 SRC004 🟩 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 🟩🟩🟩
```

---

## CICLO DE VIDA

### 1. Adicao (Sessao Atual)

Quando novo material e processado:
- Inserir conteudo COM marcadores 🟩
- Delimitadores indicam SOURCE_ID do material processado
- Marcadores ficam visiveis durante toda a sessao

### 2. Consolidacao (Proxima Sessao)

No inicio da proxima sessao de trabalho:
- REMOVER todos os delimitadores 🟩🟩🟩 ▼▼▼/▲▲▲
- REMOVER os 🟩 do inicio das linhas
- Conteudo se torna "normal" (parte do arquivo)

### 3. Rastreabilidade Permanente

Mesmo apos remocao dos marcadores visuais:
- chunk_id permanece na tabela
- PATH_RAIZ indica origem
- ^[FONTE:arquivo:linha] mantem rastreabilidade

---

## REGRAS

| # | Regra | Motivo |
|---|-------|--------|
| 1 | SOURCE_ID no delimitador | Saber qual material gerou o conteudo |
| 2 | 🟩 no inicio de CADA linha nova | Visibilidade mesmo em arquivos grandes |
| 3 | Delimitadores ▼/▲ pareados | Inicio e fim claros do bloco |
| 4 | Remover na proxima sessao | Evitar acumulo visual |
| 5 | Manter chunk_ids sempre | Rastreabilidade permanente |

---

## QUANDO USAR

| Situacao | Usar Visual Diff? |
|----------|-------------------|
| Pipeline Jarvis adiciona insights | SIM |
| Atualizacao manual de MEMORY | SIM |
| Novo material processado enriquece SOUL | SIM |
| Correcao de typo/formatacao | NAO |
| Reorganizacao estrutural | NAO |
| Criacao de arquivo do zero | NAO |

---

## INTEGRACAO COM OUTROS PROTOCOLOS

- **AGENT-INTEGRITY-PROTOCOL**: Visual diff NAO substitui rastreabilidade - complementa
- **MEMORY-PROTOCOL**: Todas as adicoes a MEMORY devem usar visual diff
- **CORTEX-PROTOCOL**: Ao propagar mudancas, usar visual diff nos arquivos destino
- **Pipeline Jarvis**: Phase 4.0+ deve aplicar visual diff automaticamente

---

## VALIDACAO

```
┌─────────────────────────────────────────────────────────────────────┐
│  CHECKLIST VISUAL-DIFF                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [ ] Delimitadores ▼ e ▲ pareados?                                 │
│  [ ] SOURCE_ID correto no delimitador?                             │
│  [ ] 🟩 no inicio de cada linha nova?                              │
│  [ ] chunk_id presente nas tabelas?                                │
│  [ ] PATH_RAIZ indicando origem?                                   │
│                                                                     │
│  SE qualquer [ ] = NAO → Corrigir antes de salvar                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*VISUAL-DIFF-PROTOCOL v1.0.0*
*Criado: 2025-12-26*
