import os
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Try to find token
token_state_path = Path("/Users/kennydwillker/Documents/GitHub/Thiago Finch/AIOX-GPS/.claude/mission-control/ML-TOKEN-STATE.json")
if not token_state_path.exists():
    print("Token state not found")
    sys.exit(1)

with open(token_state_path, 'r') as f:
    state = json.load(f)
    default_user = state.get("default_user_id", "694166791")
    token = state.get("accounts", {}).get(default_user, {}).get("access_token")
    if not token:
        print(f"❌ Token not found for user {default_user}")
        sys.exit(1)

seller_id = "694166791"
# Dynamic date_from: today at 00:00:00
today_str = datetime.now().strftime('%Y-%m-%d')
date_from = f"{today_str}T00:00:00.000-03:00"

url = f"https://api.mercadolibre.com/orders/search?seller={seller_id}&order.date_created.from={date_from}"
headers = {"Authorization": f"Bearer {token}"}

print(f"Searching: {url}")
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    results = data.get("results", [])
    print(f"Found {len(results)} orders since {date_from}")
    for order in results:
        print(f"- ID: {order.get('id')}, Date: {order.get('date_created')}, Status: {order.get('status')}")
else:
    print(resp.text)
