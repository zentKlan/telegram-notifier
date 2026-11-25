import os, time, httpx, json, logging
from dotenv import load_dotenv

load_dotenv()
github_token = os.environ["GITHUB_TOKEN"]
tg_token = os.environ["TELEGRAM_TOKEN"]
chat_id = os.environ["TELEGRAM_CHAT_ID"]
git_user = os.environ["GITHUB_USERNAME"]
INTERVAL = int(os.environ["INTERVAL"])

logging.basicConfig(
    level=logging.info,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("stars.log", encoding="utf-8")
    ]
)

headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github+json",    
}

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
        
    r.raise_for_status() 
    stars = {repo["name"]: repo["stargazers_count"] for repo in r.json()}    
    return stars, r.headers.get("etag")

def send_telegram(text):
    r = httpx.post(
        f"https://api.telegram.org/bot{tg_token}/sendMessage",
        json={"chat_id": chat_id, "text": str(text)[2:-2]},
        timeout=30,
    )
    r.raise_for_status()
    print("Notified")


def find_changes(old, new):
    changes = []
    for name, stars in new.items():
        if name not in old:
            changes.append(f"New repository {name}: {stars} stars")
        elif stars != old[name]:
            changes.append(f"{name}: {old[name]} --> {stars}")    
    return changes



print("Ctrl+C to stop")
old, etag = get_stars(git_user)
try:
    while True:
        try:
            time.sleep(INTERVAL)
            new, etag = get_stars(git_user, etag)
            if new is None:
                print(old)
                print("304")
                continue                
                    
        except httpx.HTTPStatusError as e:
            r = e.response
            if r.status_code in (403, 429) and r.headers.get("x-ratelimit-remaining") == "0":
                wait = max(0, int(r.headers["x-ratelimit-reset"]) - time.time())
                print(f"limit, waiting {int(wait)} c")
                time.sleep(wait)
            else:
                print("server error:", r.status_code)
            continue
        except httpx.HTTPError as e:
            print("network or timeout:", type(e).__name__)
            continue
        
        send_telegram(find_changes(old, new))
        old = new
        
except KeyboardInterrupt:
    print("Script stopped")