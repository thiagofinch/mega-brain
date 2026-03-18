# /verify - Verificação Pós-Sessão

---
name: verify
description: Verifica todo o trabalho da sessão atual - segurança, qualidade, logs e estados
version: 1.0.0
author: JARVIS
triggers:
  - /verify
  - verifique seu trabalho
  - verificação
  - review do trabalho
---

## PROPÓSITO

Executar verificação completa de todo trabalho realizado na sessão atual, garantindo:
- Boas práticas de código
- Segurança (sem vulnerabilidades óbvias)
- Logs gerados corretamente
- Estados atualizados
- Consistência com plano original

---

## QUANDO USAR

- Após processar qualquer batch
- Após criar/modificar código
- Após criar novo agente ou playbook
- Antes de encerrar sessão longa (>1 hora)
- Quando usuário disser "terminamos" / "é isso por hoje"
- Após qualquer operação que modifique múltiplos arquivos

---

## EXECUÇÃO

Ao receber `/verify`, JARVIS deve:

### 1. IDENTIFICAR ALTERAÇÕES DA SESSÃO

```
Listar todas as alterações feitas desde o início da sessão:
- Arquivos criados
- Arquivos modificados
- Arquivos deletados
- Comandos executados
- Batches processados
```

### 2. VERIFICAR CÓDIGO (se aplicável)

```
Para cada arquivo de código alterado:
[ ] Segue convenções do projeto?
[ ] Não há secrets/tokens hardcoded?
[ ] Não há vulnerabilidades óbvias (injection, XSS, etc)?
[ ] Imports estão corretos?
[ ] Não há código comentado desnecessário?
[ ] Error handling adequado?
```

### 3. VERIFICAR LOGS

```
[ ] Batch logs gerados em /logs/batches/?
[ ] JSON logs gerados em /.claude/mission-control/batch-logs/?
[ ] Session log atualizado?
[ ] Dual-location mantido?
```

### 4. VERIFICAR ESTADOS

```
[ ] MISSION-STATE.json atualizado?
[ ] JARVIS-STATE.json atualizado?
[ ] Progresso % correto?
[ ] next_action definido?
```

### 5. VERIFICAR CONSISTÊNCIA

```
[ ] Trabalho segue o plano original (se havia plano)?
[ ] Nenhum arquivo temporário esquecido?
[ ] Nenhuma tarefa incompleta deixada para trás?
[ ] Commits necessários foram feitos?
```

---

## FORMATO DE RESPOSTA

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VERIFICAÇÃO PÓS-SESSÃO                                    ║
║                         JARVIS SECURITY CHECK                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Sessão: SESSION-YYYY-MM-DD-XXX                                              ║
║  Duração: X horas Y minutos                                                  ║
║  Verificação: YYYY-MM-DD HH:MM                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                           ALTERAÇÕES NA SESSÃO                               │
├──────────────────────────────────────────────────────────────────────────────┤
│  Arquivos criados:     X                                                    │
│  Arquivos modificados: Y                                                    │
│  Batches processados:  Z                                                    │
│  Comandos executados:  N                                                    │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           CHECKLIST DE SEGURANÇA                             │
├──────────────────────────────────────────────────────────────────────────────┤
│  [✓] Sem secrets/tokens hardcoded                                           │
│  [✓] Sem vulnerabilidades óbvias                                            │
│  [✓] Error handling adequado                                                │
│  [✓] Código segue convenções                                                │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           CHECKLIST DE LOGS                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│  [✓] Batch logs gerados                                                     │
│  [✓] JSON logs gerados                                                      │
│  [✓] Dual-location mantido                                                  │
│  [✓] Session log atualizado                                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           CHECKLIST DE ESTADOS                               │
├──────────────────────────────────────────────────────────────────────────────┤
│  [✓] MISSION-STATE.json atualizado                                          │
│  [✓] JARVIS-STATE.json atualizado                                           │
│  [✓] Progresso % correto                                                    │
│  [✓] next_action definido                                                   │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           RESULTADO FINAL                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STATUS: ✅ APROVADO / ⚠️ ATENÇÃO NECESSÁRIA / ❌ PROBLEMAS ENCONTRADOS     │
│                                                                              │
│  Issues encontrados: X                                                       │
│  Warnings: Y                                                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

➡️  AÇÕES RECOMENDADAS:
   1. [Ação 1 se necessário]
   2. [Ação 2 se necessário]

✅ Sessão verificada. Seguro encerrar.
```

---

## AÇÕES AUTOMÁTICAS

Se encontrar problemas:

1. **SECRET EXPOSTO** → Alertar IMEDIATAMENTE, não encerrar sessão
2. **LOG FALTANDO** → Gerar log automaticamente
3. **ESTADO DESATUALIZADO** → Atualizar automaticamente
4. **ARQUIVO TEMPORÁRIO** → Perguntar se deve deletar

---

## INTEGRAÇÃO

Este comando deve ser executado:
- Automaticamente via hook `PreToolUse` quando detectar fim de sessão
- Manualmente via `/verify`
- Automaticamente após `/save`

---

**JARVIS COMMAND v1.0.0**
*Verificação de segurança e qualidade pós-sessão*
