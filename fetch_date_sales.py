import os
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Data a buscar (padrão: ontem)
target_date = sys.argv[1] if len(sys.argv) > 1 else (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

token_state_path = Path(".claude/mission-control/ML-TOKEN-STATE.json")
with open(token_state_path, 'r') as f:
    state = json.load(f)
    default_user = state.get("default_user_id", "694166791")
    token = state.get("accounts", {}).get(default_user, {}).get("access_token")
    if not token:
        print(f"❌ Token not found")
        sys.exit(1)

seller_id = "694166791"
date_from = f"{target_date}T00:00:00.000-03:00"
date_to = f"{target_date}T23:59:59.000-03:00"

url = f"https://api.mercadolibre.com/orders/search?seller={seller_id}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50"
headers = {"Authorization": f"Bearer {token}"}

resp = requests.get(url, headers=headers)
if resp.status_code != 200:
    print(f"Error: {resp.status_code}")
    sys.exit(1)

orders = resp.json().get("results", [])
total_faturamento = 0
total_pedidos = len(orders)
produtos = {}

for order in orders:
    order_id = order.get("id")
    order_detail_resp = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=headers)
    if order_detail_resp.status_code == 200:
        o = order_detail_resp.json()
        items = o.get("order_items", [])
        if items:
            title = items[0].get("item", {}).get("title", "Produto")
            if title not in produtos:
                produtos[title] = {"qty": 0, "valor": 0}
            produtos[title]["qty"] += 1
            amount = o.get("total_amount", 0)
            produtos[title]["valor"] += amount
        total_faturamento += o.get("total_amount", 0)

print(f"📊 DADOS REAIS KPI - {target_date}")
print("="*70)
print(f"Total de Pedidos: {total_pedidos}")
print(f"Faturamento Total: R$ {total_faturamento:.2f}")
if total_pedidos > 0:
    print(f"Ticket Médio: R$ {total_faturamento/total_pedidos:.2f}")
    print(f"\nProdutos Vendidos:")
    for prod, data in sorted(produtos.items(), key=lambda x: x[1]["valor"], reverse=True):
        print(f"  • {prod}: {data['qty']} unid x R$ {data['valor']:.2f}")

print("="*70)
