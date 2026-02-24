import time
import random
import re
import asyncio
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

WORKING_PROXIES = []

# --- 1. PROXY HAVUZU (REPOLAR BURADA) ---
async def fetch_and_test_proxies():
    global WORKING_PROXIES
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
                    proxies.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text))
                except: continue
        if proxies:
            random.shuffle(proxies)
            WORKING_PROXIES = proxies[:50] # En taze 50 taneyi tut
        await asyncio.sleep(300)

# --- 2. CLOUDFLARE VE CAPTCHA SAVAR DRIVER ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 🕵️ HAYALET MOD (Cloudflare'i geçmek için en kritik kısım)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")

    driver = webdriver.Chrome(options=options)
    # Bot izlerini silen script
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- 3. TAM OTOMATİK BYPASS (SENİN JS MANTIĞINLA) ---
def start_bypass_process(url):
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(45)
        driver.get(url)
        
        # ADIM 1: "Doğrulamayı Başlat" Simülasyonu
        time.sleep(5)
        try:
            start_btn = driver.execute_script("""
                return Array.from(document.querySelectorAll('a, button')).find(el => 
                    el.textContent.toLowerCase().includes('başlat') || el.textContent.toLowerCase().includes('start')
                );
            """)
            if start_btn: driver.execute_script("arguments[0].click();", start_btn)
        except: pass

        # ADIM 2: Bekleme ve Kontrol (Captcha çıkmaması için 'insansı' bekleme)
        time.sleep(12) 

        # ADIM 3: Hedef Linki Cımbızla Çekme
        source = driver.page_source
        # Eğer Cloudflare çıkarsa burada takılır, o yüzden proxy değişimi önemli
        if "cloudflare" in driver.current_url:
            return {"status": "error", "msg": "Cloudflare Engeli (Proxy Değiştiriliyor)"}

        # Linkperisi olmayan ilk harici linki bul
        links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
        target = next((l for l in links if "linkperisi" not in l and "google" not in l and "cloudflare" not in l), None)

        if target:
            return {"status": "success", "url": target}
        else:
            return {"status": "success", "url": driver.current_url} # Bazen direkt yönlenir

    except Exception as e:
        return {"status": "error", "msg": "Sistem Meşgul / Zaman Aşımı"}
    finally:
        if driver: driver.quit()
