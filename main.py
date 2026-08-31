import os, requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

stats = {"last_check":"Never","total_sales":0,"balance":"$0.00","checks_done":0,"nickname":"KALYAN1212","last_error":""}

def get_secret(name):
    for p in [f"/etc/secrets/{name}", f"/etc/secrets/{name.lower()}"]:
        if os.path.exists(p):
            with open(p) as f:
                v=f.read().strip()
                if v: return v
    return os.environ.get(name,"").strip()

def fetch():
    try:
        nick = get_secret("CLICKBANK_NICKNAME") or "KALYAN1212"
        key = get_secret("CLICKBANK_API_KEY") or get_secret("CLICKBANK_DEV_KEY")
        stats["nickname"]=nick.upper()
        if not key:
            stats["last_error"]="❌ API Key missing in Secret Files"
            stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            stats["checks_done"]+=1
            return stats
        
        # NEW ClickBank spec: Authorization = API-... directly (no DEV prefix)
        # Try 3 auth formats
        auth_formats = [
            key,  # Just API- key
            f"Bearer {key}",  # Bearer format
            f"APIKey {key}",  # APIKey format
        ]
        
        today = datetime.now()
        start = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        
        endpoints = [
            f"https://api.clickbank.com/rest/1.3/analytics/affiliate/{nick}/summary?startDate={start}&endDate={end}&account={nick}",
            f"https://api.clickbank.com/rest/1.3/orders/list?account={nick}&startDate={start}&endDate={end}",
            f"https://api.clickbank.com/rest/1.3/orders2/list?account={nick}&startDate={start}&endDate={end}",
            f"https://api.clickbank.com/rest/1.3/orders/list",
            f"https://api.clickbank.com/rest/1.3/analytics/status",
        ]
        
        last_msg=""
        for auth_val in auth_formats:
            for url in endpoints:
                try:
                    headers = {"Authorization": auth_val, "Accept":"application/json", "Content-Type":"application/json"}
                    r = requests.get(url, headers=headers, timeout=12)
                    last_msg = f"{auth_val[:10]}... -> {url.split('/')[-1][:30]} => {r.status_code}: {r.text[:250]}"
                    print(last_msg)
                    if r.status_code==200:
                        try:
                            data=r.json()
                            # Try parse analytics
                            if "analytics" in url or "summary" in url:
                                # analytics returns XML sometimes, but try json
                                if isinstance(data, dict):
                                    # Look for sales data
                                    sales = data.get("totalSales") or data.get("saleCount") or data.get("netSaleCount") or 0
                                    # If data has nested
                                    if "data" in data and isinstance(data["data"], dict):
                                        sales = data["data"].get("saleCount", sales)
                                    stats["total_sales"]=int(sales) if str(sales).isdigit() else 0
                                    stats["balance"]=f"${data.get('netSaleAmount',0)}"
                                    stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                                    stats["checks_done"]+=1
                                    stats["last_error"]=f"✅ LIVE OK! Analytics API working! Sales: {stats['total_sales']}"
                                    return stats
                                else:
                                    # XML response - still success
                                    stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                                    stats["checks_done"]+=1
                                    stats["last_error"]=f"✅ LIVE OK! API connected (XML). No sales last 60 days or parse needed. Raw: {r.text[:120]}"
                                    return stats
                            else:
                                # orders API
                                orders = data.get("orderData") or data.get("orders") or data.get("data") or []
                                if isinstance(orders, list):
                                    stats["total_sales"]=len(orders)
                                    tot=sum([float(o.get("totalAccountAmount",0) or o.get("accountAmount",0) or 0) for o in orders if isinstance(o,dict)])
                                    stats["balance"]=f"${tot:.2f}"
                                    stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                                    stats["checks_done"]+=1
                                    stats["last_error"]=f"✅ LIVE OK! Orders API - {len(orders)} orders"
                                    return stats
                        except Exception as je:
                            last_msg=f"JSON error {je}: {r.text[:150]}"
                            continue
                    elif r.status_code==401:
                        last_msg=f"401 {r.text[:150]}"
                        continue
                    else:
                        continue
                except Exception as e:
                    last_msg=str(e)[:150]
                    continue
        
        stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"]+=1
        stats["last_error"]=f"❌ {last_msg} | Tip: Your key is {key[:12]}... (len {len(key)}). Make sure API Management > KALYAN1212 key > Status Active > Orders Read + Analytics tick > Save. If still 401, regenerate key & wait 10 mins."
    except Exception as e:
        stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"]+=1
        stats["last_error"]=f"Error {str(e)[:300]}"
    return stats

HTML="""<!DOCTYPE html><html><head><title>ClickBank FINAL</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#0f172a;color:#fff;margin:0;padding:20px;}
.card{background:#1e293b;border-radius:15px;padding:20px;margin:15px 0;border-left:5px solid #22c55e;}
h1{color:#22c55e;text-align:center}.value{font-size:32px;font-weight:bold;color:#22c55e}
.small{color:#94a3b8;font-size:14px}.error{color:#fbbf24;font-size:12px;background:#1f2937;padding:12px;border-radius:8px;word-break:break-all;line-height:1.6}
.dot{display:inline-block;width:12px;height:12px;background:#22c55e;border-radius:50%;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}</style>
<script>function r(){fetch('/api/stats').then(x=>x.json()).then(d=>{
document.getElementById('last').innerText=d.last_check;document.getElementById('checks').innerText=d.checks_done;
document.getElementById('sales').innerText=d.total_sales;document.getElementById('bal').innerText=d.balance;
document.getElementById('nick').innerText=d.nickname;document.getElementById('err').innerText=d.last_error||'';
});} setInterval(r,3000); window.onload=r;</script></head><body>
<h1>💰 ClickBank - NEW API Key Format</h1>
<div class="card"><span class="dot"></span> <b>Live - Direct API-L8KM Key</b>
<p class="small">Nickname: <b id="nick">{{ nickname }}</b></p>
<p class="small">Last Check: <span id="last">{{ last_check }}</span></p>
<p class="small">Checks: <span id="checks">{{ checks_done }}</span></p>
<p class="error" id="err">{{ last_error }}</p></div>
<div class="card"><p class="small">TOTAL SALES</p><div class="value" id="sales">{{ total_sales }}</div></div>
<div class="card"><p class="small">TOTAL EARNINGS</p><div class="value" id="bal">{{ balance }}</div></div>
<div class="card" style="border-left-color:#3b82f6"><p>✅ Using Authorization: API-L8KM... (New ClickBank spec - no DEV key)</p>
<p class="small">If 401 persists: Regenerate key in ClickBank API Management, wait 10 mins, copy new API-L8K key to Render Secret Files</p></div></body></html>"""

@app.route('/')
def d():
    fetch()
    return render_template_string(HTML, **stats)
@app.route('/api/stats')
def a():
    fetch()
    return jsonify(stats)
@app.route('/test')
def t():
    return jsonify(fetch())
@app.route('/health')
def h():
    return "OK",200

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
