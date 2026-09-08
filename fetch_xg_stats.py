import csv
import glob
import os
import shutil
import subprocess

DATASET = "hubertsidorowicz/football-players-stats-2025-2026"

try:
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", "xg_data", "--unzip"],
        check=True,
    )
except Exception as e:
    print(f"Error al bajar dataset de Kaggle: {e}")

csvs = sorted(glob.glob("xg_data/*.csv"))
print("Archivos encontrados:", csvs)

if not csvs:
    print("No se encontraron CSVs en el dataset de Kaggle.")
elif len(csvs) == 1:
    shutil.copy(csvs[0], "player_stats_xg.csv")
    print("Copiado player_stats_xg.csv con éxito.")
else:
    # Combinar múltiples CSVs usando módulo csv estándar (sin requerir pandas)
    combined_rows = []
    header = None
    for file in csvs:
        with open(file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            file_header = next(reader, None)
            if not header:
                header = file_header
                combined_rows.append(header)
            for row in reader:
                combined_rows.append(row)

    with open("player_stats_xg.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(combined_rows)
    print("Combinados múltiples CSVs en player_stats_xg.csv")
