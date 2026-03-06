#!/usr/bin/env python3
"""
Script para obter vendas do dia de Hugo Jobs no MercadoLivre

Uso:
  python3 get-vendas-dia.py
"""

import sys
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

sys.path.insert(0, 'core/mcp')
from token_manager import MercadoLivreTokenManager
import requests

def get_vendas_dia():
    """Buscar vendas do dia"""
    
    print("\n" + "="*70)
    print("📊 VENDAS DO DIA - MERCADOLIVRE")
    print("="*70 + "\n")
    
    # Obter token
    manager = MercadoLivreTokenManager()
    token = manager.get_valid_token()
    
    if not token:
        print("❌ Erro: Token inválido. Execute autorização primeiro.")
        return False
    
    # Get user info
    headers = {"Authorization": f"Bearer {token}"}
    user_resp = requests.get("https://api.mercadolibre.com/users/me", 
                             headers=headers, timeout=10)
    
    if user_resp.status_code != 200:
        print(f"❌ Erro ao obter dados da conta: {user_resp.status_code}")
        return False
    
    user = user_resp.json()
    seller_id = user.get('id')
    nickname = user.get('nickname')
    
    print(f"👤 Conta: {nickname} (ID: {seller_id})")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    # Get orders
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    date_from = f"{today_str}T00:00:00.000-03:00"
    date_to = f"{today_str}T23:59:59.999-03:00"
    
    orders_url = f"https://api.mercadolibre.com/orders/search?seller={seller_id}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50"
    orders_resp = requests.get(orders_url, headers=headers, timeout=10)
    
    if orders_resp.status_code != 200:
        print(f"❌ Erro ao buscar pedidos: {orders_resp.status_code}")
        return False
    
    orders = orders_resp.json().get('results', [])
    
    # Processar pedidos do dia
    today_orders = []
    total_value = 0
    
    print("🔄 Carregando detalhes dos pedidos...\n")
    
    # Invert the order so chronologically earlier orders appear first (since API returns desc)
    # or keep desc. We'll just take them as is.
    for order in orders:
        status = order.get('status', 'unknown')
        if status not in ['paid', 'shipped', 'delivered']:
            continue
            
        order_id = order.get('id')
        date_created = order.get('date_created', '')
        
        order_items = order.get('order_items', [])
        item_title = order_items[0].get('item', {}).get('title', 'Sem título')[:50] if order_items else "Sem título"
        
        total = order.get('total_amount', 0)
        
        today_orders.append({
            'ID': order_id,
            'Hora': date_created[11:16],
            'Produto': item_title,
            'Valor': f"R$ {total:.2f}",
            'Status': status
        })
        
        total_value += total
    
    # Exibir tabela
    if today_orders:
        print(tabulate(
            today_orders,
            headers="keys",
            tablefmt="grid",
            maxcolwidths=[20, 6, 40, 12, 10]
        ))
        
        print(f"\n{'='*70}")
        print(f"📦 Total de pedidos: {len(today_orders)}")
        print(f"💰 Total de vendas: R$ {total_value:,.2f}")
        print(f"{'='*70}\n")
    else:
        print("ℹ️  Nenhuma venda registrada para hoje.\n")
    
    return True

if __name__ == "__main__":
    success = get_vendas_dia()
    sys.exit(0 if success else 1)
