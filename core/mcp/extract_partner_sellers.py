#!/usr/bin/env python3
"""
Extract Partner Linked Sellers from Mercado Livre
Tries multiple API endpoints to find seller data
"""

import json
import requests
import argparse
from datetime import datetime
from pathlib import Path

class MLPartnerExtractor:
    def __init__(self, partner_id, token):
        self.partner_id = partner_id
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.mercadolibre.com"
        self.sellers = []

    def try_endpoint(self, endpoint, description):
        """Try a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        print(f"  🔍 Tentando: {description}")
        print(f"     URL: {url}")

        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            print(f"     Status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                print(f"     ✅ SUCESSO! Encontrou dados.")
                return data
            else:
                print(f"     ❌ Não encontrado (404) ou erro {r.status_code}")
                return None
        except Exception as e:
            print(f"     ⚠️  Erro: {str(e)}")
            return None

    def extract(self):
        """Try multiple endpoints to find seller data"""
        print(f"\n{'='*80}")
        print(f"EXTRACTING PARTNER SELLERS")
        print(f"{'='*80}")
        print(f"Partner ID: {self.partner_id}")
        print(f"Token: {self.token[:20]}...")

        endpoints = [
            (f"/partners/consultancy/linked-sellers", "Consultancy linked sellers"),
            (f"/partners/{self.partner_id}/sellers", "Partner sellers endpoint"),
            (f"/partners/{self.partner_id}/linked-sellers", "Partner linked sellers"),
            (f"/consultancy/linked-sellers", "General consultancy endpoint"),
            (f"/sellers/{self.partner_id}/partnerships", "Partnerships for seller"),
        ]

        print(f"\n📡 Testando endpoints (total: {len(endpoints)}):\n")

        for endpoint, description in endpoints:
            result = self.try_endpoint(endpoint, description)
            if result:
                self._parse_result(result, endpoint)
                if self.sellers:
                    break
            print()

        if not self.sellers:
            print("\n⚠️  NENHUM ENDPOINT RETORNOU DADOS")
            print("   A API pública do ML pode não expor sellers vinculados.")
            print("   Solução: Acesse o Dashboard em https://partners.mercadolivre.com.br/")
            return False

        return True

    def _parse_result(self, data, endpoint):
        """Parse API response to extract sellers"""
        print(f"\n     📊 Parseando resultado...")

        # Try different data structures
        sellers_data = None

        if isinstance(data, dict):
            # Check common keys
            for key in ['sellers', 'linked_sellers', 'results', 'data', 'partnerships']:
                if key in data:
                    sellers_data = data[key]
                    print(f"        Encontrado campo: '{key}'")
                    break

            if not sellers_data and 'seller' in data:
                sellers_data = [data['seller']]

        elif isinstance(data, list):
            sellers_data = data

        if sellers_data:
            self._process_sellers(sellers_data)

    def _process_sellers(self, sellers_data):
        """Process seller data"""
        if isinstance(sellers_data, dict):
            sellers_data = [sellers_data]

        for seller in sellers_data:
            if isinstance(seller, dict):
                seller_info = {
                    'seller_id': seller.get('id') or seller.get('seller_id'),
                    'nickname': seller.get('nickname') or seller.get('name'),
                    'status': seller.get('status') or 'UNKNOWN',
                    'tgmv': seller.get('tgmv') or seller.get('gmv') or 'N/A',
                }
                if seller_info['seller_id']:
                    self.sellers.append(seller_info)

    def display_results(self):
        """Display extracted sellers in table format"""
        if not self.sellers:
            print("\n❌ Nenhum seller encontrado para exibir.")
            return

        print(f"\n{'='*80}")
        print(f"✅ SELLERS VINCULADOS À HUGOJOBS (CONSULTORIA)")
        print(f"{'='*80}")
        print(f"Total: {len(self.sellers)} sellers")
        print()

        print(f"{'Seller ID':<15} {'Nickname':<30} {'Status':<15} {'TGMV':<15}")
        print("-" * 80)

        for seller in self.sellers:
            print(f"{str(seller['seller_id']):<15} {str(seller['nickname']):<30} {str(seller['status']):<15} {str(seller['tgmv']):<15}")

        print()

    def save_results(self):
        """Save results to JSON file"""
        output_path = Path("/Users/kennydwillker/Documents/GitHub/gps-iA/AIOX-GPS/.claude/mission-control/PARTNER-SELLERS.json")

        data = {
            "extraction_time": datetime.now().isoformat(),
            "partner_id": self.partner_id,
            "total_sellers": len(self.sellers),
            "sellers": self.sellers
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"📁 Resultado salvo em: {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Extract Partner Linked Sellers from ML API")
    parser.add_argument("--partner-id", required=True, help="Partner ID (ex: a5bPc000005xBXdIAM)")
    parser.add_argument("--token", required=True, help="API Token")
    parser.add_argument("--seller-id", default="694166791", help="Seller ID (default: HUGOJOBS)")

    args = parser.parse_args()

    extractor = MLPartnerExtractor(args.partner_id, args.token)

    if extractor.extract():
        extractor.display_results()
        extractor.save_results()
    else:
        print("\n⚠️  FALLBACK: Script não conseguiu acessar via API pública")
        print("    Abra o Dashboard manualmente: https://partners.mercadolivre.com.br/")

if __name__ == "__main__":
    main()
