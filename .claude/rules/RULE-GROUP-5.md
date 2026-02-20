# RULE-GROUP-5: VALIDATION

> **Auto-Trigger:** Regras de validação, integridade e enforcement automático
> **Keywords:** "validar", "source-sync", "integridade", "enforcement", "validate", "sync", "template enforcement", "cascading integrity", "phase5 validation"
> **Prioridade:** ALTA
> **Regras:** 23, 24, 25, 26

---

## 🚫 REGRA #23: VALIDAÇÃO AUTOMÁTICA DA FASE 5 (SCRIPT OBRIGATÓRIO)

**ANTES DE DECLARAR FASE 5 COMPLETA, EXECUTAR SCRIPT DE VALIDAÇÃO.**

### O Problema que Esta Regra Resolve:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  CAUSA RAIZ IDENTIFICADA (2026-01-10):                                       │
│                                                                              │
│  1. Template 5.4 tinha INTENÇÃO de atualizar dossiers, mas era INFORMATIVO   │
│  2. REGRA #21 foi criada REATIVAMENTE após bug ser detectado                 │
│  3. NÃO EXISTIA validação automática que detectasse dossiers desatualizados  │
│                                                                              │
│  Resultado: 12 dossiers ficaram desatualizados sem ninguém perceber          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Script de Validação:

```bash
# EXECUTAR ANTES DE DECLARAR FASE 5 COMPLETA:
python3 scripts/validate_phase5.py --fix
```

### O Que o Script Verifica:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VALIDAÇÕES AUTOMÁTICAS:                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. AGG FILES                                                               │
│     → AGG-VENDAS.yaml existe?                                               │
│     → AGG-OFFERS.yaml existe?                                               │
│     → AGG-OUTBOUND.yaml existe?                                             │
│                                                                             │
│  2. THEME DOSSIERS vs BATCH DATES (REGRA #21 ENFORCEMENT)                   │
│     → Para cada dossier: data_modificação vs data_batches                   │
│     → Se dossier < batches → OUTDATED → FALHA                               │
│     → Lista dossiers que precisam atualização                               │
│                                                                             │
│  3. EXIT CODE                                                               │
│     → 0 = PASSED (pode avançar)                                             │
│     → 1 = FAILED (NÃO pode avançar)                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Obrigatório:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ANTES DE DECLARAR FASE 5 COMPLETA:                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Executar: python3 scripts/validate_phase5.py                         │
│                                                                             │
│  2. Se FAILED:                                                              │
│     → Ler lista de dossiers desatualizados                                  │
│     → Atualizar cada dossier com conhecimento dos AGGs                      │
│     → Executar script novamente                                             │
│     → Repetir até PASSED                                                    │
│                                                                             │
│  3. Se PASSED:                                                              │
│     → Pode declarar Fase 5 como COMPLETE                                    │
│     → Atualizar MISSION-STATE.json                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Regras Absolutas:

- **NÃO PODE** declarar Fase 5 completa sem executar validate_phase5.py
- **NÃO PODE** ignorar exit code 1 (FAILED)
- **NÃO PODE** avançar com dossiers desatualizados
- **DEVE** executar script no início de cada sessão que trabalhe na Fase 5
- **DEVE** corrigir TODOS os dossiers desatualizados antes de avançar

```
⚠️ SCRIPT RETORNOU 1? NÃO PODE AVANÇAR.
⚠️ VALIDAÇÃO AUTOMÁTICA > VERIFICAÇÃO MANUAL
⚠️ ENFORCEMENT VIA CÓDIGO > ENFORCEMENT VIA REGRA
```

---

## 🚫 REGRA #24: TEMPLATE ENFORCEMENT OBRIGATÓRIO PARA AGENTES

**TODA CRIAÇÃO DE AGENTE DEVE USAR OS TEMPLATES OFICIAIS.**

### Templates Obrigatórios:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LOCALIZAÇÃO DOS TEMPLATES OFICIAIS:                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  /agents/_TEMPLATES/                                                     │
│  ├── TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md    ← AGENT.md (OBRIGATÓRIO)     │
│  └── INDEX.md                                  ← Guia de estrutura          │
│                                                                             │
│  /agents/protocols/                                                      │
│  ├── SOUL-TEMPLATE.md                          ← SOUL.md (OBRIGATÓRIO)     │
│  └── DNA-CONFIG-TEMPLATE.yaml                  ← DNA-CONFIG.yaml (OBRIG.)  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Estrutura Obrigatória do AGENT.md (Template V3):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  11 PARTES OBRIGATÓRIAS:                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PARTE 0:  ÍNDICE                      (Status de cada parte)               │
│  PARTE 1:  COMPOSIÇÃO ATÔMICA          (Arquitetura do agente)              │
│  PARTE 2:  GRÁFICO DE IDENTIDADE       (Domínios e expertise)               │
│  PARTE 3:  MAPA NEURAL (DNA Destilado) (5 camadas DNA)                      │
│  PARTE 4:  NÚCLEO OPERACIONAL          (Instruções de operação)             │
│  PARTE 5:  SISTEMA DE VOZ              (Como fala, frases, tom)             │
│  PARTE 6:  MOTOR DE DECISÃO            (Regras de decisão)                  │
│  PARTE 7:  INTERFACES DE CONEXÃO       (Interação com outros agentes)       │
│  PARTE 8:  PROTOCOLO DE DEBATE         (Como debate com outros)             │
│  PARTE 9:  MEMÓRIA EXPERIENCIAL        (Casos, aprendizados)                │
│  PARTE 10: EXPANSÕES E REFERÊNCIAS     (Links para arquivos)                │
│                                                                             │
│  ELEMENTOS VISUAIS OBRIGATÓRIOS:                                            │
│  ✓ ASCII Art Header grande com nome do agente                               │
│  ✓ Bordas duplas ╔═══╗ para headers principais                              │
│  ✓ Bordas simples ┌───┐ para subseções                                      │
│  ✓ Barras de progresso para status (████████░░░░)                           │
│  ✓ Citações rastreáveis ^[FONTE:arquivo:linha]                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Gatilhos para Criação de Agentes:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  QUANDO ESTA REGRA SE APLICA:                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✓ Criar novo PERSON agent (pessoa/entidade)                                │
│  ✓ Criar novo CARGO agent (papel/função)                                    │
│  ✓ Criar novo SUB-AGENT (especialista)                                      │
│  ✓ ATUALIZAÇÃO ESTRUTURAL de agente existente                               │
│  ✓ Migração de agente para nova versão de template                          │
│  ✓ Qualquer gatilho automático de criação de agente                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Obrigatório:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ANTES DE CRIAR QUALQUER AGENTE:                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. LER os templates:                                                       │
│     └── TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md                              │
│     └── SOUL-TEMPLATE.md                                                    │
│     └── DNA-CONFIG-TEMPLATE.yaml                                            │
│                                                                             │
│  2. ESTRUTURAR seguindo as 11 partes do Template V3                         │
│                                                                             │
│  3. INCLUIR citações rastreáveis:                                           │
│     └── ^[FONTE:arquivo:linha] para dados de arquivos                       │
│     └── ^[chunk_id] para insights do Pipeline                               │
│     └── ^[insight_id] para insights consolidados                            │
│     └── ^[RAIZ:path/completo] para link direto ao inbox                  │
│                                                                             │
│  4. VALIDAR antes de salvar:                                                │
│     └── Todas as 11 partes presentes?                                       │
│     └── ASCII header correto?                                               │
│     └── Barras de progresso incluídas?                                      │
│     └── Citações rastreáveis?                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Regras Absolutas:

- **NÃO PODE** criar AGENT.md sem seguir as 11 partes do Template V3
- **NÃO PODE** criar SOUL.md sem rastreabilidade 100% (^[FONTE])
- **NÃO PODE** criar DNA-CONFIG.yaml sem paths para inbox
- **NÃO PODE** inventar estrutura própria diferente do template
- **DEVE** declarar versão do template usado no header
- **DEVE** incluir barras de progresso e maturidade
- **DEVE** ter citações rastreáveis para TODA afirmação factual

```
⚠️ AGENTE SEM TEMPLATE = AGENTE INVÁLIDO
⚠️ ESTRUTURA CUSTOMIZADA = VIOLAÇÃO
⚠️ RASTREABILIDADE É OBRIGATÓRIA
⚠️ TEMPLATES SÃO LEI, NÃO SUGESTÃO
```

---

## 🚫 REGRA #25: SOURCE SYNC OBRIGATÓRIO PARA NOVOS CONTEÚDOS

**ANTES DE PROCESSAR NOVOS CONTEÚDOS, EXECUTAR /source-sync.**

### Conceito Fundamental:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLANILHA (Google Sheets)                                                   │
│       │                                                                     │
│       ▼                                                                     │
│  COMPARAR com SNAPSHOT LOCAL (PLANILHA-INDEX.json)                          │
│       │                                                                     │
│       ├── NOVOS? → Gerar TAG na planilha → Baixar com [TAG]                │
│       │                                                                     │
│       └── IGUAIS? → Nada a fazer                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Diferença Crítica vs Fase 2.5:

| Aspecto | Fase 2.5 (Antigo) | Source Sync (Novo) |
|---------|-------------------|---------------------|
| Momento | APÓS download | ANTES do download |
| Local | Arquivo local | Planilha (fonte) |
| Automação | Scripts locais | MCP + Planilha |
| Rastreabilidade | Pós-facto | Nativa |

### Quando Executar:

- Antes de iniciar nova missão
- Quando informado que há novos conteúdos na planilha
- Semanalmente (verificação de rotina)
- Ao iniciar sessão se alerta for exibido

### Arquivos do Sistema:

```
.claude/skills/source-sync/SKILL.md           → Skill completa
.claude/scripts/source-sync.py                → Script de detecção
.claude/hooks/session-source-sync.py          → Hook de sessão
.claude/mission-control/SOURCE-SYNC-STATE.json→ Estado
.claude/mission-control/PLANILHA-INDEX.json   → Snapshot (915+ entries)
```

### Regras Absolutas:

- **NÃO PODE** baixar arquivos manualmente sem usar /source-sync
- **NÃO PODE** ignorar alerta de delta pendente
- **NÃO PODE** processar no Pipeline sem sincronização
- **DEVE** sempre verificar snapshot antes de baixar
- **DEVE** atualizar snapshot após cada sincronização
- **DEVE** taguear NA FONTE (planilha) antes do download

```
⚠️ SYNC ANTES DE DOWNLOAD
⚠️ TAG NA FONTE, NÃO NO LOCAL
⚠️ SNAPSHOT É A VERDADE
⚠️ /source-sync SUBSTITUI Fases 1-3 para novos conteúdos
```

---

## 🛡️ REGRA #26: VALIDAÇÃO DE INTEGRIDADE DO CASCATEAMENTO

**CASCATEAMENTO SÓ ESTÁ COMPLETO SE VALIDAÇÃO PASSAR.**

### O Problema que Esta Regra Resolve:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  BUG DETECTADO (2026-01-13):                                                 │
│                                                                              │
│  • Batches eram marcados como "Cascateamento Executado" após processamento   │
│  • Logs (cascading.jsonl) estavam incompletos ou desatualizados             │
│  • NÃO HAVIA verificação se conteúdo REALMENTE chegou aos destinos          │
│  • Resultado: Batches marcados como completos, mas destinos não atualizados │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Validação Obrigatório:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  APÓS CASCATEAMENTO, ANTES DE MARCAR COMPLETO:                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. EXTRAIR destinos declarados no batch                                    │
│     └── Agentes, Playbooks, DNAs, Dossiers                                  │
│                                                                             │
│  2. VERIFICAR se cada destino:                                              │
│     ├── Arquivo EXISTE no filesystem?                                       │
│     └── Arquivo REFERENCIA o batch ID?                                      │
│                                                                             │
│  3. AVALIAR resultado:                                                      │
│     ├── PASSED: Destinos existem E referenciam batch                        │
│     ├── WARNING: Destinos existem mas sem referência explícita              │
│     └── FAILED: Destinos não existem ou seção cascateamento ausente         │
│                                                                             │
│  4. SÓ MARCAR COMPLETO se status != FAILED                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Scripts de Validação:

```bash
# Validar batch específico
python3 scripts/validate_cascading_integrity.py BATCH-050

# Validar todos os batches
python3 scripts/validate_cascading_integrity.py
```

### Integração com Hook:

O hook `post_batch_cascading.py` (v2.1.0+) executa validação AUTOMATICAMENTE:

```python
# No final de process_batch(), ANTES de marcar completo:
from validate_cascading_integrity import validate_batch_integrity

validation = validate_batch_integrity(batch_id)
if validation['status'] == 'FAILED':
    return {"success": False, "reason": "Validation failed"}

# Só marca como completo SE validação passou
mark_cascading_complete(batch_path, result)
```

### Arquivos do Sistema:

```
scripts/validate_cascading_integrity.py    → Script de validação
logs/cascading-verified.jsonl              → Log de validações
.claude/hooks/post_batch_cascading.py         → Hook integrado (v2.1.0+)
```

### Regras Absolutas:

- **NÃO PODE** marcar batch como completo sem validação
- **NÃO PODE** ignorar status FAILED
- **NÃO PODE** confiar apenas em logs - validar arquivos reais
- **DEVE** verificar existência dos arquivos de destino
- **DEVE** verificar referências ao batch nos destinos
- **DEVE** executar validate_cascading_integrity.py em auditorias

```
⚠️ MARCOU COMPLETO SEM VALIDAR? INVÁLIDO.
⚠️ VALIDAÇÃO FAILED? NÃO PODE AVANÇAR.
⚠️ LOGS INCOMPLETOS? VALIDAÇÃO COMPENSA.
⚠️ DESTINO NÃO EXISTE? CASCATEAMENTO FALHOU.
```

---

## 📋 CHECKLIST RÁPIDO - VALIDATION

```
[ ] Fase 5 completa? Executou validate_phase5.py?
[ ] Script retornou 0 (PASSED)?
[ ] Criando agente? Template V3 sendo seguido?
[ ] Todas as 11 partes presentes no AGENT.md?
[ ] Citações rastreáveis incluídas?
[ ] Novos conteúdos? Executou /source-sync antes?
[ ] Snapshot PLANILHA-INDEX.json atualizado?
[ ] Cascateamento executado? Validação passou?
[ ] Destinos existem no filesystem?
[ ] Destinos referenciam o batch ID?
```

---

**FIM DO RULE-GROUP-5**
