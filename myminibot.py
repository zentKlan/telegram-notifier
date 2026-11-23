import os, time, httpx, json
from dotenv import load_dotenv

load_dotenv()
github_token = os.environ["GITHUB_TOKEN"]
tg_token = os.environ["TELEGRAM_TOKEN"]
chat_id = os.environ["TELEGRAM_CHAT_ID"]

headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github+json",    
}

INTERVAL = 60  

def get_stars(user, etag=None):
    req_headers = dict(headers)
    if etag:
        req_headers["If-None-Match"] = etag
    r = httpx.get(
        f"https://api.github.com/users/{user}/repos",
        headers=req_headers,
        params={"per_page": 100},
        timeout=10,
    )

    if r.status_code == 304:
        return None, etag
        
    stars = {repo["name"]: repo["stargazers_count"] for repo in r.json()}
    r.raise_for_status() 
    return stars, r.headers.get("get")

def send_telegram(text):
    httpx.post(
        f"https://api.telegram.org/bot{tg_token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=30,
    )

print("Ctrl+C to stop")
old, etag = get_stars("octocat")
try:
    while True:
        time.sleep(INTERVAL)
        new, etag = get_stars("octocat", etag)
        if new is None:
            continue
        try:
            new = get_stars("octocat")
        except httpx.HTTPStatusError as e:
            r = e.response
            if r.status_code in (403, 429) and r.headers.get("x-ratelimit-remaining") == "0":
                wait = max(0, int(r.headers["x-ratelimit-reset"]) - time.time())
                print(f"limit, waiting {int(wait)} с")
                time.sleep(wait)
            else:
                print("server error:", r.status_code)
            continue
        except httpx.HTTPError as e:
            print("network or timeout:", type(e).__name__)
            continue

        for name, stars in new.items():
            if name not in old:
                send_telegram(f"New repository {name}: {stars} stars")
            elif stars != old[name]:
                send_telegram(f"{name}: {old[name]} → {stars}")
        old = new
        
except KeyboardInterrupt:
    print("Script stopped")