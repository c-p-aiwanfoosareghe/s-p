import os, io, json, time, random, hashlib, base64
import requests
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.utils import rand_ua, polite_sleep, load_proxies_from_env
from app.storage import upload_bytes, _client, S3_BUCKET
from app.db import insert_or_update_reel

PROXIES = load_proxies_from_env()
MAX_PER_PROXY = int(os.getenv("MAX_REQUESTS_PER_PROXY", "10"))
AUTO_SOLVE = os.getenv("AUTO_SOLVE", "false").lower() == "true"
CAPTCHA_PROVIDER = os.getenv("CAPTCHA_PROVIDER", "2captcha")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")

# simple in-memory counters
_proxy_counters = {p: 0 for p in PROXIES} if PROXIES else {}

def choose_proxy():
    if not PROXIES:
        return None
    available = [p for p, c in _proxy_counters.items() if c < MAX_PER_PROXY]
    if not available:
        for k in _proxy_counters: _proxy_counters[k] = 0
        available = list(_proxy_counters.keys())
    p = random.choice(available)
    _proxy_counters[p] += 1
    return p

def detect_captcha_html(html: str, url: str):
    h = html.lower()
    triggers = ["captcha", "confirm you are not a robot", "security check", "we detected unusual", "checkpoint"]
    if any(t in h for t in triggers):
        return True
    if "recaptcha" in h or "g-recaptcha" in h:
        return True
    if "checkpoint" in url:
        return True
    return False

def solve_captcha_2captcha_b64(b64_image: str, timeout=120):
    in_url = "http://2captcha.com/in.php"
    res_url = "http://2captcha.com/res.php"
    r = requests.post(in_url, data={"key": CAPTCHA_API_KEY, "method": "base64", "body": b64_image})
    if r.status_code != 200 or "OK|" not in r.text:
        raise RuntimeError("2captcha submit failed: " + r.text)
    captcha_id = r.text.split("|")[1]
    elapsed = 0
    while elapsed < timeout:
        time.sleep(5)
        elapsed += 5
        rr = requests.get(res_url, params={"key": CAPTCHA_API_KEY, "action":"get", "id":captcha_id})
        if rr.text.startswith("OK|"):
            return rr.text.split("|",1)[1]
        if rr.text == "CAPCHA_NOT_READY":
            continue
        raise RuntimeError("2captcha error: " + rr.text)
    raise RuntimeError("2captcha timeout")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(Exception))
async def scrape_reel(url: str, prefer_proxy: bool = True, max_wait=30):
    proxy = choose_proxy() if prefer_proxy else None
    ua = rand_ua()
    proxy_obj = {"server": proxy} if proxy else None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(user_agent=ua, proxy=proxy_obj, locale="en-US", timezone_id="America/New_York")
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=max_wait*1000)
            # polite behaviour
            await page.mouse.move(100, 100, steps=10)
            await asyncio.sleep(random.uniform(1.0, 2.5))

            html = await page.content()
            if detect_captcha_html(html, page.url):
                if AUTO_SOLVE:
                    # try to find image
                    img_sel = await page.query_selector("img")
                    if img_sel:
                        b = await img_sel.screenshot()
                        b64 = base64.b64encode(b).decode()
                        solution = solve_captcha_2captcha_b64(b64)
                        # attempt to insert solution
                        try:
                            # generic attempts: common input selectors
                            if await page.query_selector("input[name='captcha_response']"):
                                await page.fill("input[name='captcha_response']", solution)
                                if await page.query_selector("button[type='submit']"):
                                    await page.click("button[type='submit']")
                                    await page.wait_for_load_state("networkidle", timeout=10000)
                            else:
                                # fallback: evaluate to set token if reCAPTCHA-like
                                await page.evaluate("""(token)=>{
                                    let el = document.querySelector('textarea#g-recaptcha-response');
                                    if(el) el.value = token;
                                }""", solution)
                                await asyncio.sleep(2)
                        except Exception as e:
                            raise RuntimeError("Auto-solve attempted but failed: " + str(e))
                    else:
                        await context.close()
                        await browser.close()
                        insert_or_update_reel({"url": url, "status":"captcha_detected", "error":"captcha_no_image"})
                        return {"url": url, "status":"captcha_detected", "proxy": proxy}
                else:
                    await context.close()
                    await browser.close()
                    insert_or_update_reel({"url": url, "status":"captcha_detected"})
                    return {"url": url, "status":"captcha_detected", "proxy": proxy}

            # wait for dynamic content
            await asyncio.sleep(1.0)

            # extract possible video url
            video_src = None
            try:
                og = await page.get_attribute('meta[property="og:video"]', 'content')
                if og:
                    video_src = og
                else:
                    v = await page.query_selector("video")
                    if v:
                        video_src = await v.get_attribute("src")
            except Exception:
                video_src = None

            # network sniff fallback
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

            # title/uploader heuristics
            title = await page.title()
            uploader = None
            try:
                el = await page.query_selector("header a")
                uploader = await el.inner_text() if el else None
            except:
                uploader = None

            s3_key = None
            if video_src:
                # download with requests + optional proxy
                headers = {"User-Agent": ua}
                proxies = {}
                if proxy and proxy.startswith("http"):
                    proxies = {"http": proxy, "https": proxy}
                r = requests.get(video_src, headers=headers, proxies=proxies, timeout=60)
                if r.status_code == 200:
                    key = "reels/" + hashlib.sha256(url.encode()).hexdigest() + ".mp4"
                    upload_bytes(key, r.content, content_type="video/mp4")
                    s3_key = key

            meta = {
                "platform": "facebook",
                "url": url,
                "title": title,
                "uploader": uploader,
                "post_id": None,
                "posted_time": None,
                "video_s3_key": s3_key,
                "raw_metadata": {},
                "status": "fetched" if s3_key else ("no_video_found"),
                "error": None
            }
            insert_or_update_reel(meta)
            await context.close()
            await browser.close()
            return meta
        except PWTimeoutError as e:
            await context.close()
            await browser.close()
            insert_or_update_reel({"url": url, "status":"error", "error":"timeout"})
            raise
        except Exception as e:
            try:
                await context.close()
            except:
                pass
            try:
                await browser.close()
            except:
                pass
            insert_or_update_reel({"url": url, "status":"error", "error": str(e)})
            raise
