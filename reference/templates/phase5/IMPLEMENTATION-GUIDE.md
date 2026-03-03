# 🚨 INSTRUÇÃO CRÍTICA DE IMPLEMENTAÇÃO
## Templates Visuais da Fase 5 - MOGA BRAIN / JARVIS Pipeline

---

## ⚠️ LEIA ISTO PRIMEIRO

Este documento acompanha o arquivo `MOGA-BRAIN-PHASE5-TEMPLATES.md` e contém instruções **OBRIGATÓRIAS** para sua implementação no sistema JARVIS.

**VOCÊ DEVE:**
1. Internalizar o arquivo de templates no local correto
2. Usar os templates automaticamente sempre que a Fase 5 for executada
3. Nunca executar a Fase 5 sem produzir o output visual correspondente

---

## 📁 ONDE COLOCAR O ARQUIVO

O arquivo `MOGA-BRAIN-PHASE5-TEMPLATES.md` deve ser colocado em:

```
/system/templates/PHASE5/MOGA-BRAIN-PHASE5-TEMPLATES.md
```

### Estrutura esperada após implementação:

```
/system/
├── TEMPLATES/
│   ├── PHASE1/
│   │   └── ... (templates existentes)
│   ├── PHASE2/
│   │   └── ... (templates existentes)
│   ├── PHASE3/
│   │   └── ... (templates existentes)
│   ├── PHASE4/
│   │   └── ... (templates existentes)
│   ├── PHASE5/                              ← CRIAR SE NÃO EXISTIR
│   │   └── MOGA-BRAIN-PHASE5-TEMPLATES.md   ← COLOCAR AQUI
│   └── _INDEX.md                            ← ATUALIZAR
├── OPEN-LOOPS.json
├── SESSION-STATE.md
└── ...
```

### Comando para implementar:

```bash
# Criar diretório se não existir
mkdir -p /system/templates/PHASE5/

# Mover/copiar o arquivo
cp MOGA-BRAIN-PHASE5-TEMPLATES.md /system/templates/PHASE5/

# Atualizar _INDEX.md
echo "- PHASE5/MOGA-BRAIN-PHASE5-TEMPLATES.md" >> /system/templates/_INDEX.md
```

---

## 🔴 REGRA ABSOLUTA DE USO

### SEMPRE QUE A FASE 5 FOR EXECUTADA:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   REGRA: FASE 5 EXECUTADA = TEMPLATE EXIBIDO                                 ║
║                                                                              ║
║   Não existe execução da Fase 5 sem output visual.                           ║
║   Os templates NÃO são opcionais.                                            ║
║   Os templates são parte INTEGRAL do output da fase.                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Fluxo obrigatório:

```
USUÁRIO SOLICITA: "Executar Fase 5 para [FONTE]"
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. CARREGAR template de /system/templates/PHASE5/                       │
│  2. EXECUTAR lógica da subfase (5.1, 5.2, etc.)                             │
│  3. PREENCHER template com dados reais                                      │
│  4. EXIBIR template completo no chat                                        │
│  5. AGUARDAR confirmação ou próximo comando                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 QUANDO USAR CADA TEMPLATE

| Situação | Template a Usar |
|----------|-----------------|
| Processando DNA de uma fonte | **5.1 - FOUNDATION** |
| Criando/atualizando PERSON Agent | **5.2 - PERSON AGENTS** |
| Criando/atualizando CARGO Agents | **5.3 - CARGO AGENTS** |
| Consolidando Theme Dossiers | **5.4 - THEME DOSSIERS** |
| Sincronizando ORG-LIVE | **5.5 - ORG-LIVE** |
| Validação final de uma fonte | **5.6 - VALIDATION** |
| Todas as fontes processadas | **5.FINAL - CONSOLIDADO** |

### Ordem de execução POR FONTE:

```
FONTE: Cole Gordon
├── Exibir Template 5.1
├── Exibir Template 5.2
├── Exibir Template 5.3
├── Exibir Template 5.4
├── Exibir Template 5.5
└── Exibir Template 5.6

FONTE: Jeremy Miner
├── Exibir Template 5.1
├── Exibir Template 5.2
...

APÓS TODAS AS FONTES:
└── Exibir Template 5.FINAL
```

---

## 🔧 COMO PREENCHER OS TEMPLATES

### Variáveis a substituir:

Todas as variáveis estão no formato `{NOME_VARIAVEL}`:

| Variável | Como obter | Exemplo |
|----------|------------|---------|
| `{NOME_DA_FONTE}` | Nome da pessoa/entidade sendo processada | "COLE GORDON" |
| `{YYYY-MM-DD HH:MM}` | `datetime.now().strftime("%Y-%m-%d %H:%M")` | "2026-01-09 15:30" |
| `{VERSION}` | De JARVIS-VERSION ou config | "3.33.0" |
| `{N}` | Contador do contexto | "15" |
| `{N_ANTES}` | Valor antes da execução | "45" |
| `{N_DEPOIS}` | Valor após execução | "58" |
| `{DELTA}` | `N_DEPOIS - N_ANTES` | "+13" |
| `{%}` | Porcentagem calculada | "39.5" |

### Barras de progresso:

```python
def progress_bar(percentage, width=20):
    filled = int(percentage / 100 * width)
    empty = width - filled
    return "█" * filled + "░" * empty

# Exemplo:
# 75% → ███████████████░░░░░
```

### Ícones de status:

| Status | Ícone |
|--------|-------|
| Completo/OK | ✅ |
| Novo (criado nesta execução) | 🆕 |
| Atenção/Parcial | ⚠️ |
| Crítico/Ação requerida | 🔴 |
| Monitorar | 🟡 |
| Info | 🟢 |

---

## 🚨 GATILHOS AUTOMÁTICOS

### O template DEVE ser exibido automaticamente quando:

1. **Comando direto:**
   - "Executar Fase 5"
   - "Rodar Phase 5"
   - "Processar [FONTE] na Fase 5"
   - "Alimentar agentes com [FONTE]"
   - "Consolidar [FONTE]"

2. **Comando de pipeline completo:**
   - "Executar pipeline completo"
   - "Processar [FONTE] do início ao fim"
   - Quando Fase 4 termina e Fase 5 inicia automaticamente

3. **Comandos específicos de subfase:**
   - "Criar PERSON Agent para [FONTE]" → Template 5.2
   - "Atualizar CARGO Agents" → Template 5.3
   - "Gerar Theme Dossiers" → Template 5.4
   - "Sincronizar ORG-LIVE" → Template 5.5

4. **Ao final de todas as fontes:**
   - Automaticamente exibir Template 5.FINAL

---

## ❌ O QUE NUNCA FAZER

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  PROIBIDO:                                                                   ║
║                                                                              ║
║  ❌ Executar Fase 5 sem exibir template visual                               ║
║  ❌ Resumir ou abreviar os templates                                         ║
║  ❌ Omitir seções "porque não há dados"                                      ║
║  ❌ Usar texto corrido ao invés do formato visual                            ║
║  ❌ Esquecer o header ASCII                                                  ║
║  ❌ Pular o menu de ações no final                                           ║
║  ❌ Não mostrar deltas (antes → depois)                                      ║
║  ❌ Ignorar gatilhos e alertas                                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Se não houver dados para uma seção:

**ERRADO:**
```
(omitir a seção)
```

**CORRETO:**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🆕 NOVOS CARGO AGENTS CRIADOS                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Nenhum novo CARGO Agent criado nesta execução.                              │
│  Agentes existentes foram enriquecidos (ver seção seguinte).                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 EXEMPLO DE USO COMPLETO

### Cenário: Usuário pede para processar Cole Gordon na Fase 5

**Input do usuário:**
```
"Execute a Fase 5 para Cole Gordon"
```

**Comportamento esperado do Claude Code:**

1. Carregar `/system/templates/PHASE5/MOGA-BRAIN-PHASE5-TEMPLATES.md`

2. Executar subfase 5.1 (Foundation)
   - Processar DNA
   - Preencher template 5.1 com dados reais
   - **EXIBIR template 5.1 completo no chat**

3. Executar subfase 5.2 (Person Agents)
   - Criar/atualizar AGENT-COLE-GORDON
   - Preencher template 5.2 com dados reais
   - **EXIBIR template 5.2 completo no chat**

4. [Repetir para 5.3, 5.4, 5.5, 5.6]

5. Ao final:
   - **EXIBIR menu de ações numeradas**
   - Aguardar próximo comando

---

## 🔗 INTEGRAÇÃO COM OUTROS SISTEMAS

### SESSION-STATE.md

Após cada subfase, atualizar:

```markdown
## ÚLTIMA EXECUÇÃO FASE 5

- **Fonte processada:** Cole Gordon
- **Subfase atual:** 5.3 - CARGO AGENTS
- **Status:** Em andamento
- **Último template exibido:** 5.2 - PERSON AGENTS
- **Timestamp:** 2026-01-09 15:30
```

### OPEN-LOOPS.json

Se algum alerta for gerado, adicionar:

```json
{
  "id": "OL-XXX",
  "type": "JD_UPDATE_NEEDED",
  "description": "JD-CLOSER.md precisa atualização após +15 heurísticas de Cole Gordon",
  "context": "Fase 5.5 detectou divergência",
  "suggested_command": "Atualizar JD-CLOSER com novas heurísticas",
  "priority": "MEDIUM",
  "status": "OPEN"
}
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

Antes de considerar implementado, verificar:

- [ ] Arquivo `MOGA-BRAIN-PHASE5-TEMPLATES.md` está em `/system/templates/PHASE5/`
- [ ] `_INDEX.md` foi atualizado com referência ao novo arquivo
- [ ] Templates são carregados automaticamente quando Fase 5 é invocada
- [ ] Todas as 7 variações de template estão funcionando
- [ ] Variáveis são substituídas corretamente
- [ ] Barras de progresso renderizam corretamente
- [ ] Menu de ações aparece no final de cada template
- [ ] SESSION-STATE.md é atualizado após cada subfase
- [ ] OPEN-LOOPS.json recebe alertas quando aplicável

---

## 📌 LEMBRETE FINAL

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   O PROPÓSITO DOS TEMPLATES É:                                               ║
║                                                                              ║
║   1. DAR VISIBILIDADE ao usuário sobre o que está acontecendo                ║
║   2. MOSTRAR DELTAS claros (o que mudou)                                     ║
║   3. ALERTAR sobre gatilhos e ações necessárias                              ║
║   4. DOCUMENTAR automaticamente cada execução                                ║
║   5. MANTER CONSISTÊNCIA entre todas as execuções                            ║
║                                                                              ║
║   Os templates são a INTERFACE entre o sistema e o usuário.                  ║
║   Sem eles, o usuário está "cego" sobre o que acontece internamente.         ║
║                                                                              ║
║   NUNCA EXECUTE FASE 5 SEM EXIBIR OS TEMPLATES.                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🆘 SE ALGO DER ERRADO

Se por algum motivo os templates não puderem ser carregados:

1. Verificar se o arquivo existe no path correto
2. Verificar se o formato está íntegro (não corrompido)
3. Se necessário, reconstruir a partir do backup ou solicitar ao usuário

**NUNCA** executar a Fase 5 sem output visual. Se os templates não estiverem disponíveis, **PARAR** e informar o usuário.

---

**Versão:** 1.0.0
**Data:** 2026-01-09
**Autor:** Sistema MOGA BRAIN
**Compatível com:** JARVIS v3.33.0+
