# Adds new posts from the public channel page to news.json (runs daily on GitHub Actions).
import datetime, html, json, re, urllib.request

CHANNEL = "abr20kk"
FILE = "news.json"
MAX_PAGES = 10

def fetch(before=None):
    url = f"https://t.me/s/{CHANNEL}" + (f"?before={before}" if before else "")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (news updater)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

POST = re.compile(r'data-post="' + CHANNEL + r'/(\d+)"(.*?)(?=data-post="|\Z)', re.S)
TEXT = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)

def clean(h):
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h).replace("\u00a0", " ")
    return re.sub(r"\n{3,}", "\n\n", h).strip()

def parse(page):
    out = {}
    for pid, block in POST.findall(page):
        texts = TEXT.findall(block)
        if texts:
            t = clean(texts[-1])          # last one = the post itself (a reply quote comes first)
            if len(t) >= 8:
                out[int(pid)] = t
    return out

def main():
    with open(FILE, encoding="utf-8") as f:
        data = json.load(f)
    have = {p["id"] for p in data["posts"]}
    top = max(have) if have else 0
    found, before = {}, None
    for _ in range(MAX_PAGES):
        got = parse(fetch(before))
        if not got:
            break
        found.update(got)
        low = min(got)
        if low <= top:
            break
        before = low
    new = [{"id": i, "text": t} for i, t in found.items() if i > top]
    if not new:
        print("no new posts")
        return
    data["posts"] = sorted(data["posts"] + new, key=lambda p: -p["id"])
    data["updated"] = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d")
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"added {len(new)} posts")

if __name__ == "__main__":
    main()
