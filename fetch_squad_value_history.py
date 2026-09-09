"""
Fetch de HISTORIAL de valor de plantilla (squad value) por club y fecha, para
poder correr el backtest correcto (dev-set / confirmacion / bootstrap) del
hallazgo de squad value del 2026-09-09 (ver estado-y-proximos-pasos.md,
seccion "Valor de plantilla como fuente de informacion faltante").

POR QUE ESTE SCRIPT Y NO UN SCRAPE DIRECTO DE TRANSFERMARKT:
Transfermarkt no permite scraping directo de forma confiable -- de hecho el
propio proyecto open-source que mantiene este dataset (dcaribou/transfermarkt-
datasets, la fuente publicada mas seria y usada de datos de Transfermarkt)
tuvo que PAUSAR su pipeline automatico en julio 2026 porque, cito al
mantenedor: "The pipeline depends on pages from the upstream source that are
no longer reliably reachable from GitHub Actions runners." Si un proyecto
profesional dedicado a esto no puede sostener un scraper de Transfermarkt
corriendo en GitHub Actions, construir el nuestro seria repetir el mismo
problema. Por eso usamos su dataset ya publicado (no re-scrapeamos nosotros).

LIMITACION IMPORTANTE, HONESTA: este dataset especifico esta CONGELADO desde
julio 2026 (dejo de actualizarse) y NO cubre los planteles de la temporada
2026/27 (fichajes de este verano no estan reflejados en la tabla `clubs`).
Por eso este script sirve SOLO para reconstruir el HISTORIAL (temporadas
2023-24 a 2025-26, que es exactamente el rango que ya usamos en el
confirmation-set del proyecto) -- NO sirve como fuente de valor de plantilla
ACTUAL/EN VIVO para la temporada en curso. Para eso ver
fetch_squad_values_current.py (scrape de footballwhispers.com, que si tiene
datos 2026-27).

QUE HACE:
1. Descarga `player_valuations.csv.gz` (registros historicos de valor de
   mercado POR JUGADOR, con fecha y el club en el que estaba en esa fecha --
   la resolucion de club-por-fecha ya viene hecha en el dataset via join
   contra transfers, asi que no hay que reconstruir plantillas nosotros) y
   `clubs.csv.gz` (para mapear club_id -> nombre/liga) desde el CDN publico
   sin autenticacion del proyecto.
2. Filtra a las 5 ligas del proyecto (codigos de competicion confirmados:
   ES1=La Liga, GB1=Premier League, L1=Bundesliga, IT1=Serie A, FR1=Ligue 1).
3. Agrega valor de plantilla por (club, mes) sumando el valor de mercado mas
   reciente conocido de cada jugador activo en ese club en ese momento --
   SIN look-ahead bias: para evaluar un partido de una fecha X, solo se usa
   informacion de valoraciones con fecha <= X.
4. Mapea nombres de club a nuestro name_map interno.

Salida: `squad_value_history.csv` con columnas
  league,team,year_month,squad_value_eur_m
pensado para que weekly_refresh.py (o un script de backtest aparte) haga
join por (team, year_month <= fecha del partido, tomando el mas reciente).

OJO -- Igual que fetch_squad_values.py, este script se escribio y compilo
desde el entorno de Claude, que tiene la red restringida a un allowlist y NO
pudo alcanzar el CDN de este dataset (confirmado: connect_rejected por
politica de organizacion). Esta pensado para correr desde el robot de Juan
Pedro (GitHub Actions), que tiene salida a internet normal -- igual que
fetch_clubelo.py / fetch_european_cups.py. Una vez corra ahi, el resultado
(squad_value_history.csv) se commitea al repo de datos
(jpocampo20-hub/football-model-data), desde donde SI se puede leer
directamente (via raw.githubusercontent.com, que esta confirmado accesible
desde el entorno de Claude).

Este script es de UNA SOLA VEZ (o muy ocasional, si el dataset alguna vez
retoma actualizaciones) -- no necesita correr cada semana, porque el rango
historico que cubre no cambia. Se recomienda correrlo manualmente una vez
para generar el archivo, verificar el resultado, y comitearlo; no hace falta
agregarlo al cron semanal.
"""
import sys
import pandas as pd
import numpy as np

import name_map_fd_org as nm  # reusa el mismo mapeo de nombres del proyecto

BASE_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
VALUATIONS_URL = f"{BASE_URL}/player_valuations.csv.gz"
CLUBS_URL = f"{BASE_URL}/clubs.csv.gz"

COMPETITION_TO_LEAGUE = {
    "GB1": "Premier League",
    "ES1": "La Liga",
    "IT1": "Serie A",
    "L1": "Bundesliga",
    "FR1": "Ligue 1",
}

# Rango historico que nos interesa (coincide con el confirmation-set del
# proyecto: marzo 2023 en adelante). El dataset deja de tener datos de
# player_valuations despues de 2026-06-12 -- eso ya es una limitacion del
# dataset, no de este filtro.
MIN_DATE = "2023-01-01"


def main():
    try:
        clubs = pd.read_csv(CLUBS_URL, compression="gzip")
    except Exception as e:
        print(f"ERROR descargando {CLUBS_URL}: {e}", file=sys.stderr)
        sys.exit(1)

    print("Columnas en clubs.csv.gz:", list(clubs.columns))

    comp_col = next((c for c in ["domestic_competition_id", "competition_id"] if c in clubs.columns), None)
    club_id_col = "club_id" if "club_id" in clubs.columns else None
    if not (comp_col and club_id_col):
        print("No se encontraron domestic_competition_id / club_id en clubs.csv.gz -- revisar esquema real arriba.", file=sys.stderr)
        sys.exit(1)

    clubs = clubs[clubs[comp_col].isin(COMPETITION_TO_LEAGUE)].copy()
    clubs["league"] = clubs[comp_col].map(COMPETITION_TO_LEAGUE)

    try:
        val = pd.read_csv(
            VALUATIONS_URL,
            compression="gzip",
            usecols=lambda c: c in {
                "player_id", "date", "market_value_in_eur",
                "current_club_id", "current_club_name",
                "player_club_domestic_competition_id",
            },
        )
    except Exception as e:
        print(f"ERROR descargando {VALUATIONS_URL}: {e}", file=sys.stderr)
        sys.exit(1)

    print("Columnas en player_valuations.csv.gz:", list(val.columns))

    val["date"] = pd.to_datetime(val["date"], errors="coerce")
    val = val[val["date"] >= MIN_DATE].copy()
    val = val.dropna(subset=["current_club_id", "market_value_in_eur"])

    # Solo clubes de nuestras 5 ligas
    club_league = clubs.set_index(club_id_col)["league"].to_dict()
    val["league"] = val["current_club_id"].map(club_league)
    val = val.dropna(subset=["league"])

    # Mapear club_id -> nombre corto interno del proyecto, via el nombre de
    # club que trae el propio player_valuations (current_club_name) o, si no,
    # via clubs.csv
    name_col_clubs = next((c for c in ["name", "club_name"] if c in clubs.columns), None)
    club_name_map = clubs.set_index(club_id_col)[name_col_clubs].to_dict() if name_col_clubs else {}

    val["club_name_raw"] = val["current_club_id"].map(club_name_map)
    if "current_club_name" in val.columns:
        val["club_name_raw"] = val["club_name_raw"].fillna(val["current_club_name"])

    val["team"] = val["club_name_raw"].map(nm.to_short_name)
    unmapped = sorted(val.loc[val["team"].isna(), "club_name_raw"].dropna().unique().tolist())
    if unmapped:
        print(f"AVISO: {len(unmapped)} nombres de club sin mapeo en name_map_fd_org: {unmapped[:20]}", file=sys.stderr)
    val = val.dropna(subset=["team"])

    val["year_month"] = val["date"].dt.to_period("M").astype(str)

    # Suma de valor de mercado de todos los jugadores registrados en ese club
    # ese mes (aproximacion de valor de plantilla en ese punto del tiempo,
    # sin look-ahead: solo usa valoraciones con fecha <= fin de ese mes).
    agg = (
        val.groupby(["league", "team", "year_month"])["market_value_in_eur"]
        .sum()
        .reset_index()
    )
    agg["squad_value_eur_m"] = agg["market_value_in_eur"] / 1_000_000.0
    out = agg[["league", "team", "year_month", "squad_value_eur_m"]].sort_values(
        ["league", "team", "year_month"]
    )
    out.to_csv("squad_value_history.csv", index=False)
    print(f"\nGuardado squad_value_history.csv con {len(out)} filas "
          f"({out['team'].nunique()} equipos, {out['year_month'].nunique()} meses).")


if __name__ == "__main__":
    main()
