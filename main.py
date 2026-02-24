import time
import asyncio
import re
import httpx
import random
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

WORKING_PROXIES = []

# --- 1. PROXY REPOLARI BURADA (HER 5 DAKİKADA BİR ÇEKER) ---
async def fetch_proxies():
    global WORKING_PROXIES
    # En taze ve ücretsiz proxy listeleri
    sources = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt"
    ]
    while True:
        proxies = []
        async with httpx.AsyncClient() as client:
            for url in sources:
                try:
                    resp = await client.get(url, timeout=10)
                    # IP:PORT formatını ayıkla
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)
                    proxies.extend(found)
                except: continue
        
        if proxies:
            random.shuffle(proxies)
            WORKING_PROXIES = proxies[:100] # En fazla 100 tanesini sakla
            print(f"✅ Proxy Havuzu Güncellendi: {len(WORKING_PROXIES)} IP hazır.")
        
        await asyncio.sleep(300) # 5 dakikada bir yenile

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_proxies())

# --- 2. GİZLİ (STEALTH) DRIVER ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Havuzdan rastgele bir proxy seç
    if WORKING_PROXIES:
        proxy = random.choice(WORKING_PROXIES)
        options.add_argument(f"--proxy-server=http://{proxy}")
        print(f"📡 Kullanılan Proxy: {proxy}")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- 3. ANA SAYFA VE BYPASS ---
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/bypass")
async def api_bypass(request: Request):
    data = await request.json()
    url = data.get('url')
    
    def process():
        driver = None
        try:
            driver = get_driver()
            driver.set_page_load_timeout(35) # Zaman aşımını 35 saniyeye çıkardık
            driver.get(url)
            
            # Cloudflare'in botu tartması için bekleme
            time.sleep(8) 
            
            # Sayfa yönlendirmesi bittiyse veya butona basılmışsa yeni linki çek
            final_url = driver.current_url
            
            # Eğer hala reklamlı sitedeyse sayfa kaynağını tara
            if "linkperisi" in final_url or "cloudflare" in final_url:
                source = driver.page_source
                # Harici bir link ara
                links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
                for l in links:
                    if "linkperisi" not in l and "google" not in l and "cloudflare" not in l:
                        return {"status": "success", "url": l}
            
            return {"status": "success", "url": final_url}
                
        except Exception as e:
            return {"status": "error", "msg": "Zaman Aşımı (Sunucu/Proxy Meşgul)"}
        finally:
            if driver: driver.quit()

    return await asyncio.to_thread(process)
