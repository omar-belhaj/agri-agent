"""
Tool: recherche de bonnes pratiques agricoles.
Version simplifiée sans API de recherche payante : renvoie des conseils
depuis une petite base de connaissances locale, indexée par mot-clé.
"""

KNOWLEDGE_BASE = {
    "stress hydrique": (
        "Augmenter la fréquence d'irrigation de 15 à 25%. "
        "Privilégier l'arrosage tôt le matin ou en soirée pour limiter l'évaporation."
    ),
    "ndvi faible": (
        "Un NDVI bas peut indiquer un stress hydrique, une carence en azote, "
        "ou une maladie. Recommandé : inspection visuelle sous 48h et analyse de sol."
    ),
    "mildiou": (
        "Retirer les feuilles atteintes, améliorer l'aération entre les plants, "
        "envisager un traitement fongicide adapté à la culture."
    ),
}


def search_best_practices(query: str) -> str:
    """
    Cherche une recommandation dans la base de connaissances locale.
    Fallback générique si aucun mot-clé ne correspond.
    """
    query_lower = query.lower()
    for keyword, advice in KNOWLEDGE_BASE.items():
        if keyword in query_lower:
            return advice
    return "Aucune recommandation spécifique trouvée. Inspection manuelle conseillée."
