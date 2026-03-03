# /save - Salvar Sessão

## Propósito

Salva a sessão atual com um título descritivo para posterior retomada via `/resume`.

## Uso

```
/save
```

## Comportamento

Ao executar `/save`, você DEVE:

### 1. Capturar Estado Atual

Colete automaticamente:

- **Agentes ativados**: Quais agentes (@dev, @architect, etc.) foram usados
- **Tarefas**: Estado atual da TodoList (completas, pendentes, em progresso)
- **Arquivos**: Arquivos criados ou modificados na sessão
- **Contexto**: Último tópico de trabalho e resumo

### 2. Exibir Resumo

```
📁 Sessão capturada!

Tarefas: X completas | Y pendentes
Agentes: @agent1, @agent2
Arquivos: Z modificados

Qual título deseja para esta sessão?
> _
```

### 3. Aguardar Título do Usuário

**CRÍTICO**: Sempre perguntar o título. Nunca salvar automaticamente sem input.

### 4. Salvar Sessão

Após receber o título:

1. Gerar arquivo em `.aiox/data/logs/sessions/`
2. Formato: `YYYY-MM-DD-HH-mm-{slug-titulo}.session.json`
3. Confirmar salvamento:

```
✅ Sessão salva!

📄 2026-01-31-16-45-titulo-da-sessao.session.json

Para retomar: /resume
Para listar: /sessions
```

## Estrutura do Arquivo de Sessão

```json
{
  "id": "2026-01-31-16-45-abc123",
  "title": "Título fornecido pelo usuário",
  "slug": "titulo-fornecido-pelo-usuario",
  "created": "2026-01-31T16:45:00Z",
  "lastModified": "2026-01-31T16:45:00Z",
  "status": "saved",
  "agents": ["architect", "dev"],
  "todos": {
    "completed": [...],
    "pending": [...],
    "inProgress": [...]
  },
  "files": {
    "created": [...],
    "modified": [...]
  },
  "context": {
    "lastTopic": "Descrição do último trabalho",
    "summary": "Resumo do que foi feito na sessão"
  },
  "resumable": true
}
```

## Localização

Sessões são salvas em:

```
.aiox/data/logs/sessions/
```

## Integração

- **Terminal**: Comando disponível como `/save`
- **IDE**: Sessões aparecem na coluna de sessões (Antigravity/VSCode)
- **Retomada**: Use `/resume` para retomar sessões salvas

## Regras Críticas

1. ✅ SEMPRE perguntar título ao usuário
2. ✅ SEMPRE capturar estado da TodoList
3. ✅ SEMPRE confirmar salvamento com caminho do arquivo
4. ❌ NUNCA salvar sem título fornecido pelo usuário
5. ❌ NUNCA sobrescrever sessões existentes

---

_AIOS Session Persistence - /save Command_
