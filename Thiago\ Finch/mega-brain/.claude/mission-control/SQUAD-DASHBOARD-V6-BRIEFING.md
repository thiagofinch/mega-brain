╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                  🚀 SQUAD DASHBOARD v6.0 - BRIEFING                          ║
║                                                                              ║
║           Integração de API do MercadoLivre + Redesign da Interface         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

---

## 📋 MISSÃO DO SQUAD

**Objetivo:** Criar Dashboard v6.0 com tarifas e métricas real-time do MercadoLivre

**Duração:** Sprint de 2 semanas (v1.0 MVP)

**Escopo:**
- Integrar API do MercadoLivre (comissões, frete, políticas)
- Redesenhar interface (UX + Dark mode)
- Implementar pipeline de sync automático
- Deploy em staging + monitoramento

---

## 👥 COMPOSIÇÃO DO SQUAD (4 agentes)

### 1️⃣ **PRODUCT OWNER** (Coordenador)
**Responsabilidade:** Visão, priorização, stakeholder management

**Tarefas Iniciais:**
- [ ] Definir escopo MVP vs nice-to-have
- [ ] Identificar 3 KPIs críticas para v6.0
- [ ] Mapear dependências técnicas
- [ ] Schedule daily standups

**Pergunta para começar:**
```
@po: Qual é o escopo MVP de Dashboard v6.0?
- Mostrar tarifas atualizadas do ML?
- Comparar com concorrentes (TikTok Shop, Shopee)?
- Alertas de mudanças de comissão?
- Projeção de margem por categoria?
```

---

### 2️⃣ **UX-DESIGN-EXPERT** (Design)
**Responsabilidade:** Interface, experiência, wireframes

**Tarefas Iniciais:**
- [ ] Criar wireframes do novo dashboard
- [ ] Definir componentes de tarifas (tabelas, gráficos)
- [ ] Dark mode palette
- [ ] Fluxo de atualização de dados (real-time vs manual)

**Pergunta para começar:**
```
@ux-design-expert: Redesenhe Dashboard v6.0
- Dark mode + Light mode support?
- Mostrar tarifas por categoria em tabela ou cards?
- Comparativa de marketplaces em dashboard principal?
- Alertas visuais para mudanças de comissão?
```

---

### 3️⃣ **SOFTWARE-DEVELOPER** (Backend/Frontend)
**Responsabilidade:** Implementação, integração de APIs

**Tarefas Iniciais:**
- [ ] Consumir MCP do MercadoLivre
- [ ] Criar endpoints para dashboard
- [ ] Sincronizar dados em banco de dados
- [ ] Implementar UI conforme wireframes

**Pergunta para começar:**
```
@dev: Implemente integração de Dashboard v6.0
- Stack: qual framework (React/Vue/Next)?
- DB: usar PostgreSQL/MongoDB?
- Frequência de sync: 1h, 6h, 24h?
- Cache de tarifas: Redis ou memória?
```

---

### 4️⃣ **QA-ENGINEER** (Qualidade)
**Responsabilidade:** Testes, validação, release

**Tarefas Iniciais:**
- [ ] Criar test cases para sincronização de dados
- [ ] Validar precisão de tarifas vs API
- [ ] Testes de performance (load testing)
- [ ] Release checklist

**Pergunta para começar:**
```
@qa: Estruture testes para Dashboard v6.0
- Dados sincronizados corretamente?
- UI responde em < 2s?
- Dark mode não tem bugs de contraste?
- Offline mode funciona?
```

---

## 🔌 RECURSOS DISPONÍVEIS

### ✅ API do MercadoLivre
```
- Token: VÁLIDO (auto-refresh ativado)
- Endpoints: Categorias, Comissões, Frete, Políticas
- MCP: core/mcp/mercadolivre_mcp.py (v2.0.0)
- Status: 🟢 OPERACIONAL
```

### ✅ Agentes de Suporte
```
- ARCHITECT: Design da infraestrutura
- DATA-ENGINEER: Pipeline de dados
- DEVOPS: Deploy e monitoramento
- SM: Remove bloqueios
- AIOX-MASTER: Orquestra o squad
```

### ✅ Documentação
```
- CFO MEMORY: Estrutura de tarifas
- CMO MEMORY: Políticas de anúncios
- TARIFAS-MARKETPLACES-2026-03.md: Manual de taxas
```

---

## 📊 TIMELINE (2 semanas)

```
┌─────────────────────────────────────────────────────────────────────┐
│ SEMANA 1: PLANEJAMENTO + DESIGN + ARQUITETURA                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Seg: PO define escopo, UX faz wireframes                           │
│ Ter: ARCHITECT desenha pipeline, DEV setup inicial                 │
│ Qua: Revisão + feedback, testes planejados                         │
│ Qui: Prototipagem de componentes críticos                          │
│ Sex: Sprint review, ajustes                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────┐
│ SEMANA 2: IMPLEMENTAÇÃO + TESTES + DEPLOY                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Seg: DEV implementa MVP, QA testa iterações                        │
│ Ter: Sync de tarifas automatizado, dark mode                       │
│ Qua: Testes de performance, load testing                           │
│ Qui: Staging deployment, smoke tests                               │
│ Sex: Fix final bugs, produção ou beta                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 KPIs DE SUCESSO

```
[ ] Dashboard carrega em < 2 segundos
[ ] Tarifas sincronizadas a cada 1 hora
[ ] 0 bugs críticos em QA
[ ] Dark mode 100% funcional
[ ] API availability > 99.5%
[ ] Usuário consegue ver margem por categoria
[ ] Comparativo de 5 marketplaces visível
```

---

## 🔄 ORQUESTRAÇÃO

```
SQUAD FORMADO
    ↓
PO: Define escopo (2h)
    ↓
UX: Wireframes (4h)
    ↓
ARCHITECT: Design técnico (6h)
    ↓
DEV: Implementação (40h)
    ↓
DATA-ENGINEER: Pipeline (12h)
    ↓
QA: Testes (20h)
    ↓
DEVOPS: Deploy (4h)
    ↓
STADIUM RELEASE ✅
```

---

## 📞 COMO COMEÇAR AGORA

```bash
# Opção 1: Pedir para @squad-creator montar o squad
@squad-creator: Monte squad de Dashboard v6.0 (PO, UX-EXPERT, DEV, QA)

# Opção 2: Chamar direto cada agente
@po: Qual é o escopo MVP de Dashboard v6.0?
@ux-design-expert: Redesenhe a interface do dashboard
@dev: Implemente integração com API do MercadoLivre
@qa: Estruture testes para o dashboard

# Opção 3: Orquestração automática
@aiox-master: Orquestra o squad de Dashboard v6.0 (começa PO)
```

---

## 📋 PRÓXIMAS AÇÕES (EM ORDEM)

1. ✅ Ativar MCP do MercadoLivre
2. ✅ Montar squad (ESTE BRIEFING)
3. ⏳ PO define escopo (aguarda)
4. ⏳ UX faz wireframes (aguarda)
5. ⏳ ARCHITECT desenha sistema (aguarda)
6. ⏳ DEV implementa (aguarda)

---

**Status:** 🟢 PRONTO PARA COMEÇAR

**Próximo comando:**
```
@squad-creator: Monte squad para Dashboard v6.0 (PO, UX, DEV, QA)
```

---

*Criado por: JARVIS*
*Data: 2026-03-06*
*Briefing v1.0.0*
