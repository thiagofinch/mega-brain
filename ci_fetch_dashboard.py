#!/usr/bin/env python3
"""
CI Dashboard Fetcher — runs in GitHub Actions
Reads credentials from env vars, refreshes ML token, fetches data,
writes dashboard-data.json, updates ML_REFRESH_TOKEN secret.
"""

import json
import os
import requests
import subprocess
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

SELLER_ID = "694166791"
OUTPUT_PATH = Path("dashboard-data.json")

# ── 1. Credentials from env vars ──────────────────────────────────────────────
CLIENT_ID     = os.environ["ML_CLIENT_ID"]
CLIENT_SECRET = os.environ["ML_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["ML_REFRESH_TOKEN"]
GH_PAT        = os.environ.get("GH_PAT", "")
GH_REPO       = os.environ.get("GH_REPO", "")


# ── 2. Refresh ML access token ─────────────────────────────────────────────────
def refresh_ml_token():
    resp = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"❌ Token refresh failed: {resp.status_code} {resp.text[:200]}")
        sys.exit(1)

    data = resp.json()
    access_token   = data["access_token"]
    new_refresh    = data.get("refresh_token", REFRESH_TOKEN)
    print(f"✅ Token refreshed. Expires in {data.get('expires_in', '?')}s")
    return access_token, new_refresh


# ── 3. Update GitHub Secret (so next run still works) ─────────────────────────
def update_gh_secret(new_refresh_token):
    if not GH_PAT or not GH_REPO:
        print("⚠️  GH_PAT or GH_REPO not set — skipping secret update")
        return
    try:
        result = subprocess.run(
            ["gh", "secret", "set", "ML_REFRESH_TOKEN",
             "--body", new_refresh_token,
             "--repo", GH_REPO],
            env={**os.environ, "GH_TOKEN": GH_PAT},
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            print("✅ ML_REFRESH_TOKEN secret updated")
        else:
            print(f"⚠️  Secret update error: {result.stderr[:100]}")
    except Exception as e:
        print(f"⚠️  Secret update exception: {e}")


# ── 4. Fetch orders ────────────────────────────────────────────────────────────
def fetch_orders(token, date_from, max_offset=500):
    headers = {"Authorization": f"Bearer {token}"}
    all_orders, offset, limit = [], 0, 50
    while offset <= max_offset:
        url = (
            f"https://api.mercadolibre.com/orders/search"
            f"?seller={SELLER_ID}&order.date_created.from={date_from}"
            f"&limit={limit}&offset={offset}"
        )
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        d = r.json()
        results = d.get("results", [])
        all_orders.extend(results)
        total = d.get("paging", {}).get("total", 0)
        offset += limit
        if not results or offset >= total:
            break
    return all_orders


# ── 5. Compute KPIs (same logic as local script) ──────────────────────────────
def compute_kpis(orders_today, orders_week):
    paid_today = [o for o in orders_today if o.get("status") == "paid"]
    total_vendas = len(paid_today)
    faturamento  = sum(o.get("total_amount", 0) for o in paid_today)
    ticket_medio = faturamento / total_vendas if total_vendas else 0
    margem_pct   = 0.15
    lucro_bruto  = faturamento * margem_pct
    lucro_por_pedido = lucro_bruto / total_vendas if total_vendas else 0

    product_sales  = defaultdict(lambda: {"vendas": 0, "faturamento": 0, "title": ""})
    category_sales = defaultdict(lambda: {"vendas": 0, "faturamento": 0})

    for o in paid_today:
        for item in o.get("order_items", []):
            title = item.get("item", {}).get("title", "Desconhecido")[:50]
            qty   = item.get("quantity", 1)
            price = item.get("unit_price", 0)
            rev   = qty * price
            pid   = item.get("item", {}).get("id", title)

            product_sales[pid]["title"]       = title
            product_sales[pid]["vendas"]      += qty
            product_sales[pid]["faturamento"] += rev

            t = title.lower()
            if any(w in t for w in ["infantil", "criança", "bebê", "kids"]):
                cat = "Vestuário Infantil"
            elif any(w in t for w in ["moletom", "camiseta", "calça", "blusa", "conjunto", "camisa", "short", "vestido"]):
                cat = "Vestuário Adult"
            elif any(w in t for w in ["carteira", "cinto", "bolsa", "mochila", "acessório", "kit"]):
                cat = "Acessórios"
            else:
                cat = "Outros"

            category_sales[cat]["vendas"]      += qty
            category_sales[cat]["faturamento"] += rev

    top5 = sorted(product_sales.values(), key=lambda x: x["faturamento"], reverse=True)[:5]
    for p in top5:
        p["lucro"]       = round(p["faturamento"] * margem_pct, 2)
        p["faturamento"] = round(p["faturamento"], 2)
        p["score"]       = min(99, max(70, int(80 + p["vendas"] * 2)))

    days_data = defaultdict(lambda: {"vendas": 0, "faturamento": 0})
    for o in orders_week:
        if o.get("status") != "paid":
            continue
        date_str = o.get("date_created", "")[:10]
        days_data[date_str]["vendas"]      += 1
        days_data[date_str]["faturamento"] += o.get("total_amount", 0)

    today_dt    = datetime.now().date()
    day_names   = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    chart_labels, chart_vendas, chart_fat = [], [], []
    for i in range(6, -1, -1):
        d = today_dt - timedelta(days=i)
        chart_labels.append(f"{day_names[d.weekday()]} ({d.day:02d})")
        chart_vendas.append(days_data[str(d)]["vendas"])
        chart_fat.append(round(days_data[str(d)]["faturamento"], 2))

    vendas_semana     = sum(1 for o in orders_week if o.get("status") == "paid")
    faturamento_semana = sum(o.get("total_amount", 0) for o in orders_week if o.get("status") == "paid")

    cats_sorted = sorted(category_sales.items(), key=lambda x: x[1]["faturamento"], reverse=True)
    categories  = [
        {"nome": n, "vendas": v["vendas"],
         "faturamento": round(v["faturamento"], 2),
         "pct": round(v["faturamento"] / faturamento * 100, 1) if faturamento else 0}
        for n, v in cats_sorted
    ]

    return {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "kpis": {
            "faturamento_hoje":   round(faturamento, 2),
            "vendas_hoje":        total_vendas,
            "ticket_medio":       round(ticket_medio, 2),
            "lucro_bruto":        round(lucro_bruto, 2),
            "margem_pct":         margem_pct * 100,
            "lucro_por_pedido":   round(lucro_por_pedido, 2),
            "vendas_semana":      vendas_semana,
            "faturamento_semana": round(faturamento_semana, 2),
        },
        "top5":       top5,
        "categories": categories,
        "chart":      {"labels": chart_labels, "vendas": chart_vendas, "faturamento": chart_fat},
        "meta":       {"seller_id": SELLER_ID, "source": "MercadoLivre API v1 — LIVE via GitHub Actions"},
    }


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')} UTC] Starting dashboard refresh...")

    access_token, new_refresh = refresh_ml_token()

    if new_refresh != REFRESH_TOKEN:
        update_gh_secret(new_refresh)

    today    = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")

    print("Fetching today's orders...")
    orders_today = fetch_orders(access_token, f"{today}T00:00:00.000-03:00")
    print(f"  {len(orders_today)} orders today")

    print("Fetching week orders...")
    orders_week = fetch_orders(access_token, f"{week_ago}T00:00:00.000-03:00", max_offset=700)
    print(f"  {len(orders_week)} orders this week")

    data = compute_kpis(orders_today, orders_week)
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    k = data["kpis"]
    print(f"✅ Vendas: {k['vendas_hoje']} | Fat: R$ {k['faturamento_hoje']:,.2f} | Lucro: R$ {k['lucro_bruto']:,.2f}")
    print(f"✅ Written: {OUTPUT_PATH}")
