import csv
import io
import urllib.request
import pandas as pd

print("Iniciando extracción de árbitros y tarjetas (Búsqueda dinámica)...")

LEAGUES_MAP = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "D1": "Bundesliga",
    "I1": "Serie A",
    "F1": "Ligue 1",
}

# Probamos las rutas espejo conocidas en orden de más reciente a más antigua
# El código se detiene en la primera que responda 200 OK exitosamente
URL_PATTERNS = [
    "https://raw.githubusercontent.com/football-data/data/master/{code}.csv",
    "https://raw.githubusercontent.com/datasets/football-data/master/data/{code}.csv",
    "https://www.football-data.co.uk/mmz4281/2526/{code}.csv",
    "https://www.football-data.co.uk/mmz4281/2425/{code}.csv",
]

headers = {"User-Agent": "Mozilla/5.0"}
referee_rows = []

for league_code, league_name in LEAGUES_MAP.items():
    success = False
    for pattern in URL_PATTERNS:
        url = pattern.format(code=league_code)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="replace")
                    reader = csv.DictReader(io.StringIO(content))
                    count = 0
                    for row in reader:
                        r = {
                            k.strip().lower(): v.strip()
                            for k, v in row.items()
                            if k
                        }
                        referee = r.get("referee", "")
                        home_team = r.get("hometeam", "")

                        if home_team:
                            referee_rows.append({
                                "League": league_name,
                                "Date": r.get("date", ""),
                                "HomeTeam": home_team,
                                "AwayTeam": r.get("awayteam", ""),
                                "Referee": referee if referee else "Desconocido",
                                "YellowCards_Home": r.get("hy", "0"),
                                "YellowCards_Away": r.get("ay", "0"),
                                "RedCards_Home": r.get("hr", "0"),
                                "RedCards_Away": r.get("ar", "0"),
                                "Fouls_Home": r.get("hf", "0"),
                                "Fouls_Away": r.get("af", "0"),
                            })
                            count += 1
                    if count > 0:
                        print(
                            f"✅ {league_name}: {count} partidos procesados desde {url}"
                        )
                        success = True
                        break
        except Exception:
            continue

    if not success:
        print(f"⚠️ {league_name}: No se pudo obtener datos de ninguna fuente.")

df_referees = pd.DataFrame(referee_rows)
if df_referees.empty:
    df_referees = pd.DataFrame(
        columns=[
            "League",
            "Date",
            "HomeTeam",
            "AwayTeam",
            "Referee",
            "YellowCards_Home",
            "YellowCards_Away",
            "RedCards_Home",
            "RedCards_Away",
            "Fouls_Home",
            "Fouls_Away",
        ]
    )

df_referees.to_csv("referees_stats.csv", index=False, encoding="utf-8")
print(
    f"✅ Total registros guardados en referees_stats.csv: {len(df_referees)}"
)
