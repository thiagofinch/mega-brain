# ✅ AIOX CONTROL ASSUMPTION CHECKLIST

> **Objetivo:** Garantir que equipe AIOX assume 100% do controle daqui para frente
> **Data:** 2026-03-05
> **Status:** 🔴 PENDENTE — AIOX ASSINAR
> **Proprietário:** ORION (AIOX Validator)

---

## 📋 CHECKLIST: KNOWLEDGE & ACCESS

### ✅ TODOS TÊMACESSO A:

```
[ ] ORION: Leu KNOWLEDGE-DUMP-AIOX-HANDOVER.md completo?
[ ] ORION: Tem acesso a agents/cargo/c-level/cfo/?
[ ] ORION: Tem acesso a agents/cargo/c-level/cmo/?
[ ] ORION: Tem acesso a core/mcp/mercadolivre_mcp.py?
[ ] ORION: Tem acesso a .aiox-core/constitution.md?
[ ] ORION: Tem acesso a docs/MCP-MERCADOLIVRE-INTEGRATION.md?
[ ] Crítico-Metodológico: Tem acesso a CFO MEMORY.md?
[ ] Advogado-do-Diabo: Tem acesso a CMO MEMORY.md?
[ ] Sintetizador: Pode ler arquivos de Hugo Jobs data?
```

### ✅ TODOS ENTENDEM:

```
[ ] CFO agent é 60% completo (Part 10 faltando)
[ ] CMO agent é 60% completo (Part 10 faltando)
[ ] Padrões validados em APENAS 1 caso (Hugo Jobs)
[ ] ROAS >= 3 origem não documentada
[ ] CAC <= 15% não tem justificativa
[ ] Tarifas incompletas (TikTok, Magalu)
[ ] MCP implementado mas OAuth token faltando
[ ] AIOX compliance atual: 65% (full audit needed)
```

---

## 🔧 CHECKLIST: OWNERSHIP TRANSFER

### Phase 1: Immediate (This Week)

**ORION Validator:**
```
TASK 1: Audit CFO Agent Structure
[ ] Leia: agents/cargo/c-level/cfo/AGENT.md
[ ] Checklist:
    [ ] Parte 1 (Composição) — presente e válida?
    [ ] Parte 2 (Identidade) — mapeado corretamente?
    [ ] Parte 3 (DNA Destilado) — referências corretas?
    [ ] Parte 4 (Operacional) — decisões documentadas?
    [ ] Parte 5 (VOZ) — características únicas?
    [ ] Parte 6 (Motor de Decisão) — regras explícitas?
    [ ] Parte 7 (Interfaces) — coordenação com CMO?
    [ ] Parte 8 (Debate) — protocolo definido?
    [ ] Parte 9 (Memória) — 3 padrões documentados?
    [ ] Parte 10 (Referências) — FALTANDO ❌
[ ] Resultado: Sign-off como "AIOX VALIDATOR"

TASK 2: Audit CMO Agent Structure
[ ] Leia: agents/cargo/c-level/cmo/AGENT.md
[ ] Aplicar mesmo checklist da Task 1
[ ] Resultado: Sign-off como "AIOX VALIDATOR"

TASK 3: Create AIOX Stories
[ ] Leia: .aiox-core/constitution.md § 3 (Story-Driven Dev)
[ ] Criar 5 stories para CFO:
    [ ] Story 1: "As CFO, I need Part 10 (Protocolo de Debate)"
    [ ] Story 2: "As CFO, I need ROAS >= 3 origin documented"
    [ ] Story 3: "As CFO, I need TikTok Shop tarifa added"
    [ ] Story 4: "As CFO, I need Magalu tarifa added"
    [ ] Story 5: "As CFO, I need pattern validation on 2+ categories"
[ ] Criar 5 stories para CMO:
    [ ] Adaptado do CFO com foco em policy

TASK 4: OAuth Blocker
[ ] Atribuir: Quem vai completar OAuth flow?
[ ] Deadline: END OF DAY today
[ ] Steps: Follow MCP-MERCADOLIVRE-INTEGRATION.md § 3
[ ] Result: Add MERCADOLIVRE_ACCESS_TOKEN to .env
```

**Crítico-Metodológico:**
```
TASK: Find Tarifas Gaps
[ ] Leia: agents/cargo/c-level/cfo/TARIFAS-MARKETPLACES-2026-03.md
[ ] Identifique: Quais marketplaces faltam campos?
[ ] Lista completa esperada:
    [ ] Mercado Livre — ✅ completo?
    [ ] OLX — ✅ completo?
    [ ] Amazon — ✅ completo?
    [ ] TikTok Shop — ❌ faltando
    [ ] Magalu — ❌ faltando
[ ] Resultado: Create backlog items para cada gap
```

**Advogado-do-Diabo:**
```
TASK: Validate Metric Origins
[ ] ROAS >= 3:
    [ ] Check: CFO MEMORY.md — origin documented?
    [ ] Check: Conclave findings — flagged como undocumented
    [ ] Action: Create task "Trace ROAS >= 3 origin"

[ ] CAC <= 15%:
    [ ] Check: CMO MEMORY.md — origin documented?
    [ ] Check: Conclave findings — flagged como untraced
    [ ] Action: Create task "Justify CAC <= 15% limit"
```

**Sintetizador:**
```
TASK: Pattern Validation Plan
[ ] Leia: CFO + CMO MEMORY.md (3 patterns each)
[ ] Pergunta: Em quais outras categorias testar?
[ ] Sugestão: Além de Hugo Jobs (vestuário):
    [ ] Eletrônicos?
    [ ] Livros?
    [ ] Cosméticos?
[ ] Resultado: Create "Category Testing Roadmap"
```

---

### Phase 2: This Month

**ORION:**
```
TASK: Full AIOX Compliance Audit
[ ] Leia: constitution.md novamente (5 principles)
[ ] Audit CFO/CMO contra cada princípio:
    [ ] § 1 (CLI First) — MCP documented in CLI?
    [ ] § 2 (Agent Authority) — CFO/CMO domains clear?
    [ ] § 3 (Story-Driven) — Stories created (from Phase 1)?
    [ ] § 4 (No Invention) — Patterns traced to data?
    [ ] § 5 (Quality First) — Unit tests for formulas?
[ ] Score: 65% → 95%+ compliance
[ ] Resultado: Full audit report
```

**All AIOX Agents:**
```
TASK: Quality Gate Implementation
[ ] Criar unit tests para:
    [ ] CFO margin formula validation
    [ ] ROAS calculation correctness
    [ ] CAC formula consistency
[ ] Resultado: Automated quality checks passing
```

---

### Phase 3: This Quarter

**ORION + Crítico-Metodológico:**
```
TASK: COO Agent Creation
[ ] Design: Chief Operations Officer role
[ ] Integration: Works with CFO (costs) + CMO (policies)
[ ] Coverage: Logistics, fulfillment, customer support
[ ] Resultado: COO agent deployed and tested
```

**ORION:**
```
TASK: Automate Tariff Syncs
[ ] Current: Manual TARIFAS-MARKETPLACES-2026-03.md
[ ] Target: Real-time MCP calls to Mercado Livre API
[ ] Setup: After OAuth token in .env
[ ] Resultado: CFO gets real-time tariff data
```

---

## 🎯 IMMEDIATE ACTIONS (DO NOW)

### ✅ CRITICAL PATH

```
1. ORION reads KNOWLEDGE-DUMP-AIOX-HANDOVER.md
   └─ Time: 15 min
   └─ Sign-off: "I understand the current state"

2. Assign OAuth completion
   └─ Person: ???
   └─ Deadline: TODAY (EOD)
   └─ Steps: MCP-MERCADOLIVRE-INTEGRATION.md § 3

3. Create backlog of 10 remediation tasks
   └─ Owner: ORION
   └─ Deadline: TOMORROW
   └─ Format: AIOX story cards

4. Start Part 10 (Protocolo de Debate)
   └─ CFO Agent: Who writes?
   └─ CMO Agent: Who writes?
   └─ Deadline: This week

5. Document ROAS >= 3 origin
   └─ Owner: Crítico-Metodológico
   └─ Deadline: This week
   └─ Format: ^[FONTE:arquivo:linha]
```

### ⏳ BLOCK EVERYTHING ELSE

```
Until OAuth token is added:
❌ CFO cannot call real-time MCP endpoints
❌ Tariff updates must be manual (TARIFAS file)
❌ Cannot fully test CFO margin calculations

Priority: Unblock OAuth TODAY
```

---

## 📝 SIGN-OFF SECTION

### ORION Validator

```
[_] I have read KNOWLEDGE-DUMP-AIOX-HANDOVER.md
[_] I understand CFO/CMO current state (60% maturidade)
[_] I understand the 8 gaps from conclave findings
[_] I am ready to assume control and drive remediation
[_] I have identified AIOX Constitution violations

Signature: ________________  Date: _______

"AIOX Control Assumption: AUTHORIZED"
```

### Team Leads

```
CFO Lead: [ ] Assigned to complete Part 10
CMO Lead: [ ] Assigned to complete Part 10
API Lead: [ ] Assigned to complete OAuth flow
DevOps:   [ ] Assigned to automate story tracking

All: [ ] Read KNOWLEDGE-DUMP-AIOX-HANDOVER.md
All: [ ] Ready to start Phase 1 tasks THIS WEEK
```

---

## 🚨 ESCALATION TRIGGERS

**If any of these happen, escalate to CEO:**

```
❌ OAuth token not added by EOD today
   → Block: MCP cannot function
   → Action: Daily standup until resolved

❌ Part 10 (Protocolo de Debate) not started by Friday
   → Block: Agent structure incomplete
   → Action: Reallocate resources

❌ ROAS >= 3 origin cannot be traced
   → Block: Might be arbitrary threshold
   → Action: Decide: Keep/change/justify

❌ Pattern validation fails on 2nd category
   → Block: Patterns might not generalize
   → Action: Redesign patterns or scope to Hugo Jobs only

❌ AIOX compliance still < 90% by month-end
   → Block: Does not meet Constitution standards
   → Action: Extend timeline or add resources
```

---

## 🎓 TRAINING MATERIALS

**All AIOX agents must review:**

```
1. AIOX Constitution (.aiox-core/constitution.md)
2. Knowledge Dump (this directory, KNOWLEDGE-DUMP-AIOX-HANDOVER.md)
3. CFO AGENT.md (Parts 1-9, note Part 10 gap)
4. CMO AGENT.md (Parts 1-9, note Part 10 gap)
5. MCP Integration guide (docs/MCP-MERCADOLIVRE-INTEGRATION.md)
6. Conclave findings (reference in knowledge dump)
```

**Time estimate:** 2 hours per agent

---

## 📊 PROGRESS TRACKING

### Week 1 (This Week)
- [ ] OAuth token added (CRITICAL)
- [ ] 10 remediation tasks in backlog
- [ ] Part 10 started for CFO
- [ ] Part 10 started for CMO
- [ ] ROAS >= 3 origin documented

### Week 2-4 (This Month)
- [ ] Part 10 completed for both agents
- [ ] Pattern validation on 2+ categories
- [ ] AIOX compliance audit completed
- [ ] Unit tests for financial formulas
- [ ] 5 additional AIOX stories in backlog

### Month 2-3 (This Quarter)
- [ ] COO agent deployed
- [ ] Automated tariff syncs live
- [ ] 95%+ AIOX compliance achieved
- [ ] 5+ product categories validated

---

**Last Updated:** 2026-03-05
**Next Review:** 2026-03-12
**Owner:** ORION (AIOX Validator)

**"AIOX assumes control. All systems ready for review."**
