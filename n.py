import httpx
r = httpx.get("https://api.github.com/users/octocat/repos", timeout=10)
print(r.headers["etag"])
print(r.headers.get("x-ratelimit-limit"))
print(type(r.json()), len(r.json()))
print(r.headers)