import asyncio
from bypass_motoru import fetch_and_test_proxies
import os
import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify
from bypass_motoru import start_bypass_process

app = Flask(__name__, template_folder='.') # index.html aynı klasörde olduğu için

    
    import threading
    threading.Thread(target=run_loop, daemon=True).start()

DB_NAME = "history.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.cursor().execute('''CREATE TABLE IF NOT EXISTS logs 
                          (id INTEGER PRIMARY KEY, original TEXT, bypassed TEXT, date TEXT, ip TEXT)''')
        conn.commit()

init_db()
def start_proxy_engine():
    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # bypass_motoru içindeki otonom fonksiyonun
        from bypass_motoru import fetch_and_test_proxies
        loop.run_until_complete(fetch_and_test_proxies())
    
    import threading
    threading.Thread(target=run_loop, daemon=True).start()

# Flask 3.0+ için uygulama ayağa kalkarken çalıştır
with app.app_context():
    start_proxy_engine()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/bypass', methods=['POST'])
def api_bypass():
    data = request.json
    url = data.get('url')
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if not url: return jsonify({"status": "error", "msg": "Link boş olamaz!"})

    result = start_bypass_process(url)
    
    if result["status"] == "success":
        with sqlite3.connect(DB_NAME) as conn:
            conn.cursor().execute("INSERT INTO logs (original, bypassed, date, ip) VALUES (?, ?, ?, ?)", 
                                  (url, result["url"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_ip))
            conn.commit()
    
    return jsonify(result)

@app.route('/logs')
def view_logs():
    with sqlite3.connect(DB_NAME) as conn:
        logs = conn.cursor().execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify(logs)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
