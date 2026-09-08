import csv
import datetime
import json
import os
import time
import urllib.parse
import urllib.request

API_KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io",
}

# IDs oficiales confirmados en API-Football
COMPETITIONS = {
    "FA Cup": 45,
    "Copa del Rey": 143,
    "DFB Pokal": 529,
    "Coppa Italia": 137,
    "Coupe de France": 66,
    "UEFA Europa League": 3,
    "UEFA Conference League": 848,
}

# Año de inicio de la temporada actual (ej. 2025 para la temporada 2025-2026)
SEASON = 2025

date_from = (datetime.date.today() - datetime.timedelta(days=60)).isoformat()
date_to = (datetime.date.today() + datetime.timedelta(days=45)).isoformat()


def api_get(path, params):
    query = urllib.parse.urlencode(params)
    url = f"{BASE}/{path}?{query}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)

            # Imprimir advertencias o errores devueltos en el JSON por la API
            if data.get("errors"):
                print(f"⚠️ Advertencia de API-Football ({path}): {data['errors']}")
            return data
    except Exception as e:
        print(f"❌ Error HTTP/Red pidiendo {path}: {e}")
        return None


rows = []

for name, league_id in COMPETITIONS.items():
    print(f"Consultando {name} (ID: {league_id})...")

    # Intentar primero filtrando por el rango de fechas ampliado
    data = api_get(
        "fixtures",
        {
            "league": league_id,
            "season": SEASON,
            "from": date_from,
            "to": date_to,
        },
    )

    matches = data.get("response", []) if data else []

    # RECURSO DE RESPALDO: Si no hay partidos en esas fechas, traer los partidos de toda la temporada
    if not matches:
        print(
            f"   No hubo partidos cercanos para {name}. Pidiendo temporada completa..."
        )
        data = api_get("fixtures", {"league": league_id, "season": SEASON})
        matches = data.get("response", []) if data else []

    print(f"   Encontrados {len(matches)} partidos para {name}")

    for m in matches:
        rows.append(
            {
                "competition": name,
                "date": m["fixture"]["date"][:10],
                "home_team": m["teams"]["home"]["name"],
                "away_team": m["teams"]["away"]["name"],
                "status": m["fixture"]["status"]["short"],
                "home_score": (
                    m["goals"]["home"]
                    if m["goals"]["home"] is not None
                    else ""
                ),
                "away_score": (
                    m["goals"]["away"]
                    if m["goals"]["away"] is not None
                    else ""
                ),
            }
        )

    time.sleep(1.2)  # Respetar rate limits de la API

# Guardar resultados en el CSV
with open("cups_europe.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "competition",
            "date",
            "home_team",
            "away_team",
            "status",
            "home_score",
            "away_score",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"\n✅ Proceso finalizado: Guardados {len(rows)} partidos en cups_europe.csv")
