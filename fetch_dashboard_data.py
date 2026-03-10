#!/usr/bin/env python3
"""
JARVIS Dashboard Data Fetcher
Fetches live data from MercadoLivre API and writes dashboard-data.json
Run: python3 fetch_dashboard_data.py
Auto-refresh: python3 fetch_dashboard_data.py --watch (loop every 60s)
"""

import json
import os
import requests
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

TOKEN_PATH = Path(__file__).parent / ".claude/mission-control/ML-TOKEN-STATE.json"
OUTPUT_PATH = Path(__file__).parent / "dashboard-data.json"
SELLER_ID = "694166791"

# ───────────────────────────────────────────────────────────────────────────────
# CI MODE: Support env vars for token refresh (GitHub Actions)
# ───────────────────────────────────────────────────────────────────────────────
ML_CLIENT_ID = os.environ.get("ML_CLIENT_ID")
ML_CLIENT_SECRET = os.environ.get("ML_CLIENT_SECRET")
ML_REFRESH_TOKEN = os.environ.get("ML_REFRESH_TOKEN")
GH_PAT = os.environ.get("GH_PAT", "")
GH_REPO = os.environ.get("GH_REPO", "")

# ---------------------------------------------------------------------------
# CMV Lookup: (keywords_list, manufacturing_cost_per_unit)
# Match is done against the product title (lowercase, first match wins).
# ---------------------------------------------------------------------------
PRODUCT_CMV_LOOKUP = [
    # Infantil
    (["conjunto infantil"],                                              44.91),
    (["moletom infantil", "moletom canguru infantil"],                   26.91),
    (["calça moletom infantil", "calca moletom infantil"],               20.61),
    # Moletons adulto
    (["moletom ziper", "moletom zipper", "moletom de ziper"],           44.99),
    (["moletom canguru"],                                                35.99),
    (["moletom milano"],                                                 34.19),
    (["moletom italia"],                                                 34.19),
    (["moletom paris"],                                                  34.19),
    (["moletom gola careca", "moletom careca"],                          31.49),
    (["moletom"],                                                        35.84),  # fallback avg
    # Shorts / Bermudas
    (["bermuda moletom"],                                                22.49),
    (["short linho"],                                                    17.99),
    (["short tactel"],                                                   17.99),
    (["short estampado"],                                                16.19),
    (["short", "bermuda"],                                               18.67),  # fallback avg
    # Acessórios
    (["porta cartão", "porta cartao"],                                   11.61),
    (["carteira e1"],                                                    21.59),
    (["carteira pocket"],                                                21.59),
    (["carteira", "cinto", "bolsa", "mochila"],                          18.26),  # fallback avg
]

CATEGORY_CMV_FALLBACK = {
    "Vestuário Infantil": 30.81,
    "Vestuário Adult":    35.84,
    "Acessórios":         18.26,
    "Outros":             25.00,
}


# ---------------------------------------------------------------------------
# Token Management
# ---------------------------------------------------------------------------

def refresh_ml_token_ci():
    """Refresh ML token via OAuth (GitHub Actions only)."""
    if not (ML_CLIENT_ID and ML_CLIENT_SECRET and ML_REFRESH_TOKEN):
        return None

    try:
        r = requests.post(
            "https://api.mercadolibre.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": ML_CLIENT_ID,
                "client_secret": ML_CLIENT_SECRET,
                "refresh_token": ML_REFRESH_TOKEN,
            },
            timeout=15,
        )
        if r.status_code != 200:
            print(f"⚠️  Token refresh failed: {r.status_code}")
            return None

        data = r.json()
        access_token = data.get("access_token")
        new_refresh = data.get("refresh_token", ML_REFRESH_TOKEN)

        # Update TOKEN_PATH with new access token
        if TOKEN_PATH.exists():
            token_state = json.loads(TOKEN_PATH.read_text())
            token_state["accounts"][SELLER_ID]["access_token"] = access_token
            TOKEN_PATH.write_text(json.dumps(token_state, indent=2))

        print(f"✅ ML token refreshed (expires in {data.get('expires_in', '?')}s)")
        return access_token
    except Exception as e:
        print(f"⚠️  Token refresh error: {e}")
        return None


def load_token():
    """Load token from JSON file (or refreshed env vars in CI)."""
    # Try CI refresh first
    ci_token = refresh_ml_token_ci()
    if ci_token:
        return ci_token

    # Fallback to JSON file
    d = json.loads(TOKEN_PATH.read_text())
    return d["accounts"][SELLER_ID]["access_token"]


def fetch(url, headers):
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def get_product_cost(title: str, category: str) -> float:
    """Return manufacturing cost per unit based on product title keywords."""
    title_lower = title.lower()
    for keywords, cost in PRODUCT_CMV_LOOKUP:
        if any(kw in title_lower for kw in keywords):
            return cost
    return CATEGORY_CMV_FALLBACK.get(category, 25.00)


def fetch_shipping_cost(shipping_id: int, headers: dict) -> float:
    """Fetch shipping cost charged to the seller for a specific shipment."""
    try:
        r = requests.get(
            f"https://api.mercadolibre.com/shipments/{shipping_id}",
            headers=headers, timeout=10
        )
        r.raise_for_status()
        data = r.json()
        # list_cost = actual charge to seller
        cost = data.get("shipping_option", {}).get("list_cost", 0) or 0
        return float(cost)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# MANUAL ADS DATA FALLBACK (ML API bug workaround)
# Update these values manually from HugoJobs Painel or ClickUp campaigns
# Format: {"date": "YYYY-MM-DD", "product_ads": {...}, "brand_ads": {...}}
# ---------------------------------------------------------------------------

ADS_DATA_MANUAL_OVERRIDE = {
    # TOTAL ATUAL: 7 campanhas Product Ads (R$ 3.243,55) + 2 Brand Ads (R$ 644,71)
    # Data de última atualização: 2026-03-10
    "last_updated": "2026-03-10",
    "total_active_campaigns": {
        "product_ads": 7,
        "brand_ads": 2,
    },
    "total_spend": 3888.26,  # R$ 3.243,55 + R$ 644,71
    "estimated_daily_spend": 370.0,  # rough estimate
    "note": "⚠️ ML API /product_ads/campaigns returns HTTP 200 empty body (bug). Manual override enabled."
}


# ---------------------------------------------------------------------------
# API Fetchers
# ---------------------------------------------------------------------------

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

    # Fetch shipping costs for paid orders
    paid_orders = [o for o in all_orders if o.get("status") == "paid"]
    shipping_costs = {}
    for order in paid_orders:
        shipping_id = order.get("shipping", {}).get("id")
        if shipping_id:
            shipping_costs[order["id"]] = fetch_shipping_cost(shipping_id, headers)
        else:
            shipping_costs[order["id"]] = 0.0

    # Attach shipping cost to each order
    for order in all_orders:
        order["_shipping_cost_seller"] = shipping_costs.get(order["id"], 0.0)

    return all_orders


def fetch_orders_week(token):
    """Fetch last 7 days orders for chart."""
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


def fetch_orders_month(token):
    """Fetch current calendar month orders for monthly chart."""
    headers = {"Authorization": f"Bearer {token}"}
    month_start = datetime.now().strftime("%Y-%m-01")
    date_from = f"{month_start}T00:00:00.000-03:00"

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
        if offset >= total or not results or offset > 2000:
            break

    return all_orders


def fetch_pads_data(token, date_from: str = None, date_to: str = None) -> dict:
    """
    Fetch MercadoLivre PADS (advertising) metrics.

    ⚠️  CRITICAL BUG DISCOVERED (2026-03-10):
    - Endpoint: /advertising/advertisers/{id}/product_ads/campaigns
    - Returns: HTTP 200 OK with Content-Length: 0 (EMPTY BODY)
    - This is a ML API BUG, not an auth issue
    - /brand_ads also broken (HTTP 401)

    WORKAROUND: Use manual override (ADS_DATA_MANUAL_OVERRIDE) when API fails.
    Instructions:
    1. Go to HugoJobs Painel de Vendas → Produtos Anúncios
    2. Extract total gasto, impressões, cliques, atribuído
    3. Update ADS_DATA_MANUAL_OVERRIDE above
    4. Script will use these values until ML API is fixed
    """
    empty = {"ad_spend": 0, "ad_revenue": 0, "ad_impressions": 0, "ad_clicks": 0}

    try:
        headers = {"Authorization": f"Bearer {token}"}

        # === ATTEMPT 1: Try ML API (will likely fail) ===
        candidate_ids = [SELLER_ID, f"MLB{SELLER_ID}", f"MLB:{SELLER_ID}"]
        payload = None

        for adv_id in candidate_ids:
            url = (
                f"https://api.mercadolibre.com/advertising/advertisers"
                f"/{adv_id}/product_ads/campaigns"
            )
            if date_from:
                url += f"?date_from={date_from}"
                if date_to:
                    url += f"&date_to={date_to}"

            try:
                r = requests.get(url, headers=headers, timeout=10)

                if r.status_code == 200 and len(r.content) > 0:
                    payload = r.json()
                    print(f"  ✅ PADS API: Got data from {adv_id!r}")
                    break
                elif r.status_code == 200 and len(r.content) == 0:
                    print(f"  ⚠️  PADS API: HTTP 200 EMPTY (ML bug) — using manual override")
                else:
                    print(f"  ⚠️  PADS API: HTTP {r.status_code}")
            except Exception as e:
                print(f"  ⚠️  PADS request error: {e}")
                continue

        # === FALLBACK: Use manual override if API failed ===
        if payload is None:
            print("  📊 Using ADS_DATA_MANUAL_OVERRIDE (update by hand from painel)")

            # Estimate daily spend based on total_spend
            daily_estimate = ADS_DATA_MANUAL_OVERRIDE.get("estimated_daily_spend", 0)

            return {
                "ad_spend": daily_estimate,
                "ad_revenue": 0,  # Not tracked in manual override
                "ad_impressions": 0,  # Manual override doesn't include these
                "ad_clicks": 0,
                "_note": "Manual override (ML API bug workaround)",
                "_total_spend_all_time": ADS_DATA_MANUAL_OVERRIDE["total_spend"],
                "_last_updated": ADS_DATA_MANUAL_OVERRIDE["last_updated"],
            }

        # === PARSE API RESPONSE (if we got one) ===
        campaigns = []
        if isinstance(payload, list):
            campaigns = payload
        elif isinstance(payload, dict):
            for key in ("campaigns", "results", "data", "items"):
                if key in payload and isinstance(payload[key], list):
                    campaigns = payload[key]
                    break

        ad_spend = 0.0
        ad_revenue = 0.0
        ad_impressions = 0
        ad_clicks = 0

        for c in campaigns:
            if not isinstance(c, dict):
                continue
            ad_spend += float(
                c.get("spend", 0) or c.get("cost", 0)
                or c.get("total_cost", 0) or c.get("total_spend", 0) or 0
            )
            ad_revenue += float(
                c.get("attributed_revenue", 0) or c.get("revenue", 0)
                or c.get("total_revenue", 0) or c.get("attributed_sales", 0) or 0
            )
            ad_impressions += int(
                c.get("impressions", 0) or c.get("total_impressions", 0) or 0
            )
            ad_clicks += int(
                c.get("clicks", 0) or c.get("total_clicks", 0) or 0
            )

        print(f"  ✅ PADS parsed: spend={ad_spend}, impressions={ad_impressions}")

        return {
            "ad_spend": round(ad_spend, 2),
            "ad_revenue": round(ad_revenue, 2),
            "ad_impressions": ad_impressions,
            "ad_clicks": ad_clicks,
        }

    except Exception as e:
        print(f"  ⚠️  PADS error: {e} — using manual override")
        return {**empty, "_error": str(e)}


# ---------------------------------------------------------------------------
# Period Helpers
# ---------------------------------------------------------------------------

def compute_period_totals(orders):
    """Compute aggregate KPIs for a period. No shipping detail (performance)."""
    paid = [o for o in orders if o.get("status") == "paid"]
    vendas = len(paid)
    faturamento = sum(o.get("total_amount", 0) for o in paid)
    taxa_ml = sum(
        item.get("sale_fee", 0) or 0
        for o in paid
        for item in o.get("order_items", [])
    )
    return {
        "vendas": vendas,
        "faturamento": round(faturamento, 2),
        "taxa_ml": round(taxa_ml, 2),
        "faturamento_menos_taxa": round(faturamento - taxa_ml, 2),
        "ticket_medio": round(faturamento / vendas, 2) if vendas > 0 else 0,
    }


def compute_month_chart(orders_month):
    """Build daily chart data for the current calendar month."""
    days_data = defaultdict(lambda: {"vendas": 0, "faturamento": 0})
    for o in orders_month:
        if o.get("status") != "paid":
            continue
        date_str = o.get("date_created", "")[:10]
        days_data[date_str]["vendas"] += 1
        days_data[date_str]["faturamento"] += o.get("total_amount", 0)

    today_dt = datetime.now().date()
    month_start = today_dt.replace(day=1)
    day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    labels = []
    vendas = []
    faturamento = []

    current = month_start
    while current <= today_dt:
        label = f"{day_names[current.weekday()]} ({current.day:02d})"
        labels.append(label)
        vendas.append(days_data[str(current)]["vendas"])
        faturamento.append(round(days_data[str(current)]["faturamento"], 2))
        current += timedelta(days=1)

    return {
        "labels": labels,
        "vendas": vendas,
        "faturamento": faturamento,
    }


# ---------------------------------------------------------------------------
# KPI Computation
# ---------------------------------------------------------------------------

def compute_kpis(orders_today, orders_week, pads_data):
    # --- TODAY ---
    paid_today = [o for o in orders_today if o.get("status") == "paid"]
    total_vendas = len(paid_today)
    faturamento = sum(o.get("total_amount", 0) for o in paid_today)
    ticket_medio = faturamento / total_vendas if total_vendas > 0 else 0

    # --- PRODUCTS with real CMV ---
    product_sales = defaultdict(
        lambda: {"vendas": 0, "faturamento": 0, "custo": 0, "title": "", "taxa_ml": 0}
    )
    category_sales = defaultdict(
        lambda: {"vendas": 0, "faturamento": 0, "custo": 0, "taxa_ml": 0}
    )

    for o in paid_today:
        for item in o.get("order_items", []):
            title = item.get("item", {}).get("title", "Desconhecido")[:50]
            qty = item.get("quantity", 1)
            unit_price = item.get("unit_price", 0)
            revenue = qty * unit_price
            pid = item.get("item", {}).get("id", title)

            # ML fee fields from bulk search (zero extra calls)
            sale_fee = item.get("sale_fee", 0) or 0
            full_unit_price = item.get("full_unit_price", unit_price)

            # Category detection
            title_lower = title.lower()
            if any(w in title_lower for w in ["infantil", "criança", "bebê", "kids"]):
                cat = "Vestuário Infantil"
            elif any(w in title_lower for w in ["moletom", "camiseta", "calça", "blusa",
                                                  "conjunto", "camisa", "short", "vestido"]):
                cat = "Vestuário Adult"
            elif any(w in title_lower for w in ["carteira", "cinto", "bolsa", "mochila",
                                                  "acessório", "kit", "porta cartão",
                                                  "porta cartao"]):
                cat = "Acessórios"
            else:
                cat = "Outros"

            # Real CMV per unit
            unit_cost = get_product_cost(title, cat)
            total_cost = unit_cost * qty

            product_sales[pid]["title"] = title
            product_sales[pid]["vendas"] += qty
            product_sales[pid]["faturamento"] += revenue
            product_sales[pid]["custo"] += total_cost
            product_sales[pid]["taxa_ml"] += sale_fee * qty
            product_sales[pid]["full_unit_price"] = full_unit_price

            category_sales[cat]["vendas"] += qty
            category_sales[cat]["faturamento"] += revenue
            category_sales[cat]["custo"] += total_cost
            category_sales[cat]["taxa_ml"] += sale_fee * qty

    # --- AGGREGATE CMV & MARGIN (gross) ---
    cmv_total = sum(ps["custo"] for ps in product_sales.values())
    lucro_bruto = faturamento - cmv_total
    margem_pct_real = (lucro_bruto / faturamento * 100) if faturamento > 0 else 0
    lucro_por_pedido = lucro_bruto / total_vendas if total_vendas > 0 else 0

    # --- ML FEES & SHIPPING (net P&L) ---
    taxa_ml_total = sum(ps.get("taxa_ml", 0) for ps in product_sales.values())
    shipping_total = sum(o.get("_shipping_cost_seller", 0) for o in paid_today)

    # Net revenue = gross revenue - ML fees - shipping cost to seller
    faturamento_liquido = faturamento - taxa_ml_total - shipping_total
    margem_liquida_pct = (
        (faturamento_liquido - cmv_total) / faturamento * 100
        if faturamento > 0 else 0
    )
    lucro_liquido = faturamento_liquido - cmv_total

    # --- ADS METRICS ---
    ad_spend = pads_data.get("ad_spend", 0)
    ad_revenue = pads_data.get("ad_revenue", 0)
    organic_revenue = max(0.0, faturamento - ad_revenue)
    acos = round(ad_spend / ad_revenue * 100, 1) if ad_revenue > 0 else 0
    tacos = round(ad_spend / faturamento * 100, 1) if faturamento > 0 else 0

    # --- TOP 5 PRODUCTS ---
    top5 = sorted(product_sales.values(), key=lambda x: x["faturamento"], reverse=True)[:5]
    for p in top5:
        p["faturamento"] = round(p["faturamento"], 2)
        p["custo"] = round(p.get("custo", p["faturamento"] * 0.30), 2)
        p["taxa_ml"] = round(p.get("taxa_ml", 0), 2)
        p["lucro"] = round(p["faturamento"] - p["custo"], 2)
        p["margem_pct"] = (
            round(p["lucro"] / p["faturamento"] * 100, 1)
            if p["faturamento"] > 0 else 0
        )
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
    faturamento_semana = sum(
        o.get("total_amount", 0) for o in orders_week if o.get("status") == "paid"
    )

    # --- CATEGORIES ---
    cats_sorted = sorted(
        category_sales.items(), key=lambda x: x[1]["faturamento"], reverse=True
    )
    categories = []
    for name, vals in cats_sorted:
        fat = vals["faturamento"]
        custo = vals.get("custo", 0)
        pct = (fat / faturamento * 100) if faturamento > 0 else 0
        margem_cat = ((fat - custo) / fat * 100) if fat > 0 else 0
        categories.append({
            "nome": name,
            "vendas": vals["vendas"],
            "faturamento": round(fat, 2),
            "custo": round(custo, 2),
            "taxa_ml": round(vals.get("taxa_ml", 0), 2),
            "pct": round(pct, 1),
            "margem_pct": round(margem_cat, 1),
        })

    return {
        "updated_at": datetime.now().isoformat(),
        "kpis": {
            "faturamento_hoje": round(faturamento, 2),
            "vendas_hoje": total_vendas,
            "ticket_medio": round(ticket_medio, 2),
            # Real CMV-based gross margin
            "cmv_total": round(cmv_total, 2),
            "lucro_bruto": round(lucro_bruto, 2),
            "margem_pct_real": round(margem_pct_real, 1),
            "lucro_por_pedido": round(lucro_por_pedido, 2),
            # ML fees & net P&L
            "taxa_ml_total": round(taxa_ml_total, 2),
            "shipping_total": round(shipping_total, 2),
            "faturamento_liquido": round(faturamento_liquido, 2),
            "margem_liquida_pct": round(margem_liquida_pct, 1),
            "lucro_liquido": round(lucro_liquido, 2),
            # Week
            "vendas_semana": vendas_semana,
            "faturamento_semana": round(faturamento_semana, 2),
            # Ads (PADS)
            "ad_spend": round(ad_spend, 2),
            "ad_revenue": round(ad_revenue, 2),
            "organic_revenue": round(organic_revenue, 2),
            "acos": acos,
            "tacos": tacos,
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
            "pads_campaigns_found": pads_data.get("ad_impressions", 0) > 0 or pads_data.get("ad_spend", 0) > 0,
        },
    }


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching live data...")
    token = load_token()

    today_dt        = datetime.now()
    today_str       = today_dt.strftime("%Y-%m-%d")
    week_ago_str    = (today_dt - timedelta(days=6)).strftime("%Y-%m-%d")
    month_start_str = today_dt.strftime("%Y-%m-01")

    orders_today = fetch_orders_today(token)   # includes _shipping_cost_seller per order
    orders_week  = fetch_orders_week(token)
    orders_month = fetch_orders_month(token)

    # PADS: today (no date filter — API returns current-day aggregate by default)
    pads_today = fetch_pads_data(token)
    # PADS: explicit date ranges for week and month totals
    pads_week  = fetch_pads_data(token, date_from=week_ago_str,   date_to=today_str)
    pads_month = fetch_pads_data(token, date_from=month_start_str, date_to=today_str)

    data = compute_kpis(orders_today, orders_week, pads_today)

    # ── Semana aggregates + PADS ─────────────────────────────────────────
    semana = compute_period_totals(orders_week)
    semana["ad_spend"]       = pads_week["ad_spend"]
    semana["ad_revenue"]     = pads_week["ad_revenue"]
    semana["ad_impressions"] = pads_week["ad_impressions"]
    semana["ad_clicks"]      = pads_week["ad_clicks"]
    semana["organic_revenue"] = round(
        max(0.0, semana["faturamento"] - semana["ad_revenue"]), 2
    )
    semana["acos"]  = (
        round(semana["ad_spend"] / semana["ad_revenue"] * 100, 1)
        if semana["ad_revenue"] > 0 else 0
    )
    semana["tacos"] = (
        round(semana["ad_spend"] / semana["faturamento"] * 100, 1)
        if semana["faturamento"] > 0 else 0
    )
    data["semana"] = semana

    # ── Mês aggregates + PADS ────────────────────────────────────────────
    mes = compute_period_totals(orders_month)
    mes["ad_spend"]       = pads_month["ad_spend"]
    mes["ad_revenue"]     = pads_month["ad_revenue"]
    mes["ad_impressions"] = pads_month["ad_impressions"]
    mes["ad_clicks"]      = pads_month["ad_clicks"]
    mes["organic_revenue"] = round(
        max(0.0, mes["faturamento"] - mes["ad_revenue"]), 2
    )
    mes["acos"]  = (
        round(mes["ad_spend"] / mes["ad_revenue"] * 100, 1)
        if mes["ad_revenue"] > 0 else 0
    )
    mes["tacos"] = (
        round(mes["ad_spend"] / mes["faturamento"] * 100, 1)
        if mes["faturamento"] > 0 else 0
    )
    mes["chart"] = compute_month_chart(orders_month)
    data["mes"] = mes

    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    kpis = data["kpis"]
    print(f"  ✅ Vendas hoje:     {kpis['vendas_hoje']} | Faturamento: R$ {kpis['faturamento_hoje']:,.2f}")
    print(f"  ✅ CMV total:       R$ {kpis['cmv_total']:,.2f} | Margem real: {kpis['margem_pct_real']:.1f}%")
    print(f"  ✅ Lucro bruto:     R$ {kpis['lucro_bruto']:,.2f} | Lucro/pedido: R$ {kpis['lucro_por_pedido']:.2f}")
    print(f"  ✅ Ticket médio:    R$ {kpis['ticket_medio']:.2f}")
    print(f"  ✅ Taxa ML:         R$ {kpis['taxa_ml_total']:,.2f} | Frete vendedor: R$ {kpis['shipping_total']:,.2f}")
    print(f"  ✅ Fat. líquido:    R$ {kpis['faturamento_liquido']:,.2f} | Lucro líquido: R$ {kpis['lucro_liquido']:,.2f}")
    print(f"  ✅ ADS hoje  — Spend: R$ {kpis['ad_spend']:,.2f} | ACoS: {kpis['acos']}% | TACoS: {kpis['tacos']}%")
    print(f"  ✅ ADS semana— Spend: R$ {semana['ad_spend']:,.2f} | ACoS: {semana['acos']}% | TACoS: {semana['tacos']}%")
    print(f"  ✅ ADS mês   — Spend: R$ {mes['ad_spend']:,.2f} | ACoS: {mes['acos']}% | TACoS: {mes['tacos']}%")
    print(f"  ✅ Semana: {semana['vendas']} vendas | R$ {semana['faturamento']:,.2f} | Taxa ML: R$ {semana['taxa_ml']:,.2f}")
    print(f"  ✅ Mês:    {mes['vendas']} vendas | R$ {mes['faturamento']:,.2f} | Taxa ML: R$ {mes['taxa_ml']:,.2f}")
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
