import csv
import io
import urllib.request

LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
BASE_URL = "https://www.football-data.co.uk/mmz4281/2526"

print("Iniciando extracción de datos de arbitraje...")

referee_rows = []
for league in LEAGUES:
    url = f"{BASE_URL}/{league}.csv"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                referee = row.get("Referee", "")
                if referee and row.get("HomeTeam"):
                    referee_rows.append(
                        {
                            "Date": row.get("Date", ""),
                            "HomeTeam": row.get("HomeTeam", ""),
                            "AwayTeam": row.get("AwayTeam", ""),
                            "Referee": referee,
                            "HY": row.get("HY", ""),  # Amarillas Local
                            "AY": row.get("AY", ""),  # Amarillas Visitante
                            "HR": row.get("HR", ""),  # Rojas Local
                            "AR": row.get("AR", ""),  # Rojas Visitante
                        }
                    )
    except Exception as e:
        print(f"Error procesando árbitros para {league}: {e}")

with open("referees_stats.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Date",
            "HomeTeam",
            "AwayTeam",
            "Referee",
            "HY",
            "AY",
            "HR",
            "AR",
        ],
    )
    writer.writeheader()
    writer.writerows(referee_rows)

print(
    f"✅ Guardadas estadísticas de arbitraje ({len(referee_rows)} partidos) en referees_stats.csv"
)
