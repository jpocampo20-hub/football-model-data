"""
Descarga resultados y calendario de Europa League, Conference League y las
5 copas domesticas top (FA Cup, Copa del Rey, DFB-Pokal, Coppa Italia,
Coupe de France) desde FBref.

Por que FBref y no football-data.org: football-data.org (que ya usamos en
fetch_fixtures.py para PL/PD/BL1/SA/FL1/CL) NO incluye estas competencias
en su plan gratuito -- exigen el plan "Standard" (49 EUR/mes) o superior.
FBref las publica gratis y sin login, asi que el costo es cero, a cambio
de un scraping mas fragil (si FBref cambia el HTML de la pagina, este
script puede romper -- por eso el bloque try/except por competencia, igual
que en fetch_fixtures.py).

Guarda TODOS los partidos de estas 7 competencias, incluyendo los que
involucran clubes que no estan en las 5 ligas top (ej. Zira, Corvinul,
Kryvbas). Eso es intencional: el objetivo principal de este archivo es
poder contar descanso/congestion de calendario para CUALQUIER equipo de
las 5 ligas top que juegue estas competencias, no solo mostrar los
partidos entre equipos conocidos. El filtro de "solo mostrar cruces entre
equipos de las 5 ligas top" se aplica despues, en weekly_refresh.py, no
aqui.
"""

import csv
import io
import re
import time

import pandas as pd
import requests

# id de FBref (fbref.com/en/comps/<id>/...) -- verificados en fbref.com en 2026-09.
# Si alguno deja de funcionar (0 partidos guardados para esa competencia),
# lo mas probable es que FBref haya reasignado el id -- buscar
# "fbref.com <nombre competencia> scores fixtures" para encontrar el nuevo.
COMPETITIONS = [
    {"id": 19, "code": "EL", "name": "Europa League"},
    {"id": 882, "code": "UECL", "name": "Conference League"},
    {"id": 514, "code": "FAC", "name": "FA Cup"},
    {"id": 569, "code": "CDR", "name": "Copa del Rey"},
    {"id": 521, "code": "DFB", "name": "DFB-Pokal"},
    {"id": 529, "code": "CI", "name": "Coppa Italia"},
    {"id": 518, "code": "CDF", "name": "Coupe de France"},
]

HEADERS = {
    # FBref bloquea o devuelve paginas incompletas a clientes sin
    # User-Agent de navegador real.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# Codigo de pais de 2-3 letras que FBref pega al final del nombre del
# equipo (viene del icono de bandera). Se remueve con regex generico.
_FLAG_SUFFIX_RE = re.compile(r"\s+[a-z]{2,3}$")

# Formatos de marcador que vienen de FBref:
#   "2–1"          -> partido normal
#   "(4) 1–1 (5)"  -> empate que se definio por penales (guardamos el
#                      marcador de los 90+30 min, NO el de penales)
_SCORE_RE = re.compile(r"(?:\(\d+\)\s*)?(\d+)\s*[–‒-]\s*(\d+)(?:\s*\(\d+\))?")


def strip_flag(name: str) -> str:
    if not isinstance(name, str):
        return name
    return _FLAG_SUFFIX_RE.sub("", name).strip()


def parse_score(raw):
    if not isinstance(raw, str) or not raw.strip() or raw.strip() in ("—", "-"):
        return None, None
    m = _SCORE_RE.search(raw)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def fetch_competition(comp):
    url = f"https://fbref.com/en/comps/{comp['id']}/schedule/"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text))
    # La tabla de calendario es la que tiene columnas Date/Home/Away/Score.
    sched = None
    for t in tables:
        cols = [str(c) for c in t.columns]
        if "Date" in cols and "Home" in cols and "Away" in cols:
            sched = t
            break
    if sched is None:
        raise ValueError("no se encontro la tabla de calendario (Date/Home/Away)")

    rows = []
    for _, r in sched.iterrows():
        date = r.get("Date")
        if not isinstance(date, str) or not date.strip():
            continue  # filas de separador de ronda sin fecha
        home = strip_flag(r.get("Home"))
        away = strip_flag(r.get("Away"))
        round_name = r.get("Round", "")
        hs, as_ = parse_score(r.get("Score"))
        status = "FINISHED" if hs is not None else "SCHEDULED"
        rows.append({
            "competition": comp["code"],
            "round": round_name,
            "date": date,
            "home_team": home,
            "away_team": away,
            "status": status,
            "home_score": hs,
            "away_score": as_,
        })
    return rows


def main():
    all_rows = []
    for comp in COMPETITIONS:
        try:
            rows = fetch_competition(comp)
            all_rows.extend(rows)
            print(f"OK {comp['name']}: {len(rows)} partidos.")
        except Exception as e:
            print(f"Error pidiendo {comp['name']} (id {comp['id']}): {e}")
        time.sleep(4)  # cortesia con FBref -- evitar bloqueo por rate-limit

    with open("european_cups.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["competition", "round", "date", "home_team", "away_team",
                        "status", "home_score", "away_score"],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Guardados {len(all_rows)} partidos en european_cups.csv")


if __name__ == "__main__":
    main()
