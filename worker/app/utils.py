import random, time, os
USER_AGENTS = [
    # minimal list — extend this in production
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
]

def rand_ua():
    return random.choice(USER_AGENTS)

def polite_delay(min_s=1.5, max_s=4.0):
    t = random.uniform(min_s, max_s)
    time.sleep(t)
    return t

def load_proxies_from_env():
    val = os.getenv("PROXY_LIST", "")
    return [p.strip() for p in val.split(",") if p.strip()]
