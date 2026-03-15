# DOSSIER -- IP PROTECTION

> **Tipo:** Tema (Cross-meeting)
> **Meetings:** MEET-0097, MEET-0098
> **Ultima atualizacao:** 2026-03-14
> **Versao:** 1.0.0

---

## Definicao

Estrategias e mecanismos para proteger propriedade intelectual (IP) do ecossistema AIOX/Syntra/Allfluence. Inclui protecao de codigo, metodologias, e dados de negocio contra copia, engenharia reversa, e vazamento nao intencional.

---

## Consensos

1. **IP esta exposto e precisa de protecao urgente.** Alan: "to louco para esconder tudo." Todos reconhecem o problema. ^[MEET-0098 Tensao 3]

2. **Decoy paths como primeira camada.** Caminhos falsos que parecem parte do sistema mas levam a lugar nenhum. Motor fica em caixa preta. Engenharia reversa nao funciona. ^[chunk_MEET-0097_020, chunk_MEET-0097_028]

3. **Syntra nao tera livro.** Pedro nao publicara sobre a metodologia porque qualquer pessoa poderia replicar como base de Squad. ^[chunk_MEET-0098_019, chunk_MEET-0098_010]

4. **Narrativa protegida.** Dados de negocio nao podem ser alterados automaticamente. Mudancas precisam de confirmacao humana. ^[chunk_MEET-0098_009, chunk_MEET-0098_014]

---

## Divergencias

1. **Nivel de protecao:**
   - **Pedro:** Registro formal de IP + nao publicacao + monetizacao via exclusividade. Approach legal e estrutural.
   - **Alan:** Decoy paths + "caixa preta" + repo limpo com dados minimos. Approach tecnico e de obscuridade.
   - Nao ha conflito direto -- abordagens complementares. Mas Pedro e mais rigoroso e formal.

2. **Exposicao no evento:**
   - **Thiago:** "Muito arriscado" ter tudo funcionando via terminal para 20+ pessoas. Risco de exposicao.
   - **Alan:** Quer mostrar o maximo possivel para impressionar. Precisa de plano de contingencia.
   ^[MEET-0098 Tensao 2]

---

## Decisoes Tomadas

| # | Decisao | Meeting | Status |
|---|---------|---------|--------|
| 1 | Protecao Enterprise via decoy paths | MEET-0097 | CONFIRMADA |
| 2 | Syntra = IP protegido, distribuido via parcerias por nicho | MEET-0098 | CONFIRMADA |
| 3 | Alan cria repo limpo com apenas 6 squads (dados minimos) | MEET-0098 | CONFIRMADA |
| 4 | Modo Enterprise com caminhos inertes para quem nao tem acesso | MEET-0097 | CONFIRMADA |

---

## Open Loops

1. **Mecanismo formal de protecao** alem de decoy paths -- Nao definido. Registro de patente? Contrato de NDA para evento?
2. **Definicao de o que e Enterprise vs Community** -- Separacao clara entre features livres e protegidas.
3. **Plano de contingencia para vazamento** -- O que acontece se alguem copiar? Sem plano definido.
4. **Claudio como ponte para registro formal** -- Em andamento mas sem confirmacao de escopo.

---

## Evolucao Temporal

```
MEET-0097 (Equipe completa)
├── Problema surfaceado: como proteger modo Enterprise
├── Solucao tatica: decoy paths (bomba de fumaca)
├── Alan assume ownership da protecao
└── Risco: complexidade adicional pode confundir o proprio time

MEET-0098 (Alan + Thiago + Pedro)
├── Pedro traz abordagem mais madura: registro IP + nao publicar livro
├── Modelo de monetizacao via nichos (nao via venda aberta)
├── Alan cria repo limpo como protecao pratica para evento
└── Gap: nenhum NDA ou contrato formal para participantes do evento
```
