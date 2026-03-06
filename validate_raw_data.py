#!/usr/bin/env python3
import sys
import os
import requests
from datetime import datetime
import json

# Add core to path
sys.path.insert(0, os.path.abspath('core/mcp'))
from token_manager import MercadoLivreTokenManager

def validate():
    print("🔍 INICIANDO AUDITORIA DE DADOS REAIS...")
    manager = MercadoLivreTokenManager()
    token = manager.get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # User Info
    user_resp = requests.get("https://api.mercadolibre.com/users/me", headers=headers)
    seller_id = user_resp.json().get('id')
    print(f"✅ Seller ID: {seller_id}")

    # Today's Orders
    today_str = datetime.now().strftime('%Y-%m-%d')
    date_from = f"{today_str}T00:00:00.000-03:00"
    date_to = f"{today_str}T23:59:59.999-03:00"
    
    orders_url = f"https://api.mercadolibre.com/orders/search?seller={seller_id}&order.date_created.from={date_from}&order.date_created.to={date_to}"
    orders_data = requests.get(orders_url, headers=headers).json()
    results = orders_data.get('results', [])
    
    print(f"\n📦 PEDIDOS ENCONTRADOS (HOJE): {len(results)}")
    
    audit_log = []
    total_gmv = 0
    total_fees = 0
    
    for order in results:
        order_id = order.get('id')
        status = order.get('status')
        total_amount = order.get('total_amount', 0)
        
        # Detailed order info for shipping and exact fees
        detail_url = f"https://api.mercadolibre.com/orders/{order_id}"
        detail_resp = requests.get(detail_url, headers=headers).json()
        
        items = []
        order_fees = 0
        for item_info in detail_resp.get('order_items', []):
            order_fees += item_info.get('sale_fee', 0)
            title = item_info.get('item', {}).get('title', 'N/A')
            qty = item_info.get('quantity', 0)
            price = item_info.get('unit_price', 0)
            items.append(f"{qty}x {title} (R$ {price})")
        
        # Check shipping
        shipping_cost = 0
        shipping = detail_resp.get('shipping', {})
        if shipping.get('id'):
            ship_url = f"https://api.mercadolibre.com/shipments/{shipping.get('id')}"
            ship_resp = requests.get(ship_url, headers=headers).json()
            # If the cost to the buyer is 0, it means it was "free shipping" for them.
            # We check the 'list_cost' or 'cost' which is billed to the seller.
            if ship_resp.get('shipping_option', {}).get('cost') == 0:
                 shipping_cost = ship_resp.get('shipping_option', {}).get('list_cost', 0)
        
        current_order_total_cost = order_fees + shipping_cost
        
        if status in ['paid', 'shipped', 'delivered']:
            total_gmv += total_amount
            total_fees += current_order_total_cost
            
        audit_log.append({
            "ID": order_id,
            "Status": status,
            "Valor": total_amount,
            "Taxas_ML": current_order_total_cost,
            "Itens": items
        })
        print(f" - [{status}] ID: {order_id} | Valor: R$ {total_amount} | Taxas: R$ {current_order_total_cost:.2f}")

    # Ads Metrics
    print("\n📢 AUDITORIA DE ADS (PUBLICIDADE):")
    ads_cost = 0
    advertiser_ids = ['126426', '136527']
    for ad_id in advertiser_ids:
        url_c = f"https://api.mercadolibre.com/marketplace/advertising/MLB/advertisers/{ad_id}/product_ads/campaigns/search"
        rc = requests.get(url_c, headers=headers)
        if rc.status_code == 200:
            campaigns = rc.json().get('results', [])
            for c in campaigns:
                cid = c.get('id')
                url_m = f"https://api.mercadolibre.com/advertising/product_ads_2/campaigns/{cid}/metrics?date_from={today_str}&date_to={today_str}"
                rm = requests.get(url_m, headers=headers)
                if rm.status_code == 200:
                    m = rm.json()
                    c_cost = m.get('cost', 0)
                    ads_cost += c_cost
                    if c_cost > 0:
                        print(f"   - Campanha {cid}: R$ {c_cost}")

    print("\n📊 RESUMO GERAL (RAW DATA):")
    print(f" > GMV TOTAL: R$ {total_gmv:.2f}")
    print(f" > TAXAS ML:  R$ {total_fees:.2f}")
    print(f" > GASTO ADS: R$ {ads_cost:.2f}")
    print(f" > LÍQUIDO:   R$ {total_gmv - total_fees - ads_cost:.2f}")
    
    # Save report
    with open('data-audit-report.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "gmv": total_gmv,
                "fees": total_fees,
                "ads": ads_cost,
                "net": total_gmv - total_fees - ads_cost
            },
            "orders": audit_log
        }, f, indent=4)
    print("\n✅ Relatório 'data-audit-report.json' gerado.")

if __name__ == "__main__":
    validate()
