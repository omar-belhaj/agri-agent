"""
Tool: récupère l'indice NDVI (santé de la végétation) pour une parcelle.
En mode réel, on utiliserait Sentinel Hub. Ici : simulation.
NDVI va de -1 à 1 ; au-dessus de 0.4 = végétation en bonne santé.
"""

import random


def get_ndvi(parcelle_id: int) -> float:
    """Retourne une valeur NDVI simulée pour la parcelle."""
    # On simule une majorité de parcelles saines, avec parfois une anomalie
    value = random.choices(
        population=[random.uniform(0.5, 0.9), random.uniform(0.1, 0.35)],
        weights=[0.75, 0.25],  # 25% de chance d'anomalie, pour rendre la démo intéressante
        k=1,
    )[0]
    return round(value, 2)
