import urllib.request
import urllib.parse
import json

PATRON_PAGES = {
    "lema": "Stanisław_Lem",
    "szymborskiej": "Wisława_Szymborska",
    "florianska": "Florian_(męczennik)",
    "dietla": "Józef_Dietl",
    "slowackiego": "Juliusz_Słowacki"
}

with open("data/streets_sample.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for feature in data["features"]:
    sid = feature["properties"]["id"]
    if sid in PATRON_PAGES:
        page = PATRON_PAGES[sid]
        url = "https://pl.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(page)
        req = urllib.request.Request(url, headers={"User-Agent": "KrakowStreets/1.0 (test@krakow.pl)"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                info = json.loads(resp.read().decode("utf-8"))
            thumb = info.get("thumbnail", {}).get("source")
            if thumb and feature["properties"].get("patron"):
                feature["properties"]["patron"]["image"] = thumb
                print(f"[OK] {sid} -> {thumb[:70]}...")
        except Exception as e:
            print(f"[ERR] {sid}: {e}")

with open("data/streets_sample.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nZapisano zaktualizowane miniatury z Wikipedii!")
