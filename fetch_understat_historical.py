"""
Bajada UNICA de xG historico (varias temporadas) para poder probar si xG
mejora el modelo con el mismo rigor que se uso para Elo. No es parte del
itinerario semanal -- correr una sola vez con Run workflow, borrar el paso
despues si quieres.
"""
import pandas as pd
import soccerdata as sd

LEAGUES = ["ENG-Premier League", "ESP-La Liga", "GER-Bundesliga", "ITA-Serie A", "FRA-Ligue 1"]
SEASONS = [str(y) for y in range(2016, 2026)]  # 2016-17 a 2025-26

understat = sd.Understat(leagues=LEAGUES, seasons=SEASONS)
match_data = understat.read_team_match_stats()
df = match_data.reset_index()

cols = ["league", "season", "date", "home_team", "away_team", "home_goals", "away_goals",
        "home_xg", "away_xg", "home_np_xg", "away_np_xg", "home_ppda", "away_ppda"]
df[[c for c in cols if c in df.columns]].to_csv("understat_historical.csv", index=False)
print(f"Guardadas {len(df)} filas en understat_historical.csv")
