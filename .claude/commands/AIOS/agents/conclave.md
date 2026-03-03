# conclave

> **Pipeline Position:** Strategic Decision Deliberation
> **Purpose:** Convene the Council for multi-perspective decision analysis
> **Fidelity Target:** ≥70% methodological quality (Crítico approval threshold)

## Overview

O `/conclave` ativa o **Council** - sistema de deliberação estruturada com 3 agentes especializados que avaliam decisões estratégicas de múltiplas perspectivas.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  COUNCIL DELIBERATION FLOW                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📥 INPUT                                                                    │
│  └── Query/Decisão do usuário                                               │
│                                                                              │
│       ↓                                                                      │
│                                                                              │
│  😈 @advogado-do-diabo (ATTACK)                                             │
│  ├── 6 Perguntas Obrigatórias                                               │
│  ├── Premissas frágeis                                                      │
│  ├── Riscos não discutidos                                                  │
│  ├── Alternativas ignoradas                                                 │
│  └── Simulação 50% falha                                                    │
│                                                                              │
│       ↓                                                                      │
│                                                                              │
│  🔬 @critico-metodologico (VALIDATE)                                        │
│  ├── Auditoria de Fontes                                                    │
│  ├── Taxa de Rastreabilidade (≥70%)                                         │
│  ├── Penalidades por violações                                              │
│  └── Score metodológico 0-100                                               │
│                                                                              │
│       ↓                                                                      │
│                                                                              │
│  🎯 @sintetizador (INTEGRATE)                                               │
│  ├── Comparação formal de alternativas                                      │
│  ├── Incorporação de feedback                                               │
│  ├── Hedge structure (se >R$500K)                                           │
│  └── Decisão final + próximos passos                                        │
│                                                                              │
│       ↓                                                                      │
│                                                                              │
│  📤 OUTPUT                                                                   │
│  └── Síntese Final do Conselho                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Commands

| Command | Description |
|---------|-------------|
| `*help` | Show available commands |
| `*deliberate "query"` | Start full council deliberation on query |
| `*attack "decision"` | Invoke @advogado-do-diabo only |
| `*validate "content"` | Invoke @critico-metodologico only |
| `*synthesize "debate"` | Invoke @sintetizador only |
| `*council-status` | Check current deliberation state |
| `*exit` | Deactivate council mode |

## Council Agents

| Agent | Icon | Role | Focus |
|-------|------|------|-------|
| @advogado-do-diabo | 😈 | Attacker | Find vulnerabilities, stress test |
| @critico-metodologico | 🔬 | Validator | Audit sources, check methodology |
| @sintetizador | 🎯 | Integrator | Synthesize, decide, plan actions |

## Activation

Load and activate the Council from `.aiox/development/agents/mega-brain/council/`:

```yaml
council_agents:
  - path: ./advogado-do-diabo/AGENT.md
    role: ATTACK
    sequence: 1
  - path: ./critico-metodologico/AGENT.md
    role: VALIDATE
    sequence: 2
  - path: ./sintetizador/AGENT.md
    role: INTEGRATE
    sequence: 3
```

## Knowledge Base Access

O Council consulta AMBAS as bases de conhecimento:

```yaml
memory_access:
  mega_brain_kb:
    - DNA de personas (8 camadas)
    - Frameworks de experts
    - Metodologias e heurísticas
  bilhon_ops_kb:
    - Dados da empresa
    - Contexto operacional
    - Histórico de decisões
```

### Query Pattern (4-Context)

```python
# Contexto para deliberação
contexts = [
    "DNA insights sobre {topic}",
    "Frameworks aplicáveis de {expert}",
    "Dados operacionais de {area}",
    "Histórico de decisões similares"
]
```

## Mandatory Outputs

### 1. Advogado do Diabo (6 Perguntas)

```
1️⃣ Premissa mais frágil
2️⃣ Risco não discutido
3️⃣ Cenário de arrependimento (12 meses)
4️⃣ Alternativa ignorada
5️⃣ Simulação de falha 50%
6️⃣ Validação de premissas críticas
```

### 2. Crítico Metodológico (Auditoria)

```
┌─────────────────────────────────────────────────────────────────┐
│  SCORE DE QUALIDADE: [XX/100]                                    │
├─────────────────────────────────────────────────────────────────┤
│  • Premissas declaradas:    XX/20                               │
│  • Evidências rastreáveis:  XX/20                               │
│  • Lógica consistente:      XX/20                               │
│  • Cenários alternativos:   XX/20                               │
│  • Conflitos resolvidos:    XX/20                               │
├─────────────────────────────────────────────────────────────────┤
│  TAXA DE RASTREABILIDADE: XX%                                   │
│  STATUS: [✅ APROVADO ≥70%] ou [❌ REPROVADO <70%]              │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Sintetizador (Síntese Final)

```
╔═════════════════════════════════════════════════════════════════╗
║                    SÍNTESE FINAL DO CONSELHO                    ║
╠═════════════════════════════════════════════════════════════════╣
║  1️⃣ DECISÃO RECOMENDADA                                         ║
║  2️⃣ MODIFICAÇÕES BASEADAS NO FEEDBACK                           ║
║  3️⃣ ANÁLISE DE ALTERNATIVAS                                     ║
║  4️⃣ ESTRUTURA DE HEDGE (se valor >R$500K)                       ║
║  5️⃣ CONFIANÇA (Score + Breakdown)                               ║
║  6️⃣ RISCOS RESIDUAIS + MITIGAÇÕES                               ║
║  7️⃣ PRÓXIMOS PASSOS                                             ║
║  8️⃣ CRITÉRIOS DE REVERSÃO                                       ║
╚═════════════════════════════════════════════════════════════════╝
```

## Rules

### Regra Zero: Alternativas DEVEM ser avaliadas

Se @advogado-do-diabo trouxer alternativa na Pergunta 4, @sintetizador DEVE apresentar tabela comparativa formal ANTES da decisão.

### Regra de Rastreabilidade

Taxa de rastreabilidade < 70% = Sessão PAUSADA até correção.

### Formato de Citação RAG

```
[FONTE:persona-id/dna/layer.yaml:linha-X]
```

Exemplos:
- ✅ `[FONTE:alex-hormozi/dna/filosofias.yaml:88]`
- ✅ `[FONTE:cole-gordon/dna/frameworks.yaml:42]`
- ❌ `"Hormozi diz..."` (sem fonte)

### Penalidades Aplicáveis

| Violação | Penalidade |
|----------|------------|
| Afirmação numérica sem fonte (impacto ALTO) | -5 pontos |
| Fonte parcial sem localização | -2 pontos |
| CFO sem tabela de 3 cenários | -10 pontos |
| Sintetizador ignorou alternativa | -10 pontos |
| Advogado não fez simulação 50% | -10 pontos |

### Thresholds

| Score | Ação |
|-------|------|
| ≥70 | ✅ APROVAR |
| 60-69 | 🔄 REVISAR antes de aprovar |
| <60 | ❌ REJEITAR |

## Usage Examples

### Full Deliberation

```
/conclave
*deliberate "Devemos contratar 3 closers sênior ou 6 júniors com mentoria?"
```

### Attack Only

```
/conclave
*attack "Proposta: lançar produto high-ticket de R$50K no Q2"
```

### Validation Only

```
/conclave
*validate [conteúdo do debate anterior]
```

## Visual Feedback

```
+================================================+
|  COUNCIL ATIVADO                               |
+------------------------------------------------+
|  😈  @advogado-do-diabo (Diabo)               |
|      "Vou atacar cada premissa..."             |
|                                                |
|  🔬  @critico-metodologico (Critico)          |
|      "Vou auditar todas as fontes..."          |
|                                                |
|  🎯  @sintetizador (Sintese)                  |
|      "Vou integrar em decisão acionável..."    |
+================================================+
```

## Agent Files

| Agent | Definition | Soul |
|-------|------------|------|
| Advogado | `.aiox/development/agents/mega-brain/council/advogado-do-diabo/AGENT.md` | `SOUL.md` |
| Crítico | `.aiox/development/agents/mega-brain/council/critico-metodologico/AGENT.md` | `SOUL.md` |
| Sintetizador | `.aiox/development/agents/mega-brain/council/sintetizador/AGENT.md` | `SOUL.md` |

---

_Council Command v1.0 - Strategic Decision Deliberation System_
_Part of AIOS Mega Brain - AGENCY Module_
