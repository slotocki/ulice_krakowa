import json
import urllib.request

url = "https://api.openstreetmap.org/api/0.6/way/39393926/full.json"
req = urllib.request.Request(url, headers={"User-Agent": "KrakowStreetsDirect/1.0"})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

nodes = {el["id"]: [el["lon"], el["lat"]] for el in data["elements"] if el["type"] == "node"}
way = next(el for el in data["elements"] if el["type"] == "way")
coords = [nodes[nid] for nid in way["nodes"] if nid in nodes]

print(f"Pobrano {len(coords)} punktow obrysu Parku im. Wislawy Szymborskiej!")

# Aktualizacja data/streets_sample.json
with open("data/streets_sample.json", "r", encoding="utf-8") as f:
    sample = json.load(f)

for f in sample["features"]:
    if f["properties"]["id"] == "szymborskiej":
        f["geometry"] = {
            "type": "LineString",
            "coordinates": coords
        }
        f["properties"]["prefix"] = "park / aleja"
        f["properties"]["full_name"] = "Park im. Wisławy Szymborskiej"
        print("Zaktualizowano szymborskiej!")

with open("data/streets_sample.json", "w", encoding="utf-8") as f:
    json.dump(sample, f, ensure_ascii=False, indent=2)
