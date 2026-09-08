"""
Segundo script del robot: copas domesticas + Europa League / Conference
League, via API-Football (api-sports.io) -- football-data.org (el primer
proveedor) no las cubre ni pagando, es una limitacion del proveedor.

Busca el ID de cada copa POR NOMBRE en vez de asumir un numero de memoria
(la vez pasada nos salio mal adivinar un endpoint sin verificar) -- asi el
script se auto-corrige si el ID real es distinto al esperado.

Necesita la variable de entorno APIFOOTBALL_KEY (Secret de GitHub).
"""
import csv
import datetime
import json
import os
import time
import urllib.error
import urllib.request

API_KEY = os.environ["APIFOOTBALL_KEY"]
BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# nombres tal cual los devuelve la API -- si alguno no aparece, el script
# lo reporta pero no se rompe (sigue con las demas copas)
COMPETITIONS = [
    "FA Cup",
    "Copa del Rey",
    "DFB Pokal",
    "Coppa Italia",
    "Coupe de France",
    "UEFA Europa League",
    "UEFA Europa Conference League",
]

SEASON = 2026  # la API usa el anio de inicio de la temporada

date_from = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
date_to = (datetime.date.today() + datetime.timedelta(days=21)).isoformat()


def api_get(path, params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE}/{path}?{query}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Error HTTP {e.code} pidiendo {path}: {body[:300]}")
        return None
    except Exception as e:
        print(f"Error pidiendo {path}: {e}")
        return None


def find_league_id(name):
    data = api_get("leagues", {"name": name.replace(" ", "%20"), "season": SEASON})
    if not data or not data.get("response"):
        print(f"No se encontro liga/copa llamada '{name}'")
        return None
    return data["response"][0]["league"]["id"]


rows = []
for name in COMPETITIONS:
    league_id = find_league_id(name)
    if league_id is None:
        continue
    time.sleep(1)

    data = api_get("fixtures", {
        "league": league_id, "season": SEASON,
        "from": date_from, "to": date_to,
    })
    if not data:
        continue

    for m in data.get("response", []):
        rows.append({
            "competition": name,
            "date": m["fixture"]["date"][:10],
            "home_team": m["teams"]["home"]["name"],
            "away_team": m["teams"]["away"]["name"],
            "status": m["fixture"]["status"]["short"],
            "home_score": m["goals"]["home"],
            "away_score": m["goals"]["away"],
        })
    time.sleep(1)

with open("cups_europe.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["competition", "date", "home_team", "away_team",
                    "status", "home_score", "away_score"],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Guardados {len(rows)} partidos en cups_europe.csv")
