"""
Copas domesticas + Europa League / Conference League, via API-Football
(api-sports.io) -- football-data.org no las cubre.
Busca cada competencia por nombre (con alternativas) en vez de asumir un ID.
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

COMPETITIONS = [
    ("FA Cup", ["FA Cup"]),
    ("EFL Cup (Carabao Cup)", ["EFL Cup", "Carabao Cup", "League Cup"]),
    ("Copa del Rey", ["Copa del Rey"]),
    ("DFB Pokal", ["DFB Pokal", "DFB-Pokal"]),
    ("Coppa Italia", ["Coppa Italia"]),
    ("Coupe de France", ["Coupe de France"]),
    ("UEFA Europa League", ["UEFA Europa League"]),
    ("UEFA Europa Conference League", ["UEFA Europa Conference League"]),
]

SEASON = 2026
date_from = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
date_to = (datetime.date.today() + datetime.timedelta(days=21)).isoformat()


def api_get(path, params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE}/{path}?{query}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"Error HTTP {e.code} pidiendo {path}: {e.read().decode('utf-8', errors='replace')[:300]}")
        return None
    except Exception as e:
        print(f"Error pidiendo {path}: {e}")
        return None

    errors = data.get("errors")
    if errors:
        print(f"⚠️ La API respondio 200 pero con error interno pidiendo {path}: {errors}")
        return None
    return data


def find_league_id(alt_names):
    for name in alt_names:
        data = api_get("leagues", {"name": name.replace(" ", "%20"), "season": SEASON})
        if data and data.get("response"):
            return data["response"][0]["league"]["id"]
    return None


rows = []
for display_name, alt_names in COMPETITIONS:
    league_id = find_league_id(alt_names)
    if league_id is None:
        print(f"No se encontro competencia '{display_name}'")
        continue
    time.sleep(1)

    data = api_get("fixtures", {"league": league_id, "season": SEASON, "from": date_from, "to": date_to})
    if not data:
        continue

    for m in data.get("response", []):
        rows.append({
            "competition": display_name,
            "date": m["fixture"]["date"][:10],
            "home_team": m["teams"]["home"]["name"],
            "away_team": m["teams"]["away"]["name"],
            "status": m["fixture"]["status"]["short"],
            "home_score": m["goals"]["home"],
            "away_score": m["goals"]["away"],
            "referee": m["fixture"].get("referee") or "",
        })
    time.sleep(1)

with open("cups_europe.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["competition", "date", "home_team", "away_team", "status", "home_score", "away_score", "referee"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Guardados {len(rows)} partidos en cups_europe.csv")
