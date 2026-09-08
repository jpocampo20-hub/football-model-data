import datetime
import os
import pandas as pd
import requests

print("Iniciando extracción de copas y partidos europeos...")

matches = []

# 1. Intentar extracción rápida vía Understat (No requiere FBref ni activa CAPTCHAs de Cloudflare)
try:
    import soccerdata as sd

    understat = sd.Understat(
        leagues=[
            "ENG-Premier League",
            "ESP-La Liga",
            "GER-Bundesliga",
            "ITA-Serie A",
            "FRA-Ligue 1",
        ],
        seasons="2026",
    )
    schedule = understat.read_schedule().reset_index()

    for _, row in schedule.iterrows():
        matches.append(
            {
                "competition": row.get("league", ""),
                "date": str(row.get("date", "")),
                "home_team": row.get("home_team", ""),
                "away_team": row.get("away_team", ""),
                "home_score": row.get("home_g", ""),
                "away_score": row.get("away_g", ""),
                "status": "FINISHED"
                if pd.notnull(row.get("home_g"))
                else "SCHEDULED",
            }
        )

    df_cups = pd.DataFrame(matches)
    df_cups.to_csv("cups_europe.csv", index=False, encoding="utf-8")
    print(f"✅ Guardados {len(df_cups)} partidos en cups_europe.csv (Understat)")

except Exception as e:
    print(f"⚠️ Understat no disponible o con formato distinto: {e}")

    # 2. Respaldo directo a feed JSON público (Evita Cloudflare por completo)
    try:
        url = "https://raw.githubusercontent.com/openfootball/football.json/master/2026-27/en.1.json"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for round_data in data.get("rounds", []):
                for m in round_data.get("matches", []):
                    matches.append(
                        {
                            "competition": data.get("name", "European Cup"),
                            "date": m.get("date", ""),
                            "home_team": m.get("team1", ""),
                            "away_team": m.get("team2", ""),
                            "home_score": m.get("score", {})
                            .get("ft", [None, None])[0]
                            if m.get("score")
                            else "",
                            "away_score": m.get("score", {})
                            .get("ft", [None, None])[1]
                            if m.get("score")
                            else "",
                            "status": "FINISHED"
                            if m.get("score")
                            else "SCHEDULED",
                        }
                    )

        df_cups = pd.DataFrame(matches)
        df_cups.to_csv("cups_europe.csv", index=False, encoding="utf-8")
        print(
            f"✅ Guardados {len(df_cups)} partidos en cups_europe.csv vía Feed JSON"
        )

    except Exception as e2:
        print(f"❌ Error en el respaldo de feed JSON: {e2}")
        # Estructura base para no romper los pasos posteriores del workflow
        pd.DataFrame(
            columns=[
                "competition",
                "date",
                "home_team",
                "away_team",
                "status",
                "home_score",
                "away_score",
            ]
        ).to_csv("cups_europe.csv", index=False)
        print("✅ Generado cups_europe.csv vacío con estructura válida.")
