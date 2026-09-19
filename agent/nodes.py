"""
Nœuds de la boucle agentique :
observer -> decider -> (research si anomalie) -> act

Chaque nœud ajoute une entrée à state["trace"] expliquant en langage
naturel ce qu'il a fait et pourquoi — c'est ça qui rend chaque décision
de l'agent explicable, pas seulement son résultat final.

Séparation des responsabilités :
- decider_node : détection PAR RÈGLES FIXES uniquement (fiable, déterministe).
  Le sol et le NDVI sont évalués indépendamment : une parcelle peut cumuler
  plusieurs anomalies (contrairement à une version qui ne détecterait qu'un
  seul problème à la fois).
- act_node : rédaction par le LLM, qui reçoit le diagnostic déjà établi et
  ne fait que le formuler en langage naturel.
"""

from agent.state import AgentState
from agent.llm import llm_write_recommendation
from tools.search import search_best_practices
from config import SOIL_MOISTURE_LOW_THRESHOLD, NDVI_LOW_THRESHOLD, USE_LLM_FOR_WRITING


def observer_node(state: AgentState) -> dict:
    """
    Journalise les données saisies manuellement (elles sont déjà dans le
    state d'entrée, ce nœud ne fait qu'expliquer ce qui a été reçu).
    """
    detail = (
        f"Données saisies pour {state['parcelle_nom']} ({state['culture']}) : "
        f"humidité du sol = {state['soil_moisture']}%, NDVI = {state['ndvi']}, "
        f"météo = {state['weather']}."
    )
    print(f"[OBSERVER] {detail}")

    return {"trace": [{"step": "OBSERVER", "detail": detail}]}


def decider_node(state: AgentState) -> dict:
    """
    Détecte les anomalies à partir de seuils fixes. Le sol et le NDVI sont
    vérifiés INDÉPENDAMMENT (pas de elif) : les deux peuvent être en
    anomalie en même temps, et c'est reflété dans la liste "anomalies".
    """
    anomalies = []

    if state["soil_moisture"] < SOIL_MOISTURE_LOW_THRESHOLD:
        anomalies.append(
            {
                "type": "stress_hydrique",
                "explanation": (
                    f"humidité du sol à {state['soil_moisture']}%, "
                    f"sous le seuil de {SOIL_MOISTURE_LOW_THRESHOLD}%"
                ),
            }
        )

    if state["ndvi"] < NDVI_LOW_THRESHOLD:
        anomalies.append(
            {
                "type": "ndvi_faible",
                "explanation": (
                    f"NDVI à {state['ndvi']}, sous le seuil de {NDVI_LOW_THRESHOLD}"
                ),
            }
        )

    anomaly_detected = len(anomalies) > 0

    if anomaly_detected:
        detail = (
            f"Comparaison aux seuils fixes -> {len(anomalies)} anomalie(s) détectée(s) : "
            + "; ".join(f"{a['type']} ({a['explanation']})" for a in anomalies)
        )
    else:
        detail = (
            f"Comparaison aux seuils fixes -> sol ({state['soil_moisture']}% >= "
            f"{SOIL_MOISTURE_LOW_THRESHOLD}%) et NDVI ({state['ndvi']} >= {NDVI_LOW_THRESHOLD}) "
            f"dans les normes, aucune anomalie."
        )

    print(f"[DECIDER] {detail}")

    return {
        "anomalies": anomalies,
        "anomaly_detected": anomaly_detected,
        "trace": [{"step": "DECIDER", "detail": detail}],
    }


def research_node(state: AgentState) -> dict:
    """Cherche une bonne pratique pour CHAQUE anomalie détectée."""
    contexts = []
    for anomaly in state["anomalies"]:
        query = anomaly["type"].replace("_", " ")
        advice = search_best_practices(query)
        contexts.append({"type": anomaly["type"], "advice": advice})

    detail = (
        f"Recherche de bonnes pratiques pour {len(state['anomalies'])} anomalie(s) : "
        + ", ".join(c["type"] for c in contexts)
    )
    print(f"[RESEARCH] {detail}")

    return {
        "recommendations_context": contexts,
        "trace": [{"step": "RESEARCH", "detail": detail}],
    }


def act_node(state: AgentState) -> dict:
    """
    Rédige la recommandation finale. Le LLM ne fait QUE la formulation ;
    les faits (anomalies, chiffres, bonnes pratiques) lui sont imposés.
    Repli sur un texte fixe si Ollama est indisponible.
    """
    icon = "⚠️" if state.get("anomaly_detected") else "✅"
    anomalies = state.get("anomalies", [])
    contexts = state.get("recommendations_context", [])

    if USE_LLM_FOR_WRITING:
        try:
            text = llm_write_recommendation(
                parcelle_nom=state["parcelle_nom"],
                culture=state["culture"],
                soil_moisture=state["soil_moisture"],
                ndvi=state["ndvi"],
                anomalies=anomalies,
                recommendations_context=contexts,
            )
            recommendation = f"{icon} {state['parcelle_nom']} ({state['culture']}) : {text}"
            detail = "Recommandation rédigée par le LLM (Llama), à partir des faits imposés ci-dessus."
            print(f"[ACT-LLM] {recommendation}")
            return {
                "final_recommendation": recommendation,
                "trace": [{"step": "ACT", "detail": detail}],
            }
        except Exception as exc:
            print(f"[ACT-LLM] Échec ({exc}) -> repli sur texte fixe")

    # --- Repli : texte fixe (utilisé si LLM désactivé ou indisponible) ---
    if anomalies:
        details_txt = " ; ".join(
            f"{a['type']} -> {next((c['advice'] for c in contexts if c['type'] == a['type']), '')}"
            for a in anomalies
        )
        recommendation = f"{icon} {state['parcelle_nom']} ({state['culture']}) : {details_txt}"
    else:
        recommendation = f"{icon} {state['parcelle_nom']} ({state['culture']}) : aucune anomalie détectée, situation normale."

    detail = "LLM indisponible : recommandation composée directement à partir des règles (texte de secours)."
    print(f"[ACT-RULES] {recommendation}")

    return {
        "final_recommendation": recommendation,
        "trace": [{"step": "ACT", "detail": detail}],
    }


def route_after_decision(state: AgentState) -> str:
    """Fonction de routage conditionnel utilisée par LangGraph."""
    return "research" if state.get("anomaly_detected") else "act"
