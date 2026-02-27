# RULE-GROUP-4: PHASE-5-SPECIFIC

> **Auto-Trigger:** Regras específicas da Fase 5 e cascateamento de conhecimento
> **Keywords:** "agente", "dossier", "cascateamento", "source", "Fase 5", "person agent", "cargo agent", "5.1", "5.2", "5.3", "5.4", "theme", "dna"
> **Prioridade:** ALTA
> **Regras:** 18, 19, 20, 21, 22

---

## 🚫 REGRA #18: TEMPLATES FASE 5 OBRIGATÓRIOS

**TODA EXECUÇÃO DA FASE 5 DEVE USAR OS TEMPLATES VISUAIS OFICIAIS.**

### Templates Disponíveis:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LOCALIZAÇÃO: /reference/templates/PHASE5/                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ARQUIVOS:                                                                  │
│  ├── MOGA-BRAIN-PHASE5-TEMPLATES.md    (7 templates visuais)                │
│  ├── IMPLEMENTATION-GUIDE.md            (guia de uso)                       │
│  └── README.md                          (instruções)                        │
│                                                                             │
│  SUB-TEMPLATES:                                                             │
│  ├── 5.1 - FOUNDATION         → Após extrair DNA de uma fonte              │
│  ├── 5.2 - PERSON AGENTS      → Após criar/atualizar agente de pessoa      │
│  ├── 5.3 - CARGO AGENTS       → Após criar/atualizar agentes de cargo      │
│  ├── 5.4 - THEME DOSSIERS     → Após consolidar dossiers temáticos         │
│  ├── 5.5 - SUA-EMPRESA        → Após sincronizar estrutura organizacional  │
│  ├── 5.6 - VALIDATION         → Validação final por fonte                  │
│  └── 5.FINAL - CONSOLIDADO    → Relatório cross-source após todas fontes   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Uso Obrigatório por Momento:

| MOMENTO | TEMPLATE OBRIGATÓRIO |
|---------|----------------------|
| Após extrair DNA de uma fonte | Template 5.1 - FOUNDATION |
| Após criar/atualizar PERSON agent | Template 5.2 - PERSON AGENTS |
| Após criar/atualizar CARGO agents | Template 5.3 - CARGO AGENTS |
| Após consolidar theme dossiers | Template 5.4 - THEME DOSSIERS |
| Após sincronizar SUA-EMPRESA | Template 5.5 - SUA-EMPRESA |
| Após validar uma fonte completa | Template 5.6 - VALIDATION |
| Após COMPLETAR TODA A FASE 5 | Template 5.FINAL - CONSOLIDADO |

### Regras Absolutas:

- **NÃO PODE** executar Fase 5 sem carregar template correspondente
- **NÃO PODE** resumir ou abreviar os templates
- **NÃO PODE** omitir seções ou headers ASCII
- **NÃO PODE** criar "resumos" em vez de logs oficiais com template
- **DEVE** exibir template COMPLETO no chat após cada subfase
- **DEVE** preencher variáveis com dados reais
- **DEVE** incluir menu de ações no final
- **DEVE** usar Template 5.FINAL para log de conclusão da Fase 5

```
⚠️ FASE 5 SEM TEMPLATE = FASE 5 INCOMPLETA
⚠️ O TEMPLATE É A INTERFACE DO SISTEMA
⚠️ SEM TEMPLATE, O USUÁRIO ESTÁ CEGO
⚠️ RESUMOS NÃO SUBSTITUEM TEMPLATES OFICIAIS
```

---

## 🚫 REGRA #19: CARREGAMENTO POR FONTE NA FASE 5 (ISOLAMENTO)

**NA FASE 5, CADA READ DEVE CARREGAR TODOS OS BATCHES DE UMA ÚNICA FONTE.**

### Estratégia de Isolamento:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ESTRATÉGIA: MONOLÍTICA COM ISOLAMENTO POR FONTE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OBJETIVO: Máxima pureza. Zero contaminação cross-source.                   │
│                                                                             │
│  FLUXO:                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ READ 1: Carregar TODOS os batches de Jeremy Miner (JM)               │   │
│  │         → Consolidar DNA-JM + SOURCE-JM + DOSSIER-JM + AGENT-JM      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ READ 2: Carregar TODOS os batches de Jeremy Haynes (JH)              │   │
│  │         → Consolidar DNA-JH + SOURCE-JH + DOSSIER-JH + AGENT-JH      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ READ FINAL: Carregar todos os PERSON DNAs já consolidados            │   │
│  │             → Criar CARGO Agents, Theme Dossiers, SUA-EMPRESA        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Por Que Isolamento:

| Problema | Solução com Isolamento |
|----------|------------------------|
| Contaminação cross-source inconsciente | Cada read carrega apenas uma fonte |
| Perda de pureza | Voz do especialista preservada 100% |
| Mistura de perspectivas | PERSON Agent = 100% única fonte |

### Regras Absolutas:

- **NÃO PODE** carregar batches de fontes diferentes no mesmo read
- **NÃO PODE** consolidar fonte enquanto outra está carregada
- **DEVE** processar uma fonte completa antes de passar para próxima
- **DEVE** criar PERSON Agent imediatamente após consolidar cada fonte

```
⚠️ ISOLAMENTO = PUREZA
⚠️ PUREZA = FIDELIDADE AO ESPECIALISTA
⚠️ FIDELIDADE = VALOR DO SISTEMA
```

---

## 🚫 REGRA #20: FLUXO MODULAR POR FONTE NA FASE 5 (AVANÇAR É DEFAULT)

**CADA FONTE COMPLETA 5.1→5.4 SEQUENCIALMENTE. SEM PERGUNTAR. AVANÇAR É O PADRÃO.**

### Fluxo Obrigatório por Fonte:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 5: FLUXO MODULAR POR FONTE                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 5.1 FOUNDATION                                                       │   │
│  │     → Ler TODOS os batches da fonte                                  │   │
│  │     → Consolidar DNA (CONFIG.yaml + 5 camadas)                       │   │
│  │     → Criar SOURCE-XX.md                                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓ AVANÇAR                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 5.2 PERSON AGENT                                                     │   │
│  │     → Atualizar/Criar AGENT.md                                       │   │
│  │     → Atualizar/Criar SOUL.md                                        │   │
│  │     → Atualizar MEMORY.md                                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓ AVANÇAR                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 5.3 CARGO CONTRIBUTIONS                                              │   │
│  │     → Identificar contribuições para CARGO agents                    │   │
│  │     → Enriquecer DNA-CONFIG.yaml dos CARGOs relevantes               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓ AVANÇAR                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 5.4 THEME DOSSIERS                                                   │   │
│  │     → Criar/Atualizar dossiers temáticos relevantes                  │   │
│  │     → Cross-referenciar com PERSON e CARGO agents                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ LOG FINAL DA FONTE                                                   │   │
│  │     → Entregar relatório completo da fonte                           │   │
│  │     → Mostrar artefatos criados/atualizados                          │   │
│  │     → Marcar fonte como COMPLETE                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PRÓXIMA FONTE                                                        │   │
│  │     → Repetir 5.1→5.4 para próxima fonte                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  APÓS TODAS AS FONTES COMPLETAS:                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 5.5 SUA-EMPRESA → Sincronizar estrutura organizacional               │   │
│  │ 5.6 VALIDATION → Validação final cross-source                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Comportamento Default:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚡ AVANÇAR É O DEFAULT - NÃO PERGUNTAR                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ❌ PROIBIDO:                                                               │
│     "Posso avançar para 5.2?"                                               │
│     "Quer que eu continue com 5.3?"                                         │
│     "Devo prosseguir para a próxima subfase?"                               │
│     "O que fazemos agora?"                                                  │
│                                                                             │
│  ✅ CORRETO:                                                                │
│     Completou 5.1 → Avança para 5.2 automaticamente                         │
│     Completou 5.2 → Avança para 5.3 automaticamente                         │
│     Completou 5.3 → Avança para 5.4 automaticamente                         │
│     Completou 5.4 → Entrega LOG FINAL → Próxima fonte                       │
│                                                                             │
│  ÚNICA EXCEÇÃO: Bloqueio técnico ou erro crítico                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Regras Absolutas:

- **NÃO PODE** perguntar se deve avançar - avançar é o padrão
- **NÃO PODE** parar entre subfases para pedir confirmação
- **NÃO PODE** sugerir alternativas ao fluxo padrão
- **DEVE** completar 5.1→5.4 para uma fonte antes de ir para outra
- **DEVE** entregar LOG FINAL após completar cada fonte
- **DEVE** avançar automaticamente entre subfases

```
⚠️ AVANÇAR É DEFAULT - NÃO PERGUNTE
⚠️ O FLUXO É FIXO - NÃO SUGIRA ALTERNATIVAS
⚠️ 90% DOS CASOS = AVANÇAR
```

---

## 🚫 REGRA #21: CASCATEAMENTO OBRIGATÓRIO DE THEME DOSSIERS (FASE 5.4)

**DOSSIERS EXISTENTES DEVEM SER ATUALIZADOS, NÃO IGNORADOS.**

### O Problema que Esta Regra Resolve:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BUG DETECTADO (2026-01-10):                                                │
│                                                                             │
│  • Batches 068-084 processados (Jeremy Haynes)                              │
│  • DOSSIER-CALL-FUNNELS existia (v2.0, 2025-12-20)                          │
│  • DOSSIER-SHOW-RATES existia (v2.0, 2025-12-20)                            │
│  • FASE 5.4 verificou que EXISTIAM → NÃO ATUALIZOU                          │
│  • Resultado: Dossiers desatualizados, conhecimento perdido                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Correto na FASE 5.4:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 5.4 - THEME DOSSIERS (FLUXO CORRETO)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PARA CADA TEMA que a fonte contribui:                                      │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 1. VERIFICAR se dossier existe                                       │   │
│  │    └── NÃO existe? → CRIAR                                           │   │
│  │    └── Existe? → VERIFICAR VERSÃO                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 2. COMPARAR data do dossier vs data dos batches                      │   │
│  │    └── Dossier mais novo que batches? → SKIP                         │   │
│  │    └── Batches mais novos que dossier? → ATUALIZAR                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                           ↓                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 3. ATUALIZAR com conteúdo dos novos batches                          │   │
│  │    ├── Incrementar versão (v2.0 → v3.0.0)                            │   │
│  │    ├── Adicionar novos frameworks/heurísticas/metodologias           │   │
│  │    ├── Atualizar referências de fonte (JH002 → JH-XXXX)              │   │
│  │    └── Atualizar timestamp e protocolo                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Checklist OBRIGATÓRIO na Fase 5.4:

```
ANTES de marcar 5.4 como completo para uma fonte:

[ ] Listei TODOS os temas que a fonte contribui
[ ] Para cada tema:
    [ ] Verifiquei se dossier existe
    [ ] Se existe, comparei versão vs data dos batches
    [ ] Se batches > dossier → ATUALIZEI
[ ] Todos os dossiers afetados estão com versão >= data dos batches
```

### Regras Absolutas:

- **NÃO PODE** assumir que "dossier existe = dossier atualizado"
- **NÃO PODE** ignorar dossiers antigos quando há batches novos
- **NÃO PODE** marcar 5.4 como completo sem verificar versões
- **DEVE** sempre comparar: data_dossier vs data_ultimo_batch
- **DEVE** atualizar se batches > dossier
- **DEVE** incrementar versão ao atualizar

```
⚠️ EXISTE ≠ ATUALIZADO
⚠️ SEMPRE COMPARAR VERSÕES
⚠️ CASCATEAMENTO É OBRIGATÓRIO
```

---

## 🚫 REGRA #22: CASCATEAMENTO MULTI-DESTINO PÓS-BATCH

**A SEÇÃO "DESTINO DO CONHECIMENTO" NÃO É INFORMATIVA - É ORDEM DE EXECUÇÃO.**

### O Problema que Esta Regra Resolve:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  BUG DETECTADO (2026-01-10):                                                 │
│                                                                              │
│  • Batches listam "DESTINO DO CONHECIMENTO" com agentes, playbooks, etc.     │
│  • Essa seção era DECORATIVA - ninguém lia, ninguém executava                │
│  • Resultado: Conhecimento extraído mas NUNCA cascateado para destinos       │
│  • Temas como CRM, Follow-Up, 3A Framework ficaram órfãos                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Obrigatório APÓS Criar Batch:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  APÓS criar qualquer batch na Fase 4, EXECUTAR IMEDIATAMENTE:               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. LER seção "DESTINO DO CONHECIMENTO" do batch                            │
│                                                                             │
│  2. PARA CADA DESTINO listado, executar cascateamento:                      │
│                                                                             │
│     ┌─ AGENTES (PERSON + CARGO) ───────────────────────────────────────┐    │
│     │  → Verificar se agente existe em /agents/                     │    │
│     │  → Se NÃO existe → CRIAR estrutura (AGENT.md, SOUL.md, etc.)     │    │
│     │  → Se EXISTE → ATUALIZAR MEMORY.md com novos elementos           │    │
│     │  → Adicionar referência ao batch na seção de fontes              │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│     ┌─ PLAYBOOKS ──────────────────────────────────────────────────────┐    │
│     │  → Verificar se playbook existe em /knowledge/playbooks/      │    │
│     │  → Se NÃO existe → CRIAR com frameworks do batch                 │    │
│     │  → Se EXISTE → ADICIONAR novos frameworks/metodologias           │    │
│     │  → Incrementar versão do playbook                                │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│     ┌─ DNAs (PERSON) ──────────────────────────────────────────────────┐    │
│     │  → Atualizar DNA-CONFIG.yaml da fonte com +N elementos           │    │
│     │  → Incrementar contadores nas 5 camadas                          │    │
│     │  → Registrar batch como fonte dos novos elementos                │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│     ┌─ SUA-EMPRESA SOWs ───────────────────────────────────────────────┐    │
│     │  → Atualizar SOW do cargo com novas responsabilidades            │    │
│     │  → Adicionar métricas identificadas no batch                     │    │
│     │  → Registrar fonte da atualização                                │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│     ┌─ THEME DOSSIERS ─────────────────────────────────────────────────┐    │
│     │  → Verificar se dossier do tema existe                           │    │
│     │  → Aplicar REGRA #21 (criar ou atualizar com versão)             │    │
│     │  → Adicionar frameworks/heurísticas do batch                     │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  3. ADICIONAR seção ao batch:                                               │
│     └── "### ✅ Cascateamento Executado"                                    │
│     └── Lista de destinos criados/atualizados com timestamps               │
│                                                                             │
│  4. SÓ ENTÃO avançar para próximo batch                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Checklist Pós-Batch OBRIGATÓRIO:

```
ANTES DE INICIAR PRÓXIMO BATCH:

[ ] Seção "DESTINO DO CONHECIMENTO" lida?
[ ] AGENTES listados criados/atualizados?
[ ] PLAYBOOKS listados criados/atualizados?
[ ] DNAs incrementados?
[ ] SOWs atualizados?
[ ] DOSSIERS temáticos criados/atualizados (REGRA #21)?
[ ] Seção "Cascateamento Executado" adicionada ao batch?

SE QUALQUER ITEM FOR "NÃO" → BATCH INCOMPLETO → NÃO AVANÇAR
```

### Regras Absolutas:

- **NÃO PODE** salvar batch e ir para próximo sem cascatear
- **NÃO PODE** tratar "DESTINO" como informativo - é ordem de execução
- **NÃO PODE** criar agente/playbook/dossier sem registrar fonte
- **DEVE** executar cascateamento IMEDIATAMENTE após salvar batch
- **DEVE** adicionar seção "Cascateamento Executado" no batch
- **DEVE** verificar TODOS os 5 tipos de destino (agentes, playbooks, DNAs, SOWs, dossiers)

```
⚠️ DESTINO DO CONHECIMENTO = ORDEM DE EXECUÇÃO
⚠️ BATCH SEM CASCATEAMENTO = BATCH INCOMPLETO
⚠️ CONHECIMENTO EXTRAÍDO MAS NÃO CASCATEADO = CONHECIMENTO PERDIDO
```

---

## 📋 CHECKLIST RÁPIDO - PHASE-5-SPECIFIC

```
[ ] Na Fase 5? Usando templates oficiais?
[ ] Carregando batches de UMA fonte por vez (isolamento)?
[ ] Avançando automaticamente entre subfases (5.1→5.4)?
[ ] Não perguntando se deve avançar (AVANÇAR É DEFAULT)?
[ ] Dossiers existentes sendo ATUALIZADOS (não ignorados)?
[ ] Comparando versões: data_dossier vs data_batches?
[ ] Cascateamento multi-destino executado após cada batch?
[ ] Seção "Cascateamento Executado" adicionada aos batches?
```

---

**FIM DO RULE-GROUP-4**
