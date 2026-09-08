import csv
import io
import urllib.request
import pandas as pd

print("Iniciando extracción de árbitros y tarjetas reales (Mirror GitHub)...")

LEAGUES_MAP = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "D1": "Bundesliga",
    "I1": "Serie A",
    "F1": "Ligue 1",
}

# Mirror público directo de GitHub sin bloqueos
URL_PATTERN = "https://raw.githubusercontent.com/football-data/data/master/2025-2026/{code}.csv"

headers = {"User-Agent": "Mozilla/5.0"}
referee_rows = []

for league_code, league_name in LEAGUES_MAP.items():
    url = URL_PATTERN.format(code=league_code)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                content = resp.read().decode("utf-8", errors="replace")
                reader = csv.DictReader(io.StringIO(content))
                count = 0
                for row in reader:
                    # Normalización de encabezados para evitar fallas por minúsculas/mayúsculas
                    r = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    referee = r.get("referee", "")
                    home_team = r.get("hometeam", "")

                    if home_team and referee:
                        referee_rows.append({
                            "League": league_name,
                            "Date": r.get("date", ""),
                            "HomeTeam": home_team,
                            "AwayTeam": r.get("awayteam", ""),
                            "Referee": referee,
                            "YellowCards_Home": r.get("hy", "0"),
                            "YellowCards_Away": r.get("ay", "0"),
                            "RedCards_Home": r.get("hr", "0"),
                            "RedCards_Away": r.get("ar", "0"),
                            "Fouls_Home": r.get("hf", "0"),
                            "Fouls_Away": r.get("af", "0"),
                        })
                        count += 1
                print(f"✅ {league_name}: {count} partidos procesados con árbitros reales.")
    except Exception as e:
        print(f"⚠️ Error descargando {league_name}: {e}")

df_referees = pd.DataFrame(referee_rows)
if df_referees.empty:
    df_referees = pd.DataFrame(columns=["League", "Date", "HomeTeam", "AwayTeam", "Referee", "YellowCards_Home", "YellowCards_Away", "RedCards_Home", "RedCards_Away", "Fouls_Home", "Fouls_Away"])

df_referees.to_csv("referees_stats.csv", index=False, encoding="utf-8")
print(f"✅ Total registros guardados en referees_stats.csv: {len(df_referees)}")
