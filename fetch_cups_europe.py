import csv
import datetime
import json
import os
import time
import urllib.parse
import urllib.request

API_KEY = os.environ["APIFOOTBALL_KEY"]
BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Mapping directo de IDs oficiales en API-Football (evita fallos de búsqueda)
COMPETITIONS = {
    "FA Cup": 45,
    "Copa del Rey": 143,
    "DFB Pokal": 529,
    "Coppa Italia": 137,
    "Coupe de France": 66,
    "UEFA Europa League": 3,
    "UEFA Conference League": 848,
}

SEASON = 2026
date_from = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
date_to = (datetime.date.today() + datetime.timedelta(days=21)).isoformat()


def api_get(path, params):
    query = urllib.parse.urlencode(params)
    url = f"{BASE}/{path}?{query}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except Exception as e:
        print(f"Error pidiendo {path}: {e}")
        return None


rows = []
for name, league_id in COMPETITIONS.items():
    data = api_get(
        "fixtures",
        {
            "league": league_id,
            "season": SEASON,
            "from": date_from,
            "to": date_to,
        },
    )

    if not data or "response" not in data:
        continue

    for m in data["response"]:
        rows.append(
            {
                "competition": name,
                "date": m["fixture"]["date"][:10],
                "home_team": m["teams"]["home"]["name"],
                "away_team": m["teams"]["away"]["name"],
                "status": m["fixture"]["status"]["short"],
                "home_score": m["goals"]["home"],
                "away_score": m["goals"]["away"],
            }
        )
    time.sleep(1.2)  # Respetar rate limits

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

print(f"Guardados {len(rows)} partidos en cups_europe.csv")
