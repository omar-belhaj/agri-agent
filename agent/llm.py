"""
Intégration du LLM local (Llama 3 via Ollama).

Rôle du LLM dans ce projet : UNIQUEMENT rédiger la recommandation finale en
langage naturel, à partir d'un diagnostic déjà établi par des règles fixes
(voir agent/nodes.py::decider_node). On ne délègue jamais la détection
d'anomalie au LLM : un modèle local peut se contredire ou halluciner sur des
données numériques, donc la décision reste 100% déterministe.

Si Ollama n'est pas installé/lancé, llm_write_recommendation lève une
exception que le nœud appelant attrape pour basculer sur un texte de secours.
"""

from langchain_ollama import ChatOllama
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

_llm_instance = None


def get_llm():
    """Retourne une instance ChatOllama, réutilisée entre les appels."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.2,  # peu de créativité : on veut du texte fidèle aux faits
        )
    return _llm_instance


def llm_write_recommendation(
    parcelle_nom: str,
    culture: str,
    soil_moisture: float,
    ndvi: float,
    anomalies: list[dict],
    recommendations_context: list[dict],
) -> str:
    """
    Rédige la recommandation finale, STRICTEMENT à partir des faits fournis.
    Gère 0, 1 ou plusieurs anomalies simultanées.
    """
    if not anomalies:
        facts = (
            f"Aucune anomalie détectée. Humidité du sol mesurée : {soil_moisture}%. "
            f"NDVI mesuré : {ndvi}. Tout est dans les normes."
        )
    else:
        lignes = []
        for a in anomalies:
            advice = next(
                (c["advice"] for c in recommendations_context if c["type"] == a["type"]),
                "aucune bonne pratique trouvée",
            )
            lignes.append(f"- {a['type']} ({a['explanation']}) -> bonne pratique : {advice}")
        facts = (
            f"Humidité du sol mesurée : {soil_moisture}%. NDVI mesuré : {ndvi}. "
            f"{len(anomalies)} anomalie(s) détectée(s) :\n" + "\n".join(lignes)
        )

    prompt = f"""Tu es un agronome qui rédige des recommandations courtes pour un exploitant agricole.

Parcelle : {parcelle_nom} (culture : {culture})
Faits établis (ne pas en inventer d'autres, ne pas les contredire) :
{facts}

Consignes strictes :
- Utilise UNIQUEMENT les faits ci-dessus. N'invente aucun chiffre, aucune cause, aucune pratique non mentionnée.
- Si plusieurs anomalies sont listées, traite-les toutes dans ta réponse.
- Si aucune anomalie n'est détectée, dis simplement que la situation est normale, sans inventer de conseil.
- Rédige en français, 2 à 3 phrases maximum, pas de JSON, juste le texte.
"""
    response = get_llm().invoke(prompt)
    return response.content.strip()
