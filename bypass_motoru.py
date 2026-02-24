import time
import random
import re
import httpx
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent

WORKING_PROXIES = []

# --- 1. PROXY MOTORU (GitHub Repoları) ---
async def fetch_and_test_proxies():
    global WORKING_PROXIES
    sources = [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(sources[0], timeout=10)
                WORKING_PROXIES = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)[:30]
        except: pass
        await asyncio.sleep(300)

# --- 2. ANTİ-BOT DRIVER ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Cloudflare'i Kandıran Kritik Ayarlar
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")
    
    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")

    driver = webdriver.Chrome(options=options)
    
    # Bot izlerini tarayıcıdan silen JavaScript
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- 3. BYPASS İŞLEMİ ---
def start_bypass_process(url):
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(45)
        driver.get(url)
        
        # Cloudflare'in "Bekleyin" ekranını geçmesi için gerçekçi süre
        time.sleep(15) 
        
        # Eğer hala Cloudflare'de takılı kaldıysa (url'de cloudflare geçiyorsa)
        if "cloudflare" in driver.current_url:
            return {"status": "error", "msg": "Cloudflare engeli aşılamadı, tekrar dene."}

        source = driver.page_source
        # Linkperisi'nin arkasındaki asıl linki cımbızla çekiyoruz
        links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
        
        target = None
        for l in links:
            # Reklam, google veya cloudflare linklerini ele
            if all(x not in l for x in ["linkperisi", "google", "cloudflare", "facebook", "twitter"]):
                target = l
                break
        
        if target:
            return {"status": "success", "url": target}
        else:
            # Link bulunamadıysa gidilen son adresi ver (Bazen direkt yönlenir)
            return {"status": "success", "url": driver.current_url}
            
    except Exception:
        return {"status": "error", "msg": "Zaman aşımı (Proxy/Site Meşgul)"}
    finally:
        if driver: driver.quit()
