"""
Script para el robot de GitHub Actions: baja partidos de las 5 ligas top +
Champions League desde la API gratuita de football-data.org, y los guarda
en fixtures.csv. Pensado para correr solo, una vez por semana, sin
intervencion manual.

Necesita la variable de entorno FOOTBALL_DATA_TOKEN (se configura como
"Secret" en GitHub, nunca se escribe la clave acá directamente).
"""
import csv
import datetime
import json
import os
import time
import urllib.request

TOKEN = os.environ["FOOTBALL_DATA_TOKEN"]

# PL=Premier League, PD=La Liga, BL1=Bundesliga, SA=Serie A, FL1=Ligue 1, CL=Champions League
COMPETITIONS = ["PL", "PD", "BL1", "SA", "FL1", "CL"]
BASE_URL = "https://api.football-data.org/v4/matches"

# ventana amplia: partidos recientes (para tener resultados ya jugados)
# + proximos (para saber cuando juega cada equipo, aunque todavia no tenga resultado)
date_from = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
date_to = (datetime.date.today() + datetime.timedelta(days=21)).isoformat()

rows = []
for comp in COMPETITIONS:
    url = f"{BASE_URL}?competitions={comp}&dateFrom={date_from}&dateTo={date_to}"
    req = urllib.request.Request(url, headers={"X-Auth-Token": TOKEN})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f"Error pidiendo {comp}: {e}")
        continue

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

    time.sleep(7)  # limite gratuito: 10 pedidos por minuto, esto lo respeta con margen

with open("fixtures.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["competition", "date", "home_team", "away_team",
                    "status", "home_score", "away_score"],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Guardados {len(rows)} partidos en fixtures.csv")
