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
    "nickname": "KALYAN1212",
    "last_error": "",
    "api_tried": ""
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
        nickname = read_secret("CLICKBANK_NICKNAME") or "KALYAN1212"
        api_key = read_secret("CLICKBANK_API_KEY") or read_secret("CLICKBANK_DEV_KEY")
        clerk_key = read_secret("CLICKBANK_API_KEY")
        dev_key = read_secret("CLICKBANK_DEV_KEY")
        
        stats["nickname"] = nickname.upper()
        
        if not api_key:
            stats["last_error"] = "⚠️ API Key missing in Render Secret Files"
            stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            stats["checks_done"] += 1
            return stats
        
        # Clean key - remove spaces/newlines
        api_key = api_key.strip()
        
        # Try NEW ClickBank API (2024+)
        # New docs: https://api.clickbank.com/api/rest/...
        endpoints_to_try = [
            # New API v1
            {"url": "https://api.clickbank.com/api/rest/v1/orders", "headers": {"Authorization": api_key, "Accept": "application/json"}},
            {"url": "https://api.clickbank.com/api/rest/v1/orders/list", "headers": {"Authorization": api_key, "Accept": "application/json"}},
            {"url": "https://api.clickbank.com/api/rest/v1.3/orders/list", "headers": {"Authorization": api_key, "Accept": "application/json"}},
            # Try with Bearer
            {"url": "https://api.clickbank.com/api/rest/v1/orders", "headers": {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}},
            # Old API with same key as both
            {"url": "https://api.clickbank.com/rest/1.3/orders/list", "headers": {"Authorization": f"{dev_key}:{clerk_key}", "Accept": "application/json"}},
            {"url": "https://api.clickbank.com/rest/1.3/orders/list", "headers": {"Authorization": f"{api_key}:{api_key}", "Accept": "application/json"}},
            # Try X header
            {"url": "https://api.clickbank.com/api/rest/v1/orders", "headers": {"X-ClickBank-API-Key": api_key, "Accept": "application/json"}},
        ]
        
        last_resp_text = ""
        last_status = 0
        
        for attempt in endpoints_to_try:
            try:
                url = attempt["url"]
                headers = attempt["headers"]
                stats["api_tried"] = f"Trying {url}"
                print(f"Trying {url} with headers {list(headers.keys())}")
                
                resp = requests.get(url, headers=headers, timeout=10)
                last_status = resp.status_code
                last_resp_text = resp.text[:500]
                
                print(f"Response {resp.status_code}: {resp.text[:200]}")
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        # New API response parsing
                        order_data = None
                        if isinstance(data, dict):
                            order_data = data.get("orderData") or data.get("orders") or data.get("orderList") or data.get("data") or data.get("ordersList")
                            if order_data is None and isinstance(data.get("data"), dict):
                                order_data = data["data"].get("orders", [])
                        elif isinstance(data, list):
                            order_data = data
                        
                        if order_data is None:
                            # Maybe single object, count as 0 or parse differently
                            order_data = []
                        
                        if isinstance(order_data, list):
                            stats["total_sales"] = len(order_data)
                            total = 0
                            for o in order_data:
                                if isinstance(o, dict):
                                    # New API fields
                                    total += float(o.get("totalAccountAmount", 0) or o.get("accountAmount", 0) or o.get("total", 0) or o.get("amount", 0) or 0)
                            stats["balance"] = f"${total:.2f}"
                        
                        stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                        stats["checks_done"] += 1
                        stats["last_error"] = f"✅ LIVE OK via {url} - {stats['total_sales']} orders - {stats['last_check']}"
                        return stats
                    except Exception as je:
                        stats["last_error"] = f"JSON Parse Error {url}: {je} - {resp.text[:200]}"
                        continue
                elif resp.status_code == 401:
                    last_resp_text = resp.text[:300]
                    continue # try next endpoint
                else:
                    last_resp_text = resp.text[:300]
                    continue
                    
            except Exception as e:
                print(f"Attempt failed {attempt['url']}: {e}")
                last_resp_text = str(e)[:300]
                continue
        
        # If all failed
        stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"] += 1
        stats["last_error"] = f"❌ All APIs failed - Last {last_status}: {last_resp_text} - Key starts with {api_key[:8]}... Length {len(api_key)}"
            
    except Exception as e:
        stats["last_check"] = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"] += 1
        stats["last_error"] = f"Error: {str(e)[:400]}"
    
    return stats

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ClickBank Dashboard - NEW API</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family: Arial; background: #0f172a; color: white; margin:0; padding:20px;}
.card{background: #1e293b; border-radius: 15px; padding: 20px; margin: 15px 0; border-left: 5px solid #22c55e;}
h1{color: #22c55e; text-align:center;}
.value{font-size: 32px; font-weight: bold; color: #22c55e;}
.small{color: #94a3b8; font-size: 14px;}
.status-dot{display:inline-block; width:12px; height:12px; background:#22c55e; border-radius:50%; animation: blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1} 50%{opacity:0.3}}
.error{color:#fbbf24; font-size:12px; margin-top:10px; word-break: break-all; background:#1f2937; padding:10px; border-radius:8px;}
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
window.onload=refresh;
</script>
</head>
<body>
<h1>💰 ClickBank - NEW API Support</h1>
<div class="card">
<span class="status-dot"></span> <b>Live Running - New API (API-L8KM...)</b>
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
<p>✅ Supports NEW single-key API: API-... format</p>
<p class="small">Auto-refresh every 3s | Tries multiple endpoints</p>
<p class="small">Key format: API-L8KM4MKQL5LU9BFOX9KTQWT6BR8NO4MVDGBP (Active)</p>
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
