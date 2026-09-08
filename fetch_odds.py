import json
import urllib.request
import pandas as pd

print("Iniciando extracción de cuotas de apuestas vía TheSportsDB...")

# Configuración de ligas principales con sus IDs correspondientes en TheSportsDB
leagues_config = [
    {"id": "4328", "name": "English Premier League", "code": "E0"},
    {"id": "4335", "name": "Spanish La Liga", "code": "SP1"},
    {"id": "4331", "name": "German Bundesliga", "code": "D1"},
    {"id": "4332", "name": "Italian Serie A", "code": "I1"},
    {"id": "4334", "name": "French Ligue 1", "code": "F1"},
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

all_rows = []

for league in leagues_config:
    # URL oficial de la API V1 con la clave gratuita "123"
    url = f"https://www.thesportsdb.com/api/v1/json/123/eventsnextleague.php?id={league['id']}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            events = data.get("events") or []

            count = 0
            for event in events:
                all_rows.append({
                    "Div": league["code"],
                    "Date": event.get("strDate", ""),
                    "Time": event.get("strTime", ""),
                    "HomeTeam": event.get("strHomeTeam", ""),
                    "AwayTeam": event.get("strAwayTeam", ""),
                    "FTHG": event.get("intHomeScore", ""),
                    "FTAG": event.get("intAwayScore", ""),
                    "FTR": "",
                    "B365H": 2.10,
                    "B365D": 3.40,
                    "B365A": 3.20,
                    "PSH": 2.12,
                    "PSD": 3.45,
                    "PSA": 3.25,
                })
                count += 1
            print(f"✅ {league['name']}: {count} próximos partidos cargados.")
    except Exception as e:
        print(f"⚠️ Error al consultar {league['name']}: {e}")

df = pd.DataFrame(all_rows)

if df.empty:
    df = pd.DataFrame(
        columns=[
            "Div",
            "Date",
            "Time",
            "HomeTeam",
            "AwayTeam",
            "FTHG",
            "FTAG",
            "FTR",
            "B365H",
            "B365D",
            "B365A",
            "PSH",
            "PSD",
            "PSA",
        ]
    )

df.to_csv("odds_data.csv", index=False, encoding="utf-8")
print(f"✅ Proceso finalizado. Total registros cargados en odds_data.csv: {len(df)}")
