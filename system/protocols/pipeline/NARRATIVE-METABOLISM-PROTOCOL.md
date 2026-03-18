# NARRATIVE METABOLISM PROTOCOL v1.0

> **Propósito:** Transformar insights fragmentados em narrativas vivas e evolutivas
> **Aplicação:** SOURCES/, DOSSIERS/persons/, DOSSIERS/THEMES/
> **Criado:** 2025-12-20

---

## Conceito Central

O documento tem **metabolismo** — ele **digere** novos insights e **consolida** quando fica denso demais. Não é um resumo estático, é um organismo vivo de conhecimento.

```
┌─────────────────────────────────────────────────────────────────┐
│                    NARRATIVE METABOLISM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   NOVO INSIGHT                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌────────────────────────────────────┐                       │
│   │  1. CLASSIFICAÇÃO SEMÂNTICA        │                       │
│   │     Qual seção? Qual conceito?     │                       │
│   │     Reforça ou expande existente?  │                       │
│   └────────────────────────────────────┘                       │
│        │                                                        │
│        ▼                                                        │
│   ┌────────────────────────────────────┐                       │
│   │  2. INJEÇÃO CONTEXTUAL             │                       │
│   │     Inserir no ponto certo         │                       │
│   │     Conectar com texto existente   │                       │
│   │     Preservar fluxo narrativo      │                       │
│   └────────────────────────────────────┘                       │
│        │                                                        │
│        ▼                                                        │
│   ┌────────────────────────────────────┐                       │
│   │  3. CHECK DE CONSOLIDAÇÃO          │                       │
│   │     Densidade > threshold?         │                       │
│   │     Se sim → reescrever seção      │                       │
│   └────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuração Padrão

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| **Tom** | Voz da Fonte | Autenticidade, conexão, terminologia preservada |
| **Idioma** | Português BR + termos técnicos em inglês | Fluidez natural |
| **Granularidade** | 800-1500 palavras | Acionável + consultável + escalável |
| **Consolidação** | Automática + Safeguards | Fluidez sem perder controle |
| **Diagramas** | Apenas para exemplificar | Não decorativo |

---

## Estrutura do Documento Narrativo

```markdown
# [FONTE] — [TEMA]

> **Em resumo:** [Síntese executiva — máximo 3 linhas]
> **Versão:** X.Y | **Atualizado:** YYYY-MM-DD
> **Densidade:** ◯◯◯◯◯ (1-5) — trigger consolidação em 4+

---

## Filosofia Central
[O "porquê" — princípios fundamentais, crenças, mentalidade]

## Modus Operandi
[O "como" — processos, frameworks, sequência de ações]

## Arsenal Técnico
[O "o quê" — táticas concretas, scripts, números específicos]

## Armadilhas
[O que NÃO fazer — erros comuns, anti-patterns]

## Evolução
[Mudanças de pensamento ao longo do tempo — se aplicável]

---

## Citações Originais
> "Citação exata preservada" — [Fonte:chunk_id]

## Metadados
- **Chunks:** [IDs]
- **Insights:** [IDs]
- **Última consolidação:** [data]
```

---

## Regras de Voz

### Princípio: A Fonte Fala

O texto deve soar como se a pessoa estivesse explicando diretamente para você. Não é uma análise sobre a pessoa — é a pessoa compartilhando conhecimento.

### Exemplos

**❌ ERRADO (voz de analista):**
```
Jordan Lee utiliza uma estrutura hierárquica com team leads
que recebem overrides. A metodologia dele prioriza sistemas
sobre dependência de indivíduos.
```

**✅ CORRETO (voz da fonte):**
```
Minha operação tem 240 pessoas, mas sabe quantas são realmente
insubstituíveis? Três. Só três além do Jacob. Isso não acontece
por acaso — construí sistemas, não feudos. Quando um closer sai,
o sistema continua rodando.
```

### Marcadores de Voz

| Elemento | Como Aplicar |
|----------|--------------|
| **Primeira pessoa** | "Eu faço...", "Minha abordagem...", "Aprendi que..." |
| **Tom conversacional** | Como se estivesse num podcast explicando |
| **Termos próprios** | Preservar jargão do expert (Farm System, 7 Beliefs, etc.) |
| **Números específicos** | Nunca arredondar — "4.3 calls/dia", não "cerca de 4" |
| **Convicção** | Experts têm opiniões fortes — preservar assertividade |

---

## Regras de Injeção

Quando novo insight chega, classificar e injetar:

| Tipo de Insight | Seção Destino | Método de Integração |
|-----------------|---------------|----------------------|
| Princípio/Crença | Filosofia Central | Expandir ou contrastar com existente |
| Processo/Sequência | Modus Operandi | Detalhar passos, adicionar nuances |
| Tática/Número | Arsenal Técnico | Novo item ou enriquecer existente |
| Erro/Lição | Armadilhas | Adicionar caso ou reforçar padrão |
| Contradição/Mudança | Evolução | Documentar tensão temporal |
| Citação marcante | Citações Originais | Sempre preservar na íntegra |

### Exemplo de Injeção

**Texto existente:**
```
Meu time de vendas roda com 70 closers fazendo 300 calls por dia.
```

**Novo insight:** "Team leads recebem override de 3% sobre vendas do time"

**Após injeção:**
```
Meu time de vendas roda com 70 closers fazendo 300 calls por dia.
Os team leads não são só gerentes — eles têm skin in the game com
override de 3% sobre as vendas do time inteiro. Isso muda tudo:
eles querem que os closers vendam, não que falhem.
```

---

## Regras de Consolidação

### Trigger Automático

```
SE seção.palavras > 600
   OU seção.insights > 5
   OU densidade >= 4:

   → EXECUTAR consolidação
```

### Processo de Consolidação

1. **Snapshot** — Salvar versão anterior em `_ARCHIVE/`
2. **Identificar núcleo** — O que é essencial vs. repetitivo
3. **Reescrever** — Manter essência + integrar detalhes
4. **Preservar** — Números, citações, termos técnicos
5. **Logar** — Registrar consolidação em metadados

### Exemplo de Consolidação

**ANTES (fragmentado, densidade 5):**
```
- "Contrato por competência, não experiência"
- "Experiência pode ser ensinada, competência é inata"
- "Prefiro alguém que aprende rápido do que alguém que já sabe"
- "Gente experiente traz vícios, gente competente traz potencial"
- "Competência > Experiência, sempre"
```

**DEPOIS (consolidado, densidade 2):**
```
Minha filosofia de contratação é simples: competência bate experiência,
sempre. Experiência você ensina — em 3 meses a pessoa está calibrada.
Mas competência? Ou a pessoa tem, ou não tem. Prefiro alguém que
aprende rápido e chega zerado do que um "veterano" cheio de vícios
que vai levar 6 meses pra desaprender.
```

---

## Safeguards Obrigatórios

| Regra | Implementação |
|-------|---------------|
| **Nunca deletar** | Consolidar = reescrever, texto antigo vai pro archive |
| **Preservar números** | Métricas específicas são intocáveis |
| **Manter citações** | Quotes originais sempre preservadas na seção dedicada |
| **Versionar** | Incrementar versão a cada mudança significativa |
| **Logar** | Registrar data e motivo de cada consolidação |

---

## Aplicação por Camada

### SOURCES/{pessoa}/{tema}

| Aspecto | Configuração |
|---------|--------------|
| **Foco** | Profundidade máxima naquele tema específico |
| **Voz** | 100% voz da fonte |
| **Detalhe** | Scripts, números, passo-a-passo |
| **Extensão** | 800-1500 palavras |

### DOSSIERS/persons/{pessoa}

| Aspecto | Configuração |
|---------|--------------|
| **Foco** | Perfil completo — padrões decisórios |
| **Voz** | 80% voz da fonte, 20% contextualização |
| **Detalhe** | Filosofias, frameworks, jornada |
| **Extensão** | 1500-3000 palavras |

### DOSSIERS/THEMES/{tema}

| Aspecto | Configuração |
|---------|--------------|
| **Foco** | Comparativo entre múltiplas fontes |
| **Voz** | Narrador que apresenta cada perspectiva |
| **Detalhe** | Consensos, tensões, síntese |
| **Extensão** | 1500-2500 palavras |

---

## Indicador de Densidade

Visual para sinalizar necessidade de consolidação:

```
◯◯◯◯◯ (1) — Documento novo, espaço para crescer
◐◯◯◯◯ (2) — Conteúdo básico estabelecido
◐◐◯◯◯ (3) — Bem desenvolvido
◐◐◐◯◯ (4) — Denso, monitorar (trigger warning)
◐◐◐◐◯ (5) — CONSOLIDAR AGORA
```

---

## Checklist de Qualidade

Antes de finalizar qualquer documento narrativo:

- [ ] Tom soa como a fonte falando?
- [ ] Números específicos preservados?
- [ ] Termos técnicos em inglês mantidos?
- [ ] Português BR fluido e natural?
- [ ] Diagramas apenas onde necessário?
- [ ] Citações originais na seção dedicada?
- [ ] Metadados atualizados?
- [ ] Densidade calculada corretamente?

---

## Integração com Pipeline Jarvis

Este protocolo é executado nas fases:

| Fase | Aplicação |
|------|-----------|
| **4.0 Dossier Compilation** | Criar/atualizar DOSSIERS/ com voz narrativa |
| **4.1 Sources Compilation** | Criar/atualizar SOURCES/ com voz da fonte |
| **Incremental Updates** | Injetar novos insights seguindo regras |

---

*Protocol Version 1.0 — Narrative Metabolism*
*Mega Brain System v3.21.0*
