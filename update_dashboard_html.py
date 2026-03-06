#!/usr/bin/env python3
import json
import re
from pathlib import Path
from datetime import datetime

HTML_FILE = Path('index.html')
DATA_FILE = Path('data-audit-report.json')

def format_currency(value):
    return f"R$ {value:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')

def update_dashboard():
    if not DATA_FILE.exists():
        print(f"❌ Erro: {DATA_FILE} não encontrado.")
        return

    if not HTML_FILE.exists():
        print(f"❌ Erro: {HTML_FILE} não encontrado.")
        return

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    summary = data.get('summary', {})
    orders = data.get('orders', [])
    timestamp = data.get('timestamp', '')
    
    # Formatar data/hora legível
    dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
    readable_time = dt.strftime('%H:%M:%S')
    readable_date = dt.strftime('%d/%m/%Y')

    content = HTML_FILE.read_text()

    # 1. Injetar Resumo
    content = re.sub(r'id="total-gmv"[^>]*>.*?</div>', f'id="total-gmv">{format_currency(summary.get("gmv", 0))}</div>', content)
    content = re.sub(r'id="total-ads"[^>]*>.*?</div>', f'id="total-ads" style="color: var(--primary);">{format_currency(summary.get("ads", 0))}</div>', content)
    content = re.sub(r'id="total-fees"[^>]*>.*?</div>', f'id="total-fees" style="color: var(--danger);">{format_currency(summary.get("fees", 0))}</div>', content)
    content = re.sub(r'id="total-net"[^>]*>.*?</div>', f'id="total-net" style="color: var(--accent);">{format_currency(summary.get("net", 0))}</div>', content)
    
    # 2. Injetar Timestamp
    content = re.sub(r'id="last-update-time">.*?</span>', f'id="last-update-time">{readable_time}</span>', content)

    # 3. Gerar HTML dos Pedidos
    rows_html = ""
    for order in orders:
        status_color = "#3fb950" if order.get('Status') == 'paid' else "#f85149" if order.get('Status') == 'cancelled' else "#d29922"
        itens_text = "<br>".join(order.get('Itens', []))
        rows_html += f"""
                <tr>
                    <td>{order.get('ID')}</td>
                    <td><span style="color: {status_color}; font-weight: bold;">{order.get('Status').upper()}</span></td>
                    <td>{format_currency(order.get('Valor', 0))}</td>
                    <td>{format_currency(order.get('Taxas_ML', 0))}</td>
                    <td style="font-size: 0.8rem; color: #8b949e;">{itens_text}</td>
                </tr>"""

    content = re.sub(r'<tbody id="order-rows">.*?</tbody>', f'<tbody id="order-rows">{rows_html}\n            </tbody>', content, flags=re.DOTALL)

    # 4. Injetar objeto JSON completo no Script para referências futuras
    json_str = json.dumps(data, indent=4)
    placeholder = 'const auditData = {};'
    if placeholder in content:
        content = content.replace(placeholder, f'const auditData = {json_str};')
    else:
        # Fallback se já tiver dados
        json_escaped = json_str.replace("\\", "\\\\")
        content = re.sub(r'const auditData = \{.*?\};', f'const auditData = {json_escaped};', content, flags=re.DOTALL)

    HTML_FILE.write_text(content)
    print(f"✅ Dashboard HTML atualizado com sucesso às {readable_time}.")

if __name__ == "__main__":
    from datetime import datetime
    update_dashboard()
