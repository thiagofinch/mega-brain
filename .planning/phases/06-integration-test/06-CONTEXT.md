# Phase 6: Integration Test - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Testar pipeline completa em modo autônomo com 10 arquivos reais do inbox. Validar que todos os sistemas implementados nas fases 4-5 funcionam integrados: orquestrador, queue, loop, recovery, monitoring, checkpoint.

</domain>

<decisions>
## Implementation Decisions

### Seleção de arquivos
- Mix representativo: 2-3 arquivos de cada fonte principal (Hormozi, Cole Gordon, Jeremy Haynes)
- Usar apenas arquivos não processados (sem chunks/insights existentes)
- Copiar para pasta isolada `/test-inbox/` — não processar inbox real
- Manter pasta de teste após execução para inspeção manual

### Simulação de falha
- Incluir 1 arquivo corrompido (encoding quebrado ou binário inválido) entre os 10
- Arquivos que falham após 3 retries: mover para `/test-inbox/failed/` e continuar processando os outros
- 3 retries com backoff exponencial (1s, 2s, 4s) — já implementado na fase 5
- Testar checkpoint/restore: pausar no arquivo 5, restaurar, verificar que continua do 6

### Critério de sucesso
- **Passou:** 9/10 arquivos processados com sucesso + 1 arquivo corrompido movido para /failed/ corretamente
- Verificação: confirmar que artefatos existem (chunks, insights, logs) — não validar conteúdo
- Checkpoint: comparar estado antes/depois da interrupção — sem duplicação
- Tempo máximo: 30 minutos para os 10 arquivos (~3 min por arquivo)

### Artefatos do teste
- Gerar: JSON estruturado + Markdown summary legível
- Local: `logs/integration-tests/`
- Timing: incluir tempo de processamento por arquivo (identificar gargalos)
- Nomenclatura: `integration-test-YYYY-MM-DD-HHMM.json` e `.md`

### Claude's Discretion
- Seleção exata dos arquivos (dentro dos critérios definidos)
- Estrutura interna do JSON de report
- Como simular o checkpoint (kill process, mock, ou pause manual)
- Formato exato do arquivo corrompido

</decisions>

<specifics>
## Specific Ideas

- Teste deve ser reproduzível: se rodar novamente com mesmos arquivos, mesmo resultado
- Recovery deve funcionar sem intervenção humana — o objetivo é modo autônomo
- Logs devem ser suficientes para debugar qualquer problema pós-facto

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-integration-test*
*Context gathered: 2026-02-27*
