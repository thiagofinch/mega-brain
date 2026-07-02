# Battle Logging Templates

## Overview

Templates padronizados para os arquivos de log que cada Battle Royale (Pattern 6) produz. Estes templates são copiados e preenchidos automaticamente pelo chief durante a execução do Battle.

**Referências:**
- Workflow: `workflows/battle-round.md`
- Schema: `knowledge/BATTLE-CONFIG-SCHEMA.md`
- Execution logging rule: `.claude/rules/execution-logging.md`

## Estrutura de Diretório

Cada Battle produz o seguinte diretório em `.data/executions/`:

```
{YYYY-MM-DD}_battle-{slug}/
├── battle-state.json           ← Estado da máquina (JSON, não têm template)
├── 00-battle-plan.md           ← Fase 1: Plano do Battle (TEMPLATE)
├── 01-{team-a}-output.md       ← Fase 2: Output equipe A (gerado pela equipe)
├── 02-{team-b}-output.md       ← Fase 2: Output equipe B (gerado pela equipe)
├── 03-{team-c}-output.md       ← Fase 2: Output equipe C (gerado pela equipe)
├── 04-voting-results.md        ← Fase 3: Resultados da votação (TEMPLATE)
├── 05-debate-transcript.md     ← Fase 4: Transcrição do debate (TEMPLATE)
├── 06-board-review-r1.md       ← Fase 5: Board review rodada 1 (TEMPLATE)
├── 07-board-review-r2.md       ← Fase 5: Board review rodada 2 (se necessário)
├── 08-final-version.md         ← Versão final aprovada (gerado pela equipe)
└── 99-battle-report.md         ← Relatório final (TEMPLATE)
```

## Quando Cada Arquivo é Criado

| Arquivo | Fase | Momento | Criado por |
|---------|------|---------|------------|
| `battle-state.json` | Fase 1 | Início do Battle | Chief |
| `00-battle-plan.md` | Fase 1 | Após validar brief e config | Chief |
| `01..03-{team}-output.md` | Fase 2 | Ao receber output de cada equipe | Chief (salva) |
| `04-voting-results.md` | Fase 3 | Após todos os votos coletados | Chief |
| `05-debate-transcript.md` | Fase 4 | Após as 3 rodadas + veredito | Chief |
| `06-board-review-rN.md` | Fase 5 | Após cada rodada de revisão | Chief |
| `08-final-version.md` | Fase 5 | Após aprovação do board | Chief (copia versão aprovada) |
| `99-battle-report.md` | Final | Após Battle completo | Chief |

## Como Usar os Templates

1. **Copiar** o template para o diretório de execução
2. **Preencher** os placeholders `{...}` com dados reais
3. **Remover** seções não aplicáveis (ex: tiebreaker round se não houve)
4. **Manter** a estrutura de headings intacta para parsing automático

Os arquivos `01..03` e `08` são gerados pelos agentes do squad — não têm template genérico aqui pois o formato depende do tipo de deliverable (carta de vendas, roteiro, criativo visual, etc.).

O `battle-state.json` é um arquivo de estado em formato JSON usado para resumir execuções interrompidas — não é template Markdown.

## Compatibilidade

Todos os templates seguem o padrão de execution logging do Mega Brain definido em `.claude/rules/execution-logging.md`. Os campos de Metadata (Data, Status, Squad) são consistentes com o formato geral.

---

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-02-17 |
| Templates | 5 (00, 04, 05, 06, 99) |
| Maintained By | Orchestrator (orquestrador-global) |
