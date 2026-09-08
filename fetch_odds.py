import csv
import io
import os
import subprocess

LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
BASE_URL = "https://www.football-data.co.uk/mmz4281/2627"

print("Iniciando descarga de cuotas de apuestas vía curl (Temporada 2026-2027)...")

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
    print(f"Descargando cuotas para {league}...")
    try:
        # Uso de curl directo para evadir el bloqueo HTTP 503
        cmd = [
            "curl",
            "-sL",
            "-A",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        content = result.stdout

        if "HomeTeam" in content:
            reader = csv.DictReader(io.StringIO(content))
            count = 0
            for row in reader:
                extracted = {k: row.get(k, "") for k in fieldnames}
                if extracted.get("HomeTeam") and extracted.get("Date"):
                    all_rows.append(extracted)
                    count += 1
            print(f"✅ {league}: {count} partidos procesados.")
        else:
            print(f"⚠️ {league}: No se obtuvieron datos válidos (posible URL en cambio).")

    except Exception as e:
        print(f"❌ Error bajando cuotas para {league}: {e}")

# Guardar en odds_data.csv
with open("odds_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"✅ Guardadas cuotas de {len(all_rows)} partidos en odds_data.csv")
