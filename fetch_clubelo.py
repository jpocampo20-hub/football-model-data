"""
Cuarto script del robot: Elo EN VIVO de todos los clubes, via clubelo.com
(fuente publica y gratuita, sin necesidad de API key) usando la misma
libreria `soccerdata` que ya usa fetch_understat.py -- no es una fuente
nueva que instalar, es un metodo distinto de la misma libreria.

Guarda el snapshot de Elo de HOY para todos los equipos (rank, liga, elo).
Esto es la pieza que faltaba para poder generar predicciones reales de
partidos futuros con el modelo (antes solo teniamos Elo historico, nunca
actualizado).
"""
import soccerdata as sd

elo = sd.ClubElo()
current = elo.read_by_date()  # Elo de todos los clubes conocidos, a la fecha de hoy
current = current.reset_index().rename(columns={"index": "team"})

current.to_csv("clubelo_current.csv", index=False)
print(f"Guardado clubelo_current.csv con {len(current)} equipos")
print(current.head(10))
