import time
import random
import re
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WORKING_PROXIES = [] # fetch_and_test_proxies tarafından doldurulacak

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    if WORKING_PROXIES:
        options.add_argument(f"--proxy-server=http://{random.choice(WORKING_PROXIES)}")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def start_bypass_process(url):
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 20)
        
        # --- ADIM 1: LİNKPERİSİ ANA SAYFA ---
        driver.get(url)
        print("📍 Linkperisi açıldı, 'Başlat' aranıyor...")
        
        # Senin JS mantığın: 'Doğrulamayı Başlat' butonunu bul ve tıkla
        start_script = """
        const btn = Array.from(document.querySelectorAll('a, button, .btn, [class*="btn"]')).find(el => {
            const text = el.textContent.trim().toLowerCase();
            return text.includes("başlat") || text.includes("baslat") || text.includes("start");
        });
        if (btn) { btn.click(); return true; }
        return false;
        """
        driver.execute_script(start_script)
        time.sleep(5) # Google sekmesinin/yönlendirmenin açılmasını bekle

        # --- ADIM 2: GOOGLE ARAMA VEYA HEDEF SİTE ---
        # Eğer sistem Google'a attıysa ilk siteye tıkla
        if "google.com" in driver.current_url:
            print("📍 Google sayfası algılandı, ilk siteye giriliyor...")
            google_script = """
            const link = document.querySelector('#search a[href^="http"]:not([href*="google.com"])');
            if (link) { window.location.href = link.href; return true; }
            return false;
            """
            driver.execute_script(google_script)
            time.sleep(5)

        # --- ADIM 3: SİTE İÇİ REKLAM TIKLAMA ---
        print("📍 Siteye girildi, reklam otomasyonu başlıyor...")
        ad_script = """
        const adSelectors = ['iframe[src*="doubleclick"]', 'ins.adsbygoogle', 'a[href*="googleadservices"]', '[id*="ad-"]'];
        for (const s of adSelectors) {
            const ad = document.querySelector(s);
            if (ad) { ad.click(); return true; }
        }
        return false;
        """
        driver.execute_script(ad_script)
        print("⏳ Reklam bekleme süresi (10sn)...")
        time.sleep(10)

        # --- ADIM 4: LİNKPERİSİNE DÖNÜŞ VE KONTROL ---
        # Genelde bu aşamada driver.get(url) ile geri dönmek veya pencere değiştirmek gerekir
        driver.get(url)
        time.sleep(5)
        
        print("📍 'Kontrol Et' butonuna basılıyor...")
        control_script = """
        const btn = Array.from(document.querySelectorAll('a, button, .btn')).find(el => {
            const text = el.textContent.trim().toLowerCase();
            return text.includes("kontrol") || text.includes("check") || text.includes("verify");
        });
        if (btn) { btn.click(); return true; }
        return false;
        """
        driver.execute_script(control_script)
        time.sleep(8) # Senin JS'deki 8 saniyelik bekleme

        # --- ADIM 5: FİNAL LİNKİ AL ---
        source = driver.page_source
        final_links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
        target = next((l for l in final_links if "linkperisi" not in l and "google" not in l), driver.current_url)
        
        return {"status": "success", "url": target}

    except Exception as e:
        return {"status": "error", "msg": f"Otomasyon Hatası: {str(e)}"}
    finally:
        if driver: driver.quit()
