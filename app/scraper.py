import os, io, json, time, random, hashlib, base64
import requests
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

from utils import rand_ua, polite_sleep, load_proxies_from_env

PROXIES = load_proxies_from_env()
MAX_PER_PROXY = int(os.getenv("MAX_REQUESTS_PER_PROXY", "10"))
AUTO_SOLVE = os.getenv("AUTO_SOLVE", "false").lower() == "true"
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")

_proxy_counters = {p: 0 for p in PROXIES} if PROXIES else {}

def choose_proxy():
    if not PROXIES:
        return None
    available = [p for p, c in _proxy_counters.items() if c < MAX_PER_PROXY]
    if not available:
        for k in _proxy_counters:
            _proxy_counters[k] = 0
        available = list(_proxy_counters.keys())
    p = random.choice(available)
    _proxy_counters[p] += 1
    return p

def detect_captcha_html(html: str, url: str):
    h = html.lower()
    triggers = ["captcha", "confirm you are not a robot", "security check", "unusual activity"]
    if any(t in h for t in triggers): return True
    if "recaptcha" in h or "g-recaptcha" in h: return True
    if "checkpoint" in url: return True
    return False


async def scrape_reel(url: str, prefer_proxy: bool = True, max_wait=30):
    proxy = choose_proxy() if prefer_proxy else None
    ua = rand_ua()
    proxy_obj = {"server": proxy} if proxy else None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent=ua,
            proxy=proxy_obj,
            locale="en-US",
            timezone_id="America/New_York"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=max_wait * 1000)
            await asyncio.sleep(random.uniform(1.0, 2.5))

            html = await page.content()
            if detect_captcha_html(html, page.url):
                await browser.close()
                return {"status": "captcha_detected", "url": url, "proxy": proxy}

            # extract title
            title = await page.title()

            # extract uploader
            try:
                el = await page.query_selector("header a")
                uploader = await el.inner_text() if el else None
            except:
                uploader = None

            # extract video URL
            video_src = await page.get_attribute('meta[property="og:video"]', 'content')
            if not video_src:
                v = await page.query_selector("video")
                if v:
                    video_src = await v.get_attribute("src")

            # fallback sniff
            if not video_src:
                found = []

                def grab(resp):
                    try:
                        u = resp.url
                        if u and (".mp4" in u or "video" in u):
                            found.append(u)
                    except:
                        pass

                page.on("response", grab)
                await page.reload()
                await asyncio.sleep(2)
                if found:
                    video_src = found[0]

            await browser.close()

            return {
                "status": "success" if video_src else "no_video_found",
                "url": url,
                "title": title,
                "uploader": uploader,
                "video_url": video_src
            }

        except PWTimeoutError:
            await browser.close()
            return {"status": "error", "error": "timeout", "url": url}

        except Exception as e:
            try: await browser.close()
            except: pass
            return {"status": "error", "error": str(e), "url": url}
