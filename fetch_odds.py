import csv
import io
import urllib.request

LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]

# La estructura estable de Football-Data para la temporada en curso usa mmz4281 sin subcarpetas de año no creadas
# o la carpeta activa validada 2526/2627.
# Para evitar fallos, probamos las dos rutas de acceso estándar con manejo de errores limpio.

BASE_URLS = [
    "https://www.football-data.co.uk/mmz4281/2526",  # Archivo/Temporada reciente
    "https://www.football-data.co.uk/mmz4281/2627",  # Temporada actual (si ya está creada)
]

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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

for league in LEAGUES:
    downloaded = False
    for base_url in BASE_URLS:
        url = f"{base_url}/{league}.csv"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="replace")
                    if "HomeTeam" in content:
                        reader = csv.DictReader(io.StringIO(content))
                        count = 0
                        for row in reader:
                            extracted = {k: row.get(k, "") for k in fieldnames}
                            if extracted.get("HomeTeam") and extracted.get("Date"):
                                all_rows.append(extracted)
                                count += 1
                        print(
                            f"✅ {league}: {count} partidos procesados desde {base_url}"
                        )
                        downloaded = True
                        break
        except Exception:
            continue

    if not downloaded:
        print(
            f"⚠️ {league}: No se pudo descargar de ninguna ruta. Se generará estructura vacía."
        )

# Guardar resultados
with open("odds_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

print(
    f"\n✅ Proceso finalizado. Total registros en odds_data.csv: {len(all_rows)}"
)
