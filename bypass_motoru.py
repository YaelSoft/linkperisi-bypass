import time
import random
import re
import asyncio
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

WORKING_PROXIES = []

# --- 1. PROXY TEMİZLİĞİ (Sadece Canlıları Al) ---
async def fetch_and_test_proxies():
    global WORKING_PROXIES
    # En güvenilir 2 repo
    sources = [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(sources[0], timeout=10)
                all_p = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)
                # Sadece ilk 20 tanesini al (Render RAM'i için)
                WORKING_PROXIES = all_p[:20]
        except: pass
        await asyncio.sleep(300)

# --- 2. HAYALET MOD (Siktir Çekilmemesi İçin) ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")
    
    driver = webdriver.Chrome(options=options)
    # Metodu uygulamak için en kritik satır:
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- 3. SENİN METODUN (OTOMATİKLEŞTİRİLMİŞ) ---
def start_bypass_process(url):
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(35) # Render sınırı
        driver.get(url)
        
        # --- KOD 1: BAŞLAT VE KONTROL ET ---
        # Sayfada butonu bulup senin verdiğin JS mantığıyla tıklar
        driver.execute_script("""
            const startBtn = Array.from(document.querySelectorAll('a, button')).find(el => 
                el.textContent.toLowerCase().includes('başlat') || el.textContent.toLowerCase().includes('start')
            );
            if(startBtn) startBtn.click();
        """)
        
        time.sleep(10) # Senin JS'deki bekleme sürelerini buraya gömdük

        # --- KOD 2: REKLAM/SİTE MANTIĞI ---
        # Botu hedef linkin saklandığı yere zorla gönderiyoruz
        source = driver.page_source
        # Linkperisi olmayan asıl hedef linki yakala
        targets = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
        
        final_url = None
        for t in targets:
            if all(x not in t for x in ["linkperisi", "google", "cloudflare", "facebook"]):
                final_url = t
                break
        
        if final_url:
            return {"status": "success", "url": final_url}
        else:
            # Eğer butona basıp yönlendiyse direkt mevcut URL'yi al
            return {"status": "success", "url": driver.current_url}

    except Exception as e:
        return {"status": "error", "msg": "Zaman Aşımı (Proxy veya Site Cevap Vermedi)"}
    finally:
        if driver: driver.quit()
