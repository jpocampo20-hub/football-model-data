import csv
import io
import urllib.request

# Códigos de ligas en Football-Data.co.uk para la temporada 2025-2026
# E0=Premier League, SP1=La Liga, D1=Bundesliga, I1=Serie A, F1=Ligue 1
LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
BASE_URL = "https://www.football-data.co.uk/mmz4281/2526"

print("Iniciando descarga de cuotas de apuestas...")

all_rows = []
fieldnames = [
    "Div",
    "Date",
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
    "MaxH",
    "MaxD",
    "MaxA",
    "AvgH",
    "AvgD",
    "AvgA",
]

for league in LEAGUES:
    url = f"{BASE_URL}/{league}.csv"
    print(f"Descargando cuotas para {league} desde {url}...")
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(content))

            for row in reader:
                # Extraer solo las columnas relevantes de cuotas y resultados
                extracted = {k: row.get(k, "") for k in fieldnames}
                if extracted["HomeTeam"] and extracted["Date"]:
                    all_rows.append(extracted)
            print(f"✅ {league}: {len(all_rows)} partidos procesados.")
    except Exception as e:
        print(f"❌ Error bajando cuotas para {league}: {e}")

# Guardar en odds_data.csv
with open("odds_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

print(
    f"✅ Guardadas cuotas de {len(all_rows)} partidos en odds_data.csv"
)
