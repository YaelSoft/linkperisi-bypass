import time
import random
import asyncio
import re
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

WORKING_PROXIES = []

# --- OTONOM PROXY MOTORU ---
async def fetch_proxies():
    global WORKING_PROXIES
    url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                WORKING_PROXIES = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)[:50]
        except: pass
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(fetch_proxies())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")
    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")
    return webdriver.Chrome(options=options)

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/bypass")
async def api_bypass(request: Request):
    data = await request.json()
    url = data.get('url')
    if not url: return {"status": "error", "msg": "Link yok!"}

    def start_engine():
        driver = None
        try:
            driver = get_driver()
            driver.set_page_load_timeout(25)
            driver.get(url)
            
            # --- OTONOM METOT (BYPASS LOGIC) ---
            # 1. Sayfanın yüklenmesini bekle
            wait = WebDriverWait(driver, 15)
            
            # 2. Linkperisi butonunu veya yönlendirmeyi bekle (Manuel metodun otonom hali)
            # Burada sitenin yapısına göre 'Devam Et' veya 'Linki Al' butonuna tıklama simülasyonu yapılır
            time.sleep(5) 
            
            # 3. Yönlendirmeyi takip et
            current_url = driver.current_url
            
            # Eğer hala reklam sayfasındaysak (Örn: buton tıklama gerekliyse)
            # driver.find_element(By.ID, "skip-button").click() gibi komutlar buraya gelir.
            
            if "linkperisi" in current_url:
                # Metot: Sayfa kaynağındaki gizli linki bulmaya çalış
                page_source = driver.page_source
                found_links = re.findall(r'href=[\'"]?([^\'" >]+)', page_source)
                for link in found_links:
                    if "http" in link and "linkperisi" not in link:
                        return {"status": "success", "url": link}
                return {"status": "error", "msg": "Bypass başarısız"}
            
            return {"status": "success", "url": current_url}
        except Exception as e:
            return {"status": "error", "msg": "Zaman aşımı veya engel"}
        finally:
            if driver: driver.quit()

    return await asyncio.to_thread(start_engine)
