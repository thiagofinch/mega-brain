# Changelog

## 2.0.1 — 2026-10-29

Correções da release 2.0 (Free). O corte da 2.0 tirou arquivos do repositório sem
tirar as referências a eles: módulos Python importados que não existiam, hooks
apontando para runtimes ausentes, registros e docs citando caminhos inexistentes.
Esta versão não traz conteúdo novo; ela faz o que já é distribuído funcionar.

### Engine

- `graph_builder.py` não quebra mais com `ModuleNotFoundError: derivational_edges`
  (issue #2). As arestas derivacionais viraram opcionais, com erro claro se
  forem ligadas sem o módulo.
- Novos `engine/paths.py` e `engine/config.py`, importados por 81 e 15 arquivos
  e ausentes na 2.0.
- Windows: o pipeline usava `fcntl` (só existe em POSIX). Novo
  `engine/intelligence/pipeline/_file_lock.py` com lock portátil; checagem de PID
  do `slug_lock` funciona no Windows; `SafeStateWriter` não quebra mais.
- Imports de módulos ausentes viraram opcionais ou foram reapontados
  (`memory_manager`, compilador de dossiê, backend pgvector, `tagging` no rebuild
  com vetores).
- A rota de dossiê do `pipeline_orchestrator` usa o compilador V1 e não duplica
  conteúdo quando o mesmo `CREATE` chega de novo.
- Scripts VAPI (`engine/jarvis/voice/`) tinham erro de sintaxe e exigiam chave
  de API no import; agora a falta de credencial só é reportada ao usar.

### Hooks

- `synapse-engine.js` quebrava em todo prompt (runtime SYNAPSE não distribuído);
  agora é no-op silencioso.
- `workspace_contract_guard` bloqueava toda escrita em `L0`/`L1` do workspace
  (registry não distribuído); as checagens de higiene continuam.
- `memory_persistence`, `stop_workspace_audit`, `brain_first_lookup`,
  `promotion_detector_hook` e `precompact-session-digest.js` imprimiam erro a cada
  sessão; agora saem em silêncio quando o artefato não existe.
- `structure-validation.py` dava traceback em todo Write/Edit.
- `session_start.py` e `.claude/skills/chronicler/render_dispatcher.py` usavam
  f-string que só compila no Python 3.12; o `session_start` também deixou de
  acusar como "crítico" arquivos que a release não distribui.
- `startup_health` e `hook_auditor` sem falsos "missing"/"stale".

### Referências quebradas

- Removidas ou reapontadas as referências a arquivos que não fazem parte da
  release (registro de skills, regras, skills, squads, ADR, templates).
  `skill-registry.yaml` ficou com as 26 skills que existem.
- Skills que dependem de componentes não distribuídos (`services/etl/`,
  `squads/squad-creator-pro/`) avisam isso no topo do `SKILL.md`.

### CLI e publicação

- Comandos do `bin/mega-brain.js` que dependiam de `engine/operations.py`
  (não distribuído) saem com mensagem clara em vez de stack trace.
- Removido o script `npm run validate`, que chamava um comando inexistente.
- O gate `prepublishOnly` bloqueava a publicação da 2.0: `audit_layers.py` ainda
  esperava `core/` (renomeado para `engine/`) e, no Windows, nenhum padrão de
  diretório casava (separador `\`).
  Os padrões L1 agora seguem o layout 2.0.

### CI

- Novo `scripts/check_engine_imports.py`: falha em erro de sintaxe, import de
  módulo inexistente ou módulo da engine que não importa.
- `test.yml` roda em Linux e Windows, Python 3.11 e 3.12.
- Removidos passos que chamavam scripts e testes não distribuídos
  (`validate.yml`, `rag-health.yml`) e o workflow `obsidian-sync-tests.yml`, que
  falharia em todo push na `main`.

### Requisitos

- Python mínimo passa a ser **3.11** (o README dizia 3.10, mas 108 arquivos usam
  `datetime.UTC`, que só existe a partir do 3.11).

### Continua fora desta versão

Recursos que dependem de componentes não distribuídos seguem desligados: camada
de capabilities, runtime SYNAPSE, `services/etl/`, `squad-creator-pro`,
obsidian-sync e o compilador de dossiê V2.
