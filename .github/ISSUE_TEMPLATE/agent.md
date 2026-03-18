---
name: Agent Task
about: Criação ou atualização de agentes (PERSON/cargo/SUB-AGENT)
title: '[AGENT] '
labels: ['agent', 'knowledge']
assignees: ''
---

## Tipo de Agente
- [ ] PERSON Agent (baseado em pessoa/especialista)
- [ ] CARGO Agent (baseado em função/papel)
- [ ] SUB-AGENT (especialista JARVIS)

## Ação
- [ ] Criar novo agente
- [ ] Atualizar agente existente
- [ ] Migrar para Template V3
- [ ] Enriquecer DNA

## Identificação do Agente

| Campo | Valor |
|-------|-------|
| Nome | |
| Código | |
| Localização | `/agents/[TIPO]/[NOME]/` |
| Versão Atual | |
| Versão Target | |

## Fonte(s) de Conhecimento
<!-- De onde vem o conhecimento para este agente -->
- [ ] HORMOZI (AH)
- [ ] COLE-GORDON (CG)
- [ ] JEREMY MINER (JM)
- [ ] JEREMY HAYNES (JH)
- [ ] Batches:

## Arquivos a Criar/Atualizar
<!-- Estrutura de arquivos do agente -->
```
/agents/[TIPO]/[NOME]/
├── AGENT.md           # [ ] Criar [ ] Atualizar
├── SOUL.md            # [ ] Criar [ ] Atualizar
├── DNA-CONFIG.yaml    # [ ] Criar [ ] Atualizar
├── MEMORY.md          # [ ] Criar [ ] Atualizar
├── VOICE-SAMPLES.md   # [ ] Criar [ ] Atualizar
├── DECISIONS.md       # [ ] Criar [ ] Atualizar
└── CLAUDE.md          # [ ] Criar [ ] Atualizar
```

## Template V3 Compliance
<!-- Verificar que segue REGRA #24 -->

### AGENT.md - 11 Partes Obrigatórias
- [ ] PARTE 0: ÍNDICE
- [ ] PARTE 1: COMPOSIÇÃO ATÔMICA
- [ ] PARTE 2: GRÁFICO DE IDENTIDADE
- [ ] PARTE 3: MAPA NEURAL (DNA)
- [ ] PARTE 4: NÚCLEO OPERACIONAL
- [ ] PARTE 5: SISTEMA DE VOZ
- [ ] PARTE 6: MOTOR DE DECISÃO
- [ ] PARTE 7: INTERFACES DE CONEXÃO
- [ ] PARTE 8: PROTOCOLO DE DEBATE
- [ ] PARTE 9: MEMÓRIA EXPERIENCIAL
- [ ] PARTE 10: EXPANSÕES E REFERÊNCIAS

### Elementos Visuais
- [ ] ASCII Art Header
- [ ] Bordas duplas ╔═══╗ para headers
- [ ] Bordas simples ┌───┐ para subseções
- [ ] Barras de progresso
- [ ] Citações rastreáveis ^[FONTE]

## DNA Cognitivo (5 Camadas)
<!-- Quantidade de elementos a adicionar -->
| Camada | Atual | +Novos | Total |
|--------|-------|--------|-------|
| [FILOSOFIA] | | | |
| [MODELO-MENTAL] | | | |
| [HEURISTICA] | | | |
| [FRAMEWORK] | | | |
| [METODOLOGIA] | | | |

## Regras Aplicáveis
- REGRA #19: Isolamento por fonte
- REGRA #21: Cascateamento obrigatório
- REGRA #24: Template enforcement
- REGRA #:

## Checklist de Verificação (6 Níveis)
- [ ] 1. Hooks/Lint passed
- [ ] 2. Tests passed
- [ ] 3. Build successful
- [ ] 4. Visual verification
- [ ] 5. Staging tested
- [ ] 6. Security audit
