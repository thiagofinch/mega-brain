# PROTOCOLO DE ALIMENTAÇÃO: Como o Conhecimento Flui para o Organograma Vivo

> **Versão:** 7.0.0 | **Criado:** 2025-12-20 | **Atualizado:** 2025-12-29
> **Ecossistema:** [SUA EMPRESA] (100% Sincronizado com AGENTS/SALES e AGENTS/C-LEVEL)
> **Protocolo:** ORG-LIVE-DOCUMENT-PROTOCOL v1.0

---

## CABEÇALHO VISUAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                PROTOCOLO DE ALIMENTAÇÃO - MODELO HÍBRIDO v7.0               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Define COMO conhecimento flui do Pipeline Jarvis → Agentes IA → Cargos.    │
│  Garante rastreabilidade total: toda informação tem origem documentada.      │
│  NOVA ESTRUTURA: MODEL/ + OPERATIONS/ + YOUR-ORG/ + TRIGGERS/ + LOGS/       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**O que isso significa na prática:**
Este documento explica por que você vê citações como `[VIA: AGENT-CLOSER → Cole Gordon CG003]` nos arquivos de cargo. Não é burocracia - é garantia de que nenhuma informação crítica (como "desconto máximo de 10%") apareceu do nada. Tudo tem origem rastreável.

---

## FILOSOFIA

> **[FONTE: Richard Linder - RL001]**
> "Companies move at the speed of the founder."

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRINCÍPIO FUNDAMENTAL                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NENHUMA informação em documentos ORG-LIVE sem origem rastreável.           │
│                                                                             │
│  Formato obrigatório:                                                       │
│  • [VIA: AGENT-X → Fonte CÓDIGO] - Conhecimento via agente IA               │
│  • [FONTE: Nome - CÓDIGO] - Citação direta de fonte externa                 │
│  • [DECISÃO [SUA EMPRESA]] - Decisão interna da empresa                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**O que isso significa na prática:**
Quando você lê "Desconto máximo de 10% [DECISÃO [SUA EMPRESA]]", você sabe que foi VOCÊ quem decidiu, não Cole Gordon nem Alex Hormozi. Quando lê "[VIA: AGENT-CLOSER → CG003]", você sabe que veio de conhecimento processado do Cole Gordon. Isso evita confundir best practice geral com política específica da sua empresa.

---

## ARQUITETURA DE SINCRONIZAÇÃO (3 NÍVEIS)

> **REGRA FUNDAMENTAL:** As MEMORYs de cargos devem ler de TRÊS fontes, não apenas dos agentes IA.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA DE SINCRONIZAÇÃO v2.0                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   NÍVEL 1: AGENTES IA (conhecimento processado)                            │
│   ├── /agents/SALES/AGENT-*-MEMORY.md                                   │
│   └── /agents/C-LEVEL/AGENT-*-MEMORY.md                                 │
│   → Conhecimento JÁ PROCESSADO pelo Pipeline Jarvis                        │
│   → Fonte rápida de consulta para decisões do dia a dia                    │
│                                                                             │
│   NÍVEL 2: PIPELINE JARVIS (fontes brutas - MAIS RICAS)                    │
│   ├── /knowledge/dossiers/persons/  → 1 pessoa, TODOS os temas          │
│   ├── /knowledge/dossiers/THEMES/   → 1 tema, MÚLTIPLAS pessoas         │
│   └── /knowledge/SOURCES/           → 1 pessoa × 1 tema                 │
│   → Fonte COMPLETA para consultas aprofundadas                              │
│   → Quando Nível 1 não tem resposta, consultar Nível 2                     │
│                                                                             │
│   NÍVEL 3: CARGOS RELACIONADOS (dependências organizacionais)              │
│   └── /agents/ORG-LIVE/MEMORY/                                           │
│       ├── MEMORY-SDR.md        ←→ MEMORY-CLOSER.md                         │
│       ├── MEMORY-CLOSER.md     ←→ MEMORY-CLOSER-CHEFE.md                   │
│       └── MEMORY-SALES-MANAGER.md ←→ MEMORY-CMO.md                         │
│   → Dependências entre cargos (quem envia, quem recebe, quem supervisiona) │
│                                                                             │
│   NÍVEL 4: MODELO ORGANIZACIONAL (estrutura de referência)                 │
│   └── /agents/ORG-LIVE/MODEL/                                            │
│       ├── ORG-CHART-MODEL.md     → 25 funções + 5 fases de scaling         │
│       ├── FUNCTION-MAP.md        → Mapa detalhado de cada função           │
│       ├── CORRELATION-MATRIX.md  → Dependências entre funções              │
│       └── SCALING-PATH.md        → Ordem de contratação por fase           │
│   → Referência para decisões de estrutura e crescimento                    │
│                                                                             │
│   NÍVEL 5: DOCUMENTOS OPERACIONAIS                                         │
│   └── /agents/ORG-LIVE/OPERATIONS/                                       │
│       ├── RITUALS/               → Reuniões e cadências (diárias, 1:1s)    │
│       ├── TOOLS/                 → Stack tecnológico por cargo             │
│       └── COMMUNICATION/         → Protocolos de comunicação               │
│   → Define COMO cada cargo opera no dia a dia                              │
│                                                                             │
│   NÍVEL 6: TRIGGERS E REGRAS                                               │
│   └── /agents/ORG-LIVE/TRIGGERS/                                         │
│       ├── SCALING-TRIGGERS.md    → Gatilhos para contratar                 │
│       └── HYBRID-RULES.md        → Quando separar papéis híbridos          │
│   → Decisões de quando escalar e especializar                              │
│                                                                             │
│   NÍVEL 7: INSTÂNCIA DA EMPRESA                                            │
│   └── /agents/ORG-LIVE/YOUR-ORG/                                         │
│       ├── YOUR-ORG-CHART.md      → Seu organograma atual                   │
│       ├── YOUR-TEAM.md           → Fichas individuais do time              │
│       └── YOUR-METRICS.md        → Dashboard de métricas                   │
│   → Templates para você preencher com dados da SUA empresa                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**O que isso significa na prática:**

Os arquivos MEMORY-*.md em ORG-LIVE não são ilhas isoladas. Cada MEMORY tem:
1. **Links para Agentes IA** - Conhecimento já digerido, pronto para usar
2. **Links para DOSSIERs** - Quando precisa de mais detalhes ou contexto
3. **Links para outros cargos** - Para entender quem depende de quem

Exemplo: Quando o CLOSER recebe um lead ruim, ele pode consultar:
- MEMORY-SDR.md para entender o processo de qualificação
- AGENT-SDS-MEMORY.md para ver frameworks de qualificação
- DOSSIER-FUNIL-APLICACAO.md para ver o que as fontes dizem sobre qualificação

---

### Mapeamento Completo de Sincronização

| Cargo | Agentes IA Fonte | DOSSIERs Principais | Cargos Relacionados |
|-------|------------------|---------------------|---------------------|
| SDR | SDS, LNS, BDR | FUNIL-APLICACAO, METRICAS, ESTRUTURA-TIME | CLOSER, CLOSER-CHEFE |
| CLOSER | CLOSER | PROCESSO-VENDAS, PRICING, COMISSIONAMENTO | SDR, CLOSER-CHEFE |
| CLOSER-CHEFE | CLOSER, SALES-MANAGER | GESTAO, PROCESSO-VENDAS, ESTRUTURA-TIME | CLOSER, SDR, SM |
| SALES-MANAGER | SALES-MANAGER | GESTAO, METRICAS, CONTRATACAO | CLOSER, SDR |
| CMO | CMO | FUNIL-APLICACAO, METRICAS, PRICING | SDR (via leads) |

---

## MODELO HÍBRIDO DE ALIMENTAÇÃO

### Evolução v1.0 → v2.0 → v3.0 → v4.0

| Versão | Modelo | Problema |
|--------|--------|----------|
| v1.0 | Pipeline Jarvis → Cargos direto | Sem processamento intermediário |
| v2.0 | Pipeline → Agentes IA → Cargos | Falta padronização de citação |
| v3.0 | Pipeline → Agentes → Cargos (com protocolo) | Termos técnicos em inglês |
| v4.0 | Pipeline → Agentes → Cargos (protocolo + português) | **ATUAL** |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE CONHECIMENTO v4.0                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ANTES (v1.0 - ISOLADO):                                                   │
│   Pipeline Jarvis ──────────────────────────────► Cargos                    │
│   ⛔ Problema: Conhecimento não processado, sem contexto                    │
│                                                                             │
│   AGORA (v4.0 - HÍBRIDO COM PROTOCOLO + CLAREZA):                          │
│   Pipeline Jarvis ──► Agentes IA ──► Cargos                                │
│                       (SALES)        (Humanos)                              │
│                       (C-LEVEL)      + CITAÇÃO OBRIGATÓRIA                  │
│                                      + TRADUÇÃO PARA PORTUGUÊS              │
│                                      + SEÇÕES "NA PRÁTICA"                  │
│                                                                             │
│   ✅ Benefício: Cargos herdam conhecimento JÁ PROCESSADO + RASTREÁVEL      │
│                 + COMPREENSÍVEL para quem não domina jargão técnico         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**O que isso significa na prática:**
Quando você processa um vídeo do Cole Gordon, ele não vai direto para o arquivo ROLE-CLOSER.md. Primeiro passa pelo Pipeline Jarvis (quebra semântica, extração de insights), depois alimenta o AGENT-CLOSER (que contextualiza o conhecimento), e SÓ ENTÃO chega ao ROLE-CLOSER.md com a tag `[VIA: AGENT-CLOSER → CG003]`. Isso garante que o conhecimento foi "digerido" e não é só um copy-paste bruto.

---

## FLUXO COMPLETO DE ALIMENTAÇÃO

```
inbox (Material Bruto)
     │
     ▼
processing (Pipeline Jarvis Fases 1-6)
     │
     ├──────────────────────────────────────────────────────────────┐
     ▼                                                              │
knowledge                                                        │
(Dossiês PESSOAS + TEMAS)                                           │
     │                                                              │
     ▼                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASE 7: ENRIQUECIMENTO DE AGENTES                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  agents/SALES/              agents/C-LEVEL/                           │
│  ├── AGENT-CLOSER              ├── AGENT-CRO                                │
│  │   Conhecimento: 7 Beliefs,  │   Conhecimento: Receita,                   │
│  │   6-Phase Flow, Objeções    │   Ofertas, Pricing                         │
│  │                             │                                            │
│  ├── AGENT-SALES-MANAGER       ├── AGENT-CMO                                │
│  │   Conhecimento: QC,         │   Conhecimento: Purple Ocean,              │
│  │   Projeções, Coaching       │   ICP, CAC/LTV                             │
│  │                             │                                            │
│  ├── AGENT-BDR                 ├── AGENT-CFO                                │
│  │   Conhecimento: Prospecção  │   Conhecimento: Unit Economics             │
│  │                             │                                            │
│  ├── AGENT-SDS                 └── AGENT-COO                                │
│  │   Conhecimento: Discovery       Conhecimento: Operações                  │
│  │                                                                          │
│  ├── AGENT-LNS                                                              │
│  │   Conhecimento: Show Rate                                                │
│  │                                                                          │
│  └── AGENT-CUSTOMER-SUCCESS                                                 │
│      Conhecimento: NPS, LTV                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FASE 8.2: ENRIQUECIMENTO DE CARGOS (ORG-LIVE)           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  agents/ORG-LIVE/SOW/                (Statement of Work por área)        │
│  ├── LEADERSHIP/                                                            │
│  │   └── SOW-FOUNDER.md         ◄── AGENT-CRO + AGENT-CFO                  │
│  │                                                                          │
│  ├── SALES/                                                                 │
│  │   ├── SOW-CLOSER-CHEFE.md    ◄── AGENT-CLOSER + AGENT-SALES-MANAGER     │
│  │   │   Citação: [VIA: AGENT-CLOSER → Cole Gordon CG003]                   │
│  │   │                                                                      │
│  │   ├── SOW-CLOSER.md          ◄── AGENT-CLOSER                           │
│  │   │   Citação: [VIA: AGENT-CLOSER → Cole Gordon DOSSIÊ]                 │
│  │   │                                                                      │
│  │   ├── SOW-SALES-MANAGER.md   ◄── AGENT-SALES-MANAGER                    │
│  │   │   Citação: [VIA: AGENT-SALES-MANAGER → Cole Gordon CG003]            │
│  │   │                                                                      │
│  │   └── SOW-SDR.md             ◄── AGENT-BDR + AGENT-SDS + AGENT-LNS      │
│  │       Citação: [VIA: AGENT-LNS → Cole Gordon DOSSIÊ]                    │
│  │                                                                          │
│  ├── MARKETING/                                                             │
│  │   └── SOW-CMO.md             ◄── AGENT-CMO                              │
│  │       Citação: [VIA: AGENT-CMO → Sam Ovens SU006-12]                     │
│  │                                                                          │
│  └── OPERATIONS/                                                            │
│      └── SOW-COO.md             ◄── AGENT-COO                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
ORGANOGRAMA.md (Visualização Final)
```

**O que isso significa na prática:**
Este fluxo tem 3 "estações de processamento": (1) Pipeline Jarvis quebra vídeos em pedaços semânticos, (2) Agentes IA contextualizam o conhecimento para funções específicas, (3) Cargos humanos recebem conhecimento aplicável com citação rastreável. Se você pular alguma estação, perde rastreabilidade ou contexto.

---

## MAPEAMENTO AGENTE → CARGO

### Tabela Completa

| Cargo [SUA EMPRESA] | Agente(s) Fonte | Tipo de Conhecimento | Localização SOW |
|-------------|----------------|----------------------|-----------------|
| SOW-FOUNDER | AGENT-CRO, AGENT-CFO | Estratégia + Finanças | `/agents/ORG-LIVE/SOW/LEADERSHIP/` |
| SOW-CLOSER-CHEFE | AGENT-CLOSER, AGENT-SALES-MANAGER | Híbrido (vender + gerir) | `/agents/ORG-LIVE/SOW/SALES/` |
| SOW-CLOSER | AGENT-CLOSER | Técnico (fechamento) | `/agents/ORG-LIVE/SOW/SALES/` |
| SOW-SALES-MANAGER | AGENT-SALES-MANAGER | Gestão (QC, coaching) | `/agents/ORG-LIVE/SOW/SALES/` |
| SOW-SDR | AGENT-BDR, AGENT-SDS, AGENT-LNS | Prospecção + Qualificação | `/agents/ORG-LIVE/SOW/SALES/` |
| SOW-CMO | AGENT-CMO | Marketing + Aquisição | `/agents/ORG-LIVE/SOW/MARKETING/` |
| SOW-COO | AGENT-COO | Operações + Entrega | `/agents/ORG-LIVE/SOW/OPERATIONS/` |

> **Documento completo:** [AGENT-ROLE-MAPPING.md](../AGENT-ROLE-MAPPING.md)

**O que isso significa na prática:**
ROLE-CLOSER-CHEFE recebe conhecimento de DOIS agentes porque é cargo híbrido (vende + gerencia). ROLE-CLOSER recebe só de AGENT-CLOSER porque é cargo técnico puro. Este mapeamento garante que cada cargo recebe conhecimento relevante - sem ruído de outras áreas.

---

## FORMATO DE CITAÇÃO (v4.0)

### Tipo 1: Conhecimento via AGENTE

```markdown
> **[VIA: AGENT-CLOSER → Cole Gordon CG003]**
> "7 Beliefs: Pain, Doubt, Cost, Desire, Money, Support, Trust"

**APLICAÇÃO [SUA EMPRESA]:**
Usar framework 7 Beliefs durante discovery para mapear objeções do prospect.

**O que isso significa na prática:**
Durante a fase de discovery da call, use este framework para identificar
qual das 7 crenças está bloqueando o fechamento.
```

### Tipo 2: Citação Direta de Fonte

```markdown
> **[FONTE: Richard Linder - RL001]**
> "1-3-1: One problem, three possible solutions, one recommendation."

**O que isso significa na prática:**
Quando escalar decisão para o Founder, não traga só o problema.
Traga 3 soluções possíveis e indique qual você recomenda.
```

### Tipo 3: Decisão Interna [SUA EMPRESA]

```markdown
| Decisão | Valor | Fonte |
|---------|-------|-------|
| Desconto máximo autônomo | 10% | [DECISÃO [SUA EMPRESA]] |

**O que isso significa na prática:**
Você pode aprovar descontos de até 10% sem escalar.
Acima disso, precisa pedir autorização ao Founder.
```

### Tipo 4: Múltiplos Agentes para mesmo Cargo

```markdown
> **[VIA: AGENT-CLOSER → Cole Gordon CG003]**
> "QC é prioridade #1 do Sales Manager"

> **[VIA: AGENT-SALES-MANAGER → Richard Linder RL001]**
> "1-3-1: One problem, three solutions, one recommendation"

**APLICAÇÃO [SUA EMPRESA] (CLOSER CHEFE):**
Como cargo híbrido, aplicar QC diário (2-3 calls) usando framework 1-3-1
para escalar decisões ao FOUNDER.

**O que isso significa na prática:**
Como Closer Chefe você faz QC de 2-3 calls por dia (Cole Gordon).
Quando encontrar problema, use 1-3-1 para escalar (Richard Linder).
Exemplo: "Problema: Close rate caindo. Soluções: (1) Treinar objeções,
(2) Mudar script, (3) Rever qualificação. Recomendo opção 1."
```

**O que isso significa na prática (desta seção):**
Use SEMPRE um desses 4 formatos ao adicionar informação nos arquivos de cargo. Nunca escreva "segundo especialistas" ou "best practice é X" sem citar fonte específica. Isso protege contra alucinações e permite auditar de onde veio cada política.

---

## O QUE CARGO HERDA vs NÃO HERDA

### HERDA do AGENTE (com citação obrigatória)

| Tipo | Exemplo | Formato Citação |
|------|---------|-----------------|
| Frameworks | 7 Beliefs, SPIN, MEDDIC | [VIA: AGENTE → Fonte] |
| Métricas de referência | Close Rate >25%, 3 offers/dia | [VIA: AGENTE → Fonte] |
| Scripts e templates | Objection handling scripts | [VIA: AGENTE → Fonte] |
| Cenários e exemplos | Com [FONTE] preservada | [VIA: AGENTE → Fonte] |
| Best practices | QC, coaching, projeções | [VIA: AGENTE → Fonte] |

**O que isso significa na prática:**
Se Cole Gordon diz "3 offers por dia por closer", isso entra no ROLE-CLOSER.md como `[VIA: AGENT-CLOSER → CG003]`. É referência externa - você pode ajustar para sua realidade, mas precisa documentar o desvio.

### NÃO HERDA (Específico [SUA EMPRESA] - usar [DECISÃO [SUA EMPRESA]])

| Tipo | Definido em | Responsável |
|------|-------------|-------------|
| Pricing/Descontos | SOW-*.md | FOUNDER |
| Limites de autonomia | SOW-*.md | FOUNDER |
| Linhas de comunicação | ORG-CHART-MODEL.md | FOUNDER |
| Ferramentas específicas | SOW-*.md | FOUNDER |
| Contexto local (ticket, ICP) | JD-*.md | FOUNDER |

**O que isso significa na prática:**
Cole Gordon pode dizer "desconto de 15% é aceitável", mas na [SUA EMPRESA] você decidiu 10%. Use `[DECISÃO [SUA EMPRESA]]` para marcar essa diferença. Assim fica claro que você ESCOLHEU ser mais conservador - não é falta de conhecimento do best practice externo.

---

## TRATAMENTO DE CONFLITOS ENTRE FONTES

Quando AGENTE A diz X e AGENTE B diz Y:

```markdown
### [TÓPICO]

> **[VIA: AGENT-CLOSER → Cole Gordon CG003]:**
> "QC diário de 2-3 calls"

> **[VIA: AGENT-SALES-MANAGER → Alex Hormozi MM001]:**
> "QC pode ser semanal em times pequenos"

**TENSÃO DOCUMENTADA:**
| Fonte | Recomendação | Contexto |
|-------|--------------|----------|
| Cole Gordon | QC diário | Times em crescimento |
| Alex Hormozi | QC semanal | Times já validados |

**DECISÃO [SUA EMPRESA]:**
Adotar QC diário (Cole Gordon) por estarmos em fase de validação.
Revisar quando time >5 closers.

**O que isso significa na prática:**
Estamos em Fase 1 (validação), então seguimos Cole Gordon (QC diário).
Se em 12 meses estivermos em Fase 3 com time maduro, podemos mudar
para QC semanal (Alex Hormozi) e atualizar este documento.
```

**O que isso significa na prática (desta seção):**
Não delete informação conflitante - documente a tensão. Isso te força a ESCOLHER conscientemente (em vez de ignorar um lado) e deixa rastro para revisitar a decisão quando o contexto mudar.

---

## PROCESSO DE ATUALIZAÇÃO

### Gatilho: Novo material processado

```
1. Pipeline Jarvis processa material (Fases 1-6)
   │
   ▼
2. Fase 7 atualiza Agentes IA relevantes
   │   └── AGENT-*.md recebe novo conhecimento
   │
   ▼
3. Fase 8.2 propaga para Cargos via mapeamento
   │   └── ROLE-*.md recebe com [VIA: AGENTE → Fonte]
   │
   ▼
4. Memórias registram fontes processadas
   │   └── MEMORY-*.md atualizada
   │
   ▼
5. ORGANOGRAMA.md atualizado se mudança estrutural
```

**O que isso significa na prática:**
Quando você processa um vídeo novo do Cole Gordon sobre objeções, o sistema:
(1) Extrai insights no Pipeline Jarvis,
(2) Alimenta AGENT-CLOSER (que já tem contexto de outros vídeos),
(3) Atualiza ROLE-CLOSER.md com novo framework de objeções,
(4) Registra em MEMORY-CLOSER.md que processou fonte CG-nova,
(5) Se o framework mudar estrutura de time, atualiza ORGANOGRAMA.md.

Você NÃO faz isso manualmente - o sistema faz. Você só valida.

### Checklist de Alimentação

```
□ RASTREABILIDADE
  □ Agente fonte identificado?
  □ [VIA: AGENTE → FONTE] citado?
  □ Número exato preservado (não arredondado)?

□ LOCALIZAÇÃO
  □ Seção correta do cargo?
  □ Tabela com coluna "Fonte"?

□ CONFLITOS
  □ Tensão documentada (se houver)?
  □ DECISÃO [SUA EMPRESA] registrada?

□ CLAREZA
  □ Termos traduzidos para português?
  □ Seção "O que isso significa na prática" adicionada?
  □ Abreviações expandidas na primeira menção?

□ REGISTRO
  □ Memória do cargo atualizada?
  □ ORGANOGRAMA atualizado (se mudança estrutural)?
```

**O que isso significa na prática:**
Use este checklist como "teste de qualidade" antes de salvar mudanças em arquivos de cargo. Se algum item falhar, você criou débito técnico (informação sem origem, conflito não resolvido, termo técnico não explicado).

---

## SISTEMA DE AUDITORIA (v6.0)

### MEMORY-LOG: Registro de Todas as Atualizações

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUDITORIA DE MEMORYs                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Localização: /agents/ORG-LIVE/MEMORY-LOG/                               │
│  Formato: LOG-YYYY-MM.md (um arquivo por mês)                              │
│                                                                             │
│  PROPÓSITO:                                                                 │
│  ├── Registro de TODAS as atualizações de MEMORY                           │
│  ├── Rastreabilidade temporal (quando cada insight chegou)                 │
│  ├── Identificação de fontes mais produtivas                               │
│  └── Auditoria para debugging (por que cargo X tem info Y?)                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Campo Obrigatório: última_sincronização

Todo arquivo MEMORY-*.md DEVE incluir no header YAML:

```yaml
---
ultima_sincronizacao: 2025-12-28
agentes_fonte: [AGENT-CLOSER, AGENT-SALES-MANAGER]
versao: 1.2.0
fontes_processadas: 15
---
```

| Campo | Descrição | Atualização |
|-------|-----------|-------------|
| `ultima_sincronizacao` | Data da última atualização | A cada modificação |
| `agentes_fonte` | Lista de AGENTs que alimentam este MEMORY | Quando novo agente contribui |
| `versao` | Versão semântica do MEMORY | A cada mudança significativa |
| `fontes_processadas` | Contador de fontes já processadas | Incrementar a cada nova fonte |

**O que isso significa na prática:**
Quando você abre MEMORY-CLOSER.md e vê `ultima_sincronizacao: 2025-12-15`, sabe que faz 13 dias que nenhum material novo chegou. Se processou vídeos recentes do Cole Gordon e a data não mudou, algo quebrou no fluxo.

### Validação de Integridade

Executar periodicamente:

```bash
python scripts/health_check_orglive.py
```

O script verifica:
- [ ] Todos SOWs têm citações válidas [VIA] ou [FONTE]?
- [ ] Todos MEMORYs têm header com última_sincronização?
- [ ] MEMORYs estão sincronizados com AGENTs correspondentes?
- [ ] Existem SOWs órfãos (sem Agent mapeado)?
- [ ] Existem referências a arquivos inexistentes?

---

## ESTRUTURA PADRÃO DE SOW-*.md (v5.0)

```markdown
# CARGO: [NOME DO CARGO]

> **Status:** ATIVO | PLANEJADO | HÍBRIDO
> **Versão:** X.X.X | **Atualizado:** YYYY-MM-DD
> **Ecossistema:** [SUA EMPRESA]
> **Alimentado por:** AGENT-X, AGENT-Y
> **Protocolo:** ORG-LIVE-DOCUMENT-PROTOCOL v1.0

---

## CONEXÃO COM AGENTES IA

| Agente Fonte | Conhecimento Herdado | Localização |
|-------------|----------------------|-------------|

**O que isso significa na prática:**
[Explicar em português simples]

---

## 1. POSIÇÃO NO ORGANOGRAMA
**O que isso significa na prática:** [...]

## 2. RESPONSABILIDADES (com [FONTE] em cada item)
**O que isso significa na prática:** [...]

## 3. LINHAS DE COMUNICAÇÃO (com [FONTE])
**O que isso significa na prática:** [...]

## 4. FRAMEWORKS OPERACIONAIS (com [VIA: AGENTE → Fonte])
**O que isso significa na prática:** [...]

## 5. FERRAMENTAS OBRIGATÓRIAS
**O que isso significa na prática:** [...]

## 6. MÉTRICAS DE SUCESSO (com [FONTE])
**O que isso significa na prática:** [...]

## 7. EXEMPLOS PRÁTICOS (com [FONTE])
**O que isso significa na prática:** [...]

## 8. ARMADILHAS (com [FONTE])
**O que isso significa na prática:** [...]

## 9. GATILHOS DE MUDANÇA (com [FONTE])
**O que isso significa na prática:** [...]

## 10. FONTES UTILIZADAS

---

## ACORDO DE TIME
[Checklist de entendimento]

---

*CARGO-[NOME] v[X.X.X]*
*Sistema ORG-LIVE*
*Protocolo: ORG-LIVE-DOCUMENT-PROTOCOL v1.0*
```

**O que isso significa na prática (desta seção):**
Todo arquivo de cargo (SOW-*.md) segue este template. Se você abrir SOW-CLOSER.md e não encontrar as 10 seções acima, o arquivo está desatualizado. Use este template para criar novos cargos ou revisar existentes.

---

## REGRAS INVIOLÁVEIS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REGRAS INVIOLÁVEIS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ⛔ NUNCA adicionar informação sem [VIA], [FONTE] ou [DECISÃO [SUA EMPRESA]]   │
│                                                                             │
│  2. ⛔ NUNCA pular a conexão com AGENTE (ir direto do Pipeline)             │
│                                                                             │
│  3. ⛔ NUNCA arredondar números quando fonte tem exatos                     │
│                                                                             │
│  4. ⛔ NUNCA usar jargão técnico sem tradução ou explicação                 │
│                                                                             │
│  5. ✅ SEMPRE verificar se AGENTE já tem o conhecimento antes de duplicar   │
│                                                                             │
│  6. ✅ SEMPRE documentar tensões entre fontes/agentes                       │
│                                                                             │
│  7. ✅ SEMPRE atualizar MEMORY ao modificar CARGO                           │
│                                                                             │
│  8. ✅ SEMPRE seguir ORG-LIVE-DOCUMENT-PROTOCOL para formato                │
│                                                                             │
│  9. ✅ SEMPRE adicionar seção "O que isso significa na prática"             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**O que isso significa na prática:**
Estas regras não são sugestões - são requisitos de qualidade. Se você violar regra 1 (adicionar info sem fonte), cria risco de alucinação. Se violar regra 4 (jargão sem explicação), aliena quem não domina o vocabulário técnico. Trate como "testes unitários" da documentação.

---

## DECISÕES [SUA EMPRESA]

| Decisão | Valor/Política | Data |
|---------|----------------|------|
| Modelo de alimentação | Híbrido (Pipeline → Agentes → Cargos) | 2025-12-20 |
| Formato de citação | [VIA: AGENTE → Fonte CÓDIGO] | 2025-12-21 |
| Protocolo padrão | ORG-LIVE-DOCUMENT-PROTOCOL v1.0 | 2025-12-21 |
| Idioma primário | Português (termos técnicos preservados) | 2025-12-21 |

**O que isso significa na prática:**
Estas decisões definem "como a [SUA EMPRESA] faz documentação". Outras empresas podem fazer diferente - não tem problema. O importante é ter padrão consistente interno.

---

## FONTES UTILIZADAS

| Código | Fonte | Contribuição |
|--------|-------|--------------|
| CG003 | Cole Gordon - Sales Manager Responsibilities | QC, Projeções, Coaching |
| RL001 | Richard Linder - Founder First Hiring | Trust traits, 1-3-1 |
| [SUA EMPRESA] | Decisões internas | Modelo híbrido, formato citação |

---

## HISTÓRICO DE MUDANÇAS

| Data | Versão | Mudança | Motivo |
|------|--------|---------|--------|
| 2025-12-20 | 1.0.0 | Criação inicial | Setup do sistema ORG-LIVE |
| 2025-12-21 | 2.0.0 | Conexão com Agentes IA | Modelo híbrido |
| 2025-12-21 | 3.0.0 | Aplicação ORG-LIVE-DOCUMENT-PROTOCOL | Padronização completa |
| 2025-12-21 | 4.0.0 | Tradução para português + seções "Na prática" | Regras de clareza |
| 2025-12-28 | 5.0.0 | Sistema de Auditoria | MEMORY-LOG + última_sincronização |
| 2025-12-28 | 6.0.0 | health_check_orglive.py | Validador de integridade |
| 2025-12-29 | 7.0.0 | Reestruturação completa de pastas | ROLES/ → SOW/ por área, +MODEL/, +OPERATIONS/, +TRIGGERS/, +YOUR-ORG/, +LOGS/ |

---

*PROTOCOLO DE ALIMENTAÇÃO v7.0.0*
*Modelo Híbrido: Pipeline → Agentes IA → Cargos*
*Arquitetura: 7 Níveis (AGENTES, PIPELINE, CARGOS, MODEL, OPERATIONS, TRIGGERS, YOUR-ORG)*
*Protocolo: ORG-LIVE-DOCUMENT-PROTOCOL v1.0*
