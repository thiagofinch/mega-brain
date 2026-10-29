#!/usr/bin/env node
/**
 * Claude Code Hook: PreCompact Session Digest (no-op nesta distribuicao)
 *
 * Na instalacao completa, este hook delegava a um runner unificado que gerava
 * o digest da sessao antes do compact de contexto. Esse runner nao faz parte
 * desta distribuicao publica, entao o hook e um no-op silencioso: nao carrega
 * nada, nao imprime nada e sai com codigo 0. Segue registrado em settings.json
 * para nao alterar a fiacao.
 *
 * @see Story MIS-3 - Session Digest (PreCompact Hook)
 */

'use strict';

// Fail-open: nunca bloqueia o compact.
process.exit(0);
