import os
import requests
import json
from datetime import datetime
from pathlib import Path
import sys

token_state_path = Path("/Users/kennydwillker/Documents/GitHub/Thiago Finch/AIOX-GPS/.claude/mission-control/ML-TOKEN-STATE.json")
with open(token_state_path, 'r') as f:
    state = json.load(f)
    default_user = state.get("default_user_id", "694166791")
    token = state.get("accounts", {}).get(default_user, {}).get("access_token")
    if not token:
        print(f"❌ Token not found for user {default_user}")
        sys.exit(1)

seller_id = "694166791"
# Dynamic date_from: today at 00:00:00
today_str = datetime.now().strftime('%Y-%m-%d')
date_from = f"{today_str}T00:00:00.000-03:00"

url = f"https://api.mercadolibre.com/orders/search?seller={seller_id}&order.date_created.from={date_from}&limit=50"
headers = {"Authorization": f"Bearer {token}"}

resp = requests.get(url, headers=headers)
if resp.status_code != 200:
    print(f"Error fetching orders: {resp.status_code}")
    sys.exit(1)

orders = resp.json().get("results", [])
total_vendas = 0
count_vendas = 0

print(f"\n📊 RELATÓRIO DE VENDAS - {datetime.now().strftime('%d/%m/%Y')}")
print("="*60)

detailed_orders = []

for order in orders:
    order_id = order.get("id")
    # Fetch full order details to get items
    order_detail_resp = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=headers)
    if order_detail_resp.status_code == 200:
        o = order_detail_resp.json()
        items = o.get("order_items", [])
        title = items[0].get("item", {}).get("title", "Produto sem título") if items else "N/A"
        amount = o.get("total_amount", 0)
        status = o.get("status")
        date_str = o.get("date_created")
        
        # Only count paid or finalized
        if status in ["paid", "shipped", "delivered"]:
            total_vendas += amount
            count_vendas += 1
        
        detailed_orders.append({
            "id": order_id,
            "title": title[:40],
            "amount": amount,
            "status": status,
            "date": date_str[11:16]
        })

# Sort by date
detailed_orders.sort(key=lambda x: x["date"])

for d in detailed_orders:
    status_icon = "✅" if d["status"] == "paid" else "❌" if d["status"] == "cancelled" else "⏳"
    print(f"{d['date']} | {status_icon} | R$ {d['amount']:>8.2f} | {d['title']}")

print("="*60)
print(f"TOTAL DE PEDIDOS: {len(detailed_orders)}")
print(f"PEDIDOS PAGOS:    {count_vendas}")
print(f"VALOR TOTAL:      R$ {total_vendas:,.2f}")
print("="*60 + "\n")
