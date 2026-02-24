import time
import random
import re
import httpx
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent

WORKING_PROXIES = []

async def fetch_and_test_proxies():
    global WORKING_PROXIES
    sources = ["https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"]
    while True:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(sources[0], timeout=10)
                WORKING_PROXIES = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)[:30]
            except: pass
        await asyncio.sleep(300)

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def start_bypass_process(url):
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(35)
        driver.get(url)
        time.sleep(8) # Bekleme süresi
        
        source = driver.page_source
        links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
        target = next((l for l in links if "linkperisi" not in l and "google" not in l), driver.current_url)
        
        return {"status": "success", "url": target}
    except:
        return {"status": "error", "msg": "Zaman aşımı (Sistem Meşgul)"}
    finally:
        if driver: driver.quit()
