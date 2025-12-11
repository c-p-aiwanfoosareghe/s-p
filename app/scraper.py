import os, hashlib, requests, asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from app.utils import rand_ua, load_proxies_from_env

PROXIES = load_proxies_from_env()
VIDEOS_DIR = "videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

async def scrape_reel(url: str, prefer_proxy: bool = True, max_wait=30):
    proxy = {"server": choose_proxy()} if prefer_proxy and PROXIES else None
    ua = rand_ua()
    video_src = None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(user_agent=ua, proxy=proxy)
        page = await context.new_page()

        # Capture all responses to detect video URLs
        video_candidates = []
        page.on("response", lambda resp: video_candidates.append(resp.url) if ".mp4" in resp.url else None)

        try:
            await page.goto(url, wait_until="networkidle", timeout=max_wait*1000)
            await asyncio.sleep(2)

            # First try meta or video tag
            og = await page.get_attribute('meta[property="og:video"]', 'content')
            v = await page.query_selector("video")
            video_src = og or (await v.get_attribute("src") if v else None)

            # Fallback: check network-captured URLs
            if not video_src and video_candidates:
                video_src = video_candidates[-1]  # usually last mp4 is the reel

            # Download the video if found
            if video_src:
                filename = hashlib.sha256(url.encode()).hexdigest() + ".mp4"
                filepath = os.path.join(VIDEOS_DIR, filename)
                headers = {"User-Agent": ua}
                proxies = {"http": proxy["server"], "https": proxy["server"]} if proxy else None

                r = requests.get(video_src, headers=headers, proxies=proxies, timeout=60)
                if r.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(r.content)
                    video_url = f"/videos/{filename}"
                else:
                    video_url = None
            else:
                video_url = None

            await context.close()
            await browser.close()
            return {
                "url": url,
                "proxy_used": bool(proxy),
                "status": "Scraped successfully" if video_url else "Video not found",
                "video_url": video_url
            }

        except PWTimeoutError:
            await context.close()
            await browser.close()
            return {"url": url, "proxy_used": bool(proxy), "status": "Timeout", "video_url": None}
        except Exception as e:
            await context.close()
            await browser.close()
            return {"url": url, "proxy_used": bool(proxy), "status": f"Error: {str(e)}", "video_url": None}


# Helper function
def choose_proxy():
    if not PROXIES:
        return None
    import random
    return random.choice(PROXIES)
