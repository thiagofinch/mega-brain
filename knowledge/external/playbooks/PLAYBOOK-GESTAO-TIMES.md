# PLAYBOOK-GESTAO-TIMES

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║   ██████╗ ███████╗███████╗████████╗ █████╗  ██████╗                            ║
║  ██╔════╝ ██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗                           ║
║  ██║  ███╗█████╗  ███████╗   ██║   ███████║██║   ██║                           ║
║  ██║   ██║██╔══╝  ╚════██║   ██║   ██╔══██║██║   ██║                           ║
║  ╚██████╔╝███████╗███████║   ██║   ██║  ██║╚██████╔╝                           ║
║   ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝                            ║
║                                                                                ║
║   ████████╗██╗███╗   ███╗███████╗███████╗                                      ║
║   ╚══██╔══╝██║████╗ ████║██╔════╝██╔════╝                                      ║
║      ██║   ██║██╔████╔██║█████╗  ███████╗                                      ║
║      ██║   ██║██║╚██╔╝██║██╔══╝  ╚════██║                                      ║
║      ██║   ██║██║ ╚═╝ ██║███████╗███████║                                      ║
║      ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝                                      ║
║                                                                                ║
║                 PLAYBOOK DE GESTÃO DE TIMES DE VENDAS                          ║
║                                                                                ║
╠════════════════════════════════════════════════════════════════════════════════╣
║  VERSÃO:    2.0.0                    CRIADO:     2026-01-13                    ║
║  FONTES:    BATCH-050 (Cole Gordon) + BATCH-125 (Full Sales System)           ║
║  FASE:      5.7 - Cascateamento                                               ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

> **Objetivo:** Framework completo para gestão contínua de times de vendas
> **Quando usar:** Após onboarding, para gestão do dia-a-dia
> **Fontes:** Cole Gordon (Closers.io) - BATCH-050 | Full Sales System - BATCH-125

---

## FILOSOFIA CENTRAL

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   "Ter uma equipe de vendas é diferente de ter uma equipe que vende"            │
│                                                                                 │
│   "A velocidade da equipe é a velocidade do líder"                              │
│                                                                                 │
│   "O ser humano se motiva mais pela necessidade do que pelo sonho"              │
│                                                                                 │
│   "Motivação é um motivo para a ação, não é pula-pula"                          │
│                                                                                 │
│   "Líderes que não delegam são líderes que não crescem"                         │
│                                                                                 │
│                                               ^[BATCH-050:Filosofias]           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## MÉTODO PTMA (FRAMEWORK PRINCIPAL)

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                           MÉTODO PTMA                                          ║
║              Planejar → Treinar → Motivar → Acompanhar/Cobrar                  ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║                        ┌─────────────────┐                                     ║
║                        │    PLANEJAR     │                                     ║
║                        │  Metas claras   │                                     ║
║                        └────────┬────────┘                                     ║
║                                 │                                              ║
║                                 ▼                                              ║
║                        ┌─────────────────┐                                     ║
║                        │    TREINAR      │                                     ║
║                        │ 87% comportam.  │                                     ║
║                        └────────┬────────┘                                     ║
║                                 │                                              ║
║                                 ▼                                              ║
║                        ┌─────────────────┐                                     ║
║                        │    MOTIVAR      │                                     ║
║                        │  Reconhecimento │                                     ║
║                        └────────┬────────┘                                     ║
║                                 │                                              ║
║                                 ▼                                              ║
║                        ┌─────────────────┐                                     ║
║                        │  ACOMPANHAR/    │                                     ║
║                        │    COBRAR       │                                     ║
║                        └────────┬────────┘                                     ║
║                                 │                                              ║
║                                 └───────────────────────────┐                  ║
║                                                             │                  ║
║                                 ┌───────────────────────────┘                  ║
║                                 │                                              ║
║                                 ▼                                              ║
║                         (CICLO CONTÍNUO)                                       ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

---

## PASSO 1: PLANEJAR

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PLANEJAR - Metas Claras e Mensuráveis                     ^[BATCH-050:PTMA]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  NÍVEIS DE META:                                                               │
│  │                                                                             │
│  │ DIÁRIA                                                                      │
│  │ ├── Quantidade de atividades (calls, reuniões, follow-ups)                 │
│  │ ├── Tempo em atividade produtiva                                           │
│  │ └── Check-in no fim do dia                                                 │
│  │                                                                             │
│  │ SEMANAL                                                                     │
│  │ ├── Reuniões realizadas                                                    │
│  │ ├── Propostas enviadas                                                     │
│  │ ├── Pipeline atualizado                                                    │
│  │ └── Revisão em reunião de equipe                                           │
│  │                                                                             │
│  │ MENSAL                                                                      │
│  │ ├── Meta de faturamento                                                    │
│  │ ├── Número de fechamentos                                                  │
│  │ ├── Ticket médio                                                           │
│  │ └── Conversão por etapa do funil                                           │
│  │                                                                             │
│                                                                                 │
│  REGRAS DE PLANEJAMENTO:                                                       │
│  │                                                                             │
│  │ ✓ Meta tem que ser específica e mensurável                                 │
│  │ ✓ Vendedor participar da construção (buy-in)                               │
│  │ ✓ Desafiadora mas alcançável                                               │
│  │ ✓ Breakdown em atividades controláveis                                     │
│  │ ✓ Visível para toda equipe (transparência)                                 │
│  │                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## PASSO 2: TREINAR

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  TREINAR - 87% Comportamental, 13% Técnico                 ^[BATCH-050:PTMA]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PROPORÇÃO MENSAL:                                                             │
│  │                                                                             │
│  │  ████████████████████████████████████████████ 87% COMPORTAMENTAL            │
│  │  ██████ 13% TÉCNICO                                                         │
│  │                                                                             │
│                                                                                 │
│  TREINAMENTO COMPORTAMENTAL (87%):                                             │
│  │                                                                             │
│  │ ✓ Mindset e atitude                                                        │
│  │ ✓ Inteligência emocional                                                   │
│  │ ✓ Gestão de rejeição                                                       │
│  │ ✓ Disciplina e rotina                                                      │
│  │ ✓ Comunicação e rapport                                                    │
│  │ ✓ Resiliência e persistência                                               │
│  │                                                                             │
│  TREINAMENTO TÉCNICO (13%):                                                    │
│  │                                                                             │
│  │ ✓ Produto/serviço (atualizações)                                           │
│  │ ✓ Ferramentas (CRM, scripts)                                               │
│  │ ✓ Processos internos                                                       │
│  │ ✓ Condições comerciais                                                     │
│  │                                                                             │
│                                                                                 │
│  10 FORMAS DE TREINAR:                                                         │
│  │                                                                             │
│  │  1. TEATRALIZAÇÃO FUNCIONAL                                                │
│  │     └── Role-plays com cenários reais                                      │
│  │                                                                             │
│  │  2. CASO DE SUCESSO SEMANAL                                                │
│  │     └── Top performer apresenta como fechou a melhor venda                 │
│  │                                                                             │
│  │  3. GRAVAÇÃO E ANÁLISE                                                     │
│  │     └── Escutar calls, identificar gaps, celebrar acertos                  │
│  │                                                                             │
│  │  4. MENTORIA 1:1                                                           │
│  │     └── Sessões individuais com líder ou top performer                     │
│  │                                                                             │
│  │  5. SHADOWING                                                              │
│  │     └── Observar e ser observado                                           │
│  │                                                                             │
│  │  6. BIBLIOTECA DE CONTEÚDO                                                 │
│  │     └── Vídeos, artigos, podcasts sobre vendas                             │
│  │                                                                             │
│  │  7. COMPETIÇÕES DE ROLE-PLAY                                               │
│  │     └── Quem executa melhor o script                                       │
│  │                                                                             │
│  │  8. DEBRIEFING PÓS-CALL                                                    │
│  │     └── O que funcionou? O que ajustar?                                    │
│  │                                                                             │
│  │  9. CERTIFICAÇÃO INTERNA                                                   │
│  │     └── Testes de conhecimento progressivos                                │
│  │                                                                             │
│  │ 10. CONVIDADOS EXTERNOS                                                    │
│  │     └── Especialistas, clientes, outros times                              │
│  │                                                                             │
│                                                                                 │
│  FILOSOFIA: "Líder que não treina não tem moral para cobrar"                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## PASSO 3: MOTIVAR

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MOTIVAR - Um Motivo Para a Ação (não é pula-pula)         ^[BATCH-050:PTMA]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  TIPOS DE MOTIVAÇÃO:                                                           │
│  │                                                                             │
│  │ EXTRÍNSECA (curto prazo)                                                   │
│  │ ├── Comissões e bônus                                                      │
│  │ ├── Prêmios e viagens                                                      │
│  │ ├── Reconhecimento público                                                 │
│  │ └── Rankings e competições                                                 │
│  │                                                                             │
│  │ INTRÍNSECA (longo prazo)                                                   │
│  │ ├── Propósito e significado                                                │
│  │ ├── Crescimento e desenvolvimento                                          │
│  │ ├── Autonomia e confiança                                                  │
│  │ └── Pertencimento à equipe                                                 │
│  │                                                                             │
│                                                                                 │
│  SISTEMA DE RECONHECIMENTO:                                                    │
│  │                                                                             │
│  │ DIÁRIO                                                                      │
│  │ └── "Parabéns pela venda de hoje" (específico, imediato)                   │
│  │                                                                             │
│  │ SEMANAL                                                                     │
│  │ └── Top da semana (reunião de equipe)                                      │
│  │                                                                             │
│  │ MENSAL                                                                      │
│  │ └── Vendedor do mês (prêmio + reconhecimento)                              │
│  │                                                                             │
│  │ TRIMESTRAL                                                                  │
│  │ └── Premiação maior (viagem, bônus extra)                                  │
│  │                                                                             │
│                                                                                 │
│  RATIO DE INTERAÇÕES (LOUSADA):                                                │
│  │                                                                             │
│  │  6-8 interações positivas = ALTA PERFORMANCE                               │
│  │  < 6 interações = Desengajamento (pouca atenção)                           │
│  │  > 8 interações = Queda de qualidade ("se acha", acomoda)                  │
│  │                                                                             │
│  │  3 positivas : 1 negativa = Equilíbrio                                     │
│  │  Menos de 3:1 = Pessoa se sente atacada                                    │
│  │                                                                             │
│                                                                                 │
│  FILOSOFIA: "O ser humano se motiva mais pela necessidade do que pelo sonho"   │
│                                                                                 │
│  IMPLICAÇÃO PRÁTICA:                                                           │
│  │ ✓ Conheça as necessidades reais (contas, família, objetivos)              │
│  │ ✓ Conecte a meta com a necessidade pessoal                                 │
│  │ ✓ "Se você bater essa meta, consegue [necessidade específica]"             │
│  │                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## PASSO 4: ACOMPANHAR/COBRAR

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ACOMPANHAR/COBRAR - Feedback e Accountability            ^[BATCH-050:PTMA]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  RITUAIS DE ACOMPANHAMENTO:                                                    │
│  │                                                                             │
│  │ DAILY STANDUP (10-15 min)                                                  │
│  │ ├── O que fez ontem?                                                       │
│  │ ├── O que vai fazer hoje?                                                  │
│  │ └── Algum bloqueio?                                                        │
│  │                                                                             │
│  │ WEEKLY REVIEW (30-60 min)                                                  │
│  │ ├── Pipeline review                                                        │
│  │ ├── Deals em risco                                                         │
│  │ ├── Vitórias da semana                                                     │
│  │ └── Treinamento/role-play                                                  │
│  │                                                                             │
│  │ MONTHLY 1:1 (60 min)                                                       │
│  │ ├── Performance vs meta                                                    │
│  │ ├── Desenvolvimento pessoal                                                │
│  │ ├── Feedback aprofundado                                                   │
│  │ └── Plano para próximo mês                                                 │
│  │                                                                             │
│                                                                                 │
│  COMO COBRAR SEM DESTRUIR:                                                     │
│  │                                                                             │
│  │ 1. PREPARAR                                                                 │
│  │    └── Dados objetivos, comportamentos específicos                         │
│  │                                                                             │
│  │ 2. AMBIENTE PRIVADO                                                         │
│  │    └── Nunca expor em público (humilhação destrói)                         │
│  │                                                                             │
│  │ 3. SANDUÍCHE DE FEEDBACK                                                    │
│  │    ├── Positivo específico                                                 │
│  │    ├── Ponto de melhoria                                                   │
│  │    └── Positivo + ação                                                     │
│  │                                                                             │
│  │ 4. FOCO NO COMPORTAMENTO                                                    │
│  │    └── "Você fez X" não "Você é Y"                                         │
│  │                                                                             │
│  │ 5. AÇÃO CLARA                                                               │
│  │    └── "O que você vai fazer diferente?"                                   │
│  │                                                                             │
│  │ 6. FOLLOW-UP                                                                │
│  │    └── Verificar se ajustou, reconhecer melhoria                           │
│  │                                                                             │
│                                                                                 │
│  QUANDO DESLIGAR:                                                              │
│  │                                                                             │
│  │ ✓ Após 3 ciclos de feedback sem melhoria                                   │
│  │ ✓ Red flags de integridade (mentira, manipulação)                          │
│  │ ✓ Impacto negativo no time (contamina outros)                              │
│  │ ✓ Não aceita coaching (blindado a feedback)                                │
│  │                                                                             │
│  │ REGRA: "Demore para contratar e seja rápido para demitir"                  │
│  │                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## GESTÃO POR PERFIL DISC

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  COMO LIDERAR CADA PERFIL                                  ^[BATCH-050:DISC]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  D - DOMINANTE                                                                  │
│  │ COMO LIDERAR:                                                               │
│  │ ✓ Dê autonomia e espaço                                                    │
│  │ ✓ Desafie com metas agressivas                                             │
│  │ ✓ Massage o ego quando entrega                                             │
│  │ ✓ Competição como combustível                                              │
│  │                                                                             │
│  │ EVITAR:                                                                     │
│  │ ✗ Microgerenciamento                                                       │
│  │ ✗ Reuniões longas sem propósito                                            │
│  │ ✗ Processos burocráticos excessivos                                        │
│  │                                                                             │
│                                                                                 │
│  I - INFLUENTE                                                                  │
│  │ COMO LIDERAR:                                                               │
│  │ ✓ Reconhecimento público frequente                                         │
│  │ ✓ Metas curtas (senão perde foco)                                          │
│  │ ✓ Ambiente divertido e social                                              │
│  │ ✓ Acompanhamento próximo nos "baixos"                                      │
│  │                                                                             │
│  │ EVITAR:                                                                     │
│  │ ✗ Colocar no financeiro (arredonda números!)                               │
│  │ ✗ Treinamentos longos e técnicos                                           │
│  │ ✗ Isolamento (precisa de grupo)                                            │
│  │                                                                             │
│                                                                                 │
│  S - ESTÁVEL                                                                    │
│  │ COMO LIDERAR:                                                               │
│  │ ✓ Processos claros e documentados                                          │
│  │ ✓ Manuais e passo-a-passo                                                  │
│  │ ✓ Paciência no início (demora mas entrega)                                 │
│  │ ✓ Consistência no acompanhamento                                           │
│  │                                                                             │
│  │ VANTAGEM:                                                                   │
│  │ ★ Fica ANOS na empresa se tratado bem                                      │
│  │                                                                             │
│  │ EVITAR:                                                                     │
│  │ ✗ Pressão por velocidade no início                                         │
│  │ ✗ Mudanças bruscas de processo                                             │
│  │ ✗ Ambiguidade nas instruções                                               │
│  │                                                                             │
│                                                                                 │
│  C - SISTEMÁTICO                                                                │
│  │ COMO LIDERAR:                                                               │
│  │ ✓ Explique o PORQUÊ de tudo                                                │
│  │ ✓ Dados e métricas são importantes                                         │
│  │ ✓ Treinamento individual                                                   │
│  │ ✓ Detalhes e fundamentos antes de prática                                  │
│  │                                                                             │
│  │ EVITAR:                                                                     │
│  │ ✗ "Faz assim porque eu disse"                                              │
│  │ ✗ Treinamentos em grupo genéricos                                          │
│  │ ✗ Pedir que execute sem entender                                           │
│  │                                                                             │
│  │ SE NÃO ENTENDE O PORQUÊ → NÃO RENDE                                        │
│  │                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 12 PONTOS DE RETENÇÃO DE TALENTOS

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  RETENÇÃO DE VENDEDORES TOP PERFORMERS                     ^[BATCH-050]         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   1. REMUNERAÇÃO COMPETITIVA                                                   │
│      └── Comissão justa, bônus por performance, OTE claro                      │
│                                                                                 │
│   2. CRESCIMENTO CLARO                                                         │
│      └── Plano de carreira visível (SDR → Closer → Líder)                      │
│                                                                                 │
│   3. RECONHECIMENTO FREQUENTE                                                  │
│      └── Celebrar vitórias, ranking, prêmios                                   │
│                                                                                 │
│   4. AUTONOMIA CRESCENTE                                                       │
│      └── Mais liberdade conforme entrega                                       │
│                                                                                 │
│   5. LIDERANÇA QUE TREINA                                                      │
│      └── Líder presente, que desenvolve, não só cobra                          │
│                                                                                 │
│   6. CULTURA DE ALTA PERFORMANCE                                               │
│      └── Estar cercado de gente boa eleva todos                                │
│                                                                                 │
│   7. FERRAMENTAS ADEQUADAS                                                     │
│      └── CRM bom, leads qualificados, estrutura                                │
│                                                                                 │
│   8. FEEDBACK CONSTRUTIVO                                                      │
│      └── Saber onde está e como melhorar                                       │
│                                                                                 │
│   9. DESAFIOS CONSTANTES                                                       │
│      └── Top performer entedia sem desafio                                     │
│                                                                                 │
│  10. EQUILÍBRIO                                                                │
│      └── Respeitar limites, evitar burnout                                     │
│                                                                                 │
│  11. CONFIANÇA E TRANSPARÊNCIA                                                 │
│      └── Comunicação clara sobre empresa e expectativas                        │
│                                                                                 │
│  12. PROPÓSITO MAIOR                                                           │
│      └── Conectar trabalho com impacto real                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## HEURÍSTICAS DE GESTÃO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  NÚMEROS QUE IMPORTAM                                      ^[BATCH-050]         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  87% / 13%          Proporção comportamental vs técnico em treinamento          │
│                                                                                 │
│  6-8 interações     Número ideal de interações positivas por período            │
│                     (< 6 = desengajado | > 8 = acomoda)                         │
│                                                                                 │
│  3:1                Ratio de feedback (3 positivos para cada 1 construtivo)     │
│                                                                                 │
│  30 dias            Tempo para saber se vendedor é bom ou não                   │
│                                                                                 │
│  3 ciclos           Máximo de ciclos de feedback antes de decisão               │
│                                                                                 │
│  1x/semana          Frequência mínima de 1:1 com cada vendedor                  │
│                                                                                 │
│  10 min/dia         Tempo máximo para daily standup                             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## CHECKLIST DE GESTÃO MENSAL

```
PLANEJAMENTO:
[ ] Metas do mês definidas por vendedor
[ ] Breakdown em atividades semanais
[ ] Metas compartilhadas com time
[ ] Buy-in de cada vendedor obtido

TREINAMENTO:
[ ] Sessão de treinamento comportamental (87%)
[ ] Atualização técnica se necessário (13%)
[ ] Role-play ou teatralização realizada
[ ] Caso de sucesso compartilhado

MOTIVAÇÃO:
[ ] Reconhecimentos diários dados
[ ] Top da semana celebrado
[ ] Premiações do mês entregues
[ ] Necessidades pessoais conhecidas

ACOMPANHAMENTO:
[ ] Daily standups realizados
[ ] Weekly review completada
[ ] 1:1 mensal com cada vendedor
[ ] Pipeline atualizado e revisado
[ ] Feedbacks dados (sanduíche)
[ ] Decisões sobre baixa performance tomadas
```

---

---

## BATCH-125: LIDERANÇA LUCRATIVA (FULL SALES SYSTEM)

> **Fonte:** Full Sales System - Liderança Lucrativa
> **Elementos:** 142 DNA (28 filosofias, 18 modelos, 36 heurísticas, 38 frameworks, 22 metodologias)

### MÉTODO PTAC (VARIANTE FSS DO PTMA)

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                           MÉTODO PTAC                                          ║
║                  (Full Sales System Leadership Cycle)                          ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║          ┌─────────────┐                      ┌─────────────┐                  ║
║          │  PLANEJAR   │──────────────────────│   TREINAR   │                  ║
║          │  Definir    │                      │   87/13     │                  ║
║          │  metas      │                      │   regra     │                  ║
║          └──────┬──────┘                      └──────┬──────┘                  ║
║                 │                                    │                         ║
║                 │        ┌──────────────┐            │                         ║
║                 └───────▶│    CICLO     │◀───────────┘                         ║
║                          │   CONTÍNUO   │                                      ║
║                 ┌───────▶│              │◀───────────┐                         ║
║                 │        └──────────────┘            │                         ║
║                 │                                    │                         ║
║          ┌──────┴──────┐                      ┌──────┴──────┐                  ║
║          │   COBRAR    │──────────────────────│ ACOMPANHAR  │                  ║
║          │  Feedback   │                      │  + MOTIVAR  │                  ║
║          │  sanduíche  │                      │  Proporção  │                  ║
║          └─────────────┘                      │  de Lousada │                  ║
║                                               └─────────────┘                  ║
║                                                                                ║
║   DIFERENÇA PTMA vs PTAC:                                                      ║
║   PTMA = Motivar separado | PTAC = Motivar integrado no Acompanhar             ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

### LIDERANÇA 360° (5 ÁREAS DE VIDA)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LIDERANÇA 360°                                        │
│                    "Líder bom é líder equilibrado"                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                            PROFISSIONAL                                         │
│                                 ▲                                               │
│                                 │                                               │
│                     PESSOAL ◀───┼───▶ FINANCEIRO                                │
│                                 │                                               │
│                     ESPIRITUAL ◀┼▶ EMOCIONAL                                    │
│                                                                                 │
│   "Não adianta ser um monstro no trabalho e um lixo em casa"                    │
│   "O líder que negligencia qualquer área eventualmente paga o preço"            │
│                                                                                 │
│                                               ^[BATCH-125:Liderança360]         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10 CHAVES DA AUTOLIDERANÇA

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    10 CHAVES DA AUTOLIDERANÇA                                   │
│                    "Antes de liderar outros, lidere a si mesmo"                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   1. AUTOCONHECIMENTO    Conhecer forças, fraquezas, gatilhos                   │
│   2. AUTODISCIPLINA      Fazer o que precisa mesmo sem vontade                  │
│   3. AUTOCONTROLE        Dominar reações emocionais                             │
│   4. AUTOMOTIVAÇÃO       Gerar energia interna sem depender de externos         │
│   5. AUTOCONFIANÇA       Acreditar na própria capacidade                        │
│   6. AUTOCRÍTICA         Avaliar-se honestamente sem desculpas                  │
│   7. AUTORRESPONSAB.     Assumir 100% dos resultados                            │
│   8. AUTOAPRENDIZADO     Buscar conhecimento constantemente                     │
│   9. AUTOLIMPEZA         Eliminar hábitos e relações tóxicas                    │
│  10. AUTOEVOLUÇÃO        Estar sempre em versão melhorada                       │
│                                                                                 │
│                                               ^[BATCH-125:Autoliderança]        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4 ETAPAS DO PROCESSO DE COACHING

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PROCESSO DE COACHING (4 ETAPAS)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ETAPA 1: DIAGNÓSTICO                                                          │
│   └── Identificar comportamento atual vs desejado                               │
│   └── Usar dados objetivos (calls, métricas, observação)                        │
│                                                                                 │
│   ETAPA 2: QUESTIONAMENTO                                                       │
│   └── "O que você acha que está causando isso?"                                 │
│   └── "Como você resolveria?"                                                   │
│   └── Deixar o coachee chegar à resposta                                        │
│                                                                                 │
│   ETAPA 3: PLANO DE AÇÃO                                                        │
│   └── Definir 1-3 ações específicas                                             │
│   └── Timeline claro (até quando)                                               │
│   └── Métricas de sucesso                                                       │
│                                                                                 │
│   ETAPA 4: ACOMPANHAMENTO                                                       │
│   └── Check-in regular (não deixar morrer)                                      │
│   └── Ajustar plano se necessário                                               │
│   └── Celebrar wins intermediários                                              │
│                                                                                 │
│                                               ^[BATCH-125:ProcessoCoaching]     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### PROPORÇÃO DE LOUSADA (FEEDBACK CIENTÍFICO)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PROPORÇÃO DE LOUSADA                                         │
│                    (Baseado em pesquisa com times de alta performance)          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ZONA DE PERFORMANCE:                                                          │
│                                                                                 │
│   │ Performance                                                                 │
│   │                        ╭──────╮                                             │
│   │                      ╭╯      ╰╮                                             │
│   │                    ╭╯   ZONA   ╰╮                                           │
│   │                  ╭╯    ÓTIMA    ╰╮                                          │
│   │                ╭╯                ╰╮                                         │
│   │              ╭╯                    ╰╮                                       │
│   │            ╭╯                        ╰────────                              │
│   │      ─────╯                                                                 │
│   └─────┴──────┴───────┴───────┴───────┴──────────▶ Elogios/mês                 │
│         0      3       6       9       12                                       │
│                                                                                 │
│   < 3 elogios/mês   → DESENGAJADO (não se sente visto)                          │
│   3-6 elogios/mês   → SUBÓTIMO (pode melhorar)                                  │
│   7-9 elogios/mês   → ZONA ÓTIMA (peak performance)                             │
│   > 9 elogios/mês   → ACOMODAÇÃO (perde senso de urgência)                      │
│                                                                                 │
│   RATIO IDEAL: 1:3 (negativo:positivo)                                          │
│   "Para cada feedback construtivo, 3 reconhecimentos"                           │
│                                                                                 │
│                                               ^[BATCH-125:ProporçãoLousada]     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 12 PILARES DE RETENÇÃO DE TALENTOS

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    12 PILARES DE RETENÇÃO                                       │
│                    "Reter talento custa 1/3 de contratar novo"                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   FINANCEIRO          DESENVOLVIMENTO          AMBIENTE                         │
│   ───────────         ──────────────           ────────                         │
│   1. Salário justo    5. Carreira clara        9. Cultura forte                 │
│   2. Comissão justa   6. Treinamento           10. Liderança                    │
│   3. Benefícios       7. Desafios novos        11. Reconhecimento               │
│   4. Premiações       8. Autonomia             12. Propósito                    │
│                                                                                 │
│   "Se faltar 1 pilar, talento começa a olhar pro mercado"                       │
│   "Top performers saem primeiro - têm mais opções"                              │
│                                                                                 │
│                                               ^[BATCH-125:12Pilares]            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 9 ESTRATÉGIAS DE TREINAMENTO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    9 ESTRATÉGIAS DE TREINAMENTO                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   1. TREINAMENTO INDIVIDUALIZADO                                                │
│      └── Adaptar ao DISC de cada pessoa                                         │
│                                                                                 │
│   2. ROLE-PLAY / TEATRALIZAÇÃO                                                  │
│      └── Praticar cenários reais em ambiente seguro                             │
│                                                                                 │
│   3. SHADOWING (OBSERVAÇÃO)                                                     │
│      └── Novatos assistem veteranos ao vivo                                     │
│                                                                                 │
│   4. ESTUDO DE CASO                                                             │
│      └── Analisar deals ganhos e perdidos                                       │
│                                                                                 │
│   5. MICROLEARNING                                                              │
│      └── Pílulas de 5-10 min diárias                                            │
│                                                                                 │
│   6. FEEDBACK EM TEMPO REAL                                                     │
│      └── Não esperar 1:1 para corrigir                                          │
│                                                                                 │
│   7. COMPETIÇÃO SAUDÁVEL                                                        │
│      └── Rankings, gamification, premiações                                     │
│                                                                                 │
│   8. MENTORIA ENTRE PARES                                                       │
│      └── Veteranos mentoram novatos                                             │
│                                                                                 │
│   9. CERTIFICAÇÕES INTERNAS                                                     │
│      └── Níveis de proficiência formalizados                                    │
│                                                                                 │
│                                               ^[BATCH-125:9Estratégias]         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### COACHING POR PERFIL DISC

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    COACHING ADAPTADO AO DISC                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   DOMINANTE (D)                                                                 │
│   └── Direto, rápido, foco em resultados                                        │
│   └── "Vamos ao ponto: sua conversão caiu 15%. O que vai mudar?"                │
│   └── Não enrole, não seja emotivo                                              │
│                                                                                 │
│   INFLUENTE (I)                                                                 │
│   └── Entusiástico, reconhecimento, storytelling                                │
│   └── "Cara, você tava VOANDO semana passada! O que aconteceu?"                 │
│   └── Use histórias, celebre wins                                               │
│                                                                                 │
│   ESTÁVEL (S)                                                                   │
│   └── Calmo, passo-a-passo, segurança                                           │
│   └── "Vamos resolver isso juntos. Qual o primeiro passo?"                      │
│   └── Não pressione, dê tempo                                                   │
│                                                                                 │
│   CONSCIENTE (C)                                                                │
│   └── Dados, lógica, detalhes                                                   │
│   └── "Os números mostram X. Aqui está a análise completa."                     │
│   └── Traga evidências, seja preciso                                            │
│                                                                                 │
│                                               ^[BATCH-125:DISC-Coaching]        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### HEURÍSTICAS BATCH-125

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  NÚMEROS QUE IMPORTAM (BATCH-125)                    ^[BATCH-125:Heurísticas]   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  7-9 elogios/mês    Zona ótima de performance (Proporção de Lousada)            │
│  1:3                Ratio negativo:positivo ideal                               │
│  87% / 13%          Comportamental vs técnico em treinamento                    │
│  30 dias            Tempo para saber se vendedor é bom                          │
│  2x meta proposta   Sempre pedir o dobro da meta que quer                       │
│  1/3 do custo       Reter talento vs contratar novo                             │
│  3 ciclos max       Feedback antes de decisão de desligamento                   │
│  5 áreas            Equilíbrio na Liderança 360                                 │
│  10 chaves          Autoliderança antes de liderar outros                       │
│  12 pilares         Retenção completa de talentos                               │
│  4 etapas           Processo de coaching estruturado                            │
│  9 estratégias      Treinamento diversificado                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### FILOSOFIAS BATCH-125

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  FILOSOFIAS LIDERANÇA LUCRATIVA                      ^[BATCH-125:Filosofias]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  "Não adianta ser um monstro no trabalho e um lixo em casa"                     │
│                                                                                 │
│  "Antes de liderar outros, lidere a si mesmo"                                   │
│                                                                                 │
│  "Líder que não delega é líder que não cresce"                                  │
│                                                                                 │
│  "Reter talento custa 1/3 de contratar novo"                                    │
│                                                                                 │
│  "O líder que negligencia qualquer área eventualmente paga o preço"             │
│                                                                                 │
│  "Top performers saem primeiro - têm mais opções"                               │
│                                                                                 │
│  "Se faltar 1 pilar, talento começa a olhar pro mercado"                        │
│                                                                                 │
│  "Para cada feedback construtivo, 3 reconhecimentos"                            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## CROSS-REFERENCES

- **PLAYBOOK-CONTRATACAO.md** → Processo de trazer novos vendedores
- **PLAYBOOK-ONBOARDING.md** → Integração antes da gestão contínua
- **AGENT: SALES-MANAGER** → Agente responsável pela gestão

---

## CHANGELOG

| Versão | Data | Fonte | Mudanças |
|--------|------|-------|----------|
| 1.0.0 | 2026-01-13 | BATCH-050 | Criação inicial - Cole Gordon PTMA |
| 2.0.0 | 2026-01-13 | BATCH-125 | +Liderança Lucrativa, PTAC, 10 Chaves, 12 Pilares, Proporção de Lousada |

---

*Playbook gerado por JARVIS v3.33.0*
*MISSION-2026-001 | Phase 5.7 - Cascateamento*
*Fontes: BATCH-050 (Cole Gordon) + BATCH-125 (Full Sales System)*
*2026-01-13*
