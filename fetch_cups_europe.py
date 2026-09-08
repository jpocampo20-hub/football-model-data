import pandas as pd
import soccerdata as sd

print("Iniciando extracción de partidos y métricas avanzadas (Understat)...")

LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]

matches = []

try:
    # Understat consulta APIs JSON directamente y no sufre bloqueos de Cloudflare
    understat = sd.Understat(leagues=LEAGUES, seasons="2025")
    schedule = understat.read_schedule().reset_index()

    for _, row in schedule.iterrows():
        matches.append({
            "competition": row.get("league", ""),
            "date": str(row.get("date", "")),
            "home_team": row.get("home_team", ""),
            "away_team": row.get("away_team", ""),
            "home_score": row.get("home_g", ""),
            "away_score": row.get("away_g", ""),
            "status": "FINISHED" if pd.notnull(row.get("home_g")) else "SCHEDULED",
        })

    df_cups = pd.DataFrame(matches)
    df_cups.to_csv("cups_europe.csv", index=False, encoding="utf-8")
    print(f"✅ Guardados {len(df_cups)} partidos en cups_europe.csv")

except Exception as e:
    print(f"⚠️ Error al obtener partidos de Understat: {e}")
    pd.DataFrame(columns=["competition", "date", "home_team", "away_team", "status", "home_score", "away_score"]).to_csv("cups_europe.csv", index=False)
