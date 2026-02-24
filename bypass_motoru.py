import time
import random
import re
import asyncio
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

WORKING_PROXIES = []

# --- 1. TAZE PROXY REPOLARI ---
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
                WORKING_PROXIES = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)[:20]
        except: pass
        await asyncio.sleep(300)

# --- 2. HAYALET MOD AYARLARI ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- 3. SENİN METODUN (ZORLAYICI VERSİYON) ---
def start_bypass_process(url):
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(40) # Render zaman aşımı koruması
        
        # ADIM 1: LİNKPERİSİ GİRİŞ
        driver.get(url)
        time.sleep(5)

        # ADIM 2: "BAŞLAT" BUTONUNA JS İLE BAS
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('a, button')).find(el => 
                el.textContent.toLowerCase().includes('başlat') || el.textContent.toLowerCase().includes('start')
            );
            if(btn) btn.click();
        """)
        time.sleep(8) # Senin JS'deki bekleme süresi

        # ADIM 3: GOOGLE / REKLAM SİMÜLASYONU (BOTU KANDIRMA)
        # Direkt "Kontrol Et" aşamasına geçebilmek için sayfayı "Görev Tamamlandı" moduna sokuyoruz
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # ADIM 4: "KONTROL ET" BUTONUNA BAS
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('a, button')).find(el => 
                el.textContent.toLowerCase().includes('kontrol') || el.textContent.toLowerCase().includes('check')
            );
            if(btn) btn.click();
        """)
        time.sleep(10) # Doğrulama beklemesi

        # ADIM 5: LİNKİ SÖKÜP AL (REGEX + CURRENT_URL)
        final_url = driver.current_url
        
        # Eğer hala linkperisi'ndeysek butona tekrar basmayı dene veya linki ayıkla
        if "linkperisi.com" in final_url:
            source = driver.page_source
            links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
            for l in links:
                if all(x not in l for x in ["linkperisi", "google", "cloudflare", "facebook"]):
                    return {"status": "success", "url": l}
            
            return {"status": "error", "msg": "Link koruması aşılamadı (Döngü Hatası)"}

        return {"status": "success", "url": final_url}

    except Exception as e:
        return {"status": "error", "msg": "Zaman Aşımı (Proxy veya Sunucu Yetmedi)"}
    finally:
        if driver: driver.quit()
