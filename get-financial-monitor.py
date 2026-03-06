#!/usr/bin/env python3
"""
Monitor Financeiro Diário - Hugo Jobs MercadoLivre
Consolida: Vendas Brutas, Taxas do MercadoLivre, Custos de Envio (Seller)
e Investimento Diário em Ads para projetar o Recebimento Líquido (Net Payout).
"""

import sys
from pathlib import Path
from datetime import datetime
import traceback

sys.path.insert(0, 'core/mcp')
from token_manager import MercadoLivreTokenManager
import requests
from tabulate import tabulate

def get_ads_cost(headers, ad_ids):
    """Obtém o gasto total de ads para os IDs de anunciante no dia de hoje."""
    today = datetime.now().strftime('%Y-%m-%d')
    total_cost = 0

    for ad_id in ad_ids:
        # Tenta Product Ads
        url_pads = f"https://api.mercadolibre.com/marketplace/advertising/MLB/advertisers/{ad_id}/product_ads/campaigns/search"
        r = requests.get(url_pads, headers=headers)
        if r.status_code == 200:
            campaigns = r.json().get('results', [])
            for c in campaigns:
                c_id = c.get('id')
                m_url = f"https://api.mercadolibre.com/advertising/product_ads_2/campaigns/{c_id}/metrics?date_from={today}&date_to={today}"
                rm = requests.get(m_url, headers=headers)
                if rm.status_code == 200:
                    total_cost += rm.json().get('cost', 0)
    
    return total_cost

def get_financial_monitor():
    print("\n" + "="*80)
    print("💵 MONITOR FINANCEIRO DIÁRIO - HUGO JOBS")
    print("="*80 + "\n")

    manager = MercadoLivreTokenManager()
    token = manager.get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Obter Vendas de Hoje
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    date_from = f"{today_str}T00:00:00.000-03:00"
    date_to = f"{today_str}T23:59:59.999-03:00"
    
    url_users = "https://api.mercadolibre.com/users/me"
    seller_resp = requests.get(url_users, headers=headers)
    seller_id = seller_resp.json().get('id')

    orders_url = f"https://api.mercadolibre.com/orders/search?seller={seller_id}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50"
    orders_resp = requests.get(orders_url, headers=headers)
    orders = orders_resp.json().get('results', [])

    total_gross = 0
    total_ml_fees = 0
    total_shipping_cost = 0
    valid_orders = 0

    print("🔄 Processando pedidos e taxas do dia...")

    for order in orders:
        status = order.get('status', 'unknown')
        if status not in ['paid', 'shipped', 'delivered']:
            continue
            
        valid_orders += 1
        order_id = order.get('id')
        total_gross += order.get('total_amount', 0)
        
        # Obter detalhes do pedido para ver taxas (sale_fee)
        r_detail = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=headers)
        if r_detail.status_code == 200:
            order_data = r_detail.json()
            
            # Taxa de venda do produto
            for item in order_data.get('order_items', []):
                total_ml_fees += item.get('sale_fee', 0)
                
            # Custo de frete pago pelo vendedor (se houver frete grátis/compartilhado)
            shipping_id = order_data.get('shipping', {}).get('id')
            if shipping_id:
                r_ship = requests.get(f"https://api.mercadolibre.com/shipments/{shipping_id}", headers=headers)
                if r_ship.status_code == 200:
                    ship_data = r_ship.json()
                    # Custos para o vendedor ficam em base_cost do shipping_option se paid_by_seller
                    # ou podemos buscar nas tags de fulfillment.
                    for pt in ship_data.get('payment_details', {}).get('payment_methods', []):
                       if 'seller' in pt.get('payer_type', ''):
                           total_shipping_cost += pt.get('amount', 0)
                    
                    # Alternatively, check shipping option cost 
                    list_cost = ship_data.get('shipping_option', {}).get('list_cost', 0)
                    cost = ship_data.get('shipping_option', {}).get('cost', 0)
                    if list_cost > cost:
                         # Seller paid part
                         total_shipping_cost += (list_cost - cost)

    # 2. Obter Gasto em Ads
    print("🔄 Processando custos publicitários (Ads)...")
    advertiser_ids = ['126426', '136527']
    ads_cost = get_ads_cost(headers, advertiser_ids)

    # 3. Calcular Líquido Mão a Mão
    recebimento_mercado_pago = total_gross - total_ml_fees - total_shipping_cost
    lucro_liquido_aprox = recebimento_mercado_pago - ads_cost

    # 4. Exibir Quadro Financeiro
    tabela = [
        ["Total de Pedidos Gerados", f"{valid_orders}"],
        ["(+) Vendas Brutas (GMV)", f"R$ {total_gross:,.2f}"],
        ["(-) Comissões Mercado Livre", f"- R$ {total_ml_fees:,.2f}"],
        ["(-) Custos de Envio (Seller)", f"- R$ {total_shipping_cost:,.2f}"],
        ["(=) Recebimento Líquido Estimado", f"R$ {recebimento_mercado_pago:,.2f}"],
        ["(-) Investimento Mercado Ads", f"- R$ {ads_cost:,.2f}"],
        ["", ""],
        ["💸 SALDO OPERACIONAL (Dia)", f"R$ {lucro_liquido_aprox:,.2f}"]
    ]

    print("\n")
    print(tabulate(tabela, tablefmt="fancy_grid"))
    print("\n* Nota: O Saldo Operacional não desconta o Custo do Produto Vendido (CPV/Fornecedor) nem impostos da NF.")

if __name__ == "__main__":
    try:
        get_financial_monitor()
    except Exception as e:
        print("Erro ao gerar monitor financeiro:", e)
        traceback.print_exc()
