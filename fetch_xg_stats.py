"""
Tercer script del robot: stats de jugadores con xG, via el dataset de
Kaggle "Football Players Stats 2025-2026" (se actualiza por jornada por
su propio mantenedor -- nosotros solo lo bajamos).

Necesita las variables de entorno KAGGLE_USERNAME y KAGGLE_KEY (Secrets de
GitHub) -- son las que vienen en el kaggle.json que se descarga desde
Kaggle > Settings > API > Create New Token.
"""
import glob
import os
import subprocess
import sys

DATASET = "hubertsidorowicz/football-players-stats-2025-2026"

# el paquete "kaggle" no viene preinstalado en el runner de GitHub Actions
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "kaggle"], check=True)

# el paquete kaggle lee estas variables de entorno directo, no hace falta
# escribir un archivo kaggle.json a mano
os.environ["KAGGLE_USERNAME"] = os.environ["KAGGLE_USERNAME"]
os.environ["KAGGLE_KEY"] = os.environ["KAGGLE_KEY"]

subprocess.run(
    ["kaggle", "datasets", "download", "-d", DATASET, "-p", "xg_data", "--unzip"],
    check=True,
)

csvs = sorted(glob.glob("xg_data/*.csv"))
print("Archivos encontrados en el dataset:", csvs)

if not csvs:
    print("No se encontro ningun CSV adentro del dataset -- revisar manualmente.")
else:
    # el dataset trae un CSV por liga o uno combinado, segun la version del
    # mantenedor -- los dejamos todos, sin asumir un nombre fijo, y guardamos
    # una copia con nombre estable para que el modelo siempre sepa donde buscar
    import shutil
    if len(csvs) == 1:
        shutil.copy(csvs[0], "player_stats_xg.csv")
    else:
        import pandas as pd
        dfs = [pd.read_csv(c) for c in csvs]
        pd.concat(dfs, ignore_index=True).to_csv("player_stats_xg.csv", index=False)
    print("Guardado player_stats_xg.csv")
