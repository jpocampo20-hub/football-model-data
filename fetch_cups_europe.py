import datetime
import os
import pandas as pd
import soccerdata as sd

# Lista ampliada de copas locales, secundarias y torneos de copa en las 5 ligas top
COPAS = [
    "ENG-FA Cup",
    "ENG-EFL Cup",        # Carabao Cup / League Cup
    "ESP-Copa del Rey",
    "GER-DFB Pokal",
    "ITA-Coppa Italia",
    "FRA-Coupe de France",
]

print("Iniciando extracción de copas locales y EFL Cup con soccerdata (FBref)...")

try:
    # Cargar datos de la temporada actual 2026
    fbref = sd.FBref(leagues=COPAS, seasons="2026")
    schedule = fbref.read_schedule()
    schedule = schedule.reset_index()

    cols_rename = {
        "league": "competition",
        "date": "date",
        "home_team": "home_team",
        "away_team": "away_team",
        "home_g": "home_score",
        "away_g": "away_score",
    }

    # Mapeo para nombres más limpios en el CSV final
    nombre_limpio = {
        "ENG-FA Cup": "FA Cup",
        "ENG-EFL Cup": "Carabao Cup",
        "ESP-Copa del Rey": "Copa del Rey",
        "GER-DFB Pokal": "DFB Pokal",
        "ITA-Coppa Italia": "Coppa Italia",
        "FRA-Coupe de France": "Coupe de France",
    }

    df_cups = schedule[list(cols_rename.keys())].rename(columns=cols_rename)
    df_cups["competition"] = df_cups["competition"].map(lambda x: nombre_limpio.get(x, x))

    df_cups["date"] = pd.to_datetime(df_cups["date"])
    hoy = pd.Timestamp(datetime.date.today())

    # Rango de tiempo para incluir partidos recientes y próximos partidos
    fecha_inicio = hoy - pd.Timedelta(days=60)
    fecha_fin = hoy + pd.Timedelta(days=30)

    df_filtrado = df_cups[
        (df_cups["date"] >= fecha_inicio) & (df_cups["date"] <= fecha_fin)
    ].copy()

    df_filtrado["date"] = df_filtrado["date"].dt.strftime("%Y-%m-%d")
    
    # Asignar estado del partido según si ya tiene marcador registrado
    df_filtrado["status"] = df_filtrado["home_score"].apply(
        lambda x: "FINISHED" if pd.notnull(x) else "SCHEDULED"
    )

    df_filtrado.to_csv("cups_europe.csv", index=False, encoding="utf-8")
    print(f"✅ Guardados {len(df_filtrado)} partidos de copas (incluida Carabao Cup) en cups_europe.csv")

except Exception as e:
    print(f"❌ Error durante la extracción de copas con soccerdata: {e}")
    # Genera un CSV vacío válido con estructura adecuada si ocurre algún imprevisto
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
