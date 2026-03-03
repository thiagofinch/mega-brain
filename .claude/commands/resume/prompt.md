# /resume - Retomar Sessão

## Propósito

Lista e permite retomar sessões salvas anteriormente via `/save`.

## Uso

```
/resume           # Lista sessões e permite selecionar
/resume 1         # Retoma sessão pelo número
/resume {id}      # Retoma sessão pelo ID
```

## Comportamento

### Listar Sessões

Ao executar `/resume` sem argumentos:

```
📂 Sessões Salvas

| # | Data       | Título                              | Status    | Pendentes |
|---|------------|-------------------------------------|-----------|-----------|
| 1 | 31/01/2026 | Implementação do @media-buyer       | ✅ saved  | 2 tasks   |
| 2 | 30/01/2026 | Arquitetura do ETL Squad            | ⚠️ aborted| 5 tasks   |
| 3 | 29/01/2026 | Setup inicial AIOS                  | ✅ saved  | 0 tasks   |

Digite o número para retomar ou 'cancel' para cancelar:
> _
```

### Retomar Sessão

Ao selecionar uma sessão:

1. **Carregar contexto**: Ler arquivo `.session.json`
2. **Restaurar TodoList**: Recriar tarefas pendentes
3. **Exibir resumo**: Mostrar o que foi feito e o que falta

```
🔄 Sessão Retomada: "Implementação do @media-buyer"

Último trabalho: Criação do dashboard de performance
Agentes usados: @architect, @dev

📋 Tarefas pendentes:
  [ ] Testar integração com dashboard
  [ ] Validar alertas de performance

Continuando de onde parou...
```

### Detecção de Sessão Abortada

Se existir sessão com status "active" (não finalizada):

```
⚠️ SESSÃO ANTERIOR NÃO FINALIZADA

Última sessão: "Implementação do @media-buyer"
Data: 31/01/2026 às 16:45

Tarefas que ficaram em aberto:
  [ ] Testar integração com dashboard
  [ ] Validar alertas de performance

Deseja retomar esta sessão?
  [1] Sim, continuar de onde parei
  [2] Não, iniciar nova sessão
  [3] Marcar como concluída e iniciar nova
> _
```

## Verificação Automática

**Ao iniciar qualquer sessão**, verificar automaticamente:

1. Existe `.aiox/data/logs/sessions/.current-session.json`?
2. Se sim, apresentar opção de retomada
3. Se não, continuar normalmente

## Localização das Sessões

```
.aiox/data/logs/sessions/
├── 2026-01-31-14-30-titulo-sessao.session.json
├── 2026-01-30-10-15-outra-sessao.session.json
└── .current-session.json  # Sessão ativa (se houver)
```

## Regras Críticas

1. ✅ SEMPRE listar sessões com tarefas pendentes destacadas
2. ✅ SEMPRE restaurar TodoList ao retomar
3. ✅ SEMPRE verificar sessões abortadas no início
4. ✅ SEMPRE perguntar antes de sobrescrever sessão ativa
5. ❌ NUNCA perder contexto de tarefas pendentes

## Integração com IDE

Sessões são visíveis na coluna de sessões porque:

- Arquivos `.session.json` contêm metadados indexáveis
- Título e resumo aparecem na lista
- Status indica se pode ser retomada

---

_AIOS Session Persistence - /resume Command_
