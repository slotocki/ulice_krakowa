import urllib.request
import json

with open("data/streets_sample.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for f in data["features"]:
    p = f["properties"]
    patron = p.get("patron")
    if patron and patron.get("image"):
        img_url = patron["image"]
        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
            print(f"[OK] {p['name']}: {status}")
        except Exception as e:
            print(f"[ERROR] {p['name']}: {e}")
