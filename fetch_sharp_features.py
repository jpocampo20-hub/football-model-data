import csv
import io
import urllib.request
import pandas as pd

print("Iniciando extracción de datos de arbitraje...")

LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
GITHUB_MIRROR = "https://raw.githubusercontent.com/football-data/data/master"
OFFICIAL_URL = "https://www.football-data.co.uk/mmz4281/2526"

referee_rows = []

for league in LEAGUES:
    content = ""
    url_mirror = f"{GITHUB_MIRROR}/{league}.csv"
    try:
        req = urllib.request.Request(url_mirror, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except Exception:
        try:
            url_official = f"{OFFICIAL_URL}/{league}.csv"
            req = urllib.request.Request(url_official, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                content = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"Nota: No se obtuvieron árbitros para {league}: {e}")

    if content and "Referee" in content:
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            if row.get("Referee") and row.get("HomeTeam"):
                referee_rows.append({
                    "Date": row.get("Date", ""),
                    "HomeTeam": row.get("HomeTeam", ""),
                    "AwayTeam": row.get("AwayTeam", ""),
                    "Referee": row.get("Referee", ""),
                    "YellowCards_Home": row.get("HY", 0),
                    "YellowCards_Away": row.get("AY", 0),
                    "RedCards_Home": row.get("HR", 0),
                    "RedCards_Away": row.get("AR", 0),
                })

df_referees = pd.DataFrame(referee_rows)
df_referees.to_csv("referees_stats.csv", index=False, encoding="utf-8")
print(f"✅ Guardadas estadísticas de {len(df_referees)} partidos con árbitros en referees_stats.csv")
