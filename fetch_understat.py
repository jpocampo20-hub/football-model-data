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
    understat = sd.Understat(leagues=LEAGUES, seasons=["2025", "2026"])

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

        existing_cols = [c for c in columns_to_keep if c in df_metrics.columns]
        df_final = df_metrics[existing_cols]

        df_final.to_csv("understat_metrics.csv", index=False, encoding="utf-8")
        print(
            f"✅ Guardadas {len(df_final)} filas con métricas xG en understat_metrics.csv"
        )
    else:
        print("⚠️ No se encontraron partidos jugados con métricas de xG.")

except Exception as e:
    print(f"⚠️ Error extrayendo métricas de Understat: {e}")

    fallback_cols = [
        "league",
        "season",
        "date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "home_xg",
        "away_xg",
    ]
    pd.DataFrame(columns=fallback_cols).to_csv("understat_metrics.csv", index=False)
