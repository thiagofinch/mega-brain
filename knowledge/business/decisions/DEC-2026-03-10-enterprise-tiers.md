# DEC-2026-03-10 — Enterprise Tier Separation & IP Protection

> **Data:** 2026-03-10
> **Meeting:** MEET-0095
> **Decisores:** Alan Nicolas, Pedro Valerio Lopez
> **Status:** CONFIRMADA (parcial — deploy path ainda em exploração)

---

## Decisão Principal

Separar AIOX em 3 tiers com níveis distintos de acesso ao workspace e inteligência de dados:

1. **Community (Free):** Squad Creator base, open source
2. **Pro (~R$80/mês):** Squad Pro com dados via banco (sem workspace local)
3. **Enterprise (High-ticket):** Workspace completo + Synapse + implementação

---

## Justificativa

- Workspace é o core IP do AIOX (meses de trabalho, 100M+ tokens investidos)
- Entregar workspace no Pro/Community = "jogar pérolas aos porcos"
- Comunidade GitHub tende a fazer engenharia reversa, não pagar
- High-ticket implementation (R$180k referência) > SaaS recurrence para IP de alto valor

---

## Implicações

| Área | Impacto |
|------|---------|
| Produto | Workspace precisa ser extraído do CLI e virar serviço |
| Infra | Banco de dados na nuvem para Pro, API para Enterprise |
| Evento | Alunos da imersão (R$16k) recebem Enterprise temporário |
| Comercial | Modelo de implementação high-ticket para Enterprise |
| Dev | 3 deploy paths em pesquisa (Pedro) |

---

## Sub-decisões

| # | Decisão | Confiança |
|---|---------|-----------|
| 1 | Squad Creator base → Community (free) | EM DÚVIDA |
| 2 | Squad Creator Pro → só turma avançada | CONFIRMADA |
| 3 | Synapse → nunca open source | CONFIRMADA |
| 4 | Deploy: pesquisa paralela de 3 paths | EXPLORATÓRIO |

---

## Pendências

- [ ] Definir MVP de deploy (qual dos 3 paths)
- [ ] Definir escopo exato do que vai para o evento
- [ ] Criar banco de dados para Enterprise
- [ ] Separar Squad Creator versões (Community vs Pro)
