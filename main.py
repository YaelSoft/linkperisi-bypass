import time
import random
import asyncio
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Cloudflare ve bot korumalarını uyutmak için:
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    # Bot olduğumuzu gizleyen JavaScript komutu
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except: return "Slayer Engine Active"

@app.post("/api/bypass")
async def api_bypass(request: Request):
    data = await request.json()
    url = data.get('url')
    
    # Render'ın 5xx hatası vermemesi için işlemi thread'e salıyoruz
    def process():
        driver = None
        try:
            driver = get_driver()
            driver.set_page_load_timeout(20)
            driver.get(url)
            
            # --- MANUEL METODUN OTONOM HALİ ---
            # 1. Sayfada 'Devam Et' veya 'Linki Al' benzeri butonları tara
            time.sleep(6) # Linkperisi genelde 5 saniye bekletir
            
            # Sayfa içindeki tüm linkleri çek ve Linkperisi olmayan ilk harici linke odaklan
            page_source = driver.page_source
            links = re.findall(r'href=[\'"]?([^\'" >]+)', page_source)
            
            target = None
            for l in links:
                if "http" in l and "linkperisi" not in l and "google" not in l and "facebook" not in l:
                    target = l
                    break
            
            if target:
                return {"status": "success", "url": target}
            else:
                # Eğer link bulunamadıysa son durulan URL'yi döndür (Bazen direkt yönlenir)
                final_url = driver.current_url
                return {"status": "success", "url": final_url}
                
        except Exception as e:
            return {"status": "error", "msg": "Sunucu Yükü Fazla, Tekrar Dene"}
        finally:
            if driver: driver.quit()

    # Render'ın zaman aşımına düşüp 5xx vermemesi için async çalıştır
    return await asyncio.to_thread(process)
