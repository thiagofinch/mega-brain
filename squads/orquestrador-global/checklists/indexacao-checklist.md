# Checklist: Qualidade de Indexação

## Metadata
```yaml
id: indexacao-checklist
name: Checklist de Qualidade de Indexação
version: 1.0.0
executor: capability-cartographer
related_task: indexar-squad
```

## Purpose

Garantir que cada squad é indexado corretamente no SQUAD-REGISTRY, com todas as informações necessárias para matching preciso.

---

## Fase 1: Validação de Estrutura

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 1 | SQUAD.md existe? | [ ] | |
| 2 | config.yaml existe? | [ ] | |
| 3 | Pasta agents/ existe? | [ ] | |
| 4 | Pelo menos 1 agente encontrado? | [ ] | Total: ___ |
| 5 | config.yaml é YAML válido? | [ ] | |
| 6 | SQUAD.md é Markdown válido? | [ ] | |

**Score Estrutura:** ___/6

---

## Fase 2: Extração de Metadados

### Informações Básicas
| # | Check | Status |
|---|-------|--------|
| 7 | Nome do squad extraído? | [ ] |
| 8 | ID único definido? | [ ] |
| 9 | Domínio identificado? | [ ] |
| 10 | Descrição extraída? | [ ] |
| 11 | Versão registrada? | [ ] |
| 12 | Prioridade definida (P0/P1/P2)? | [ ] |

### Problemas e Capacidades
| # | Check | Status |
|---|-------|--------|
| 13 | Problemas que resolve listados (>= 1)? | [ ] |
| 14 | Capacidades especiais identificadas? | [ ] |
| 15 | Diferencial documentado? | [ ] |

**Score Metadados:** ___/9

---

## Fase 3: Mapeamento de Agentes

| # | Check | Status |
|---|-------|--------|
| 16 | Todos os agentes listados? | [ ] |
| 17 | ID de cada agente registrado? | [ ] |
| 18 | Papel/função de cada agente? | [ ] |
| 19 | Prioridade de cada agente? | [ ] |
| 20 | Tipos de tarefa por agente mapeados? | [ ] |

**Agentes Mapeados:**

| Agente | Papel | Prioridade | Tipos de Tarefa |
|--------|-------|------------|-----------------|
| ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ |

**Score Agentes:** ___/5

---

## Fase 4: Geração de Keywords

| # | Check | Status |
|---|-------|--------|
| 21 | Keywords extraídas de títulos? | [ ] |
| 22 | Keywords extraídas de descrições? | [ ] |
| 23 | Termos técnicos identificados? | [ ] |
| 24 | Mínimo 5 keywords geradas? | [ ] |
| 25 | Keywords são relevantes para matching? | [ ] |
| 26 | Sem keywords genéricas demais? | [ ] |

**Keywords Geradas:**
```
[ ] ___________  [ ] ___________  [ ] ___________
[ ] ___________  [ ] ___________  [ ] ___________
[ ] ___________  [ ] ___________  [ ] ___________
```

**Score Keywords:** ___/6

---

## Fase 5: Mapeamento de Workflows

| # | Check | Status |
|---|-------|--------|
| 27 | Workflows listados? | [ ] |
| 28 | Trigger de cada workflow? | [ ] |
| 29 | Output de cada workflow? | [ ] |
| 30 | Agentes envolvidos mapeados? | [ ] |

**Score Workflows:** ___/4

---

## Fase 6: Qualidade do Registry Entry

| # | Check | Status |
|---|-------|--------|
| 31 | Entrada formatada corretamente? | [ ] |
| 32 | Todos os campos obrigatórios preenchidos? | [ ] |
| 33 | Hash de versão gerado? | [ ] |
| 34 | Timestamp de atualização registrado? | [ ] |
| 35 | Entrada é única (sem duplicatas)? | [ ] |

**Score Registry:** ___/5

---

## Scoring Final

```
Itens completados: ___/35
Porcentagem: ___%

Qualidade da Indexação:
[ ] EXCELENTE (>90%) - Squad bem indexado
[ ] BOM (80-90%) - Pequenas lacunas
[ ] REGULAR (70-80%) - Complementar informações
[ ] FRACO (<70%) - Reindexar
```

---

## Quick Reference

### Campos Obrigatórios no Registry

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| id | Identificador único | "youtube-content" |
| nome | Nome de exibição | "YouTube Content" |
| dominio | Área de atuação | "content-production" |
| problemas | Lista de problemas | ["Problema 1", ...] |
| agentes | Lista de agentes | [{id, papel, tipos}] |
| keywords | Termos para matching | ["keyword1", ...] |
| versao | Versão do squad | "1.0.0" |
| atualizado_em | Data de atualização | "2026-02-04" |

### Formato de Entry no Registry

```markdown
### [nome-do-squad]

| Campo | Valor |
|-------|-------|
| ID | nome-do-squad |
| Domínio | [domínio] |
| Prioridade | [P0/P1/P2] |
| Versão | [X.X.X] |

**Problemas que Resolve:**
- [Problema 1]

**Agentes:**
| Agente | Papel | Tipos |
|--------|-------|-------|
| [id] | [papel] | criar, analisar |

**Keywords:**
`keyword1` `keyword2` `keyword3`
```

### Keywords Eficazes

| ✅ Boas Keywords | ❌ Keywords Genéricas |
|------------------|----------------------|
| "youtube" | "conteúdo" |
| "thumbnail" | "criar" |
| "um nicho de saúde" | "negócio" |
| "facebook-ads" | "marketing" |
| "roteiro" | "ajuda" |

### Tipos de Tarefa Padrão

| Tipo | Descrição |
|------|-----------|
| criar | Gerar algo novo |
| analisar | Examinar e avaliar |
| executar | Realizar ação |
| otimizar | Melhorar existente |
| sintetizar | Combinar informações |
| pesquisar | Buscar informações |

### Red Flags na Indexação

| ❌ Problema | Impacto |
|-------------|---------|
| SQUAD.md ausente | Squad não indexável |
| Domínio vazio | Matching falha |
| Sem problemas listados | Score de problemas = 0 |
| < 3 keywords | Matching impreciso |
| Agentes sem tipos de tarefa | Score de tipo = 0 |
