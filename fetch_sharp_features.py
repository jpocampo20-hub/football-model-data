"""
Arbitros y tarjetas por partido, via el mismo API interno de ESPN (sin key).
Primero saca la lista de partidos jugados de cada liga, luego pide el
resumen de cada uno para sacar arbitro + tarjetas.
"""
import csv
import datetime
import json
import time
import urllib.request

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

LEAGUES = [
    ("Premier League", "eng.1"),
    ("La Liga", "esp.1"),
    ("Bundesliga", "ger.1"),
    ("Serie A", "ita.1"),
    ("Ligue 1", "fra.1"),
]

date_from = (datetime.date.today() - datetime.timedelta(days=45)).strftime("%Y%m%d")
date_to = (datetime.date.today() + datetime.timedelta(days=21)).strftime("%Y%m%d")

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_json(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.load(resp)
    except Exception as e:
        print(f"⚠️ Error pidiendo {url}: {e}")
        return None


def stat_value(stats, name):
    for s in stats or []:
        if s.get("name") == name:
            return s.get("displayValue", "")
    return ""


rows = []
for league_name, slug in LEAGUES:
    sb = get_json(f"{BASE}/{slug}/scoreboard?dates={date_from}-{date_to}&limit=100")
    if not sb:
        continue

    finished = [
        ev for ev in sb.get("events", [])
        if ev.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("completed")
    ]
    print(f"{league_name}: {len(finished)} partidos jugados en la ventana")

    for ev in finished:
        event_id = ev.get("id")
        summary = get_json(f"{BASE}/{slug}/summary?event={event_id}")
        time.sleep(0.3)
        if not summary:
            continue

        comp = ev.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        home_c = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away_c = next((c for c in competitors if c.get("homeAway") == "away"), {})
        home_id = home_c.get("team", {}).get("id")
        away_id = away_c.get("team", {}).get("id")

        officials = summary.get("gameInfo", {}).get("officials", [])
        referee = officials[0].get("fullName", "") if officials else ""

        home_stats = away_stats = []
        for t in summary.get("boxscore", {}).get("teams", []):
            tid = t.get("team", {}).get("id")
            if tid == home_id:
                home_stats = t.get("statistics", [])
            elif tid == away_id:
                away_stats = t.get("statistics", [])

        rows.append({
            "League": league_name,
            "Date": ev.get("date", "")[:10],
            "HomeTeam": home_c.get("team", {}).get("displayName", ""),
            "AwayTeam": away_c.get("team", {}).get("displayName", ""),
            "Referee": referee,
            "YellowCards_Home": stat_value(home_stats, "yellowCards"),
            "YellowCards_Away": stat_value(away_stats, "yellowCards"),
            "RedCards_Home": stat_value(home_stats, "redCards"),
            "RedCards_Away": stat_value(away_stats, "redCards"),
            "Fouls_Home": stat_value(home_stats, "foulsCommitted"),
            "Fouls_Away": stat_value(away_stats, "foulsCommitted"),
        })

with open("referees_stats.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "League", "Date", "HomeTeam", "AwayTeam", "Referee",
        "YellowCards_Home", "YellowCards_Away", "RedCards_Home", "RedCards_Away",
        "Fouls_Home", "Fouls_Away",
    ])
    writer.writeheader()
    writer.writerows(rows)

print(f"Total registros guardados en referees_stats.csv: {len(rows)}")
