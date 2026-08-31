import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# === YOUR CLICKBANK DATA (yaha apni ID daal dena) ===
stats = {
    "last_check": "Starting...",
    "total_sales": 0,
    "balance": "$0.00",
    "today_sales": 0,
    "status": "Running",
    "checks_done": 0
}

def background_clickbank_check():
    """Har 60 second pe ClickBank check karega - background me"""
    while True:
        try:
            time.sleep(60)  # 60 second wait
            stats["checks_done"] += 1
            stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            # Yaha real ClickBank API call ayega - abhi demo data
            # stats["total_sales"] = your_api_call()
            print(f"[{stats['last_check']}] ClickBank Check #{stats['checks_done']} - OK")
        except Exception as e:
            print(f"Check error: {e}")

# Background thread start
thread = threading.Thread(target=background_clickbank_check, daemon=True)
thread.start()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ClickBank Dashboard - Mahesh</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family: Arial; background: #0f172a; color: white; margin:0; padding:20px;}
.card{background: #1e293b; border-radius: 15px; padding: 20px; margin: 15px 0; border-left: 5px solid #22c55e;}
h1{color: #22c55e; text-align:center;}
.value{font-size: 32px; font-weight: bold; color: #22c55e;}
.small{color: #94a3b8; font-size: 14px;}
.status-dot{display:inline-block; width:12px; height:12px; background:#22c55e; border-radius:50%; animation: blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1} 50%{opacity:0.3}}
</style>
<script>
function refresh(){fetch('/api/stats').then(r=>r.json()).then(d=>{
document.getElementById('last').innerText=d.last_check;
document.getElementById('checks').innerText=d.checks_done;
document.getElementById('sales').innerText=d.total_sales;
document.getElementById('bal').innerText=d.balance;
});}
setInterval(refresh,5000); // har 5 sec refresh
</script>
</head>
<body>
<h1>💰 Moral Actual Loop - ClickBank Dashboard</h1>
<div class="card">
<span class="status-dot"></span> <b>Live Running</b> <span class="small">- Background check every 60 sec</span>
<p class="small">Last Check: <span id="last">{{ last_check }}</span></p>
<p class="small">Total Checks Done: <span id="checks">{{ checks_done }}</span></p>
</div>
<div class="card">
<p class="small">TOTAL SALES</p>
<div class="value" id="sales">{{ total_sales }}</div>
</div>
<div class="card">
<p class="small">BALANCE</p>
<div class="value" id="bal">{{ balance }}</div>
</div>
<div class="card" style="border-left-color:#3b82f6;">
<p>✅ App is running on <b>Render - Free Forever</b> - No 29 days expiry!</p>
<p class="small">Auto-refreshes every 5 seconds</p>
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
    print(f"Starting ClickBank Dashboard on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
