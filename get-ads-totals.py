#!/usr/bin/env python3
"""
Script consolidado do Super App para extrair métricas de Ads
(Product, Brand, Display) para todos os Advertiser IDs conhecidos.
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, 'core/mcp')
from token_manager import MercadoLivreTokenManager
import requests
from tabulate import tabulate

def test_endpoints(ad_id, headers):
    today = datetime.now().strftime('%Y-%m-%d')
    ads_data = {
        'Product Ads': {'cost': 0, 'clicks': 0, 'revenue': 0, 'status': 'Verificando...'},
        'Brand Ads':   {'cost': 0, 'clicks': 0, 'revenue': 0, 'status': 'Verificando...'},
        'Display Ads': {'cost': 0, 'clicks': 0, 'revenue': 0, 'status': 'Verificando...'}
    }

    # 1. Product Ads
    url_pads = f"https://api.mercadolibre.com/marketplace/advertising/MLB/advertisers/{ad_id}/product_ads/campaigns/search"
    r_pads = requests.get(url_pads, headers=headers)
    
    if r_pads.status_code == 200:
        campaigns = r_pads.json().get('results', [])
        ads_data['Product Ads']['status'] = f'Ativo ({len(campaigns)} camp.)'
        for c in campaigns:
            c_id = c.get('id')
            m_url = f"https://api.mercadolibre.com/advertising/product_ads_2/campaigns/{c_id}/metrics?date_from={today}&date_to={today}"
            rm = requests.get(m_url, headers=headers)
            if rm.status_code == 200:
                m = rm.json()
                ads_data['Product Ads']['cost'] += m.get('cost', 0)
                ads_data['Product Ads']['clicks'] += m.get('clicks', 0)
                ads_data['Product Ads']['revenue'] += m.get('amount_total', 0)
    elif r_pads.status_code == 401:
        ads_data['Product Ads']['status'] = '⚠️ 401 Sem Permissão'
    elif r_pads.status_code == 404:
        ads_data['Product Ads']['status'] = '❌ 404 Inativo'
    else:
        ads_data['Product Ads']['status'] = f'Erro {r_pads.status_code}'

    # 2. Brand Ads
    url_bads = f"https://api.mercadolibre.com/marketplace/advertising/MLB/advertisers/{ad_id}/brand_ads/campaigns/search"
    r_bads = requests.get(url_bads, headers=headers)
    
    if r_bads.status_code == 200:
        campaigns = r_bads.json().get('results', [])
        ads_data['Brand Ads']['status'] = f'Ativo ({len(campaigns)} camp.)'
        # Would fetch metrics here if active
    elif r_bads.status_code == 401:
        ads_data['Brand Ads']['status'] = '⚠️ 401 Sem Permissão'
    elif r_bads.status_code == 404:
        ads_data['Brand Ads']['status'] = '❌ 404 Inativo/Desativado'
    else:
        ads_data['Brand Ads']['status'] = f'Erro {r_bads.status_code}'

    # 3. Display Ads
    url_disp = f"https://api.mercadolibre.com/marketplace/advertising/MLB/advertisers/{ad_id}/display_ads/campaigns/search"
    r_disp = requests.get(url_disp, headers=headers)
    
    if r_disp.status_code == 200:
        campaigns = r_disp.json().get('results', [])
        ads_data['Display Ads']['status'] = f'Ativo ({len(campaigns)} camp.)'
    elif r_disp.status_code == 401:
        ads_data['Display Ads']['status'] = '⚠️ 401 Sem Permissão'
    elif r_disp.status_code == 404:
        ads_data['Display Ads']['status'] = '❌ 404 Inativo/Desativado'
    else:
        ads_data['Display Ads']['status'] = f'Erro {r_disp.status_code}'

    return ads_data


def run_aggregator():
    print("\n" + "="*80)
    print("📈 SUPER APP: CONSOLIDAÇÃO DE INVESTIMENTO ADS - MERCADOLIVRE")
    print("="*80 + "\n")

    manager = MercadoLivreTokenManager()
    token = manager.get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    advertiser_ids = ['126426', '136527']
    
    all_results = []
    total_global_cost = 0
    total_global_rev = 0

    print(f"📅 Data Base: {datetime.now().strftime('%d/%m/%Y')} (Dados do dia)")

    for ad_id in advertiser_ids:
        data = test_endpoints(ad_id, headers)
        
        for ad_type, metrics in data.items():
            cost = metrics['cost']
            rev = metrics['revenue']
            
            total_global_cost += cost
            total_global_rev += rev

            all_results.append({
                'ID da Conta': ad_id,
                'Formato': ad_type,
                'Status Acesso': metrics['status'],
                'Cliques': metrics['clicks'] if cost > 0 else '-',
                'Investimento': f"R$ {cost:,.2f}" if cost > 0 else '-',
                'Receita': f"R$ {rev:,.2f}" if rev > 0 else '-'
            })

    print("\n" + tabulate(all_results, headers="keys", tablefmt="grid", maxcolwidths=[12, 15, 25, 10, 15, 15]))

    print(f"\n{'='*80}")
    print(f"💰 INVESTIMENTO TOTAL RASTREADO (HOJE): R$ {total_global_cost:,.2f}")
    print(f"🎯 RECEITA ATRIBUÍDA (HOJE): R$ {total_global_rev:,.2f}")
    if total_global_cost > 0:
        roas = total_global_rev / total_global_cost
        print(f"📈 ROAS Médio: {roas:.2f}x")
    print(f"{'='*80}\n")
    
    print("⚠️ DIAGNÓSTICO CRO:")
    print("Contas marcadas com '401' exigem que a Agência/Gestor aprove nosso aplicativo MercadoLivre")
    print("Contas marcadas com '404' significam que a função não está ATIVA nativamente no Mercado Livre para esse ID.")

if __name__ == "__main__":
    run_aggregator()
