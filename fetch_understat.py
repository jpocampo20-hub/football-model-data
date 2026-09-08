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

# Usamos la temporada 2024/2025 o 2025/2026 para asegurar partidos ya jugados con datos
try:
    understat = sd.Understat(leagues=LEAGUES, seasons="2024")

    # read_match_data() trae los datos reales de xG, tiros y goles de cada partido jugados
    match_data = understat.read_match_data()

    if not match_data.empty:
        df_metrics = match_data.reset_index()

        # Seleccionamos las columnas clave de xG y rendimiento
        columns_to_keep = [
            "league",
            "season",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "home_xg",
            "away_xg",
            "forecast_win",
            "forecast_draw",
            "forecast_loss",
        ]

        # Filtrar solo las columnas disponibles
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

    # Fallback técnico para mantener la resiliencia en GitHub Actions
    fallback_cols = [
        "league",
        "season",
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "home_xg",
        "away_xg",
    ]
    pd.DataFrame(columns=fallback_cols).to_csv("understat_metrics.csv", index=False)
