"""
Copas domesticas + Europa League / Conference League, via el API interno
(no oficial, sin key) que usa la web/app de ESPN. Gratis, sin necesidad de
ningun Secret de GitHub.
"""
import csv
import datetime
import json
import urllib.request

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

COMPETITIONS = [
    ("FA Cup", "eng.fa"),
    ("EFL Cup (Carabao Cup)", "eng.league_cup"),
    ("Copa del Rey", "esp.copa_del_rey"),
    ("DFB Pokal", "ger.dfb_pokal"),
    ("Coppa Italia", "ita.coppa_italia"),
    ("Coupe de France", "fra.coupe_de_france"),
    ("UEFA Europa League", "uefa.europa"),
    ("UEFA Europa Conference League", "uefa.europa.conf"),
]

date_from = (datetime.date.today() - datetime.timedelta(days=45)).strftime("%Y%m%d")
date_to = (datetime.date.today() + datetime.timedelta(days=21)).strftime("%Y%m%d")

rows = []
for display_name, slug in COMPETITIONS:
    url = f"{BASE}/{slug}/scoreboard?dates={date_from}-{date_to}&limit=100"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f"⚠️ {display_name}: error de red -- {e}")
        continue

    events = data.get("events", [])
    for ev in events:
        comp = ev.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        status = comp.get("status", {}).get("type", {}).get("name", "")

        rows.append({
            "competition": display_name,
            "date": ev.get("date", "")[:10],
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "status": status,
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
        })

    print(f"✅ {display_name}: {len(events)} partidos encontrados")

with open("cups_europe.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["competition", "date", "home_team", "away_team", "status", "home_score", "away_score"])
    writer.writeheader()
