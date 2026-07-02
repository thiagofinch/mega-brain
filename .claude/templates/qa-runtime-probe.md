# Runtime Probe — Story {ID}

## What to verify (no mocks)
- [ ] Feature artifacts exist on disk (caches, configs, queues)
- [ ] Hook fires on real trigger (nao simulated)
- [ ] Output observable (log, file, API response)
- [ ] Telemetry registra event (NOT just code path)

## Runtime test command
{comando real que prova feature funciona em prod-like env}

## Expected runtime output
{artifact ou log esperado}

## Actual runtime output
{paste do output real}

## Verdict
PASS / FAIL / INCONCLUSIVE

---

## NOTE — Scope by story type (AC4-AC5)

**Stories que adicionam HOOKS:**
Probe deve simular evento real do hook (UserPromptSubmit, PreToolUse, PostToolUse, etc.)
com transcript/payload real — nao um payload fake controlado.

**Stories que adicionam SCRIPTS:**
Probe deve invocar o script via CLI com argumentos reais e validar que output existe
no filesystem apos execucao.

**Stories de FIX em feature existente:**
Probe DEVE incluir duas partes obrigatorias:
1. Reproducao do bug original mostrando comportamento quebrado (FAIL)
2. Execucao pos-fix mostrando correcao (PASS)
Padrao: regression test runtime — sem isso nao ha prova de que o fix funciona.

**INCONCLUSIVE:**
Aceito quando credenciais ou ambiente especifico impedem execucao completa.
Justificativa DEVE ser documentada inline nesta secao.
INCONCLUSIVE nao bloqueia transicao para Done mas DEVE ser revisado pelo founder antes do merge.

---

*Template canonico — Source: STORY-TIL-RUNTIME-GATE-qa-process-improvement.md | Enforced desde 2026-05-14*
