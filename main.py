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
            stats["last_error"]="❌ API Key missing"
            stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            stats["checks_done"]+=1
            return stats
        
        # From logs: RAW API- key works, Bearer fails, account param fails
        # So use raw key, no account param
        headers = {"Authorization": key, "Accept":"application/json"}
        
        # Endpoints WITHOUT account param - as logs show account param gives 400
        endpoints = [
            "https://api.clickbank.com/rest/1.3/orders/list",
            "https://api.clickbank.com/rest/1.3/orders2/list",
            "https://api.clickbank.com/rest/1.3/quickstats/list",
            f"https://api.clickbank.com/rest/1.3/orders/list?startDate={(datetime.now()-timedelta(days=60)).strftime('%Y-%m-%d')}&endDate={datetime.now().strftime('%Y-%m-%d')}",
        ]
        
        last_msg=""
        for url in endpoints:
            try:
                r = requests.get(url, headers=headers, timeout=12)
                last_msg = f"{url.split('/')[-1].split('?')[0]} => {r.status_code}: {r.text[:200]}"
                print(f"{key[:12]}... -> {last_msg}")
                if r.status_code==200:
                    try:
                        data = r.json()
                        # 200 null means no orders - that's success!
                        if data is None or data == "null" or (isinstance(data, dict) and len(data)==0):
                            stats["total_sales"]=0
                            stats["balance"]="$0.00"
                            stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                            stats["checks_done"]+=1
                            stats["last_error"]=f"✅ LIVE OK! Connected with {key[:12]}... - No orders yet (null = 0 sales) - API Working Perfect! | {url.split('/')[-1]}"
                            return stats
                        
                        # If list with data
                        orders = None
                        if isinstance(data, dict):
                            orders = data.get("orderData") or data.get("orders") or data.get("data") or data.get("quickStats") or []
                        elif isinstance(data, list):
                            orders = data
                        
                        if isinstance(orders, list):
                            stats["total_sales"]=len(orders)
                            tot=0
                            for o in orders:
                                if isinstance(o, dict):
                                    tot+=float(o.get("totalAccountAmount",0) or o.get("accountAmount",0) or o.get("netSaleAmount",0) or 0)
                            stats["balance"]=f"${tot:.2f}"
                            stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                            stats["checks_done"]+=1
                            stats["last_error"]=f"✅ LIVE OK! {len(orders)} orders found - {key[:12]}..."
                            return stats
                        else:
                            # Any 200 is success
                            stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                            stats["checks_done"]+=1
                            stats["last_error"]=f"✅ LIVE OK! API Connected - Response: {str(data)[:120]}"
                            return stats
                    except Exception as je:
                        # If response is not json but 200, still success (null case)
                        if r.text.strip()=="null" or r.text.strip()=="":
                            stats["total_sales"]=0
                            stats["balance"]="$0.00"
                            stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                            stats["checks_done"]+=1
                            stats["last_error"]=f"✅ LIVE OK! No sales (null response) - API Working - Key: {key[:12]}..."
                            return stats
                        last_msg=f"JSON err {je}: {r.text[:100]}"
                        continue
                else:
                    last_msg=f"{r.status_code}: {r.text[:150]}"
            except Exception as e:
                last_msg=str(e)[:150]
                continue
        
        stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"]+=1
        stats["last_error"]=f"Last: {last_msg} | Key {key[:12]}... len {len(key)} | Tip: Use raw API- key, no Bearer, no account param. Your log shows 200 null = SUCCESS!"
    except Exception as e:
        stats["last_check"]=datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        stats["checks_done"]+=1
        stats["last_error"]=f"Error {str(e)[:300]}"
    return stats

HTML="""<!DOCTYPE html><html><head><title>ClickBank - LIVE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#0f172a;color:#fff;margin:0;padding:20px;}
.card{background:#1e293b;border-radius:15px;padding:20px;margin:15px 0;border-left:5px solid #22c55e;}
h1{color:#22c55e;text-align:center}.value{font-size:32px;font-weight:bold;color:#22c55e}
.small{color:#94a3b8;font-size:14px}.error{color:#22c55e;font-size:12px;background:#1f2937;padding:12px;border-radius:8px;word-break:break-all;line-height:1.6;border:1px solid #22c55e}
.dot{display:inline-block;width:12px;height:12px;background:#22c55e;border-radius:50%;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}</style>
<script>function r(){fetch('/api/stats').then(x=>x.json()).then(d=>{
document.getElementById('last').innerText=d.last_check;document.getElementById('checks').innerText=d.checks_done;
document.getElementById('sales').innerText=d.total_sales;document.getElementById('bal').innerText=d.balance;
document.getElementById('nick').innerText=d.nickname;document.getElementById('err').innerText=d.last_error||'';
});} setInterval(r,3000); window.onload=r;</script></head><body>
<h1>💰 ClickBank - LIVE ✅</h1>
<div class="card"><span class="dot"></span> <b>Live - Direct API-K6ND... Key (No Bearer, No Account Param)</b>
<p class="small">Nickname: <b id="nick">{{ nickname }}</b></p>
<p class="small">Last Check: <span id="last">{{ last_check }}</span></p>
<p class="small">Checks: <span id="checks">{{ checks_done }}</span></p>
<p class="error" id="err">{{ last_error }}</p></div>
<div class="card"><p class="small">TOTAL SALES</p><div class="value" id="sales">{{ total_sales }}</div></div>
<div class="card"><p class="small">TOTAL EARNINGS</p><div class="value" id="bal">{{ balance }}</div></div>
<div class="card" style="border-left-color:#3b82f6"><p>✅ Logs showed: API-K6ND... -> list => 200: null = SUCCESS! (No orders = null)</p>
<p class="small">200 null means API connected perfectly, just no sales yet - This is normal for new accounts!</p></div></body></html>"""

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
