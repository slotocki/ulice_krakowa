import urllib.request
import re

url = "https://rcin.org.pl/dlibra/results?q=Nazwy+ulic+Krakowa+Supranowicz"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8")
        matches = re.findall(r'/dlibra/publication/\d+', html)
        print("Found RCIN matches:", set(matches))
except Exception as e:
    print("Error:", e)
