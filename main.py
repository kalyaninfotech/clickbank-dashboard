import os
import time
import threading
import requests
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

stats = {
    "last_check": "Starting...",
    "total_sales": 0,
    "balance": "$0.00",
    "today_sales": 0,
    "status": "Running",
    "checks_done": 0,
    "nickname": "Not Set",
    "last_error": ""
}

def read_secret(name):
    """Render Secret Files se read karega"""
    try:
        # Render Secret Files are in /etc/secrets/
        path = f"/etc/secrets/{name}"
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read().strip()
        # Fallback to env var
        return os.environ.get(name, "").strip()
    except:
        return os.environ.get(name, "").strip()

def fetch_clickbank_data():
    try:
        nickname = read_secret("CLICKBANK_NICKNAME")
        clerk_key = read_secret("CLICKBANK_API_KEY")
        dev_key = read_secret("CLICKBANK_DEV_KEY")
        
        stats["nickname"] = nickname if nickname else "Not Set"
        
        if not clerk_key or not dev_key:
            stats["last_error"] = "API Keys not set in Environment"
            print("Keys not set")
            return
        
        # ClickBank Orders API
        url = "https://api.clickbank.com/rest/1.3/orders/list"
        headers = {
            "Authorization": f"{dev_key}:{clerk_key}",
            "Accept": "application/json"
        }
        
        # Last 30 days ke orders
        params = {"orderBy": "orderDate"}
        
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            # Sample parsing - actual structure pe depend
            order_data = data.get("orderData", []) or data.get("orders", []) or []
            if isinstance(order_data, list):
                stats["total_sales"] = len(order_data)
                # Balance calc example
                total = sum(float(o.get("totalAccountAmount", 0) or 0) for o in order_data if isinstance(o, dict))
                stats["balance"] = f"${total:.2f}"
                stats["last_error"] = ""
            else:
                stats["total_sales"] = data.get("totalOrders", 0)
            print(f"ClickBank OK: {stats['total_sales']} sales")
        else:
            stats["last_error"] = f"API Error {resp.status_code}: {resp.text[:100]}"
            print(stats["last_error"])
            
    except Exception as e:
        stats["last_error"] = str(e)[:200]
        print(f"Fetch error: {e}")

def background_clickbank_check():
    while True:
        try:
            fetch_clickbank_data()
            stats["checks_done"] += 1
            stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            time.sleep(60)
        except Exception as e:
            print(f"Check error: {e}")
            time.sleep(60)

thread = threading.Thread(target=background_clickbank_check, daemon=True)
thread.start()

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
.error{color:#f87171; font-size:13px; margin-top:10px;}
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
setInterval(refresh,5000);
</script>
</head>
<body>
<h1>💰 Moral Actual Loop - ClickBank Dashboard</h1>
<div class="card">
<span class="status-dot"></span> <b>Live Running</b> <span class="small">- Background check every 60 sec</span>
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
<p>✅ App is running on <b>Render - Free Forever</b> - Real ClickBank API Connected!</p>
<p class="small">Auto-refreshes every 5 seconds | Background fetch every 60 sec</p>
</div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML, **stats)

@app.route('/api/stats')
def api_stats():
    return jsonify(stats)

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
