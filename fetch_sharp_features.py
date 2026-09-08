import csv
import io
import urllib.request
import pandas as pd

print("Iniciando extracción de árbitros (Temporada 2026-2027)...")

LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
BASE_URL = "https://www.football-data.co.uk/mmz4281/2627"

referee_rows = []
for league in LEAGUES:
    url = f"{BASE_URL}/{league}.csv"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                if row.get("Referee") and row.get("HomeTeam"):
                    referee_rows.append(
                        {
                            "Date": row.get("Date", ""),
                            "HomeTeam": row.get("HomeTeam", ""),
                            "AwayTeam": row.get("AwayTeam", ""),
                            "Referee": row.get("Referee", ""),
                            "YellowCards_Home": row.get("HY", 0),
                            "YellowCards_Away": row.get("AY", 0),
                            "RedCards_Home": row.get("HR", 0),
                            "RedCards_Away": row.get("AR", 0),
                        }
                    )
    except Exception as e:
        print(f"Nota: No se pudieron bajar árbitros para {league}: {e}")

df_referees = pd.DataFrame(referee_rows)
df_referees.to_csv("referees_stats.csv", index=False, encoding="utf-8")
print(
    f"✅ Guardadas estadísticas de {len(df_referees)} partidos con árbitros en referees_stats.csv"
)
