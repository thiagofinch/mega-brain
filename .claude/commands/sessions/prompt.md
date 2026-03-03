# /sessions - Listar Sessões

## Propósito

Lista todas as sessões salvas sem iniciar retomada.

## Uso

```
/sessions         # Lista últimas 10 sessões
/sessions 20      # Lista últimas 20 sessões
/sessions --all   # Lista todas as sessões
```

## Comportamento

Ao executar `/sessions`:

```
📂 Histórico de Sessões

Últimas 10 sessões:

| # | Data       | Título                              | Status    | Pendentes |
|---|------------|-------------------------------------|-----------|-----------|
| 1 | 31/01/2026 | Implementação do @media-buyer       | ✅ saved  | 2 tasks   |
| 2 | 30/01/2026 | Arquitetura do ETL Squad            | ⚠️ aborted| 5 tasks   |
| 3 | 29/01/2026 | Setup inicial AIOS                  | ✅ saved  | 0 tasks   |
| 4 | 28/01/2026 | Migração de agentes                 | ✅ saved  | 0 tasks   |
| 5 | 27/01/2026 | Integração BILHON Docs              | ✅ saved  | 1 task    |
...

Total: 47 sessões | 3 com tarefas pendentes

Use /resume para retomar uma sessão.
Use /save para salvar a sessão atual.
```

## Status das Sessões

| Status    | Ícone | Significado                                |
| --------- | ----- | ------------------------------------------ |
| saved     | ✅    | Sessão finalizada corretamente             |
| aborted   | ⚠️    | Sessão não foi finalizada (crash, timeout) |
| active    | 🔄    | Sessão em andamento                        |
| completed | ✓     | Todas as tarefas concluídas                |

## Filtros Disponíveis

```
/sessions --pending      # Apenas sessões com tarefas pendentes
/sessions --aborted      # Apenas sessões não finalizadas
/sessions --today        # Apenas sessões de hoje
/sessions --week         # Última semana
```

## Informações Exibidas

Para cada sessão:

- **Data**: Data de criação
- **Título**: Título fornecido pelo usuário
- **Status**: Estado da sessão
- **Pendentes**: Número de tarefas não concluídas

## Localização

Sessões são lidas de:

```
.aiox/data/logs/sessions/*.session.json
```

## Integração

- **Terminal**: `/sessions` lista histórico
- **IDE**: Sessões visíveis na coluna de sessões
- **Retomada**: Use `/resume {número}` para retomar

---

_AIOS Session Persistence - /sessions Command_
