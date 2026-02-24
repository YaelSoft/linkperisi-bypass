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

# --- 1. PROXY MOTORU (GitHub Repoları Burada) ---
async def fetch_proxies():
    global WORKING_PROXIES
    sources = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
    ]
    while True:
        temp_list = []
        async with httpx.AsyncClient() as client:
            for url in sources:
                try:
                    resp = await client.get(url, timeout=10)
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)
                    temp_list.extend(found)
                except: continue
        
        if temp_list:
            random.shuffle(temp_list)
            WORKING_PROXIES = temp_list[:100] # En hızlı 100 taneyi tut
            print(f"📡 Proxy Havuzu Güncellendi: {len(WORKING_PROXIES)} IP aktif.")
        await asyncio.sleep(300) # 5 dakikada bir yenile

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_proxies())

# --- 2. HAYALET (STEALTH) SELENIUM ---
def get_stealth_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Cloudflare'i uyutan hayalet ayarlar
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    if WORKING_PROXIES:
        proxy = random.choice(WORKING_PROXIES)
        options.add_argument(f"--proxy-server=http://{proxy}")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- 3. ANA SAYFA VE BYPASS ---
@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Slayer Engine Ready."

@app.post("/api/bypass")
async def api_bypass(request: Request):
    data = await request.json()
    url = data.get('url')
    if not url: return {"status": "error", "msg": "Link boş!"}

    def process():
        driver = None
        try:
            driver = get_stealth_driver()
            driver.set_page_load_timeout(40) # Render yavaşlığı için süreyi artırdık
            driver.get(url)
            
            # Cloudflare Challenge'ın geçilmesi için gerçekçi bekleme
            time.sleep(12) 
            
            # Sayfa kaynağındaki asıl hedefi bul (Regex Metodu)
            source = driver.page_source
            # Linkperisi'nin arkasındaki gerçek linki yakalamaya çalış
            links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
            
            target = None
            for l in links:
                if "linkperisi" not in l and "google" not in l and "cloudflare" not in l and "facebook" not in l:
                    target = l
                    break
            
            return {"status": "success", "url": target if target else driver.current_url}
        except Exception:
            return {"status": "error", "msg": "Zaman aşımı (Proxy meşgul)"}
        finally:
            if driver: driver.quit()

    return await asyncio.to_thread(process)
