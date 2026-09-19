"""
Tests de la logique de décision (agent/nodes.py) et du routage du graphe.

Ces tests sont les plus importants du projet : ils vérifient que la
détection d'anomalies est correcte et déterministe (pas de dépendance au
LLM), condition nécessaire pour que le système soit fiable.
"""

import pytest
from agent.nodes import decider_node, route_after_decision
from agent.graph import build_graph
from config import SOIL_MOISTURE_LOW_THRESHOLD, NDVI_LOW_THRESHOLD


def make_state(soil_moisture: float, ndvi: float) -> dict:
    return {
        "parcelle_nom": "Parcelle Test",
        "culture": "test",
        "soil_moisture": soil_moisture,
        "ndvi": ndvi,
    }


class TestDeciderNode:
    def test_no_anomaly_when_both_values_normal(self):
        state = make_state(soil_moisture=50.0, ndvi=0.7)
        result = decider_node(state)
        assert result["anomaly_detected"] is False
        assert result["anomalies"] == []

    def test_detects_stress_hydrique_only(self):
        state = make_state(soil_moisture=10.0, ndvi=0.7)  # sol bas, ndvi bon
        result = decider_node(state)
        assert result["anomaly_detected"] is True
        types = [a["type"] for a in result["anomalies"]]
        assert types == ["stress_hydrique"]

    def test_detects_ndvi_faible_only(self):
        state = make_state(soil_moisture=50.0, ndvi=0.1)  # sol bon, ndvi bas
        result = decider_node(state)
        assert result["anomaly_detected"] is True
        types = [a["type"] for a in result["anomalies"]]
        assert types == ["ndvi_faible"]

    def test_detects_both_anomalies_simultaneously(self):
        # Cas réel signalé pendant le développement : sol=19.82%, ndvi=0.25
        state = make_state(soil_moisture=19.82, ndvi=0.25)
        result = decider_node(state)
        assert result["anomaly_detected"] is True
        types = {a["type"] for a in result["anomalies"]}
        assert types == {"stress_hydrique", "ndvi_faible"}

    def test_boundary_values_are_not_anomalies(self):
        # Exactement au seuil = pas d'anomalie (comparaison stricte "<")
        state = make_state(soil_moisture=SOIL_MOISTURE_LOW_THRESHOLD, ndvi=NDVI_LOW_THRESHOLD)
        result = decider_node(state)
        assert result["anomaly_detected"] is False

    def test_trace_entry_is_added(self):
        state = make_state(soil_moisture=10.0, ndvi=0.7)
        result = decider_node(state)
        assert len(result["trace"]) == 1
        assert result["trace"][0]["step"] == "DECIDER"
        assert "10.0" in result["trace"][0]["detail"]


class TestRouteAfterDecision:
    def test_routes_to_research_when_anomaly(self):
        assert route_after_decision({"anomaly_detected": True}) == "research"

    def test_routes_to_act_when_no_anomaly(self):
        assert route_after_decision({"anomaly_detected": False}) == "act"


class TestFullGraphManualMode:
    """
    Exécute le graphe complet de bout en bout.

    IMPORTANT : ces tests forcent USE_LLM_FOR_WRITING à False (via monkeypatch)
    pour rester rapides, déterministes, et indépendants de la machine sur
    laquelle ils tournent. Sans ça, ils appelleraient le vrai Ollama s'il est
    installé (lent : plusieurs minutes, et non-déterministe dans le texte
    généré), ou le mode de secours sinon (comportement différent selon la
    machine) — ce qui rendrait la CI GitHub Actions non fiable, puisqu'elle
    n'a pas Ollama installé.
    """

    @pytest.fixture(autouse=True)
    def force_rule_based_mode(self, monkeypatch):
        monkeypatch.setattr("agent.nodes.USE_LLM_FOR_WRITING", False)

    def _run(self, soil_moisture, ndvi):
        app = build_graph()
        state = {
            "parcelle_id": 0,
            "parcelle_nom": "Parcelle CI",
            "culture": "blé",
            "weather": {"temperature_c": 20, "precipitation_mm": 0, "humidity_pct": 50},
            "soil_moisture": soil_moisture,
            "ndvi": ndvi,
        }
        return app.invoke(state)

    def test_normal_case_skips_research(self):
        result = self._run(soil_moisture=60.0, ndvi=0.8)
        assert result["anomaly_detected"] is False
        # RESEARCH ne doit pas apparaître dans la trace : l'étape est sautée
        steps = [t["step"] for t in result["trace"]]
        assert "RESEARCH" not in steps
        assert "situation normale" in result["final_recommendation"].lower()

    def test_anomaly_case_runs_research(self):
        result = self._run(soil_moisture=10.0, ndvi=0.8)
        assert result["anomaly_detected"] is True
        steps = [t["step"] for t in result["trace"]]
        assert "RESEARCH" in steps
        assert result["recommendations_context"][0]["type"] == "stress_hydrique"

    def test_double_anomaly_produces_two_contexts(self):
        result = self._run(soil_moisture=10.0, ndvi=0.1)
        assert len(result["anomalies"]) == 2
        assert len(result["recommendations_context"]) == 2

    def test_final_recommendation_is_never_empty(self):
        for soil, ndvi in [(60.0, 0.8), (10.0, 0.8), (10.0, 0.1)]:
            result = self._run(soil, ndvi)
            assert result["final_recommendation"].strip() != ""


class TestActNodeWithMockedLLM:
    """
    Vérifie l'intégration du LLM dans act_node SANS appeler le vrai Ollama :
    on remplace llm_write_recommendation par une fonction factice (mock).
    Ça teste le câblage (le texte du LLM est bien inséré dans le résultat
    final, avec la bonne icône et le bon nom de parcelle) de façon rapide
    et reproductible, sans dépendre d'un modèle installé localement.
    """

    def test_llm_output_is_used_when_available(self, monkeypatch):
        monkeypatch.setattr("agent.nodes.USE_LLM_FOR_WRITING", True)
        monkeypatch.setattr(
            "agent.nodes.llm_write_recommendation",
            lambda **kwargs: "Texte factice généré par un LLM simulé.",
        )

        app = build_graph()
        state = {
            "parcelle_id": 0,
            "parcelle_nom": "Parcelle Mock",
            "culture": "vigne",
            "weather": {"temperature_c": 20, "precipitation_mm": 0, "humidity_pct": 50},
            "soil_moisture": 10.0,  # anomalie garantie
            "ndvi": 0.8,
        }
        result = app.invoke(state)

        assert "Texte factice généré par un LLM simulé." in result["final_recommendation"]
        assert "Parcelle Mock" in result["final_recommendation"]
        assert result["final_recommendation"].startswith("⚠️")

    def test_falls_back_to_rules_when_llm_raises(self, monkeypatch):
        monkeypatch.setattr("agent.nodes.USE_LLM_FOR_WRITING", True)

        def raise_error(**kwargs):
            raise ConnectionError("Ollama indisponible (simulé pour le test)")

        monkeypatch.setattr("agent.nodes.llm_write_recommendation", raise_error)

        app = build_graph()
        state = {
            "parcelle_id": 0,
            "parcelle_nom": "Parcelle Fallback",
            "culture": "blé",
            "weather": {"temperature_c": 20, "precipitation_mm": 0, "humidity_pct": 50},
            "soil_moisture": 10.0,
            "ndvi": 0.8,
        }
        result = app.invoke(state)

        # Le texte de secours doit quand même être généré, sans planter
        assert result["final_recommendation"].strip() != ""
        assert "Parcelle Fallback" in result["final_recommendation"]
