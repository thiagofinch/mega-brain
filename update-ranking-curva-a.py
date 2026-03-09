import sys
import json
from pathlib import Path
import requests

# Set path for token manager
sys.path.insert(0, '/Users/kennydwillker/Documents/GitHub/Thiago Finch/AIOX-GPS/core/mcp')
from token_manager import MercadoLivreTokenManager

manager = MercadoLivreTokenManager()
token = manager.get_valid_token()
item_id = 'MLB3596560539'

headers = {
    'Authorization': f'Bearer {token}', 
    'Content-Type': 'application/json'
}

# 1. Update Title and Attributes
update_data = {
    'title': 'Carteira Masculina Couro Legítimo Slim Minimalista Hugo Jobs',
    'attributes': [
        {'id': 'BRAND', 'value_name': 'Hugo Jobs'},
        {'id': 'COLOR', 'value_name': 'Preto'},
        {'id': 'MODEL', 'value_name': 'Slim Minimalista Premium'},
        {'id': 'MATERIAL', 'value_name': 'Couro Legítimo'}
    ]
}

print(f"Updating item {item_id}...")
resp = requests.put(f'https://api.mercadolobre.com/items/{item_id}', 
                   headers=headers, 
                   json=update_data) # use json= instead of data= for automatic serialization

# Correct URL spelling and handle potential 403/401
if 'mercadolobre' in resp.request.url: # typo check
     resp = requests.put(f'https://api.mercadolibre.com/items/{item_id}', 
                   headers=headers, 
                   json=update_data)

print(f'Item Update Status: {resp.status_code}')
if resp.status_code not in [200, 204]:
    print(resp.text)

# 2. Update Description
# Use a clean multiline string
description_text = (
    "🔥 CARTEIRA MASCULINA SLIM MINIMALISTA - COURO LEGÍTIMO HUGO JOBS\n\n"
    "A REVENDA MAIS VENDIDA AGORA COM DESIGN OTIMIZADO!\n"
    "Ideal para quem busca o máximo de discrição, elegância e durabilidade (100% Couro Real).\n\n"
    "✅ POR QUE ESCOLHER A HUGO JOBS?\n"
    "- COURO LEGÍTIMO: Não descasca, dura anos e mantém o aroma de couro novo.\n"
    "- ULTRA SLIM: Apenas 1cm de espessura. Não faz volume no bolso da calça ou terno.\n"
    "- CAPACIDADE INTELIGENTE: 6 slots para cartões + Compartimento Central para CNH e Cédulas.\n\n"
    "📍 ESPECIFICAÇÕES TÉCNICAS:\n"
    "- Altura: 10 cm\n"
    "- Largura: 7,5 cm\n"
    "- Espessura: 1 cm (Vazia)\n"
    "- Material: Couro Bovino de Alta Qualidade\n\n"
    "🚚 PRONTA ENTREGA | ENVIO IMEDIATO | NOTA FISCAL\n"
    "Somos fabricantes. Qualidade Hugo Jobs garantida ou seu dinheiro de volta.\n\n"
    "Adicione sofisticação ao seu dia a dia. Compre agora a carteira mais fina do mercado!"
)

new_description = {'plain_text': description_text}

print(f"Updating description for {item_id}...")
desc_resp = requests.put(f'https://api.mercadolibre.com/items/{item_id}/description', 
                        headers=headers, 
                        json=new_description)

print(f'Description Update Status: {desc_resp.status_code}')
if desc_resp.status_code not in [200, 204]:
    print(desc_resp.text)
