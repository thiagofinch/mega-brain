# /verify - Verification Loop

## Trigger
`/verify` - Use antes de declarar trabalho completo, corrigido ou passando

## Objetivo
Implementar o "Verification Loop" do workflow Boris Cherny: Claude testa seu proprio output antes de declarar que terminou.

## Fluxo de Execucao

### 1. IDENTIFICAR O QUE FOI FEITO

Antes de verificar, identifique o escopo:
- Codigo criado ou modificado
- Batches processados
- Agentes criados/atualizados
- Skills criadas
- Configuracoes alteradas

### 2. VERIFICACOES POR TIPO

#### Para CODIGO Python:
```bash
# Syntax check
python3 -m py_compile arquivo.py

# Se tiver tests, rodar
python3 -m pytest arquivo_test.py -v

# Se nao tiver tests, criar teste basico e rodar
```

#### Para BATCHES:
```
[ ] Template V2 completo? (14 secoes)
[ ] ASCII headers presentes?
[ ] Cascateamento executado? (REGRA #22)
[ ] Dual-location gravado? (REGRA #8)
[ ] Log mostrado no chat?
```

#### Para AGENTES:
```
[ ] Template V3 completo? (11 partes)
[ ] SOUL.md criado?
[ ] DNA-CONFIG.yaml criado?
[ ] Citacoes rastreaveis presentes?
[ ] Referenciado em _INDEX.md?
```

#### Para SKILLS:
```
[ ] SKILL.md com frontmatter correto?
[ ] Instrucoes claras?
[ ] Exemplos de uso?
[ ] Dependencias listadas?
```

#### Para CONFIGURACOES:
```
[ ] JSON valido?
[ ] Paths corretos?
[ ] Permissoes adequadas?
```

### 3. EXECUTAR VERIFICACAO

```python
# Template de verificacao
CHECKLIST = """
## VERIFICATION LOOP

### Escopo Verificado
- Tipo: [CODIGO/BATCH/AGENT/SKILL/config]
- Arquivos: [lista]
- Modificacoes: [lista]

### Testes Executados
- [ ] [Teste 1]: [PASS/FAIL] - [detalhes]
- [ ] [Teste 2]: [PASS/FAIL] - [detalhes]
- [ ] [Teste 3]: [PASS/FAIL] - [detalhes]

### Resultado
- Status: [VERIFIED/NEEDS_FIX]
- Confianca: [X]%
- Issues encontradas: [N]

### Proxima Acao
- [Se VERIFIED]: Trabalho pode ser declarado completo
- [Se NEEDS_FIX]: [lista de fixes necessarios]
"""
```

### 4. REGRA DE OURO

```
NAO DECLARE "PRONTO" SEM RODAR /verify
NAO DECLARE "CORRIGIDO" SEM RODAR /verify
NAO DECLARE "PASSANDO" SEM RODAR /verify
```

### 5. FALHAS COMUNS (EVITAR)

| Falha | Como Evitar |
|-------|-------------|
| Dizer "corrigido" sem testar | SEMPRE rodar verificacao |
| Assumir que syntax esta ok | SEMPRE rodar py_compile |
| Assumir que batch esta completo | SEMPRE checar 14 secoes |
| Assumir que agent esta correto | SEMPRE checar 11 partes |

## Exemplo de Uso

**Usuario**: "Crie um script para processar INBOX"

**JARVIS cria o script, depois executa /verify:**

```
## VERIFICATION LOOP

### Escopo Verificado
- Tipo: CODIGO
- Arquivos: scripts/process_inbox.py
- Modificacoes: Arquivo novo (150 linhas)

### Testes Executados
- [x] Syntax check: PASS
- [x] Import check: PASS (todas libs disponiveis)
- [x] Dry-run test: PASS (executou sem erros)
- [x] Output validation: PASS (output esperado)

### Resultado
- Status: VERIFIED
- Confianca: 95%
- Issues encontradas: 0

### Proxima Acao
- Trabalho pode ser declarado completo
- Script pronto para uso em producao
```

**SO ENTAO JARVIS declara**: "Script criado e verificado, senhor."

## Integracao com Sistema

Este skill complementa:
- `stop_hook_completeness.py` - Stop hook que verifica antes de parar
- `post_write_validator.py` - Valida automaticamente apos Write/Edit
- `LEDGER.md` - Registra verificacoes no historico

## Metricas de Sucesso

- Reducao de 80% em "bugs pos-entrega"
- Confianca de 95%+ em trabalho declarado completo
- Zero retrabalho por falta de verificacao
