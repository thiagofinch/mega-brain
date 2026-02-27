# AGENT-INTEGRITY-PROTOCOL
# Protocolo de Integridade e Fidelidade de Agentes

> **Versao:** 1.2.1
> **Status:** REGRA INQUEBRAVEL
> **Data:** 2025-12-25
> **Prioridade:** MAXIMA - Sobrepoe todos os outros protocolos
> **Ultima Atualizacao:** Templates oficiais para SOUL/MEMORY/DNA-CONFIG com rastreabilidade 100%

---

## PRINCIPIO FUNDAMENTAL

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   TODO CONTEUDO EM AGENTES DEVE SER 100% RASTREAVEL A FONTES ORIGINAIS      ║
║                                                                              ║
║   NENHUMA PALAVRA, NUMERO OU AFIRMACAO PODE SER INVENTADA                   ║
║                                                                              ║
║   O AGENTE REFLETE A ESSENCIA DAS FONTES, NAO INTERPRETACOES DO SISTEMA     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## DISTINCAO CRITICA: FORTIFICAR vs INVENTAR

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   FORTIFICAR ≠ INVENTAR                                                      ║
║                                                                              ║
║   FORTIFICAR = Expandir a essência DENTRO dos limites do DNA                 ║
║   INVENTAR   = Criar conteúdo que NÃO EXISTE nas fontes (PROIBIDO)          ║
║                                                                              ║
║   "Fortificar" significa abrir a mente do especialista no seu limite        ║
║   máximo, SEM ultrapassar os limites definidos pelo DNA.                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Quando o Usuário Pede para "Fortificar":

| Ação | Permitido? | Exemplo |
|------|------------|---------|
| Expandir conceito existente | ✅ | "Cash is king" → explicar em detalhe o que isso significa |
| Conectar conceitos da mesma fonte | ✅ | Ligar insight de SOUL.md com insight de MEMORY.md |
| Usar vocabulário do próprio mentor | ✅ | Se Hormozi usa "unit economics", usar esse termo |
| Elaborar implicações lógicas | ✅ | "Se LTV/CAC < 3, então..." (consequência lógica) |
| Inventar nova filosofia | ❌ | Criar crença que não existe em SOUL.md |
| Adicionar metáfora externa | ❌ | Usar analogia que o mentor nunca usou |
| Criar frase "inspiracional" | ❌ | Escrever quote que soa bonito mas não existe |

### Mecanismo de Fortificação Permitido:

```
FONTE: "Cash is king, everything else is noise" ^[SOUL.md:70]

FORTIFICACAO PERMITIDA:
"Cash is king, everything else is noise. Isso significa que posso ter
R$1M em vendas e estar quebrado se tudo está em recebíveis. O que
importa é o que está na conta." ^[SOUL.md:70-72]

RAZAO: Expandi usando texto que EXISTE nas linhas seguintes da mesma fonte.
```

### Teste de Validação para Fortificação:

```
PERGUNTA: O texto expandido pode ser rastreado a linhas específicas das fontes?

SE SIM → Fortificação válida (adicionar ^[FONTE])
SE NAO → Invenção proibida (REMOVER ou REESCREVER)
```

---

## PRINCIPIO DO TEMPLATE FLEXIVEL

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   O TEMPLATE É FLEXÍVEL - AS INFORMAÇÕES SÃO O LIMITE                       ║
║                                                                              ║
║   Template = Estrutura que pode crescer, expandir, melhorar                  ║
║   Limite   = Informações disponíveis do agente (SOUL/MEMORY/dna/SOURCES)    ║
║                                                                              ║
║   USE E ABUSE do template. Deixe-o mais visual, mais rico, mais completo.   ║
║   MAS respeite o limite do que EXISTE nas fontes do agente.                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### O Que Pode Fazer com o Template:

| Ação | Permitido? | Condição |
|------|------------|----------|
| Expandir seções | ✅ | Se houver mais informação nas fontes |
| Adicionar diagramas visuais | ✅ | Se representarem dados das fontes |
| Criar novas seções | ✅ | Se as fontes tiverem conteúdo para popular |
| Melhorar formatação | ✅ | Sempre permitido |
| Adicionar tabelas | ✅ | Se os dados existirem nas fontes |
| Omitir seções vazias | ✅ | Melhor omitir que inventar |
| Inventar conteúdo | ❌ | NUNCA |
| Criar seção sem fonte | ❌ | NUNCA |

### Regra de Proporcionalidade:

```
TAMANHO DO AGENTE = PROPORCIONAL ÀS INFORMAÇÕES DISPONÍVEIS

Agente com MUITAS fontes processadas:
    → AGENT.md pode ter 10 PARTES completas
    → TOP 10 INSIGHTS pode virar TOP 20
    → RADAR pode ter mais dimensões
    → MAPA DE NAVEGAÇÃO pode listar 50+ arquivos

Agente com POUCAS fontes processadas:
    → AGENT.md pode ter apenas 5 PARTES
    → TOP 5 INSIGHTS (não inventar os outros 5)
    → RADAR com menos dimensões
    → MAPA DE NAVEGAÇÃO lista apenas o que existe

NUNCA:
    → Esticar conteúdo para preencher template
    → Inventar para "completar" seções
    → Duplicar informação para parecer maior
```

### Teste de Validação do Template:

```
PARA CADA SEÇÃO DO TEMPLATE:

1. Esta seção tem fonte correspondente no agente?
   SE NÃO → OMITIR a seção (não inventar)

2. As informações existem em SOUL/MEMORY/dna/SOURCES?
   SE NÃO → OMITIR o conteúdo

3. O diagrama/visual representa dados reais?
   SE NÃO → REMOVER ou SIMPLIFICAR

RESULTADO: Template cresce APENAS com as informações do agente
```

---

## REGRAS INQUEBRAVEIS

### REGRA 1: ZERO INVENCAO

```
PROIBIDO:
- Escrever texto "floreado" sem fonte
- Inventar frases que o agente "diria"
- Criar numeros sem calculo real
- Elaborar descricoes baseadas em "interpretacao"

OBRIGATORIO:
- Todo texto extraido literalmente de SOUL.md, MEMORY.md, DNA/*.yaml
- Toda frase citada deve existir em arquivo fonte
- Todo numero derivado de contagem real em arquivos
```

**Exemplo ERRADO:**
```markdown
Minha memoria contem **26+ insights** extraidos de 7 fontes.
```

**Exemplo CORRETO:**
```markdown
Minha memoria contem **26 insights** ^[MEMORY.md:linhas46-98]
extraidos de **7 fontes** ^[DNA-CONFIG.yaml:dna_sources].
```

---

### REGRA 2: CITACAO OBRIGATORIA

Toda afirmacao em AGENT.md DEVE ter referencia no formato:

```
^[ARQUIVO:localizacao]

Onde:
- ARQUIVO = nome do arquivo fonte (SOUL.md, MEMORY.md, etc.)
- localizacao = linha, secao, ou chunk_id
```

**Aplicacao por secao:**

| Secao do AGENT.md | Fonte Obrigatoria | Formato |
|-------------------|-------------------|---------|
| QUEM SOU | SOUL.md secao "QUEM SOU EU" | ^[SOUL.md:44-62] |
| MINHA FORMACAO | DNA-CONFIG.yaml | ^[DNA-CONFIG.yaml:dna_sources] |
| COMO FALO | SOUL.md secao "SISTEMA DE VOZ" | ^[SOUL.md:XX-YY] |
| O QUE JA SEI | MEMORY.md secao "APRENDIZADOS" | ^[MEMORY.md:42-98] |
| DECISOES PADRAO | MEMORY.md secao "PADROES DECISORIOS" | ^[MEMORY.md:30-39] |

---

### REGRA 3: NUMEROS DERIVADOS, NAO ESCRITOS

```
PROIBIDO:
- Escrever "26+ insights" manualmente
- Chutar "7 fontes processadas"
- Inventar "15 arquivos de DNA"

OBRIGATORIO:
- Contar linhas reais em MEMORY.md
- Contar entradas em DNA-CONFIG.yaml
- Listar arquivos existentes em /knowledge/dna/
```

**Mecanismo de Derivacao:**

| Metrica | Como Calcular | Onde Armazenar |
|---------|---------------|----------------|
| Total de insights | Contar tabelas em MEMORY.md secao APRENDIZADOS | AGENT.md + atualizar quando MEMORY muda |
| Total de fontes | Contar entradas em DNA-CONFIG.yaml | AGENT.md + atualizar quando DNA-CONFIG muda |
| Arquivos DNA | Listar arquivos em /knowledge/dna/persons/{fontes}/ | AGENT.md secao MAPA DE NAVEGACAO |
| Decisoes padrao | Contar linhas em MEMORY.md secao PADROES DECISORIOS | AGENT.md + atualizar quando MEMORY muda |

---

### REGRA 4: TEXTO DO AGENTE = TEXTO DA FONTE

O texto em AGENT.md/DOSSIE EXECUTIVO deve ser:

1. **CITACAO DIRETA** - Copiar literalmente do SOUL.md
2. **SINTESE REFERENCIADA** - Resumir com ^[FONTE]
3. **DERIVACAO EXPLICITA** - Calcular de dados reais

**NUNCA:**
- Parafrasear sem referencia
- "Melhorar" o texto original
- Adicionar interpretacoes proprias

**Exemplo de CITACAO DIRETA:**

```markdown
## QUEM SOU

> ^[SOUL.md:46-51]
> "Eu sou o guardiao da saude financeira. O freio quando precisa frear,
> o acelerador quando os numeros permitem acelerar.
> Sam Oven me ensinou que sistemas financeiros robustos sao fundacao.
> Sem visibilidade de numeros, decisoes sao chutes. Com dados claros,
> decisoes sao estrategia."
```

---

### REGRA 5: ATUALIZACAO AUTOMATICA

Quando um arquivo fonte muda, TODOS os arquivos dependentes DEVEM ser atualizados:

```
MEMORY.md atualizado
    ↓
VERIFICAR e ATUALIZAR:
    ├── AGENT.md secao "O QUE JA SEI"
    ├── AGENT.md contagens de insights
    └── AGENT.md decisoes padrao

SOUL.md atualizado
    ↓
VERIFICAR e ATUALIZAR:
    ├── AGENT.md secao "QUEM SOU"
    ├── AGENT.md secao "COMO FALO"
    └── AGENT.md secao "O QUE ESPERAR"

DNA-CONFIG.yaml atualizado
    ↓
VERIFICAR e ATUALIZAR:
    ├── AGENT.md secao "MINHA FORMACAO"
    ├── AGENT.md contagem de fontes
    └── AGENT.md MAPA DE NAVEGACAO GRANULAR
```

---

### REGRA 6: VALIDACAO ANTES DE FINALIZAR

Antes de considerar um AGENT.md "completo", executar checklist:

```
□ Toda afirmacao tem ^[FONTE]?
□ Todos os numeros foram derivados (nao escritos)?
□ O texto do DOSSIE EXECUTIVO e citacao direta ou sintese referenciada?
□ As frases "que digo" existem literalmente em SOUL.md?
□ As decisoes padrao existem literalmente em MEMORY.md?
□ O MAPA DE NAVEGACAO GRANULAR lista arquivos que EXISTEM?
□ O indice reflete as partes que EXISTEM no documento?
```

Se QUALQUER item falhar = AGENT.md NAO ESTA COMPLETO.

---

## PRINCIPIO DE INTERCONEXAO TOTAL

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NENHUM ARQUIVO É ILHA - TODOS ESTÃO CONECTADOS                            ║
║                                                                              ║
║   Qualquer arquivo que alimenta um agente PODE modificar outros arquivos.   ║
║   Não há como incrementar informações importantes sem otimizar os demais.   ║
║   Por isso TODOS os campos devem estar bem mapeados.                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Rede de Interdependências

```
                    ┌──────────────────────────────────────────────┐
                    │           FONTES PRIMÁRIAS                   │
                    │  (inbox → processing → knowledge)   │
                    └──────────────────────┬───────────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
              ▼                            ▼                            ▼
   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
   │      DOSSIERS       │◄──►│       THEMES        │◄──►│       SOURCES       │
   │   (por pessoa)      │    │    (por tema)       │    │   (pessoa×tema)     │
   └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
              │                          │                          │
              └────────────┬─────────────┼─────────────┬────────────┘
                           │             │             │
                           ▼             ▼             ▼
              ┌─────────────────────────────────────────────────────┐
              │              DNA COGNITIVO (5 Camadas)              │
              │  FILOSOFIAS ← MODELOS ← HEURÍSTICAS ← FRAMEWORKS    │
              └──────────────────────────┬──────────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│    SOUL.md      │◄──────────►│   MEMORY.md     │◄──────────►│ DNA-CONFIG.yaml │
│  (identidade)   │            │  (experiência)  │            │    (fontes)     │
└────────┬────────┘            └────────┬────────┘            └────────┬────────┘
         │                              │                              │
         └──────────────────────────────┼──────────────────────────────┘
                                        │
                                        ▼
         ┌─────────────────────────────────────────────────────────────┐
         │                      AGENT.md                               │
         │  ┌────────────────────────────────────────────────────────┐ │
         │  │              DOSSIÊ EXECUTIVO                          │ │
         │  ├────────────────────────────────────────────────────────┤ │
         │  │ 🛡️ QUEM SOU        ← SOUL.md:44-62                    │ │
         │  │ 🧬 MINHA FORMAÇÃO  ← DNA-CONFIG.yaml + SOUL.md:20-25  │ │
         │  │ 🗣️ COMO FALO       ← SOUL.md:66-87 + 129-154         │ │
         │  │ 🧠 O QUE JÁ SEI    ← MEMORY.md:46-104                 │ │
         │  │ 📁 PROFUNDIDADE    ← DNA/* + SOURCES/* + DOSSIERS/*   │ │
         │  │ 🎯 O QUE ESPERAR   ← SOUL.md + MEMORY.md              │ │
         │  └────────────────────────────────────────────────────────┘ │
         └─────────────────────────────────────────────────────────────┘
```

### Matriz de Propagação (O Que Muda O Quê)

| Quando ESTE Arquivo Muda | ESTES Arquivos DEVEM Ser Verificados |
|--------------------------|--------------------------------------|
| **DOSSIER-{PESSOA}.md** | SOUL.md, MEMORY.md (do agente relacionado) |
| **DOSSIER-{TEMA}.md** | SOURCES/{PESSOA}/{TEMA}.md, MEMORY.md (de agentes do tema) |
| **SOURCES/{PESSOA}/{TEMA}.md** | DOSSIERS, MEMORY.md do agente, DNA se nova filosofia |
| **DNA/{PESSOA}/FILOSOFIAS.yaml** | SOUL.md, AGENT.md seção "O QUE ACREDITO" |
| **DNA/{PESSOA}/HEURISTICAS.yaml** | MEMORY.md, AGENT.md seção "REGRAS DE DECISÃO" |
| **SOUL.md** | AGENT.md (QUEM SOU, COMO FALO, O QUE ESPERAR) |
| **MEMORY.md** | AGENT.md (O QUE JÁ SEI, contagens, decisões padrão) |
| **DNA-CONFIG.yaml** | AGENT.md (MINHA FORMAÇÃO, PROFUNDIDADE) |

### Regra de Propagação Obrigatória

```
QUANDO: Novo material processado via Pipeline Jarvis
    │
    ├── SE gera novo INSIGHT em INSIGHTS-STATE.json
    │       │
    │       └── VERIFICAR: Qual agente se beneficia?
    │               │
    │               ├── ATUALIZAR: MEMORY.md do agente
    │               │       │
    │               │       └── PROPAGAR: AGENT.md seção "O QUE JÁ SEI"
    │               │
    │               └── SE nova FILOSOFIA detectada
    │                       │
    │                       ├── ATUALIZAR: SOUL.md seção "O QUE ACREDITO"
    │                       │
    │                       └── PROPAGAR: AGENT.md seção "QUEM SOU"
    │
    └── SE gera novo DOSSIER ou atualiza existente
            │
            └── VERIFICAR: Quais agentes usam este DOSSIER?
                    │
                    └── PROPAGAR: Referências em MAPA DE NAVEGAÇÃO

RESULTADO: Nenhum arquivo fica "órfão" de atualizações.
```

---

## MAPA DE DEPENDENCIAS DETALHADO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   FONTES PRIMARIAS              AGENT.md                                    │
│   ═══════════════               ═════════                                   │
│                                                                             │
│   SOUL.md ────────────────────→ DOSSIE EXECUTIVO                           │
│   │                             ├── QUEM SOU                               │
│   │                             ├── COMO FALO                              │
│   │                             └── O QUE ESPERAR                          │
│   │                                                                         │
│   MEMORY.md ──────────────────→ DOSSIE EXECUTIVO                           │
│   │                             ├── O QUE JA SEI                           │
│   │                             └── DECISOES PADRAO                        │
│   │                                                                         │
│   DNA-CONFIG.yaml ────────────→ DOSSIE EXECUTIVO                           │
│   │                             ├── MINHA FORMACAO                         │
│   │                             └── PROFUNDIDADE DISPONIVEL                │
│   │                                                                         │
│   /knowledge/dna/* ────────→ MAPA DE NAVEGACAO GRANULAR                 │
│   │                             └── DNA Cognitivo por Pessoa               │
│   │                                                                         │
│   /knowledge/SOURCES/* ────→ MAPA DE NAVEGACAO GRANULAR                 │
│   │                             └── SOURCES Granulares                     │
│   │                                                                         │
│   /knowledge/dossiers/* ───→ MAPA DE NAVEGACAO GRANULAR                 │
│                                 └── Dossiês Consolidados                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FORMATO DE REFERENCIA PADRAO

### Em Texto Corrido

```markdown
Cash flow e rei, margem e rainha ^[SOUL.md:70-72]. Esta filosofia guia
todas as minhas decisoes financeiras.
```

### Em Tabelas

```markdown
| Insight | Fonte |
|---------|-------|
| LTV/CAC minimo 3x | ^[MEMORY.md:103] |
| CCR < 10% ticket | ^[MEMORY.md:86] |
```

### Em Listas

```markdown
**Frases que digo:** ^[SOUL.md:secao-sistema-de-voz]
- "Qual e o unit economics disso?"
- "Mostra a margem."
- "Cash is king."
```

### Para Numeros Derivados

```markdown
Minha memoria contem **26 insights** ^[derivado:MEMORY.md:linhas46-98:count=26]
```

---

## PROCESSO DE CRIACAO/ATUALIZACAO DE AGENTE

### Passo 1: Ler Fontes

```
ANTES de escrever qualquer coisa em AGENT.md:

1. Ler SOUL.md completo
2. Ler MEMORY.md completo
3. Ler DNA-CONFIG.yaml completo
4. Listar arquivos em /knowledge/dna/persons/{fontes}/
5. Listar arquivos em /knowledge/SOURCES/ relevantes
```

### Passo 2: Extrair (Nao Inventar)

```
Para cada secao do AGENT.md:

1. Identificar secao correspondente na fonte
2. COPIAR texto relevante (nao parafrasear)
3. Adicionar ^[FONTE] a cada citacao
4. CONTAR numeros (nao estimar)
```

### Passo 3: Validar

```
Para cada afirmacao:

1. Verificar se existe em arquivo fonte
2. Verificar se ^[FONTE] esta correto
3. Verificar se numeros batem com contagem real
```

### Passo 4: Documentar Derivacoes

```
No final do AGENT.md, adicionar secao:

## METADADOS DE DERIVACAO

| Metrica | Valor | Fonte | Data Verificacao |
|---------|-------|-------|------------------|
| Insights | 26 | MEMORY.md:46-98 | 2025-12-25 |
| Fontes | 7 | DNA-CONFIG.yaml | 2025-12-25 |
| ... | ... | ... | ... |
```

---

## CONSEQUENCIAS DE VIOLACAO

```
SE encontrar texto sem ^[FONTE]:
    → PARAR
    → Identificar fonte ou REMOVER texto

SE encontrar numero nao derivado:
    → PARAR
    → Calcular numero real ou REMOVER

SE encontrar interpretacao/floreio:
    → PARAR
    → Substituir por citacao direta ou REMOVER

SE arquivo fonte mudar e AGENT.md nao atualizar:
    → AGENT.md considerado DESATUALIZADO
    → Flag de integridade = FALHA
```

---

## INTEGRACAO COM OUTROS PROTOCOLOS

| Protocolo | Integracao |
|-----------|------------|
| CORTEX-PROTOCOL | Adicionar AGENT.md como dependente de SOUL/MEMORY/DNA-CONFIG |
| EPISTEMIC-PROTOCOL | Aplicar mesma logica de ^[FONTE] e confidence levels |
| PIPELINE-JARVIS | Fase final deve verificar integridade de agentes afetados |
| **AGENT-COGNITION-PROTOCOL** | FASE 1.5 (Depth-Seeking) permite navegação até RAIZ quando contexto insuficiente |

### Integração com FASE 1.5 (Depth-Seeking) - v1.2.0

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  AGENT-INTEGRITY-PROTOCOL + AGENT-COGNITION-PROTOCOL FASE 1.5              │
│                                                                             │
│  Este protocolo define O QUE deve ser rastreável (todas as afirmações).    │
│  A FASE 1.5 define COMO navegar até a fonte ANTES de entregar resposta.    │
│                                                                             │
│  ⚠️ REGRA INQUEBRÁVEL (v1.2.0):                                            │
│  NAVEGAÇÃO PRÉVIA OBRIGATÓRIA - 5 ELEMENTOS SEMPRE PRONTOS                 │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ QUEM:    Nome da pessoa que disse (speaker)                        │    │
│  │ QUANDO:  Data/contexto temporal                                    │    │
│  │ ONDE:    Material exato (título, tipo, canal)                      │    │
│  │ TEXTO:   Citação bruta original (não parafraseada)                 │    │
│  │ PATH:    Caminho até o arquivo inbox                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  FLUXO INTEGRADO:                                                          │
│                                                                             │
│  1. ANTES de responder: Navegar até RAIZ                                   │
│  2. Ter 5 elementos prontos para "de onde vem essa informação?"           │
│  3. Se não conseguir = não pode afirmar como fato                          │
│                                                                             │
│  NAVEGAÇÃO COMPLETA:                                                       │
│  AGENT.md → SOUL.md → MEMORY.md → DNA → INSIGHTS → CHUNKS → RAIZ          │
│                                                                             │
│  Ver: AGENT-COGNITION-PROTOCOL.md seções 1.5.0 a 1.5.6                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CHECKLIST DE INTEGRIDADE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VALIDACAO DE INTEGRIDADE                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  □ 1. Toda afirmacao tem ^[FONTE:arquivo:localizacao]                       ║
║                                                                              ║
║  □ 2. Todos os numeros sao derivados com formula explicita                  ║
║                                                                              ║
║  □ 3. Texto do DOSSIE e citacao direta ou sintese referenciada              ║
║                                                                              ║
║  □ 4. Frases "que digo" existem LITERALMENTE em SOUL.md                     ║
║                                                                              ║
║  □ 5. Decisoes padrao existem LITERALMENTE em MEMORY.md                     ║
║                                                                              ║
║  □ 6. Arquivos listados em MAPA DE NAVEGACAO existem no filesystem          ║
║                                                                              ║
║  □ 7. Indice reflete estrutura real do documento                            ║
║                                                                              ║
║  □ 8. Secao METADADOS DE DERIVACAO esta presente e atualizada               ║
║                                                                              ║
║  □ 9. Data de ultima verificacao esta documentada                           ║
║                                                                              ║
║  □ 10. Nenhum texto foi "floreado" ou "melhorado"                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

RESULTADO: ___/10 itens OK

SE < 10/10 = AGENTE NAO ESTA EM CONFORMIDADE
```

---

## TEMPLATES OFICIAIS PARA CRIAÇÃO DE AGENTES

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   TEMPLATES GOVERNAM A ESTRUTURA E RASTREABILIDADE DOS AGENTES              ║
║                                                                              ║
║   Qualquer novo agente DEVE seguir os templates oficiais.                   ║
║   Templates garantem consistência e rastreabilidade 100%.                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Localização dos Templates

| Template | Localização | Versão | Propósito |
|----------|-------------|--------|-----------|
| **SOUL-TEMPLATE.md** | `core/templates/agents/soul-template.md` | v2.0 | Identidade viva do agente |
| **MEMORY-PROTOCOL.md** | `core/templates/agents/memory-template.md` | v2.0.0 | Experiência acumulada |
| **DNA-CONFIG-TEMPLATE.yaml** | `core/templates/agents/dna-config-template.yaml` | v2.0.0 | Configuração de fontes |

### Requisitos de Rastreabilidade por Template

| Template | Formato ^[FONTE] | Elementos Obrigatórios |
|----------|------------------|------------------------|
| **SOUL.md** | `^[chunk_id]`, `^[insight_id]`, `^[RAIZ:path:linha]` | Toda afirmação factual |
| **MEMORY.md** | Tabelas com colunas `chunk_id`, `PATH_RAIZ` | Todo insight/padrão |
| **DNA-CONFIG.yaml** | Campos `insight_ids`, `chunk_ids`, `raiz` | Toda fonte primária |

### Exemplo de Aplicação: CFO (Template V2)

```
CFO SOUL.md v2.0
├── ^[insight_id:OB002, chunk_199] em Unit Economics
├── ^[insight_id:CM001, CM002] em Compensação
├── ^[RAIZ:/inbox/ALEX HORMOZI/.../HOW I SCALED MY SALES TEAM.txt]
└── Sínteses marcadas como "opinião emergente do HÍBRIDO"

CFO MEMORY.md v2.0.0
├── Tabelas com colunas chunk_id e PATH_RAIZ
├── Fontes pendentes marcadas como *aguardando Pipeline Jarvis*
└── Seção de VALIDAÇÃO DE RASTREABILIDADE

CFO DNA-CONFIG.yaml
├── raiz: path para inbox por pessoa
├── insight_ids: lista de insights relevantes
└── materiais_fonte: lista de arquivos originais
```

---

*Este protocolo e INQUEBRAVEL. Nenhuma excecao e permitida.*
*A integridade do sistema multi-agente depende da fidelidade as fontes.*
*AGENT-INTEGRITY-PROTOCOL v1.2.1 - Atualizado com templates oficiais (2025-12-25)*

*Versao: 1.2.0 | Data: 2025-12-25 | Navegação prévia obrigatória: 5 elementos (QUEM, QUANDO, ONDE, TEXTO, PATH)*
