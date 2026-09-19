"""
Tool: récupère les données météo pour une parcelle donnée.
En mode simulation, génère des valeurs aléatoires réalistes.
"""

import random
import requests
from config import OPENWEATHER_API_KEY, SIMULATION_MODE


def get_weather(latitude: float, longitude: float) -> dict:
    """
    Retourne les données météo actuelles pour des coordonnées données.

    Returns:
        dict: {"temperature_c": float, "precipitation_mm": float, "humidity_pct": float}
    """
    if SIMULATION_MODE or not OPENWEATHER_API_KEY:
        return _simulate_weather()

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    return {
        "temperature_c": data["main"]["temp"],
        "precipitation_mm": data.get("rain", {}).get("1h", 0.0),
        "humidity_pct": data["main"]["humidity"],
    }


def _simulate_weather() -> dict:
    """Génère des données météo plausibles pour la démo."""
    return {
        "temperature_c": round(random.uniform(15, 32), 1),
        "precipitation_mm": round(random.choice([0, 0, 0, 2.5, 8.0]), 1),
        "humidity_pct": round(random.uniform(30, 80), 1),
    }
