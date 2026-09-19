"""
Point d'entrée CLI (optionnel, complémentaire au dashboard).
Simule des données pour chaque parcelle de data/parcelles.csv, puis lance
l'agent dessus. Pour un contrôle précis des scénarios de test, utiliser
plutôt le dashboard (streamlit run dashboard/app.py), qui permet la saisie
manuelle.
"""

import csv
from agent.graph import build_graph
from tools.weather import get_weather
from tools.soil import get_soil_moisture
from tools.ndvi import get_ndvi
from config import PARCELLES_CSV_PATH


def load_parcelles(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    app = build_graph()
    parcelles = load_parcelles(PARCELLES_CSV_PATH)

    results = []

    for p in parcelles:
        weather = get_weather(float(p["latitude"]), float(p["longitude"]))
        soil_moisture = get_soil_moisture(int(p["id"]), recent_precipitation_mm=weather["precipitation_mm"])
        ndvi = get_ndvi(int(p["id"]))

        initial_state = {
            "parcelle_id": int(p["id"]),
            "parcelle_nom": p["nom"],
            "culture": p["culture"],
            "weather": weather,
            "soil_moisture": soil_moisture,
            "ndvi": ndvi,
        }

        print(f"\n=== Traitement de {p['nom']} ===")
        final_state = app.invoke(initial_state)
        results.append(final_state["final_recommendation"])

    print("\n\n===== RAPPORT FINAL =====")
    for r in results:
        print(r)

    return results


if __name__ == "__main__":
    main()
