import pandas as pd
import soccerdata as sd

# Ligas soportadas en Understat vía soccerdata
LIGAS = [
    "ESP-La Liga",
    "ENG-Premier League",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]

print("Iniciando extracción de métricas avanzadas (xG, PPDA) con Understat...")

try:
    # Cargar datos de la temporada actual
    understat = sd.Understat(leagues=LIGAS, seasons="2025")

    # Leer estadísticas por partido de los equipos
    team_match_stats = understat.read_team_match_stats()
    team_match_stats = team_match_stats.reset_index()

    # Seleccionar métricas avanzadas clave para el modelo
    cols_interes = [
        "league",
        "season",
        "date",
        "home_team",
        "away_team",
        "xg",
        "xga",
        "npxg",
        "npxga",
        "ppda",
        "ppda_allowed",
        "deep",
        "deep_allowed",
    ]

    # Filtrar columnas disponibles
    cols_disponibles = [
        c for c in cols_interes if c in team_match_stats.columns
    ]
    df_understat = team_match_stats[cols_disponibles].copy()

    df_understat.to_csv("understat_metrics.csv", index=False, encoding="utf-8")
    print(
        f"✅ Guardadas métricas avanzadas de {len(df_understat)} partidos en understat_metrics.csv"
    )

except Exception as e:
    print(f"❌ Error al extraer datos de Understat: {e}")
    # Generar CSV vacío seguro en caso de fallo
    pd.DataFrame(
        columns=[
            "league",
            "date",
            "home_team",
            "away_team",
            "xg",
            "xga",
            "ppda",
        ]
    ).to_csv("understat_metrics.csv", index=False)
