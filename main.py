import time
import asyncio
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_stealth_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 🕵️ GİZLİLİK AYARLARI (Cloudflare'i Uyutmak İçin)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    
    # Bot izlerini silen kritik script
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Slayer Engine Active"

@app.post("/api/bypass")
async def api_bypass(request: Request):
    data = await request.json()
    url = data.get('url')
    
    def process():
        driver = None
        try:
            driver = get_stealth_driver()
            # Cloudflare'in çözülmesi için bekleme süresini artırıyoruz
            driver.set_page_load_timeout(45) 
            driver.get(url)
            
            # 1. Cloudflare challenge'ın geçilmesi için gerçekçi bir bekleme
            time.sleep(10) 
            
            # 2. Eğer hala Cloudflare sayfasındaysak veya engellendiysek:
            if "cloudflare" in driver.current_url or "challenge" in driver.page_source:
                return {"status": "error", "msg": "Cloudflare Engelini Geçemedim, Tekrar Dene"}

            # 3. Sayfa kaynağındaki asıl linki çek (Senin metot)
            page_source = driver.page_source
            links = re.findall(r'href=[\'"]?([^\'" >]+)', page_source)
            
            target = None
            for l in links:
                if "http" in l and "linkperisi" not in l and "google" not in l and "facebook" not in l:
                    target = l
                    break
            
            return {"status": "success", "url": target if target else driver.current_url}
                
        except Exception as e:
            return {"status": "error", "msg": "Sistem Meşgul veya Proxy Engelli"}
        finally:
            if driver: driver.quit()

    return await asyncio.to_thread(process)
