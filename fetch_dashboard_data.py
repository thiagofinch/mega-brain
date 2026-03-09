#!/usr/bin/env python3
"""
JARVIS Dashboard Data Fetcher
Fetches live data from MercadoLivre API and writes dashboard-data.json
Run: python3 fetch_dashboard_data.py
Auto-refresh: python3 fetch_dashboard_data.py --watch (loop every 60s)
"""

import json
import requests
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

TOKEN_PATH = Path(__file__).parent / ".claude/mission-control/ML-TOKEN-STATE.json"
OUTPUT_PATH = Path(__file__).parent / "dashboard-data.json"
SELLER_ID = "694166791"


def load_token():
    d = json.loads(TOKEN_PATH.read_text())
    return d["accounts"][SELLER_ID]["access_token"]


def fetch(url, headers):
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_orders_today(token):
    headers = {"Authorization": f"Bearer {token}"}
    today = datetime.now().strftime("%Y-%m-%d")
    date_from = f"{today}T00:00:00.000-03:00"

    all_orders = []
    offset = 0
    limit = 50
    while True:
        url = (
            f"https://api.mercadolibre.com/orders/search"
            f"?seller={SELLER_ID}"
            f"&order.date_created.from={date_from}"
            f"&limit={limit}&offset={offset}"
        )
        data = fetch(url, headers)
        results = data.get("results", [])
        all_orders.extend(results)
        total = data.get("paging", {}).get("total", 0)
        offset += limit
        if offset >= total or not results:
            break

    return all_orders


def fetch_orders_week(token):
    """Fetch last 7 days orders for chart"""
    headers = {"Authorization": f"Bearer {token}"}
    week_ago = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    date_from = f"{week_ago}T00:00:00.000-03:00"

    all_orders = []
    offset = 0
    limit = 50
    while True:
        url = (
            f"https://api.mercadolibre.com/orders/search"
            f"?seller={SELLER_ID}"
            f"&order.date_created.from={date_from}"
            f"&limit={limit}&offset={offset}"
        )
        data = fetch(url, headers)
        results = data.get("results", [])
        all_orders.extend(results)
        total = data.get("paging", {}).get("total", 0)
        offset += limit
        if offset >= total or not results or offset > 500:
            break

    return all_orders


def compute_kpis(orders_today, orders_week):
    # --- TODAY ---
    paid_today = [o for o in orders_today if o.get("status") == "paid"]
    total_vendas = len(paid_today)
    faturamento = sum(o.get("total_amount", 0) for o in paid_today)
    ticket_medio = faturamento / total_vendas if total_vendas > 0 else 0

    # Margem estimada (vestuário ~15%)
    margem_pct = 0.15
    lucro_bruto = faturamento * margem_pct
    lucro_por_pedido = lucro_bruto / total_vendas if total_vendas > 0 else 0

    # --- PRODUCTS ---
    product_sales = defaultdict(lambda: {"vendas": 0, "faturamento": 0, "title": ""})
    category_sales = defaultdict(lambda: {"vendas": 0, "faturamento": 0})

    for o in paid_today:
        for item in o.get("order_items", []):
            title = item.get("item", {}).get("title", "Desconhecido")[:50]
            qty = item.get("quantity", 1)
            unit_price = item.get("unit_price", 0)
            revenue = qty * unit_price
            pid = item.get("item", {}).get("id", title)

            product_sales[pid]["title"] = title
            product_sales[pid]["vendas"] += qty
            product_sales[pid]["faturamento"] += revenue

            # Simple category detection
            title_lower = title.lower()
            if any(w in title_lower for w in ["infantil", "criança", "bebê", "kids"]):
                cat = "Vestuário Infantil"
            elif any(w in title_lower for w in ["moletom", "camiseta", "calça", "blusa", "conjunto", "camisa", "short", "vestido"]):
                cat = "Vestuário Adult"
            elif any(w in title_lower for w in ["carteira", "cinto", "bolsa", "mochila", "acessório", "kit"]):
                cat = "Acessórios"
            else:
                cat = "Outros"

            category_sales[cat]["vendas"] += qty
            category_sales[cat]["faturamento"] += revenue

    top5 = sorted(product_sales.values(), key=lambda x: x["faturamento"], reverse=True)[:5]
    for p in top5:
        p["lucro"] = round(p["faturamento"] * margem_pct, 2)
        p["faturamento"] = round(p["faturamento"], 2)
        p["score"] = min(99, max(70, int(80 + p["vendas"] * 2)))

    # --- WEEK CHART ---
    days_data = defaultdict(lambda: {"vendas": 0, "faturamento": 0})
    for o in orders_week:
        if o.get("status") != "paid":
            continue
        date_str = o.get("date_created", "")[:10]
        days_data[date_str]["vendas"] += 1
        days_data[date_str]["faturamento"] += o.get("total_amount", 0)

    today_dt = datetime.now().date()
    chart_labels = []
    chart_vendas = []
    chart_faturamento = []
    day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    for i in range(6, -1, -1):
        d = today_dt - timedelta(days=i)
        label = f"{day_names[d.weekday()]} ({d.day:02d})"
        chart_labels.append(label)
        chart_vendas.append(days_data[str(d)]["vendas"])
        chart_faturamento.append(round(days_data[str(d)]["faturamento"], 2))

    # --- WEEK TOTALS ---
    vendas_semana = sum(1 for o in orders_week if o.get("status") == "paid")
    faturamento_semana = sum(o.get("total_amount", 0) for o in orders_week if o.get("status") == "paid")

    # --- CATEGORIES ---
    cats_sorted = sorted(category_sales.items(), key=lambda x: x[1]["faturamento"], reverse=True)
    categories = []
    for name, vals in cats_sorted:
        pct = (vals["faturamento"] / faturamento * 100) if faturamento > 0 else 0
        categories.append({
            "nome": name,
            "vendas": vals["vendas"],
            "faturamento": round(vals["faturamento"], 2),
            "pct": round(pct, 1),
        })

    return {
        "updated_at": datetime.now().isoformat(),
        "kpis": {
            "faturamento_hoje": round(faturamento, 2),
            "vendas_hoje": total_vendas,
            "ticket_medio": round(ticket_medio, 2),
            "lucro_bruto": round(lucro_bruto, 2),
            "margem_pct": margem_pct * 100,
            "lucro_por_pedido": round(lucro_por_pedido, 2),
            "vendas_semana": vendas_semana,
            "faturamento_semana": round(faturamento_semana, 2),
        },
        "top5": top5,
        "categories": categories,
        "chart": {
            "labels": chart_labels,
            "vendas": chart_vendas,
            "faturamento": chart_faturamento,
        },
        "meta": {
            "seller_id": SELLER_ID,
            "source": "MercadoLivre API v1 — LIVE",
            "total_orders_fetched": len(orders_today),
        },
    }


def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching live data...")
    token = load_token()

    orders_today = fetch_orders_today(token)
    orders_week = fetch_orders_week(token)

    data = compute_kpis(orders_today, orders_week)
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    kpis = data["kpis"]
    print(f"  ✅ Vendas hoje: {kpis['vendas_hoje']} | Faturamento: R$ {kpis['faturamento_hoje']:,.2f}")
    print(f"  ✅ Lucro bruto: R$ {kpis['lucro_bruto']:,.2f} | Ticket médio: R$ {kpis['ticket_medio']:.2f}")
    print(f"  ✅ Salvo em: {OUTPUT_PATH}")
    return data


if __name__ == "__main__":
    watch = "--watch" in sys.argv
    interval = 60  # seconds

    run()

    if watch:
        print(f"\n👁  Watch mode — refreshing every {interval}s (Ctrl+C to stop)\n")
        while True:
            time.sleep(interval)
            try:
                run()
            except Exception as e:
                print(f"  ⚠️  Error: {e}")
