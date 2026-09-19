"""
Tool: récupère l'humidité du sol pour une parcelle.
Pas de capteurs physiques -> simulation basée sur la pluie récente.
"""

import random


def get_soil_moisture(parcelle_id: int, recent_precipitation_mm: float = 0.0) -> float:
    """
    Retourne un pourcentage d'humidité du sol simulé (0-100).
    Plus il a plu récemment, plus le sol est humide (avec un peu de bruit aléatoire).
    """
    base = 25 + recent_precipitation_mm * 3
    noise = random.uniform(-8, 8)
    moisture = max(0.0, min(100.0, base + noise))
    return round(moisture, 1)
