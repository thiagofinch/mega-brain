# RULE-GROUP-2: PERSISTENCE

> **Auto-Trigger:** Regras de persistência, continuidade de sessão e planejamento
> **Keywords:** "sessão", "save", "resume", "plan mode", "verificação", "varredura", "planilha", "auto-save"
> **Prioridade:** ALTA
> **Regras:** 11, 12, 13, 14

---

## 🚫 REGRA #11: PERSISTÊNCIA DE SESSÃO OBRIGATÓRIA

**NUNCA MAIS PERDE CONTEXTO. SALVA TUDO.**

### AUTO-SAVE OBRIGATÓRIO:
Salvar sessão em `.claude/sessions/SESSION-YYYY-MM-DD-HHmm.md` automaticamente:

- **APÓS** completar qualquer batch
- **APÓS** qualquer tarefa significativa
- **APÓS** decisões importantes
- **A CADA** 30 minutos de atividade
- **QUANDO** detectar pausa prolongada
- **QUANDO** usuário mencionar que vai sair
- **ANTES** de qualquer operação destrutiva

### CONTEÚDO OBRIGATÓRIO DO SESSION LOG:
```
- Estado da missão (fase, progresso)
- Resumo detalhado da conversa
- Ações executadas com detalhes
- Arquivos modificados
- Pendências identificadas
- Decisões tomadas e razões
- Próximos passos planejados
- Notas importantes
```

### SKILLS DISPONÍVEIS:
- `/save` - Salvar sessão manualmente
- `/resume` - Recuperar última sessão

### REGRAS ABSOLUTAS:

- **NÃO PODE** encerrar sessão sem salvar estado
- **NÃO PODE** fazer operações longas sem checkpoint
- **NÃO PODE** deixar contexto apenas na memória
- **DEVE** manter `.claude/sessions/LATEST-SESSION.md` atualizado
- **DEVE** salvar automaticamente nos gatilhos acima
- **DEVE** ao iniciar sessão, oferecer /resume se houver sessão anterior

```
⚠️ CONTEXTO PERDIDO = TRABALHO PERDIDO
⚠️ SALVAR É OBRIGATÓRIO, NÃO OPCIONAL
⚠️ AUTO-SAVE NOS GATILHOS. SEM PEDIR.
```

---

## 🚫 REGRA #12: VARREDURA AUTOMÁTICA E LOGS OBRIGATÓRIOS

**QUANDO O USUÁRIO MENCIONAR QUALQUER VARREDURA/LEITURA DE PLANILHA:**

### Gatilhos de Ativação:
- "Faça a varredura..."
- "Leia a planilha..."
- "Verifique os downloads..."
- "De-para..."
- "O que falta baixar..."
- Link de planilha Google Sheets
- Qualquer menção a Fase 1, 2, 2.5, 3 relacionada a arquivos

### Ação Automática OBRIGATÓRIA:

```
1. IDENTIFICAR FASE ATUAL
   └── Fase 1 (Download) / Fase 2 (Organização) / Fase 2.5 (Tags) / Fase 3 (De-Para)

2. EXECUTAR VARREDURA COMPLETA
   ├── Ler planilha via MCP (todas as abas)
   ├── Identificar estrutura de colunas
   ├── Extrair lista de arquivos esperados
   ├── Comparar com INBOX atual
   └── Identificar: faltantes, extras, duplicatas

3. GERAR LOG NO FORMATO PADRÃO (OBRIGATÓRIO)
   ├── ASCII art header
   ├── Contexto da missão
   ├── Métricas por fonte
   ├── Tabela de status
   ├── Ações necessárias
   └── Próximos passos

4. EXECUTAR AÇÕES SEM PEDIR
   ├── Baixar faltantes automaticamente
   ├── Gerar TAGs para novos arquivos
   ├── Atualizar planilha com TAGs (coluna H)
   └── Mover duplicatas para backup
```

### Template de Log de Varredura:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VARREDURA DE PLANILHA - FASE X                            ║
║                         [NOME DA MISSÃO]                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Data: YYYY-MM-DD HH:MM                                                      ║
║  Planilha: [ID ou Nome]                                                      ║
║  Abas processadas: N                                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                           RESULTADO DA VARREDURA                             │
├──────────────────────────────────────────────────────────────────────────────┤
│  📋 Esperados (planilha):     XXX arquivos                                  │
│  📂 No INBOX:                 XXX arquivos                                  │
│  ✅ Com match:                XXX (XX.X%)                                   │
│  ❌ Faltantes:                XXX                                           │
│  ⚠️  Extras:                   XXX                                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           POR FONTE/ABA                                      │
├────────────────────────────────────────┬─────────┬──────────┬───────────────┤
│  FONTE                                 │ ESPERADO│ TEMOS    │ STATUS        │
├────────────────────────────────────────┼─────────┼──────────┼───────────────┤
│  [Fonte 1]                             │   XXX   │   XXX    │ ✅/⚠️/❌       │
│  [Fonte 2]                             │   XXX   │   XXX    │ ✅/⚠️/❌       │
└────────────────────────────────────────┴─────────┴──────────┴───────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           AÇÕES EXECUTADAS                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│  ✅ [Ação 1]                                                                │
│  ✅ [Ação 2]                                                                │
│  ⏳ [Ação pendente]                                                         │
└──────────────────────────────────────────────────────────────────────────────┘

➡️  PRÓXIMOS PASSOS:
   1. [Próximo passo 1]
   2. [Próximo passo 2]
```

### Regras Absolutas:

- **NÃO PODE** fazer varredura sem entregar log no formato acima
- **NÃO PODE** pedir autorização para baixar - BAIXAR automaticamente
- **NÃO PODE** pedir autorização para limpar duplicatas - LIMPAR automaticamente
- **DEVE** atualizar planilha com TAGs após download
- **DEVE** entregar log visual no chat SEMPRE
- **DEVE** salvar log em `.claude/mission-control/`

```
⚠️ VARREDURA SEM LOG = VARREDURA INCOMPLETA
⚠️ LOG SEM FORMATO PADRÃO = LOG INVÁLIDO
⚠️ AUTOMÁTICO. SEM PERGUNTAR. SEMPRE.
```

---

## 🚫 REGRA #13: PLAN MODE OBRIGATÓRIO PARA TAREFAS COMPLEXAS

**ANTES DE QUALQUER TAREFA COMPLEXA, ENTRAR EM PLAN MODE.**

### Quando Usar Plan Mode:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GATILHOS PARA PLAN MODE:                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✓ Nova feature ou funcionalidade                                          │
│  ✓ Refatoração de código existente                                         │
│  ✓ Processamento de batch grande (>10 arquivos)                            │
│  ✓ Criação de novo agente ou playbook                                      │
│  ✓ Alteração em múltiplos arquivos                                         │
│  ✓ Qualquer tarefa que leve >30 minutos                                    │
│  ✓ Quando houver múltiplas abordagens possíveis                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Como Ativar:
- **No terminal:** Pressionar `Shift+Tab` duas vezes
- **Ou digitar:** "entre em plan mode" / "vamos planejar primeiro"

### Fluxo Obrigatório:

```
1. ENTRAR EM PLAN MODE
   └── Shift+Tab 2x ou comando explícito

2. APRESENTAR PLANO INICIAL
   └── Estrutura, etapas, arquivos envolvidos

3. IR E VOLTAR MÚLTIPLAS VEZES
   └── Refinar até o plano estar sólido
   └── Perguntar: "Algo mais que devo considerar?"
   └── Pedir feedback do usuário

4. CONFIRMAR PLANO FINAL
   └── Usuário aprova antes de executar

5. SÓ ENTÃO EXECUTAR
   └── Com plano aprovado, execução é mais precisa
```

### Benefícios:

- **One-shot quality:** Plano bem feito = execução sem retrabalho
- **Menos bugs:** Antecipa problemas antes de codar
- **Alinhamento:** Usuário sabe exatamente o que vai acontecer

### Regras Absolutas:

- **NÃO PODE** iniciar tarefa complexa sem plan mode
- **NÃO PODE** executar na primeira versão do plano - refinar sempre
- **DEVE** perguntar se há algo mais a considerar
- **DEVE** obter aprovação antes de executar

```
⚠️ PLAN MODE ECONOMIZA TEMPO NO LONGO PRAZO
⚠️ PLANO RUIM = EXECUÇÃO RUIM = RETRABALHO
⚠️ SEMPRE REFINAR. SEMPRE CONFIRMAR.
```

---

## 🚫 REGRA #14: VERIFICAÇÃO PÓS-SESSÃO OBRIGATÓRIA

**AO FINAL DE CADA SESSÃO SIGNIFICATIVA, VERIFICAR TRABALHO.**

### Quando Verificar:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GATILHOS PARA VERIFICAÇÃO:                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✓ Após processar qualquer batch                                           │
│  ✓ Após criar/modificar código                                             │
│  ✓ Após criar novo agente ou playbook                                      │
│  ✓ Antes de encerrar sessão longa (>1 hora)                                │
│  ✓ Quando usuário disser "terminamos" / "é isso por hoje"                  │
│  ✓ Após qualquer operação que modifique múltiplos arquivos                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### O Que Verificar:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKLIST DE VERIFICAÇÃO:                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  [ ] Código segue boas práticas?                                           │
│  [ ] Não há vulnerabilidades de segurança óbvias?                          │
│  [ ] Arquivos foram salvos corretamente?                                   │
│  [ ] Logs foram gerados?                                                   │
│  [ ] Estado foi atualizado (MISSION-STATE, JARVIS-STATE)?                  │
│  [ ] Não há arquivos temporários esquecidos?                               │
│  [ ] Trabalho está consistente com o plano original?                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Comando de Verificação:

Use `/verify` ou diga "verifique seu trabalho" para ativar verificação completa.

### Ação Automática:

```
JARVIS deve AUTOMATICAMENTE ao final de sessões:
1. Revisar todas as alterações feitas
2. Verificar segurança do código
3. Confirmar que logs foram gerados
4. Atualizar estados do sistema
5. Reportar resumo ao usuário
```

### Regras Absolutas:

- **NÃO PODE** encerrar sessão sem verificação
- **NÃO PODE** deixar código sem review de segurança
- **DEVE** verificar automaticamente nos gatilhos acima
- **DEVE** reportar resultado da verificação ao usuário

```
⚠️ VERIFICAÇÃO PREVINE BUGS E VULNERABILIDADES
⚠️ MELHOR VERIFICAR AGORA DO QUE DESCOBRIR DEPOIS
⚠️ AUTOMÁTICO. SEM PEDIR.
```

---

## 📋 CHECKLIST RÁPIDO - PERSISTENCE

```
[ ] Sessão sendo salva automaticamente nos gatilhos?
[ ] LATEST-SESSION.md atualizado?
[ ] /save e /resume disponíveis?
[ ] Varredura gerando log no formato padrão?
[ ] Ações de varredura executadas sem pedir?
[ ] Tarefa complexa? Entrou em Plan Mode?
[ ] Plano foi refinado antes de executar?
[ ] Verificação pós-sessão executada?
[ ] Estados do sistema atualizados?
```

---

**FIM DO RULE-GROUP-2**
