# ÍNDICE DE TEMPLATES

> **Localização:** `/agents/_TEMPLATES/`
> **Propósito:** Referência canônica para todos os templates do sistema

---

## TEMPLATES DISPONÍVEIS

| Template | Arquivo | Uso | Maturidade |
|----------|---------|-----|------------|
| **AGENT-MD-ULTRA-ROBUSTO-V3** | `TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md` | AGENT.md para todos os agentes | CANÔNICO |

---

## ESTRUTURA DO TEMPLATE AGENT-MD-ULTRA-ROBUSTO-V3

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ANATOMIA DO TEMPLATE                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HEADER ASCII ART                                                           │
│  ├── Logo do agente em ASCII                                               │
│  ├── Nome e título                                                         │
│  ├── Metadados (versão, tipo, categoria)                                   │
│  └── Barra de maturidade visual                                            │
│                                                                             │
│  DOSSIÊ EXECUTIVO (com emojis 🛡️🧬🗣️🧠📁📋)                                │
│  ├── 🛡️ QUEM SOU                                                          │
│  ├── 🧬 MINHA FORMAÇÃO                                                     │
│  ├── 🗣️ COMO FALO                                                         │
│  ├── 🧠 O QUE JÁ SEI                                                       │
│  ├── 📁 PROFUNDIDADE DISPONÍVEL                                            │
│  └── 📋 O QUE ESPERAR DE MIM                                               │
│                                                                             │
│  PARTE 0: ÍNDICE                                                            │
│  ├── Box visual com bordas duplas ╔═══╗                                    │
│  ├── Lista de partes com STATUS visual (████░░ 75%)                        │
│  ├── Maturidade geral do agente                                            │
│  └── Arquivos carregados (✅/⏳)                                            │
│                                                                             │
│  PARTE 1: COMPOSIÇÃO ATÔMICA                                                │
│  ├── 1.1 ARQUITETURA DO AGENTE (file paths + status bars ████ 100%)        │
│  ├── 1.2 CAMADAS DE DNA (5 camadas: Filosofias → Metodologias)             │
│  ├── 1.3 PROTOCOLOS VINCULADOS (box visual com tabela)                     │
│  └── 1.4 MATERIAIS FONTE (tabela com PATH_RAIZ + Data)                     │
│                                                                             │
│  PARTE 2: GRÁFICO DE IDENTIDADE                                             │
│  ├── 2.1 MAPA DE DOMÍNIOS (barras ████ % por área expertise)               │
│  ├── 2.2 RADAR DE COMPETÊNCIAS (ASCII radar + barras ●●●●● 10/10)          │
│  └── 2.3 FONTES DE DNA (boxes elaborados: Domínios + Quando usar)          │
│                                                                             │
│  PARTE 3: MAPA NEURAL                                                       │
│  ├── TOP 10 insights destilados                                            │
│  └── Cada insight com CAMADA, FONTE, CONFIANÇA                             │
│                                                                             │
│  PARTE 4: NÚCLEO OPERACIONAL                                                │
│  ├── 4.1 Missão e identidade                                               │
│  ├── 4.2 Posição no organograma (diagrama ASCII)                           │
│  ├── 4.3 Triggers de ativação                                              │
│  ├── 4.4 Processo cognitivo                                                │
│  └── 4.5 Métricas de performance                                           │
│                                                                             │
│  PARTE 5: SISTEMA DE VOZ                                                    │
│  ├── 5.1 Tom geral                                                         │
│  ├── 5.2 Frases que uso / nunca uso                                        │
│  └── 5.3 Exemplos de interação                                             │
│                                                                             │
│  PARTE 6: MOTOR DE DECISÃO                                                  │
│  ├── 6.1 Heurísticas de decisão rápida                                     │
│  ├── 6.2 Regras absolutas                                                  │
│  ├── 6.3 Decision tree (ASCII)                                             │
│  └── 6.4 Quando escalar/delegar                                            │
│                                                                             │
│  PARTE 7: INTERFACES DE CONEXÃO                                             │
│  ├── 7.1 INTEGRAÇÕES COM OUTROS AGENTES                                    │
│  │   ├── RECEBO DE (tabela: Agente, O que recebo, Quando)                  │
│  │   ├── PASSO PARA (tabela: Agente, O que passo, Quando)                  │
│  │   └── CONSULTAS FREQUENTES ESPERADAS (tabela)                           │
│  └── (Seção única, não tem 7.2/7.3 separados)                              │
│                                                                             │
│  PARTE 8: PROTOCOLO DE DEBATE                                               │
│  ├── 8.1 Minha perspectiva em debates                                      │
│  ├── 8.2 Formato de output em debate                                       │
│  └── 8.3 Tensões produtivas com outros agentes                             │
│                                                                             │
│  PARTE 9: MEMÓRIA EXPERIENCIAL                                              │
│  ├── 9.1 Padrões decisórios                                                │
│  ├── 9.2 Calibração Brasil                                                 │
│  └── 9.3 Insights por fonte                                                │
│                                                                             │
│  PARTE 10: EXPANSÕES E REFERÊNCIAS                                          │
│  ├── 10.1 TABELA COMPLETA DE ARQUIVOS (boxes visuais)                      │
│  │   ├── Arquivos do agente (mesma pasta)                                  │
│  │   ├── Knowledge Base (hierarquia de consulta)                           │
│  │   └── Protocolos do sistema (paths completos)                           │
│  ├── 10.2 SISTEMA DE IDs (glossário de citação)                            │
│  ├── 10.3 MODO BATCH PROCESSING (box com regras)                           │
│  └── 10.4 MAPA DE NAVEGAÇÃO GRANULAR ⭐ CRÍTICO                            │
│       ├── Arquivos do Agente (tabela: Path + Quando carregar)              │
│       ├── DNA Cognitivo 5 Camadas (por pessoa, tabela por camada)          │
│       ├── SOURCES Granulares (filtrados por domínio do agente)             │
│       ├── Dossiês Consolidados (PESSOA/TEMA relevantes)                    │
│       └── Referências do Sistema (glossário, protocolos, configs)          │
│                                                                             │
│  VALIDAÇÃO FINAL                                                            │
│  ├── Checklist visual                                                      │
│  ├── Maturidade                                                            │
│  └── Próximos passos                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5 CAMADAS DE DNA (Especificação)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ESTRUTURA COGNITIVA - 5 CAMADAS (Obrigatório em 1.2 e 10.4)              │
│                                                                             │
│   CAMADA 1: FILOSOFIAS (Por quê?)                                          │
│   ───────────────────────────────────────────────────────────────────────   │
│   • Crenças fundamentais sobre o domínio do agente                         │
│   • Path: /knowledge/dna/persons/{PESSOA}/FILOSOFIAS.yaml               │
│   • Exemplo: "Cash flow é sobrevivência" (CFO)                             │
│                                                                             │
│   CAMADA 2: MODELOS MENTAIS (Como penso?)                                  │
│   ───────────────────────────────────────────────────────────────────────   │
│   • Frameworks de raciocínio e analogias                                   │
│   • Path: /knowledge/dna/persons/{PESSOA}/MODELOS-MENTAIS.yaml          │
│   • Exemplo: "Value Equation" (CRO), "Farm System" (BDR)                   │
│                                                                             │
│   CAMADA 3: HEURÍSTICAS (Regras rápidas)                                   │
│   ───────────────────────────────────────────────────────────────────────   │
│   • SE/ENTÃO para decisões recorrentes                                     │
│   • Path: /knowledge/dna/persons/{PESSOA}/HEURISTICAS.yaml              │
│   • Exemplo: "SE LTV/CAC < 3, ENTÃO problema" (CFO)                        │
│                                                                             │
│   CAMADA 4: FRAMEWORKS (Estruturas)                                        │
│   ───────────────────────────────────────────────────────────────────────   │
│   • Metodologias estruturadas, modelos visuais                             │
│   • Path: /knowledge/dna/persons/{PESSOA}/FRAMEWORKS.yaml               │
│   • Exemplo: "5 Armas" (Closer), "Grand Slam Offers" (CRO)                 │
│                                                                             │
│   CAMADA 5: METODOLOGIAS (Processos)                                       │
│   ───────────────────────────────────────────────────────────────────────   │
│   • Processos completos de execução                                        │
│   • Path: /knowledge/dna/persons/{PESSOA}/METODOLOGIAS.yaml             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ELEMENTOS VISUAIS OBRIGATÓRIOS

### Bordas de Boxes

| Tipo | Uso | Caracteres |
|------|-----|------------|
| Dupla | Headers de PARTE, Destaques importantes | `╔═══╗ ║ ╚═══╝` |
| Simples | Conteúdo geral, sub-boxes | `┌───┐ │ └───┘` |
| Divisória | Separação de seções dentro de box | `═══════` ou `─────────` |
| Destaque | Marcar posição atual (VOCÊ ESTÁ AQUI) | `████` preenchimento |

---

## PADRÕES VISUAIS DE REFERÊNCIA (CFO CANÔNICO)

### Padrão 4.2: POSIÇÃO NO ORGANOGRAMA

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ESTRUTURA ORGANIZACIONAL                                                      │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────┐              │
│   │                      [SUITE DO AGENTE]                      │              │
│   ├─────────────┬─────────────┬─────────────┬──────────────────┤              │
│   │   Agente A  │ ████████████│   Agente C  │    Agente D      │              │
│   │  (Subtítulo)│ ██ VOCÊ  ██ │ (Subtítulo) │   (Subtítulo)    │              │
│   │             │ ██  XXX  ██ │             │                  │              │
│   └─────────────┴─────────────┴─────────────┴──────────────────┘              │
│                        │                                                        │
│                        ▼                                                        │
│           ┌────────────────────────┐                                           │
│           │ Áreas de Influência:   │                                           │
│           │ • Área 1               │                                           │
│           │ • Área 2               │                                           │
│           │ • Área 3               │                                           │
│           └────────────────────────┘                                           │
│                                                                                 │
│   O QUE EU NÃO SOU:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  ✗ [Agente X] (não faço Y)                                             │  │
│   │  ✗ [Agente Y] (não faço Z)                                             │  │
│   │  ✗ [Cargo Z] (distinção importante)                                    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 4.3: TRIGGERS DE ATIVAÇÃO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   QUANDO SOU ACIONADO                                                          │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  TRIGGER PRIMÁRIO (Respondo diretamente):                              │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  • "Frase típica que ativa..."                                         │  │
│   │  • "Outra frase..."                                                    │  │
│   │  • Tipo de decisão X                                                   │  │
│   │  • Tipo de decisão Y                                                   │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  TRIGGER SECUNDÁRIO (Participo de debate):                             │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  • Quando [contexto X] afeta meu domínio                               │  │
│   │  • Decisões que impactam [área Y]                                      │  │
│   │  • [Tipo Z] que precisa de minha perspectiva                           │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 4.4: PROCESSO COGNITIVO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   COMO PROCESSO PERGUNTAS                                                       │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  FASE 1: PERCEPÇÃO                                                      │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  → Entender a pergunta no meu domínio                                  │  │
│   │  → Identificar variáveis relevantes                                    │  │
│   │  → Mapear dados disponíveis vs necessários                             │  │
│   │                                                                         │  │
│   │  FASE 2: CONSULTA DNA                                                   │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  → Buscar frameworks aplicáveis (IDs de fonte)                         │  │
│   │  → Verificar benchmarks existentes                                     │  │
│   │  → Identificar tensões entre fontes                                    │  │
│   │                                                                         │  │
│   │  FASE 3: RACIOCÍNIO                                                     │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  → Aplicar framework de análise                                        │  │
│   │  → [Processo específico do domínio]                                    │  │
│   │  → Avaliar riscos e trade-offs                                         │  │
│   │                                                                         │  │
│   │  FASE 4: DECISÃO                                                        │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  → Formular recomendação com confiança                                 │  │
│   │  → Citar fontes (IDs)                                                  │  │
│   │  → Explicitar limitações                                               │  │
│   │  → Definir se precisa escalar                                          │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 4.5: MÉTRICAS DE PERFORMANCE

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   KPIs QUE MONITORO                                                             │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌──────────────────┬──────────────┬─────────────────────────────────────────┐│
│   │ MÉTRICA          │ TARGET       │ COMO MEDIR                              ││
│   ├──────────────────┼──────────────┼─────────────────────────────────────────┤│
│   │ Métrica 1        │ >X%          │ Fórmula/Descrição                       ││
│   ├──────────────────┼──────────────┼─────────────────────────────────────────┤│
│   │ Métrica 2        │ <Y dias      │ Fórmula/Descrição                       ││
│   ├──────────────────┼──────────────┼─────────────────────────────────────────┤│
│   │ Métrica 3        │ >Z:1         │ Fórmula/Descrição                       ││
│   └──────────────────┴──────────────┴─────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 3.1: INSIGHT INDIVIDUAL (TOP 10)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  #N │ TÍTULO DO INSIGHT ^[FONTE.md:linha]                                     │
│  ────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│  "Citação exata do insight com aspas, preservando linguagem original           │
│   da fonte. Pode ter múltiplas linhas se necessário."                          │
│                                                                                 │
│  INTERNO: ^[SOUL.md:XX] | ORIGINAL: [ID-FONTE] Pessoa                         │
│  CAMADA: [FILOSOFIA | MODELO MENTAL | HEURÍSTICA | FRAMEWORK | METODOLOGIA]   │
│  APLICAÇÃO: Quando usar este insight                                           │
│  CONFIANÇA: XX%                                                                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 4.1: MISSÃO E IDENTIDADE

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   QUEM EU SOU ^[SOUL.md:XX-YY]                                                 │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ╔═══════════════════════════════════════════════════════════════════════════╗│
│   ║                                                                           ║│
│   ║   Sou o [CARGO] desta operação high-ticket B2B.                          ║│
│   ║                                                                           ║│
│   ║   [Descrição do papel em 2-3 linhas usando citações de SOUL.md]          ║│
│   ║   ^[SOUL.md:XX-YY]                                                       ║│
│   ║                                                                           ║│
│   ╚═══════════════════════════════════════════════════════════════════════════╝│
│                                                                                 │
│   EXPERTISE: ^[SOUL.md:XX-YY]                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  • Expertise 1                                                         │  │
│   │  • Expertise 2                                                         │  │
│   │  • Expertise 3                                                         │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   FRASE QUE ME DEFINE: ^[SOUL.md:XX]                                           │
│   "[Citação marcante que define a essência do agente]"                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 5.1: SISTEMA DE VOZ - TOM GERAL

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   COMO EU FALO ^[SOUL.md:XX]                                                   │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ╔═══════════════════════════════════════════════════════════════════════════╗│
│   ║                                                                           ║│
│   ║   [Descrição do tom predominante em 2-3 linhas]                          ║│
│   ║                                                                           ║│
│   ╚═══════════════════════════════════════════════════════════════════════════╝│
│                                                                                 │
│   CARACTERÍSTICAS DA MINHA VOZ:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ✓ CARACTERÍSTICA 1  → [descrição]                                     │  │
│   │  ✓ CARACTERÍSTICA 2  → [descrição]                                     │  │
│   │  ✓ CARACTERÍSTICA 3  → [descrição]                                     │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   MODULAÇÃO POR CONTEXTO:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  CONTEXTO A    → TOM X      "[frase exemplo]"                          │  │
│   │  CONTEXTO B    → TOM Y      "[frase exemplo]"                          │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 5.3/5.4: FRASES QUE USO / NUNCA USO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   FRASES CARACTERÍSTICAS                                                        │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  [CATEGORIA]                                                            │  │
│   │  ────────────────────────────────────────────────────────────────────  │  │
│   │  "Frase 1"                                   ^[FONTE.md:XX]            │  │
│   │  "Frase 2"                                   ^[FONTE.md:YY]            │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   FRASES PROIBIDAS                                                              │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ✗ "[Frase proibida 1]"                                                │  │
│   │     → [Razão pela qual é proibida]                                     │  │
│   │                                                                         │  │
│   │  ✗ "[Frase proibida 2]"                                                │  │
│   │     → [Razão pela qual é proibida]                                     │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 6.1: HEURÍSTICAS DE DECISÃO RÁPIDA (Categorias)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   SE... ENTÃO... (Regras rápidas de decisão)                                   │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ┌────────────────────────────────────────────────────────────────────┐│  │
│   │  │ [CATEGORIA 1]                                                      ││  │
│   │  ├────────────────────────────────────────────────────────────────────┤│  │
│   │  │ SE [condição]            → ENTÃO [ação] ^[FONTE]                  ││  │
│   │  │ SE [condição]            → ENTÃO [ação] ^[FONTE]                  ││  │
│   │  └────────────────────────────────────────────────────────────────────┘│  │
│   │                                                                         │  │
│   │  ┌────────────────────────────────────────────────────────────────────┐│  │
│   │  │ [CATEGORIA 2]                                                      ││  │
│   │  ├────────────────────────────────────────────────────────────────────┤│  │
│   │  │ SE [condição]            → ENTÃO [ação] ^[FONTE]                  ││  │
│   │  └────────────────────────────────────────────────────────────────────┘│  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 6.2: REGRAS ABSOLUTAS (SEMPRE/NUNCA)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   REGRAS INVIOLÁVEIS                                                            │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ████ SEMPRE ████                                                      │  │
│   │  ────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  ✓ [Regra 1]                                                          │  │
│   │    → [Explicação/Fonte]                                                │  │
│   │                                                                         │  │
│   │  ✓ [Regra 2]                                                          │  │
│   │    → [Explicação/Fonte]                                                │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ░░░░ NUNCA ░░░░                                                       │  │
│   │  ────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  ✗ [Regra 1]                                                          │  │
│   │    → [Explicação/Fonte]                                                │  │
│   │                                                                         │  │
│   │  ✗ [Regra 2]                                                          │  │
│   │    → [Explicação/Fonte]                                                │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 6.3: DECISION TREE (em Box)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ÁRVORE DE DECISÃO: [TÍTULO]                                                  │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│                           [PONTO INICIAL]                                       │
│                                 │                                               │
│                                 ▼                                               │
│                    ┌────────────────────────┐                                  │
│                    │   [Pergunta]           │                                  │
│                    └────────────────────────┘                                  │
│                                 │                                               │
│                    ┌────────────┴────────────┐                                 │
│                    ▼                         ▼                                  │
│          ┌─────────────────┐       ┌─────────────────┐                         │
│          │   [Opção A]     │       │   [Opção B]     │                         │
│          ├─────────────────┤       ├─────────────────┤                         │
│          │ [Descrição]     │       │ [Descrição]     │                         │
│          └────────┬────────┘       └────────┬────────┘                         │
│                   │                         │                                   │
│                   ▼                         ▼                                   │
│          ┌─────────────────┐       ┌─────────────────┐                         │
│          │   [Ação A]      │       │   [Ação B]      │                         │
│          └─────────────────┘       └─────────────────┘                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 6.5: MATRIZ DE ESCALAÇÃO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   MATRIZ DE ESCALAÇÃO                                                           │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌──────────────────────────┬──────────────┬───────────────────────────────┐  │
│   │ SITUAÇÃO                 │ DECISÃO      │ ESCALAR PARA                  │  │
│   ├──────────────────────────┼──────────────┼───────────────────────────────┤  │
│   │ [Situação 1]             │ EU DECIDO    │ —                             │  │
│   ├──────────────────────────┼──────────────┼───────────────────────────────┤  │
│   │ [Situação 2]             │ ESCALO       │ @[AGENTE]                     │  │
│   └──────────────────────────┴──────────────┴───────────────────────────────┘  │
│                                                                                 │
│   REGRA: [Princípio orientador para decisão de escalar]                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 7.1: INTERFACES COM OUTROS AGENTES

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   COMO ME CONECTO COM OUTROS AGENTES                                           │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  RECEBO DE                                                              │  │
│   │  ═══════════════════════════════════════════════════════════════════    │  │
│   │                                                                         │  │
│   │  ┌──────────────────┬──────────────────────────────┬────────────────┐  │  │
│   │  │ AGENTE           │ O QUE RECEBO                 │ QUANDO         │  │  │
│   │  ├──────────────────┼──────────────────────────────┼────────────────┤  │  │
│   │  │ @[AGENTE]        │ [Descrição]                  │ [Frequência]   │  │  │
│   │  └──────────────────┴──────────────────────────────┴────────────────┘  │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  PASSO PARA                                                             │  │
│   │  ═══════════════════════════════════════════════════════════════════    │  │
│   │                                                                         │  │
│   │  ┌──────────────────┬──────────────────────────────┬────────────────┐  │  │
│   │  │ AGENTE           │ O QUE PASSO                  │ QUANDO         │  │  │
│   │  ├──────────────────┼──────────────────────────────┼────────────────┤  │  │
│   │  │ @[AGENTE]        │ [Descrição]                  │ [Frequência]   │  │  │
│   │  └──────────────────┴──────────────────────────────┴────────────────┘  │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  CONSULTAS FREQUENTES ESPERADAS                                         │  │
│   │  ═══════════════════════════════════════════════════════════════════    │  │
│   │                                                                         │  │
│   │  ┌────────────┬─────────────────────────┬───────────┬───────────────┐  │  │
│   │  │ AGENTE     │ ASSUNTO TÍPICO          │ FREQUÊNCIA│ RESPOSTA      │  │  │
│   │  ├────────────┼─────────────────────────┼───────────┼───────────────┤  │  │
│   │  │ @[AGENTE]  │ [Assunto]               │ [Freq]    │ [Padrão]      │  │  │
│   │  └────────────┴─────────────────────────┴───────────┴───────────────┘  │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 8.1: PERSPECTIVA EM DEBATES

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   PERSPECTIVA DO [AGENTE] EM DEBATES MULTI-AGENTE                              │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ╔═══════════════════════════════════════════════════════════════════════════╗│
│   ║                                                                           ║│
│   ║   Trago a perspectiva do [DOMÍNIO].                                      ║│
│   ║                                                                           ║│
│   ║   [Descrição do filtro principal para debates]                           ║│
│   ║                                                                           ║│
│   ╚═══════════════════════════════════════════════════════════════════════════╝│
│                                                                                 │
│   MEUS FOCOS EM DEBATES:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ✓ [Foco 1]                                                            │  │
│   │    → [Explicação]                                                       │  │
│   │                                                                         │  │
│   │  ✓ [Foco 2]                                                            │  │
│   │    → [Explicação]                                                       │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   QUANDO DISCORDO:                                                              │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  → [Como lido com discordância 1]                                      │  │
│   │  → [Como lido com discordância 2]                                      │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 8.2: FORMATO DE OUTPUT EM DEBATE

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   FORMATO PADRÃO DE RESPOSTA EM DEBATE                                          │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ████ FATOS ████                                                       │  │
│   │  ────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  - [FONTE:arquivo:linha] > "citação exata"                             │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ░░░░ RECOMENDAÇÃO ░░░░                                                │  │
│   │  ────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  POSIÇÃO: [recomendação clara]                                         │  │
│   │  JUSTIFICATIVA: [baseado em dados]                                     │  │
│   │  CONFIANÇA: [ALTA/MÉDIA/BAIXA] - [justificativa]                       │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  ▓▓▓▓ LIMITAÇÕES ▓▓▓▓                                                  │  │
│   │  ────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  - [o que não sei / área de incerteza]                                 │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Padrão 8.3: TENSÕES PRODUTIVAS

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   TENSÕES INTERNAS DO AGENTE                                                   │
│   ═══════════════════════════════════════════════════════════════════════════   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                         │  │
│   │  TENSÃO #N │ [TÍTULO DA TENSÃO] ^[CONF-XXX]                            │  │
│   │  ────────────────────────────────────────────────────────────────────  │  │
│   │                                                                         │  │
│   │  [FONTE A]:                                                            │  │
│   │  "[Citação que representa a posição A]"                                │  │
│   │  ^[insight_id:XXX]                                                     │  │
│   │                                                                         │  │
│   │  [FONTE B]:                                                            │  │
│   │  "[Citação que representa a posição B]"                                │  │
│   │  ^[insight_id:YYY]                                                     │  │
│   │                                                                         │  │
│   │  MINHA SÍNTESE:                                                        │  │
│   │  ╔═══════════════════════════════════════════════════════════════════╗│  │
│   │  ║ "[Síntese emergente que reconcilia as duas posições]"             ║│  │
│   │  ╚═══════════════════════════════════════════════════════════════════╝│  │
│   │                                                                         │  │
│   │  STATUS: [Estado da síntese]                                           │  │
│   │  ^[SOUL.md:XX-YY, DNA-CONFIG.yaml:XX-YY]                              │  │
│   │                                                                         │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Barras de Progresso

```
████████████████████████████████████████░░░░░░░░░░░░░░░░ 75%
█████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 50%
████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 30%
```

### Status Indicators

| Indicador | Significado |
|-----------|-------------|
| ✅ | Completo |
| ⏳ | Parcial/Em construção |
| ❌ | Vazio/Pendente |
| ⚠️ | Atenção necessária |

---

## REGRAS DE APLICAÇÃO

1. **NUNCA simplificar** - Usar estrutura visual completa
2. **COPIAR boxes** - Não recriar, copiar do template
3. **MANTER proporções** - Largura de 80 caracteres
4. **ATUALIZAR percentuais** - Baseado em conteúdo real
5. **SEGUIR ordem** - Partes na sequência exata

---

## COMO USAR

```
1. Abrir TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md
2. Copiar estrutura completa
3. Substituir placeholders com dados do agente
4. Ajustar percentuais de maturidade
5. Validar com checklist final
```

---

*INDEX.md - Criado: 2025-12-26 - Atualizado: 2025-12-26 (PADRÃO CFO CANÔNICO COMPLETO: Parts 0-8)*
