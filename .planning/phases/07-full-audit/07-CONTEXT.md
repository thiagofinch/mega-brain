# Phase 7: Full Audit - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Varrer 100% do repositório e classificar cada arquivo/pasta em L1 (público), L2 (premium), L3 (pessoal). Gerar relatório de auditoria completo. Não executar mudanças — apenas classificar e documentar.

</domain>

<decisions>
## Implementation Decisions

### Critérios de classificação

**Modelo de distribuição:**
- **Community (npx mega-brain-ai):** Instala L1 apenas
- **Premium:** Instala L1 + L2 (versão completa)
- **L3:** Nunca vai em pacote — backup pessoal do usuário

**L1 (Community - máquina/casca):**
- Core engine, templates, hooks, skills
- bin/, core/, .claude/ (incluindo jarvis/), agents/conclave/, agents/_templates/
- Estruturas VAZIAS com .gitkeep (inbox/, knowledge/, agents/minds/, agents/cargo/)
- docs/ (documentação pública)

**L2 (Premium - conteúdo absorvido):**
- INCLUI TUDO DE L1 +
- DNAs extraídos, dossiers, playbooks reais
- agents/minds/** populados, agents/cargo/** populados
- knowledge/dossiers/**, knowledge/playbooks/**, knowledge/dna/**
- artifacts/insights/, artifacts/chunks/
- Skills premium (source-sync, etc)

**L3 (Pessoal - nunca distribuído):**
- Material bruto original: inbox/**
- Histórico: logs/**, .claude/sessions/, .claude/mission-control/
- Dados da empresa: agents/sua-empresa/

**NEVER (sempre gitignored em TODOS os layers):**
- .env, credentials.json, token.json, *.key, *.pem, *.secret
- .mcp.json, settings.local.json
- Arquivos de configuração com dados sensíveis

**DELETE (marcar para remoção):**
- finance-agent, talent-agent
- Qualquer pasta/arquivo obsoleto identificado

**REVIEW (requer revisão humana):**
- Arquivos que não encaixam claramente em nenhum layer

### Formato do relatório
- Output: JSON estruturado + Markdown legível
- Granularidade: Híbrido (pastas + arquivos especiais)
- Estatísticas: contagens e % por layer
- Local: docs/audit/

### Tratamento de exceções
- Arquivos sensíveis → categoria NEVER (não vai em nenhum layer)
- Arquivos para deletar → categoria DELETE (listar, não deletar ainda)
- Arquivos ambíguos → categoria REVIEW (decisão humana)

### Claude's Discretion
- Estrutura interna do JSON
- Formatação do MD
- Como calcular tamanhos (incluir ou não node_modules no cálculo)

</decisions>

<specifics>
## Specific Ideas

- .claude/jarvis/ inteiro vai em L1 (incluindo JARVIS-STATE.json, JARVIS-SOUL.md, etc.)
- Relatório deve ser útil para gerar .gitignore na próxima fase
- Categorias especiais (NEVER, DELETE, REVIEW) facilitam ação na fase 8-9

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-full-audit*
*Context gathered: 2026-02-27*
