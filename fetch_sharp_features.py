import csv
import io
import urllib.request
import pandas as pd

print("Iniciando extracción de árbitros y tarjetas para partidos jugados...")

LEAGUES_MAP = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "D1": "Bundesliga",
    "I1": "Serie A",
    "F1": "Ligue 1",
}

# Espejos de GitHub con los CSVs actualizados que contienen los partidos de la temporada en curso
URL_TEMPLATES = [
    "https://raw.githubusercontent.com/football-data/data/master/2026-2027/{code}.csv",
    "https://raw.githubusercontent.com/football-data/data/master/2025-2026/{code}.csv",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

referee_rows = []

for league_code, league_name in LEAGUES_MAP.items():
    downloaded = False
    for url_pattern in URL_TEMPLATES:
        url = url_pattern.format(code=league_code)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="replace")
                    reader = csv.DictReader(io.StringIO(content))

                    count = 0
                    for row in reader:
                        # Normalizar claves a minúsculas para evitar fallas por formato (HY vs hy)
                        r = {
                            k.strip().lower(): v.strip()
                            for k, v in row.items()
                            if k
                        }

                        referee = r.get("referee", "Desconocido")
                        home_team = r.get("hometeam", "")
                        away_team = r.get("awayteam", "")

                        # Solo procesamos filas de partidos efectivamente disputados (con marcador o tarjetas)
                        yellow_home = r.get("hy", r.get("homeyellow", ""))
                        yellow_away = r.get("ay", r.get("awayyellow", ""))

                        if home_team and (
                            yellow_home != "" or referee != "Desconocido"
                        ):
                            referee_rows.append({
                                "League": league_name,
                                "Date": r.get("date", ""),
                                "HomeTeam": home_team,
                                "AwayTeam": away_team,
                                "Referee": referee,
                                "YellowCards_Home": yellow_home if yellow_home != "" else "0",
                                "YellowCards_Away": yellow_away if yellow_away != "" else "0",
                                "RedCards_Home": r.get("hr", "0"),
                                "RedCards_Away": r.get("ar", "0"),
                                "Fouls_Home": r.get("hf", "0"),
                                "Fouls_Away": r.get("af", "0"),
                            })
                            count += 1

                    if count > 0:
                        print(
                            f"✅ {league_name}: {count} partidos procesados con tarjetas y árbitros reales."
                        )
                        downloaded = True
                        break
        except Exception:
            continue

    if not downloaded:
        print(
            f"⚠️ {league_name}: No se pudieron mapear tarjetas en esta ruta."
        )

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
    f"\n✅ Proceso completado. Total registros reales en referees_stats.csv: {len(df_referees)}"
)
