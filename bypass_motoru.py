import time
import random
import re
import httpx
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent

# --- PROXY HAVUZU ---
WORKING_PROXIES = []

async def fetch_and_test_proxies():
    global WORKING_PROXIES
    # En sağlam ücretsiz proxy kaynakları
    sources = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt"
    ]
    
    while True:
        print("🔄 Proxy havuzu yenileniyor...")
        raw_list = []
        async with httpx.AsyncClient() as client:
            for url in sources:
                try:
                    resp = await client.get(url, timeout=10)
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)
                    raw_list.extend(found)
                except: continue
        
        if raw_list:
            random.shuffle(raw_list)
            test_batch = raw_list[:50] # Her seferinde 50 tanesini test et
            valid_proxies = []

            async def check_proxy(px):
                try:
                    # Google üzerinden proxy testi
                    async with httpx.AsyncClient(proxies={"http://": f"http://{px}", "https://": f"http://{px}"}, timeout=5) as c:
                        r = await c.get("https://www.google.com")
                        if r.status_code == 200:
                            valid_proxies.append(px)
                except: pass

            await asyncio.gather(*(check_proxy(p) for p in test_batch))
            
            if valid_proxies:
                WORKING_PROXIES = valid_proxies
                print(f"✅ Canlı Proxy Havuzu: {len(WORKING_PROXIES)} adet.")
        
        await asyncio.sleep(300) # 5 dakikada bir güncelle

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")
    
    if WORKING_PROXIES:
        proxy = random.choice(WORKING_PROXIES)
        options.add_argument(f"--proxy-server=http://{proxy}")
        print(f"📡 Kullanılan Canlı Proxy: {proxy}")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def start_bypass_process(url):
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(40)
        driver.get(url)
        
        # Otonom Geçiş Mantığı
        time.sleep(10) # Cloudflare challenge süresi
        
        source = driver.page_source
        # Linkperisi olmayan ilk geçerli linki ara
        links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
        target = next((l for l in links if "linkperisi" not in l and "google" not in l and "cloudflare" not in l), driver.current_url)
        
        return {"status": "success", "url": target}
    except Exception as e:
        return {"status": "error", "msg": "Zaman aşımı (Proxy meşgul)"}
    finally:
        if driver: driver.quit()
