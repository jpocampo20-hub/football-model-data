import csv
import io
import urllib.request
import pandas as pd

LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
BASE_URLS = [
    "https://www.football-data.co.uk/mmz4281/2526",
    "https://www.football-data.co.uk/mmz4281/2627",
]

print("Iniciando extracción de estadísticas de árbitros...")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

referee_rows = []

for league in LEAGUES:
    downloaded = False
    for base_url in BASE_URLS:
        url = f"{base_url}/{league}.csv"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="replace")
                    if "Referee" in content or "HomeTeam" in content:
                        reader = csv.DictReader(io.StringIO(content))
                        count = 0
                        for row in reader:
                            if row.get("HomeTeam") and row.get("Date"):
                                referee_rows.append({
                                    "Date": row.get("Date", ""),
                                    "HomeTeam": row.get("HomeTeam", ""),
                                    "AwayTeam": row.get("AwayTeam", ""),
                                    "Referee": row.get("Referee", "Unknown"),
                                    "YellowCards_Home": row.get("HY", 0),
                                    "YellowCards_Away": row.get("AY", 0),
                                    "RedCards_Home": row.get("HR", 0),
                                    "RedCards_Away": row.get("AR", 0),
                                })
                                count += 1
                        print(
                            f"✅ {league}: {count} partidos procesados para árbitros desde {base_url}"
                        )
                        downloaded = True
                        break
        except Exception:
            continue

    if not downloaded:
        print(
            f"⚠️ {league}: No se obtuvieron datos de árbitros desde ninguna ruta."
        )

# Guardar dataframe
df_referees = pd.DataFrame(referee_rows)
df_referees.to_csv("referees_stats.csv", index=False, encoding="utf-8")
print(
    f"✅ Guardadas estadísticas de {len(df_referees)} partidos en referees_stats.csv"
)
