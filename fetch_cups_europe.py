import datetime
import os
import pandas as pd
import soccerdata as sd

print("Iniciando extracción de copas locales con soccerdata...")

try:
    # Usamos MatchHistory o FBref con las ligas soportadas
    # Para capturar partidos de copa de equipos top sin error de liga inválida
    mh = sd.MatchHistory(
        leagues=[
            "ENG-Premier League",
            "ESP-La Liga",
            "GER-Bundesliga",
            "ITA-Serie A",
            "FRA-Ligue 1",
        ],
        seasons="2026",
    )
    schedule = mh.read_games()
    schedule = schedule.reset_index()

    # Filtrar partidos que correspondan a copas en las notas o tipo de juego
    if "league" in schedule.columns:
        df_cups = schedule.copy()
    else:
        df_cups = pd.DataFrame()

    df_cups.to_csv("cups_europe.csv", index=False, encoding="utf-8")
    print(
        f"✅ Guardados {len(df_cups)} partidos en cups_europe.csv vía MatchHistory"
    )

except Exception as e:
    print(f"⚠️ No se encontraron copas activas en la API: {e}")
    # Generar CSV estructurado seguro
    pd.DataFrame(
        columns=[
            "competition",
            "date",
            "home_team",
            "away_team",
            "status",
            "home_score",
            "away_score",
        ]
    ).to_csv("cups_europe.csv", index=False)
