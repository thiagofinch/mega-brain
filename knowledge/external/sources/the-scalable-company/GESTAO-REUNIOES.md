# THE SCALABLE COMPANY / RYAN DEISS: GESTÃO DE REUNIÕES

> **Fonte:** The Scalable Company / Ryan Deiss (consolidação uni-fonte)
> **Tema:** GESTÃO-REUNIOES
> **Última atualização:** 2026-03-16 10:35
> **Documentos fonte:** 2 | **Chunks:** 6 | **Insights:** 3
> **Status:** 🟢 Ativo
> **Pipeline:** MCE v1.0.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SÍNTESE

Ryan Deiss trata reuniões como um problema de design, não de disciplina. Sua posição central é que a maioria das reuniões é desnecessária, e o único antídoto é um sistema de filtros que impede reuniões de serem marcadas sem justificativa real. Meetings têm custo multiplicado pelo número de participantes. O framework Blue Ocean / Black Swan define os únicos critérios legítimos para reuniões de emergência. O processo de 7 passos garante que toda reunião tenha propósito, agenda e owner antes de existir.

**Palavras-chave:** meeting architecture, Blue Ocean, Black Swan, 7-step filter, B&O list, reuniões caras

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## POSIÇÃO CENTRAL

Eu acredito que reuniões são caras e subestimadas em custo. Cada participante adicional multiplica esse custo. A primeira reação de qualquer líder ao querer "resolver um problema" é marcar uma reunião — e isso está errado. O primeiro passo não é enviar o convite do Google Calendar.

O sistema de reuniões tem duas camadas. A primeira é estrutural: reuniões regulares com cadência definida (QSP trimestral, MBR mensal, check-ins semanais, 1:1s). Quando essa cadência está funcionando, reuniões emergenciais são raras. A segunda é operacional: cada reunião tem purpose statement, success definition, agenda com tempos, um owner, e notas distribuídas em 24h.

Para reuniões não-programadas (emergências), existe exatamente um critério: Blue Ocean ou Black Swan. Blue Ocean = oportunidade que cortaria 12+ meses do plano de 3 anos. Black Swan = ameaça que poderia levar o negócio significativamente para trás. Tudo fora disso vai para o B&O list e é discutido na próxima reunião agendada.

**Nuances e condições:**
- Reuniões de check-in semanal: nunca mais de 6 dias sem o time de liderança se tocar
- Reuniões virtuais de QSP: 2-3 meios dias (presencial: 2 dias completos)
- Se estiver em dúvida se é Blue Ocean ou Black Swan: não é. Não convoque.

**Confiança:** ALTA — Frameworks próprios do ScalableOS com métricas de implementação documentadas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FRAMEWORKS E MODELOS

### Blue Ocean / Black Swan Meeting Threshold

**Fonte:** [TSC-0016] How We Do Meetings at Scalable

```
CRITÉRIO PARA CONVOCAR REUNIÃO NÃO-PROGRAMADA
──────────────────────────────────────────────
        ┌─────────────────────────────────────┐
        │                                     │
        │   É Blue Ocean?                     │
        │   → Oportunidade que corta 12+ meses│
        │     do plano de 3 anos?             │
        │                                     │
        │   OU é Black Swan?                  │
        │   → Ameaça que pode levar o negócio │
        │     significativamente para trás?  │
        │                                     │
        └──────────────┬──────────────────────┘
                       │
              SIM ─────┤──── NÃO
               │             │
          Convoca          Coloca na
          reunião          B&O List
         especial         (próxima
                          reunião
                          regular)
```

**Quando usar:** Qualquer decisão sobre convocar reunião fora da cadência regular
**Regra de ouro:** Se duvida se é Blue Ocean ou Black Swan, não é.

---

### 7-Step Meeting Request Process

**Fonte:** [TSC-0016] How We Do Meetings at Scalable

```
PASSOS ANTES DE ENVIAR QUALQUER CONVITE
────────────────────────────────────────
1. Precisa de reunião? (define o que seria "resolver")
2. Quem DEVE estar? (minimum viable list)
3. Cria agenda com tempos
4. Reunião AINDA precisa acontecer? (segundo filtro)
5. Escreve purpose statement + success definition
6. Envia agenda para stakeholders: "precisamos nos reunir?"
7. SE AINDA NECESSÁRIO → envia o convite

REGRA: Passo 1 ≠ Enviar convite do Google
```

**Quando usar:** Toda vez que alguém quiser agendar uma reunião
**Limitações:** Para reuniões regulares já na cadência, passos 4-6 são simplificados

---

### 7 Principles of the Modern Meeting (Arquitetura)

**Fonte:** [TSC-0016] How We Do Meetings at Scalable

```
┌─────────────────────────────────────────────────┐
│  1. Toda reunião tem PURPOSE                    │
│  2. Toda reunião tem AGENDA                     │
│  3. Toda reunião tem OWNER                      │
│  4. Todas as DECISÕES são capturadas            │
│  5. Todo ACTION ITEM tem dono + prazo           │
│  6. Notas distribuídas em 24h                   │
│  7. Reuniões começam e terminam na hora         │
└─────────────────────────────────────────────────┘
```

**Quando usar:** Design de cultura de reuniões, onboarding de liderança
**Relação com 3Ds:** Os 3 Ds (Decide/Discuss/Distribute) são o protocolo de execução dentro desses 7 princípios

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## MÉTRICAS E BENCHMARKS

| Métrica | Valor | Contexto | Chunk |
|---------|-------|----------|-------|
| Máximo de dias sem check-in de liderança | 6 dias | Nunca ultrapassar | [TSC-CH-019] |
| QSP presencial | 2 dias | All-hands follow-up depois | [TSC-CH-016] |
| QSP virtual | 2-3 meios-dias | Equivalente ao presencial | [TSC-CH-016] |
| Blue Ocean threshold | 12+ meses cortados do plano de 3 anos | Critério mínimo para reunião especial | [TSC-CH-017] |
| Distribuição de notas | < 24h após reunião | Padrão ScalableOS | [TSC-CH-021] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## CITAÇÕES-CHAVE

> "The first step is not: send Google invite."
> — [TSC-CH-020] Meeting Architecture, TSC-0016

> "If you're unsure whether it's a blue ocean or a black swan, don't pull that cord."
> — [TSC-CH-018] Blue Ocean / Black Swan threshold, TSC-0016

> "Every attendee raises the cost."
> — [TSC-CH-020] Meeting cost framework, TSC-0016

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## HISTÓRICO DE CONTRIBUIÇÕES

| Data | Documento | Chunks | O que foi adicionado |
|------|-----------|--------|----------------------|
| 2026-03-16 | [TSC-0016] How We Do Meetings at Scalable | 6 | Criação inicial: Blue Ocean/Black Swan, 7-Step Process, 7 Principles — MCE Pipeline v1.0.0 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## LINKS

- **Dossiê Pessoa:** → [DOSSIER-THE-SCALABLE-COMPANY.md](/knowledge/external/dossiers/persons/DOSSIER-THE-SCALABLE-COMPANY.md)
- **Dossiê Tema:** → [DOSSIER-09-GESTAO.md](/knowledge/external/dossiers/themes/DOSSIER-09-GESTAO.md)
- **DNA Framework:** → [FRAMEWORKS.yaml](/knowledge/external/dna/persons/the-scalable-company/FRAMEWORKS.yaml)
- **Documentos Originais:**
  - [TSC-0016] → knowledge/external/sources/the-scalable-company/raw/[TSC-0016] 02 How We Do Meetings at Scalable - YouTube.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                           FIM DO ARQUIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
