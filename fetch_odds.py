import csv
import io
import urllib.request
import pandas as pd

LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
BASE_URLS = [
    "https://www.football-data.co.uk/mmz4281/2526",
    "https://www.football-data.co.uk/mmz4281/2425",
]

all_data = []
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

print("Iniciando extracción de cuotas pre-partido...")

for league in LEAGUES:
    downloaded = False
    for base_url in BASE_URLS:
        url = f"{base_url}/{league}.csv"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="replace")
                    reader = csv.DictReader(io.StringIO(content))
                    count = 0
                    for row in reader:
                        if row.get("HomeTeam") and row.get("Date"):
                            row["League"] = league
                            all_data.append(row)
                            count += 1
                    print(
                        f"✅ {league}: {count} partidos procesados desde {base_url}"
                    )
                    downloaded = True
                    break
        except Exception:
            continue

    if not downloaded:
        print(
            f"⚠️ {league}: No se pudo descargar de ninguna ruta. Se omitirá esta liga."
        )

if all_data:
    df = pd.DataFrame(all_data)
else:
    df = pd.DataFrame(
        columns=[
            "League",
            "Date",
            "HomeTeam",
            "AwayTeam",
            "B365H",
            "B365D",
            "B365A",
        ]
    )

df.to_csv("odds_data.csv", index=False, encoding="utf-8")
print(f"✅ Proceso finalizado. Total registros en odds_data.csv: {len(df)}")
