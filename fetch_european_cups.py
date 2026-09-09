"""
Descarga el calendario/resultados de la fase de liga de UEFA Europa League y
UEFA Conference League desde Wikipedia.

Por que Wikipedia y no FBref: FBref bloquea con 403 el scraping desde IPs
de nube/GitHub Actions (confirmado en produccion el 2026-09-09 -- ver
claude/robot-competencias-europeas-y-copas.md -- fallo uniforme en las 7
competencias, incluso pidiendo robots.txt, señal de bloqueo por IP/bot, no
de un ID vencido). Wikipedia no bloquea este tipo de trafico.

ALCANCE -- IMPORTANTE: este script reemplaza a fetch_european_cups.py pero
SOLO cubre Europa League y Conference League (fase de liga). Las 5 copas
domesticas (FA Cup, Copa del Rey, DFB-Pokal, Coppa Italia, Coupe de
France) quedaron FUERA a proposito: sus paginas de temporada en Wikipedia
no tienen resultados, solo un calendario de fechas por ronda -- los
resultados reales viven en paginas separadas POR RONDA que Wikipedia crea
a medida que avanza la temporada (ej. "2025-26 FA Cup third round"), lo
que requiere descubrir el titulo correcto de cada pagina dinamicamente,
no solo cambiar una URL. Es una tarea aparte, todavia sin construir.

SIN VALIDAR CONTRA HTML REAL -- aviso honesto: el entorno donde se escribio
este script no pudo alcanzar en.wikipedia.org directamente (bloqueo de red
del propio sandbox, no de Wikipedia) para confirmar el parseo fila por
fila contra el HTML real. La estructura de columnas (equipo local /
marcador / equipo visitante, con menciones de fecha tipo "16 Sep" en
alguna celda) se confirmo por una herramienta de lectura de paginas, pero
no se pudo verificar el HTML crudo. Es decir: PROBAR este script con
workflow_dispatch y revisar el european_cups.csv real generado antes de
confiar en el, exactamente igual que se hizo con la version de FBref que
fallo. Si el numero de partidos encontrados es 0 o muy bajo, o las fechas
salen vacias, avisar con el log completo para ajustar el parser contra
datos reales en vez de seguir adivinando.

Usa la API de Wikipedia (action=parse) en vez de scrapear la pagina
renderizada directamente -- es el uso que la propia Wikipedia recomienda
para consumo programatico.
"""
import csv
import re
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "bet-model-bot/1.0 (contacto: jp.ocampo20@gmail.com) python-requests",
}

COMPETITIONS = [
    {"code": "EL", "name": "UEFA Europa League"},
    {"code": "UECL", "name": "UEFA Europa Conference League"},
]

_MATCHDAY_RE = re.compile(r"Matchday\s+(\d+)", re.IGNORECASE)
_SCORE_RE = re.compile(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$")
_DATE_RE = re.compile(
    r"^\s*\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?"
    r"(\s+\d{4})?\s*$", re.IGNORECASE,
)


def season_str(ref=None):
    """Temporada europea 'YYYY-YY+1' con guion largo, como titula Wikipedia
    (ej. '2026-27'). Misma convencion que SEASON_CUTOFF en weekly_refresh.py:
    julio en adelante ya es la temporada que empieza ese año."""
    ref = ref or date.today()
    start = ref.year if ref.month >= 7 else ref.year - 1
    return f"{start}–{str(start + 1)[2:]}"


def fetch_page_html(title):
    resp = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "parse", "page": title, "format": "json", "prop": "text", "redirects": 1},
        headers=HEADERS, timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(f"Wikipedia API error: {data['error']}")
    return data["parse"]["text"]["*"]


def parse_league_phase(html, comp_code, season):
    """Recorre el HTML en orden de documento: cada vez que encuentra un
    encabezado 'Matchday N', toma la(s) tabla(s) siguientes como los
    partidos de esa jornada, hasta el proximo encabezado de matchday.
    Dentro de cada fila, ubica la celda de marcador ("2-1") para anclar
    equipo local/visitante a su lado, y busca por separado una celda con
    forma de fecha ("16 Sep") en cualquier posicion de la fila -- no asume
    un numero fijo de columnas porque no se pudo confirmar contra HTML
    real (ver aviso arriba)."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    current_matchday = None

    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in ("h2", "h3", "h4"):
            m = _MATCHDAY_RE.search(el.get_text())
            current_matchday = int(m.group(1)) if m else current_matchday
            continue
        if el.name != "table" or current_matchday is None:
            continue
        for tr in el.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 3:
                continue
            score_idx = next((i for i, c in enumerate(cells) if _SCORE_RE.match(c)), None)
            if score_idx is None or score_idx == 0 or score_idx == len(cells) - 1:
                continue
            home, away = cells[score_idx - 1], cells[score_idx + 1]
            if not home or not away or home.lower() in ("home", "team 1") or away.lower() in ("away", "team 2"):
                continue
            date_str = next((c for c in cells if _DATE_RE.match(c)), None)
            sm = _SCORE_RE.match(cells[score_idx])
            rows.append({
                "competition": comp_code, "round": f"Matchday {current_matchday}",
                "date": f"{date_str} {season.split('–')[0]}" if date_str else None,
                "home_team": home, "away_team": away,
                "status": "FINISHED", "home_score": int(sm.group(1)), "away_score": int(sm.group(2)),
            })
    return rows


def main():
    season = season_str()
    all_rows = []
    for comp in COMPETITIONS:
        title = f"{season} {comp['name']}".replace(" ", "_")
        try:
            html = fetch_page_html(title)
            rows = parse_league_phase(html, comp["code"], season)
            n_with_date = sum(1 for r in rows if r["date"])
            all_rows.extend(rows)
            print(f"OK {comp['name']} ({title}): {len(rows)} partidos con marcador, {n_with_date} con fecha reconocida.")
        except Exception as e:
            print(f"Error pidiendo {comp['name']} ({title}): {e}")
        time.sleep(2)

    with open("european_cups.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["competition", "round", "date", "home_team", "away_team",
                           "status", "home_score", "away_score"],
        )
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Guardados {len(all_rows)} partidos en european_cups.csv")


if __name__ == "__main__":
    main()
