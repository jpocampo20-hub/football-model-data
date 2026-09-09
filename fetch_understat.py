"""
Tercer script del robot: métricas avanzadas (xG) de las 5 ligas principales,
via la librería soccerdata (Understat). No necesita ninguna key.
"""
import pandas as pd
import soccerdata as sd

print("Iniciando extracción de métricas avanzadas (xG) desde Understat...")

LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]

try:
    understat = sd.Understat(leagues=LEAGUES, seasons="2025")

    match_data = understat.read_team_match_stats()

    if not match_data.empty:
        df_metrics = match_data.reset_index()

        columns_to_keep = [
            "league",
            "season",
            "date",
            "home_team",
            "away_team",
            "home_goals",
            "away_goals",
            "home_xg",
            "away_xg",
            "home_np_xg",
            "away_np_xg",
            "home_ppda",
            "away_ppda",
            "home_points",
            "away_points",
        ]

        existing_cols = [c
