import os
import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def get_orders():
    access_token = os.getenv("MERCADOLIVRE_ACCESS_TOKEN")
    seller_id = "694166791" # Hugo Jobs
    
    # Today's date in -03:00
    today = datetime.now().strftime("%Y-%m-%d")
    date_from = f"{today}T00:00:00.000-03:00"
    date_to = f"{today}T23:59:59.999-03:00"
    
    endpoint = f"https://api.mercadolibre.com/orders/search?seller={seller_id}&order.date_created.from={date_from}&order.date_created.to={date_to}"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"Fetching orders from: {endpoint}")
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('results', []))} orders.")
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    orders = get_orders()
    if orders:
        with open("vendas_hoje.json", "w") as f:
            json.dump(orders, f, indent=2)
        print("Orders saved to vendas_hoje.json")
