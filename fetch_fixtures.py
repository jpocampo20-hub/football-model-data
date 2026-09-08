import csv
import datetime
import json
import os
import time
import urllib.error
import urllib.request

TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")

# PL=Premier League, PD=La Liga, BL1=Bundesliga, SA=Serie A, FL1=Ligue 1, CL=Champions League
COMPETITIONS = ["PL", "PD", "BL1", "SA", "FL1", "CL"]
BASE_URL = "https://api.football-data.org/v4/competitions"

date_from = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
date_to = (datetime.date.today() + datetime.timedelta(days=21)).isoformat()

rows = []

if not TOKEN:
    print("⚠️ No se encontró la variable FOOTBALL_DATA_TOKEN")
else:
    for comp in COMPETITIONS:
        url = f"{BASE_URL}/{comp}/matches?dateFrom={date_from}&dateTo={date_to}"
        req = urllib.request.Request(url, headers={"X-Auth-Token": TOKEN})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.load(resp)
                for m in data.get("matches", []):
                    rows.append({
                        "competition": comp,
                        "date": m["utcDate"][:10],
                        "home_team": m["homeTeam"]["name"],
                        "away_team": m["awayTeam"]["name"],
                        "status": m["status"],
                        "home_score": m["score"]["fullTime"]["home"],
                        "away_score": m["score"]["fullTime"]["away"],
                    })
                print(f"✅ Liga {comp}: procesada correctamente.")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"Error pidiendo {comp}: HTTP {e.code} -- {body}")
        except Exception as e:
            print(f"Error pidiendo {comp}: {e}")

        time.sleep(7)  # Limite gratuito: 10 pedidos por minuto

with open("fixtures.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["competition", "date", "home_team", "away_team", "status", "home_score", "away_score"],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Guardados {len(rows)} partidos en fixtures.csv")
