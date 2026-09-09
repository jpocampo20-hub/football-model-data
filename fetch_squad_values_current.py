"""
Fetch de valor de plantilla ACTUAL (temporada en curso) por club, para las 5
ligas del proyecto. Complementa a fetch_squad_value_history.py (que da el
historial 2023-2026 para backtesting, pero esta CONGELADO y no cubre
2026/27).

POR QUE FOOTBALLWHISPERS Y NO TRANSFERMARKT DIRECTO:
Transfermarkt en si no es confiablemente scrapeable de forma automatizada --
confirmado indirectamente porque el pipeline del propio dataset republicado
que usamos para el historial (dcaribou/transfermarkt-datasets) se rompio en
julio 2026 exactamente por esto ("pages... no longer reliably reachable from
GitHub Actions runners"). footballwhispers.com publica valores de plantilla
(con la misma fuente de fondo, Transfermarkt, pero republicados en su propio
sitio) en tablas simples por liga, sin las protecciones anti-bot mas duras
de Transfermarkt. Se verifico manualmente (vía fetch con IA) que las 5
paginas de liga sirven datos limpios para las 96 equipos de las 5 ligas,
temporada 2026-27, el 2026-09-09.

LIMITACION HONESTA: este script NO fue probado end-to-end contra el HTML
real desde el entorno de Claude (la red de este entorno tiene
footballwhispers.com bloqueado a nivel de proxy -- connect_rejected). Se
escribio usando pandas.read_html, que es tolerante a la estructura exacta
del HTML (no depende de una clase CSS especifica que podria cambiar), pero
la primera corrida en un entorno con internet normal (el robot de Juan
Pedro) hay que revisarla con el print() de diagnostico antes de confiar en
el resultado -- exactamente el mismo patron defensivo que
fetch_squad_values.py / fetch_squad_value_history.py.

Pensado para correr en el robot de GitHub Actions de Juan Pedro, NO cada
semana (el valor de plantilla no cambia partido a partido) sino 2 veces por
temporada, justo despues del cierre de cada ventana de fichajes:
  - primer lunes de septiembre (cierre del mercado de verano)
  - primer lunes de febrero (cierre del mercado de invierno)
agregando dos entradas de cron al workflow existente (mismo mecanismo que ya
usa weekly_refresh.py, solo con un schedule distinto y mas espaciado). Asi
queda automatico, sin que Juan Pedro tenga que pegar nada a mano.

Salida: `squad_values_current.csv` con columnas
  league,team,squad_value_eur_m,as_of_date
mismo formato de salida que el fetch_squad_values.py original (fusionado
aca), listo para que weekly_refresh.py haga join directo contra
team_snapshot por (league, team).
"""
import sys
from datetime import date

import pandas as pd
import numpy as np

import name_map_fd_org as nm  # reusa el mismo mapeo de nombres del proyecto

LEAGUE_URLS = {
    "Premier League": "https://www.footballwhispers.com/uk/team-value/premier-league",
    "La Liga": "https://www.footballwhispers.com/uk/team-value/la-liga",
    "Serie A": "https://www.footballwhispers.com/uk/team-value/serie-a",
    "Bundesliga": "https://www.footballwhispers.com/uk/team-value/bundesliga",
    "Ligue 1": "https://www.footballwhispers.com/uk/team-value/ligue-1",
}

HEADERS = {
    # Un user-agent de navegador normal -- varios sitios devuelven una
    # version reducida o bloquean el default de `requests` (python-requests/x.x).
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def parse_value_to_eur_m(raw):
    """Convierte strings tipo '£1.2bn', '€950m', '425.3m' a millones de EUR.
    Nota: footballwhispers puede mostrar en GBP -- si el simbolo es £, se dejaria
    sin convertir a EUR (aproximacion; revisar si el gap real importa antes de
    usarlo en produccion, dado que son cifras de referencia y no exactas)."""
    if pd.isna(raw):
        return np.nan
    s = str(raw).strip().replace(",", "")
    mult = 1.0
    if "bn" in s.lower():
        mult = 1000.0
    for sym in ["£", "€", "$", "bn", "Bn", "BN", "m", "M"]:
        s = s.replace(sym, "")
    s = s.strip()
    try:
        return float(s) * mult
    except ValueError:
        return np.nan


def fetch_league(league, url):
    try:
        tables = pd.read_html(url, storage_options=HEADERS)
    except Exception as e:
        print(f"ERROR descargando/parseando {url}: {e}", file=sys.stderr)
        return pd.DataFrame(columns=["league", "team", "squad_value_eur_m"])

    if not tables:
        print(f"AVISO: no se encontraron tablas HTML en {url}", file=sys.stderr)
        return pd.DataFrame(columns=["league", "team", "squad_value_eur_m"])

    # Tomamos la tabla mas grande (heuristica simple: la que tiene mas filas
    # suele ser la tabla principal de valores, no un widget lateral)
    df = max(tables, key=len).copy()
    print(f"\n[{league}] columnas detectadas: {list(df.columns)}")
    print(df.head(3).to_string())

    team_col = next((c for c in df.columns if str(c).strip().lower() in
                      ("team", "club", "team/club")), df.columns[0])
    value_col = next((c for c in df.columns if "value" in str(c).strip().lower()), None)
    if value_col is None:
        print(f"ERROR: no se identifico columna de valor en {league} -- revisar columnas arriba.", file=sys.stderr)
        return pd.DataFrame(columns=["league", "team", "squad_value_eur_m"])

    out = pd.DataFrame({
        "league": league,
        "team_raw": df[team_col],
        "squad_value_eur_m": df[value_col].map(parse_value_to_eur_m),
    })
    out["team"] = out["team_raw"].map(nm.to_short_name)
    unmapped = out.loc[out["team"].isna(), "team_raw"].tolist()
    if unmapped:
        print(f"AVISO [{league}]: sin mapeo de nombre para {unmapped}", file=sys.stderr)
    return out.dropna(subset=["team", "squad_value_eur_m"])[["league", "team", "squad_value_eur_m"]]


def main():
    frames = [fetch_league(lg, url) for lg, url in LEAGUE_URLS.items()]
    result = pd.concat(frames, ignore_index=True)
    result["as_of_date"] = date.today().isoformat()

    if result.empty:
        print("ERROR: no se pudo extraer ningun valor -- revisar el HTML real de footballwhispers y ajustar el script.", file=sys.stderr)
        sys.exit(1)

    result.to_csv("squad_values_current.csv", index=False)
    print(f"\nGuardado squad_values_current.csv con {len(result)} equipos "
          f"({result['league'].nunique()} ligas).")


if __name__ == "__main__":
    main()
