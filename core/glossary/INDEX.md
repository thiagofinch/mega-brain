# GLOSSÁRIO CENTRAL - MEGA BRAIN

## Propósito

Este glossário garante consistência terminológica em todo o sistema:
- Evita duplicação de agentes/knowledge por sinônimos
- Mapeia variações de termos entre fontes
- Serve como fonte de verdade para definições
- É atualizado automaticamente durante processamento

---

## Domínios Cobertos

| Domínio | Arquivo | Termos |
|---------|---------|--------|
| Vendas | `sales.md` | BDR, SDS, Closer, Sales Manager, etc. |
| Marketing | `marketing.md` | CAC, LTV, Funnel, etc. |
| Operações | `operations.md` | KPIs, SLAs, etc. |
| Financeiro | `finance.md` | Unit Economics, MRR, etc. |
| Geral Digital | `digital.md` | SaaS, B2B, High-ticket, etc. |

---

## Como Usar

### Durante Processamento de Novos Materiais

1. Ao encontrar termo técnico → verificar se existe no glossário
2. Se existe → usar definição padrão, mapear sinônimo se necessário
3. Se não existe → adicionar ao glossário com:
   - Definição
   - Sinônimos conhecidos
   - Fonte onde foi encontrado
   - Distinções importantes (o que NÃO é)

### Ao Criar Novos Agentes

1. Verificar glossário antes de criar
2. Se função já existe com outro nome → NÃO criar duplicata
3. Adicionar ao glossário se termo novo

---

## Log de Atualizações

| Data | Domínio | Termos Adicionados | Fonte |
|------|---------|-------------------|-------|
| 2024-12-14 | Sales | BDR, SDS, Closer, BC, AE, Sales Manager, Sales Lead, Sales Coordinator | SS001, CG001 |

---

## Template para Novo Termo

```markdown
## TERMO / Sinônimo1 / Sinônimo2
- **Domínio**: [Sales/Marketing/Ops/Finance/Digital]
- **Definição**: [O que é]
- **Sinônimos encontrados**: [Lista de variações]
- **NÃO confundir com**: [Termos similares mas diferentes]
- **Fontes**: [Onde foi definido]
- **Agente relacionado**: [Se houver]
```
