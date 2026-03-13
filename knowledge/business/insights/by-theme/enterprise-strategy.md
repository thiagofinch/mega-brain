# Enterprise Strategy — Theme Dossier

> **Versão:** 1.0.0
> **Criado:** 2026-03-12
> **Meetings:** MEET-0095
> **Batch:** BATCH-129

---

## Definição

Estratégia de produto e monetização do AIOX Enterprise — o tier mais alto do Squad Creator, que inclui workspace completo, Synapse, context engineering avançado, e implementação high-ticket.

---

## Arquitetura Enterprise

### Workspace (Fonte da Verdade)
- C-Level cerebral: CEO, CIO, CMO, CRO, COO, CFO
- CIO orquestra gestão do workspace
- Templates por área baseados em modelos estratégicos
- Multi-negócio (switch via comando)
- Taxonomias universais (entidades, glossário, workflows)

### Context Engineering (Runtime Loading)
- Script carrega: empresa, produto, campanha, status, operation notes
- Referências pré-carregadas: SAP, brand book, posicionamento, offerbook, provas
- Agente inicia PRONTO — otimizado para economia de tokens

### Enterprise Activation Flow
- Detecta: C-Level + workspace instalado + licença ativa
- Com workspace → busca direta nos dados
- Sem workspace → fallback para docs/ (funciona, sem inteligência)

---

## Tier Strategy

| Tier | Preço | Inclui | Workspace |
|------|-------|--------|-----------|
| Community | Free | Squad Creator base | NÃO |
| Pro | ~R$80/mês | Squad Pro + banco de dados | NÃO (dados via API) |
| Enterprise | High-ticket | Workspace + Synapse + implementação | SIM (completo) |

### Referência de Preço Enterprise
- Contrato 16h: R$180k (case citado na reunião)
- Imersão: R$16k/cabeça (acesso temporário ao Enterprise)

---

## IP Protection Strategy

### O Que Proteger
1. **Workspace architecture** — taxonomias, templates, context engineering
2. **Synapse** — mapeamento de processos
3. **Data extraction intelligence** — como dados são modelados e extraídos
4. **SOP certification** — pipeline de criação/validação de SOPs

### Como Proteger
- Migrar de CLI (código local) para serviço (API/Black Box)
- Banco de dados na nuvem — agentes buscam dados via API
- Cliente recebe output, não vê estrutura interna
- 3 deploy paths em pesquisa: Node.js online, Claude Container, OpenClaw

---

## Fontes

- [MEET-0095] 2026-03-10 — Squad Creator Enterprise call
