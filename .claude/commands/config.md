# /config - Configuracoes do MOGA BRAIN

Gerencia preferencias do usuario para o sistema.

## SINTAXE

```
/config [categoria] [opcao]
```

## CATEGORIAS DISPONIVEIS

### /config welcome

Configura o tipo de tela de boas-vindas.

```
/config welcome --full      → Sempre mostra versao completa (padrao)
/config welcome --compact   → Sempre mostra versao resumida
/config welcome --ask       → Pergunta qual versao quer
```

**Acao:** Salvar preferencia em `/system/user-preferences.json`

### /config loops

Configura comportamento de open loops.

```
/config loops --remind      → Lembra loops ao mudar de assunto (padrao)
/config loops --silent      → Nao mostra lembrete de loops
/config loops --aggressive  → Mostra loops em toda mensagem
```

### /config agents

Configura visibilidade de agentes.

```
/config agents --all        → Mostra todos os agentes no dashboard
/config agents --active     → Mostra apenas agentes com MEMORY recente
/config agents --minimal    → Mostra apenas contagem
```

### /config thinking

Configura profundidade de raciocinio do Claude.

```
/config thinking --extended  → Sempre usar raciocinio prolongado (mais tokens de pensamento)
/config thinking --standard  → Usar conforme necessidade (padrao)
```

**Efeito:** Quando `extended`, Claude usara mais raciocinio interno antes de responder, util para:
- Analises complexas
- Planejamento de pipelines
- Decisoes arquiteturais
- Resolucao de problemas ambiguos

### /config permissions

Configura comportamento de permissoes para comandos.

```
/config permissions --ask    → Pedir confirmacao para comandos sensiveis (padrao)
/config permissions --skip   → Pular confirmacoes (usuario assume risco)
```

**Efeito:** Quando `skip`, comandos serao executados sem pedir confirmacao.

### /config show

Mostra configuracoes atuais:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚙️ CONFIGURACOES DO MOGA BRAIN                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🖥️ Welcome Screen:    {full | compact | ask}                                ║
║  🔓 Open Loops:         {remind | silent | aggressive}                       ║
║  🤖 Agents Display:     {all | active | minimal}                             ║
║  🧠 Thinking Mode:      {standard | extended}                                ║
║  🔓 Permissions:        {ask | skip}                                         ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Para alterar: /config [categoria] --[opcao]                                 ║
║  Exemplo: /config welcome --compact                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### /config reset

Restaura configuracoes padrao:

```
✅ Configuracoes restauradas para padrao:
   • Welcome: full
   • Loops: remind
   • Agents: all
   • Thinking: standard
   • Permissions: ask
```

## ARQUIVO DE PERSISTENCIA

```
/system/user-preferences.json
```

```json
{
  "version": "1.2.0",
  "last_updated": "2025-12-21T00:00:00Z",
  "preferences": {
    "welcome": "full",
    "loops": "remind",
    "agents": "all",
    "thinking": "standard",
    "permissions": "ask"
  }
}
```

## COMPORTAMENTO

1. Se arquivo nao existe, usar padrao (full, remind, all, standard, ask)
2. Criar arquivo ao primeiro /config
3. Atualizar last_updated em cada mudanca
4. Quando thinking=extended, usar raciocinio prolongado em TODAS as respostas
5. Quando permissions=skip, executar comandos sem pedir confirmacao
