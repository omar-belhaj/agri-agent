"""
Définition de l'état (State) partagé entre les nœuds du graphe LangGraph.

Deux points importants pour l'explicabilité :
- "anomalies" est une LISTE : le sol et le NDVI sont évalués indépendamment,
  donc une parcelle peut cumuler plusieurs anomalies en même temps.
- "trace" accumule une explication textuelle à chaque étape (observer,
  decider, research, act). Contrairement aux autres champs (qui sont
  écrasés à chaque mise à jour), "trace" est ADDITIF grâce au reducer
  `operator.add` : chaque nœud AJOUTE son explication à la liste existante
  plutôt que de la remplacer.
"""

import operator
from typing import TypedDict, Optional, List, Annotated


class Anomaly(TypedDict):
    type: str          # ex: "stress_hydrique", "ndvi_faible"
    explanation: str    # pourquoi cette anomalie a été détectée (valeur vs seuil)


class RecommendationContext(TypedDict):
    type: str
    advice: str


class TraceEntry(TypedDict):
    step: str      # "OBSERVER", "DECIDER", "RESEARCH", "ACT"
    detail: str    # explication en langage naturel de ce que l'étape a fait/décidé


class AgentState(TypedDict, total=False):
    # Entrée (toujours saisie manuellement dans ce projet)
    parcelle_id: int
    parcelle_nom: str
    culture: str

    # Données observées
    weather: dict
    soil_moisture: float
    ndvi: float

    # Analyse : liste d'anomalies indépendantes (peut être vide, une, ou plusieurs)
    anomalies: List[Anomaly]
    anomaly_detected: bool

    # Recherche complémentaire : une entrée par anomalie détectée
    recommendations_context: List[RecommendationContext]

    # Sortie finale
    final_recommendation: str

    # Explicabilité : historique cumulé des explications de chaque étape
    trace: Annotated[List[TraceEntry], operator.add]
