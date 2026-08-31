import os
import requests
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

stats = {
    "last_check": "Never",
    "total_sales": 0,
    "balance": "$0.00",
    "checks_done": 0,
    "nickname": "kalyan1212",
    "last_error": ""
}

def read_secret(name):
    try:
        path = f"/etc/secrets/{name}"
        if os.path.exists(path):
            with open(path, 'r') as f:
                val = f.read().strip()
                if val:
                    return val
        return os.environ.get(name, "").strip()
    except:
        return os.environ.get(name, "").strip()

def fetch_clickbank_data():
    try:
        nickname = read_secret("CLICKBANK_NICKNAME") or "kalyan1212"
        clerk_key = read_secret("CLICKBANK_API_KEY")
        dev_key = read_secret("CLICKBANK_DEV_KEY")
        
        stats["nickname"] = nickname
        
        if not clerk_key or not dev_key:
            stats["last_error"] = f"⚠️ API Keys missing in Render Secret Files - Clerk:{'OK' if clerk_key else 'MISSING'} Dev:{'OK' if dev_key else 'MISSING'} - Secret Files me add karo"
            stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            stats["checks_done"] += 1
            return stats
        
        url = "https://api.clickbank.com/rest/1.3/orders/list"
        headers = {
            "Authorization": f"{dev_key}:{clerk_key}",
            "Accept": "application/json"
        }
        
        resp = requests.get(url, headers=headers, params={"orderBy": "orderDate"}, timeout=10)
        
        stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"] += 1
        
        if resp.status_code == 200:
            data = resp.json()
            order_data = data.get("orderData", []) or data.get("orders", []) or data.get("orderList", []) or []
            if isinstance(order_data, list):
                stats["total_sales"] = len(order_data)
                total = 0
                for o in order_data:
                    if isinstance(o, dict):
                        total += float(o.get("totalAccountAmount", 0) or o.get("amount", 0) or 0)
                stats["balance"] = f"${total:.2f}"
                stats["last_error"] = f"✅ Live OK - {len(order_data)} orders fetched at {stats['last_check']}"
            else:
                stats["total_sales"] = data.get("totalOrders", 0)
                stats["last_error"] = f"✅ Live OK - {stats['last_check']}"
        else:
            stats["last_error"] = f"❌ API Error {resp.status_code}: {resp.text[:250]} - Check Clerk Key & Dev Key from ClickBank"
            
    except Exception as e:
        stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"] += 1
        stats["last_error"] = f"Error: {str(e)[:300]}"
    
    return stats

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ClickBank Dashboard - Live</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family: Arial; background: #0f172a; color: white; margin:0; padding:20px;}
.card{background: #1e293b; border-radius: 15px; padding: 20px; margin: 15px 0; border-left: 5px solid #22c55e;}
h1{color: #22c55e; text-align:center;}
.value{font-size: 32px; font-weight: bold; color: #22c55e;}
.small{color: #94a3b8; font-size: 14px;}
.status-dot{display:inline-block; width:12px; height:12px; background:#22c55e; border-radius:50%; animation: blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1} 50%{opacity:0.3}}
.error{color:#fbbf24; font-size:13px; margin-top:10px; word-break: break-all; background:#1f2937; padding:10px; border-radius:8px;}
.ok{color:#22c55e;}
</style>
<script>
function refresh(){fetch('/api/stats').then(r=>r.json()).then(d=>{
document.getElementById('last').innerText=d.last_check;
document.getElementById('checks').innerText=d.checks_done;
document.getElementById('sales').innerText=d.total_sales;
document.getElementById('bal').innerText=d.balance;
document.getElementById('nick').innerText=d.nickname;
document.getElementById('err').innerText=d.last_error || '';
});}
setInterval(refresh,3000);
</script>
</head>
<body>
<h1>💰 Moral Actual Loop - ClickBank Dashboard</h1>
<div class="card">
<span class="status-dot"></span> <b>Live Running</b> <span class="small">- Direct check on every page load (No background hang)</span>
<p class="small">Nickname: <b id="nick">{{ nickname }}</b></p>
<p class="small">Last Check: <span id="last">{{ last_check }}</span></p>
<p class="small">Total Checks Done: <span id="checks">{{ checks_done }}</span></p>
<p class="error" id="err">{{ last_error }}</p>
</div>
<div class="card">
<p class="small">TOTAL SALES (Last Orders)</p>
<div class="value" id="sales">{{ total_sales }}</div>
</div>
<div class="card">
<p class="small">TOTAL EARNINGS</p>
<div class="value" id="bal">{{ balance }}</div>
</div>
<div class="card" style="border-left-color:#3b82f6;">
<p>✅ <b>Render - Free Forever - Real ClickBank API</b></p>
<p class="small">Auto-refreshes every 3 seconds | Checks on every page load | API: api.clickbank.com/rest/1.3/orders/list</p>
<p class="small">If you see "API Keys missing" - Go to Render > Environment > Secret Files and add: CLICKBANK_NICKNAME, CLICKBANK_API_KEY, CLICKBANK_DEV_KEY</p>
</div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    fetch_clickbank_data()
    return render_template_string(DASHBOARD_HTML, **stats)

@app.route('/api/stats')
def api_stats():
    fetch_clickbank_data()
    return jsonify(stats)

@app.route('/test')
def test():
    result = fetch_clickbank_data()
    return jsonify(result)

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
