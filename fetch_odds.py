import json
import os
import urllib.request
import pandas as pd

print("Iniciando extracción de cuotas de mercado reales...")

sports = [
    {"key": "soccer_epl", "code": "E0", "name": "Premier League"},
    {"key": "soccer_spain_la_liga", "code": "SP1", "name": "La Liga"},
    {"key": "soccer_germany_bundesliga", "code": "D1", "name": "Bundesliga"},
    {"key": "soccer_italy_serie_a", "code": "I1", "name": "Serie A"},
    {"key": "soccer_france_ligue_one", "code": "F1", "name": "Ligue 1"}
]

API_KEY = os.environ["ODDS_API_KEY"]
all_odds = []

for sport in sports:
    url = f"https://api.the-odds-api.com/v4/sports/{sport['key']}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            count = 0
            for match in data:
                home_team = match.get("home_team", "")
                away_team = match.get("away_team", "")
                commence_time = match.get("commence_time", "")

                b365_h, b365_d, b365_a = "", "", ""

                for bookmaker in match.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market.get("key") == "h2h":
                            outcomes = market.get("outcomes", [])
                            b365_h = next((o.get("price") for o in outcomes if o.get("name") == home_team), "")
                            b365_a = next((o.get("price") for o in outcomes if o.get("name") == away_team), "")
                            b365_d = next((o.get("price") for o in outcomes if o.get("name") == "Draw"), "")

                all_odds.append({
                    "Div": sport["code"],
                    "Date": commence_time[:10] if commence_time else "",
                    "Time": commence_time[11:19] if commence_time else "",
                    "HomeTeam": home_team,
                    "AwayTeam": away_team,
                    "B365H": b365_h,
                    "B365D": b365_d,
                    "B365A": b365_a,
                })
                count += 1
            print(f"✅ {sport['name']}: {count} partidos con cuotas reales cargados.")
    except Exception as e:
        print(f"⚠️ Error consultando cuotas de {sport['name']}: {e}")

df = pd.DataFrame(all_odds)
if df.empty:
    df = pd.DataFrame(columns=["Div", "Date", "Time", "HomeTeam", "AwayTeam", "B365H", "B365D", "B365A"])

df.to_csv("odds_data.csv", index=False, encoding="utf-8")
print(f"✅ Total partidos guardados en odds_data.csv: {len(df)}")
