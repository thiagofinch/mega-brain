---
description: Como realizar análise avançada de vendas com o Agente CRO
---

# WORKFLOW: Análise Avançada de Vendas (CRO)

Este workflow permite que o JARVIS acione o Agente CRO para uma leitura profunda dos dados de venda.

## Passos:

1. **Ativação:**
   O usuário solicita uma análise de vendas ou usa o comando `/analyze-sales`.

2. **Ingestão de Dados:**
   // turbo
   O JARVIS executa o script `python3 scripts/analyze-sales.py`.

3. **Interpretação (CRO):**
   O Agente CRO recebe o relatório bruto e aplica suas heurísticas (DNA-CONFIG) para extrair insights sobre:
   - Performance de produtos (Hero Products).
   - Comportamento de horário (Peak Hours).
   - Eficiência de faturamento (Ticket Médio).

4. **Entrega:**
   O JARVIS apresenta o relatório formatado com as recomendações do CRO.

---
*Mega Brain - CRO Intelligence System*
