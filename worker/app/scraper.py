import os, io, asyncio, time, random, json, hashlib
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from app.utils import rand_ua, polite_delay, load_proxies_from_env
from app.storage import upload_bytes
from app.db import insert_or_update_reel
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

PROXIES = load_proxies_from_env()
MAX_PER_PROXY = int(os.getenv("MAX_REQUESTS_PER_PROXY", "10"))
AUTO_SOLVE = os.getenv("AUTO_SOLVE", "false").lower() == "true"
CAPTCHA_PROVIDER = os.getenv("CAPTCHA_PROVIDER", "2captcha")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")

# in-memory counters (single-worker). Replace with Redis counters in prod.
_proxy_counters = {p: 0 for p in PROXIES} if PROXIES else {}

def choose_proxy():
    if not PROXIES:
        return None
    # simple round-robin + respect max usage
    available = [p for p, c in _proxy_counters.items() if c < MAX_PER_PROXY]
    if not available:
        # reset if exhausted - in prod, consider waiting/backoff instead
        for k in _proxy_counters: _proxy_counters[k] = 0
        available = list(_proxy_counters.keys())
    p = random.choice(available)
    _proxy_counters[p] += 1
    return p

async def detect_captcha(page):
    # heuristics: checkpoint in URL, presence of known strings or forms
    try:
        url = page.url.lower()
        if "checkpoint" in url or "login" in url and "checkpoint" in url:
            return True
        html = (await page.content()).lower()
        triggers = ["captcha", "confirm you are not a robot", "security check", "we detected unusual"]
        if any(t in html for t in triggers):
            return True
        # presence of recaptcha iframe
        if await page.query_selector("iframe[src*='recaptcha']"):
            return True
    except Exception:
        return True
    return False

def solve_captcha_image_b64(b64_image: str):
    # 2captcha example (polling)
    if CAPTCHA_PROVIDER == "2captcha":
        in_url = "http://2captcha.com/in.php"
        res_url = "http://2captcha.com/res.php"
        r = requests.post(in_url, data={
            "key": CAPTCHA_API_KEY,
            "method": "base64",
            "body": b64_image
        })
        if "OK|" not in r.text:
            raise RuntimeError("2captcha submit failed: " + r.text)
        captcha_id = r.text.split("|")[1]
        # poll
        for _ in range(20):
            time.sleep(5)
            rr = requests.get(res_url, params={"key": CAPTCHA_API_KEY, "action":"get", "id":captcha_id})
            if rr.text.startswith("OK|"):
                return rr.text.split("|",1)[1]
        raise RuntimeError("2captcha timeout")
    else:
        raise RuntimeError("Unsupported provider")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(Exception))
async def scrape_reel(url: str, prefer_proxy: bool = True, max_wait=20):
    proxy = choose_proxy() if prefer_proxy else None
    proxy_obj = {"server": proxy} if proxy else None
    ua = rand_ua()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(user_agent=ua, proxy=proxy_obj, locale="en-US", timezone_id="America/New_York")
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=max_wait*1000)
            # polite human-like behaviour
            await page.mouse.move(100, 100, steps=10)
            await asyncio.sleep(random.uniform(1.0, 3.0))

            if await detect_captcha(page):
                # mark detection
                if AUTO_SOLVE:
                    # try to capture image or iframe
                    # common approach: find captcha image and screenshot
                    img_sel = await page.query_selector("img")
                    if img_sel:
                        b = await img_sel.screenshot()
                        import base64
                        b64 = base64.b64encode(b).decode()
                        solution = solve_captcha_image_b64(b64)
                        # fill and submit if form exists
                        try:
                            await page.fill("input[name='captcha_response']", solution)
                            await page.click("button[type='submit']")
                            await page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception:
                            raise RuntimeError("Auto-solve attempted but unable to insert solution")
                    else:
                        raise RuntimeError("Auto-solve: captcha found but no image element")
                else:
                    # bail and report
                    await context.close()
                    await browser.close()
                    return {"url": url, "status": "captcha_detected", "proxy": proxy}
            # wait a bit for dynamic JS updates
            await asyncio.sleep(1.5)

            # attempt to extract JSON-LD or OG meta
            jsonld = None
            try:
                elem = await page.query_selector('script[type="application/ld+json"]')
                if elem:
                    text = await elem.inner_text()
                    jsonld = json.loads(text)
            except Exception:
                jsonld = None

            # try OG video meta
            def qattr(sel, attr):
                try:
                    return (await page.query_selector(sel)) and (await page.get_attribute(sel, attr))
                except:
                    return None

            og_video = await qattr('meta[property="og:video"]', 'content') or await qattr('meta[property="og:video:url"]', 'content')
            # fallback to <video> src
            video_src = og_video
            if not video_src:
                v = await page.query_selector("video")
                if v:
                    video_src = await v.get_attribute("src")

            # extra fallback: sniff network for mp4 response (best-effort)
            if not video_src:
                found = []
                def on_response(resp):
                    try:
                        u = resp.url
                        if u and (".mp4" in u or "video" in u):
                            found.append(u)
                    except:
                        pass
                page.on("response", on_response)
                await page.reload()
                await asyncio.sleep(2)
                video_src = found[0] if found else None

            # assemble metadata
            title = await page.title()
            # uploader heuristics
            uploader = None
            try:
                el = await page.query_selector('header a')
                uploader = await el.inner_text() if el else None
            except:
                uploader = None

            # download video bytes (via ordinary requests to avoid Playwright overhead)
            s3_key = None
            if video_src:
                import requests
                head = {"User-Agent": ua}
                # proxy for download if needed
                proxies = {}
                if proxy and proxy.startswith("http"):
                    proxies = {"http": proxy, "https": proxy}
                r = requests.get(video_src, headers=head, proxies=proxies, timeout=60)
                if r.status_code == 200:
                    # create deterministic key
                    key = "reels/" + hashlib.sha256(url.encode()).hexdigest() + ".mp4"
                    # upload to S3/MinIO
                    from app.storage import _client, S3_BUCKET
                    # direct upload via minio client
                    import io
                    _client.put_object(S3_BUCKET, key, io.BytesIO(r.content), length=len(r.content), content_type="video/mp4")
                    s3_key = key

            meta = {
                "platform": "facebook",
                "url": url,
                "title": title,
                "uploader": uploader,
                "post_id": None,
                "posted_time": None,
                "video_s3_key": s3_key,
                "raw_metadata": jsonld or {},
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
            # persist error
            insert_or_update_reel({"url": url, "status":"error", "error": str(e)})
            raise
