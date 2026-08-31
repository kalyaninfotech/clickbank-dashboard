import os, requests
from flask import Flask, jsonify

app = Flask(__name__)
CAPTAIN_DEV = "DEV-123456789012345678901234567890123456"

def get_key():
    for name in ["CLICKBANK_API_KEY","CLICKBANK_DEV_KEY"]:
        for path in [f"/etc/secrets/{name}", f"/etc/secrets/{name.lower()}"]:
            if os.path.exists(path):
                with open(path) as f:
                    v=f.read().strip()
                    if v: return v
        v=os.environ.get(name,"").strip()
        if v: return v
    return ""

@app.route('/')
def home():
    key = get_key()
    nick = os.environ.get("CLICKBANK_NICKNAME","KALYAN1212")
    # Try to get from secret files
    try:
        if os.path.exists("/etc/secrets/CLICKBANK_NICKNAME"):
            with open("/etc/secrets/CLICKBANK_NICKNAME") as f:
                nick=f.read().strip() or nick
    except: pass
    
    auth = f"{CAPTAIN_DEV}:{key}"
    headers = {"Authorization": auth, "Accept":"application/json"}
    
    results = []
    urls = [
        f"https://api.clickbank.com/rest/1.3/orders/list",
        f"https://api.clickbank.com/rest/1.3/orders2/list",
        f"https://api.clickbank.com/rest/1.3/analytics/affiliate/{nick}/summary?startDate=2025-07-01&endDate=2026-08-31",
    ]
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            results.append({"url": url, "status": r.status_code, "body": r.text[:800]})
        except Exception as e:
            results.append({"url": url, "status": "error", "body": str(e)[:500]})
    
    html = f"""
    <h1>DEBUG - ClickBank Raw Response</h1>
    <p>Nickname: {nick} | Key: {key[:15]}... len={len(key)} | Auth: {CAPTAIN_DEV[:10]}...:{key[:8]}...</p>
    <hr>
    """
    for res in results:
        html += f"<h3>{res['url']}</h3><p>Status: {res['status']}</p><pre style='background:#111;color:#0f0;padding:10px;overflow:auto;'>{res['body']}</pre><hr>"
    
    html += "<p>If 406 -> ClickBank > API Management > Edit Key > IP Whitelist > Add 0.0.0.0/0 > Save<br>If 0 sales -> Your KALYAN1212 has no sales in last 60 days, that's normal!</p>"
    return html

@app.route('/test')
def test():
    return home()

@app.route('/health')
def h():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
