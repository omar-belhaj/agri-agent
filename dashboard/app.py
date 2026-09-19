"""
Dashboard Streamlit — saisie manuelle uniquement.
Lancer avec : streamlit run dashboard/app.py

Chaque étape de l'agent (OBSERVER, DECIDER, RESEARCH, ACT) affiche non
seulement son résultat, mais aussi l'explication de sa décision, tirée de
state["trace"].
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from agent.graph import build_graph

st.set_page_config(page_title="Agent Agricole", page_icon="🌾", layout="centered")
st.title("🌾 Agent de surveillance agricole")
st.caption("Boucle agentique LangGraph : observer -> décider -> rechercher -> agir")

st.markdown("Entre les données observées pour une parcelle et lance l'analyse.")

with st.form("manual_form"):
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nom de la parcelle", value="Parcelle Test")
        culture = st.text_input("Culture", value="blé")
        temperature = st.number_input("Température (°C)", value=25.0)
    with col2:
        soil_moisture = st.slider("Humidité du sol (%)", 0.0, 100.0, 40.0)
        ndvi = st.slider("NDVI (0 = mort, 1 = très sain)", 0.0, 1.0, 0.6)
        precipitation = st.number_input("Précipitations récentes (mm)", value=0.0)

    submitted = st.form_submit_button("Analyser")

if submitted:
    app = build_graph()

    initial_state = {
        "parcelle_id": 0,
        "parcelle_nom": nom,
        "culture": culture,
        "weather": {
            "temperature_c": temperature,
            "precipitation_mm": precipitation,
            "humidity_pct": None,
        },
        "soil_moisture": soil_moisture,
        "ndvi": ndvi,
    }

    st.divider()
    st.subheader(f"📍 {nom} ({culture})")

    with st.spinner("Analyse en cours..."):
        final_state = app.invoke(initial_state)

    if final_state.get("anomaly_detected"):
        st.warning(final_state["final_recommendation"])
    else:
        st.success(final_state["final_recommendation"])

    # Anomalies détectées, listées individuellement
    anomalies = final_state.get("anomalies", [])
    if anomalies:
        st.markdown(f"**{len(anomalies)} anomalie(s) détectée(s) :**")
        for a in anomalies:
            st.markdown(f"- `{a['type']}` — {a['explanation']}")

    # Explicabilité : le raisonnement de chaque étape, dans l'ordre
    with st.expander("🔍 Voir le raisonnement détaillé de l'agent, étape par étape"):
        step_labels = {
            "OBSERVER": "1. OBSERVER — collecte des données",
            "DECIDER": "2. DECIDER — détection d'anomalie (règles fixes)",
            "RESEARCH": "3. RESEARCH — recherche de bonnes pratiques",
            "ACT": "4. ACT — rédaction de la recommandation",
        }
        for entry in final_state.get("trace", []):
            st.markdown(f"**{step_labels.get(entry['step'], entry['step'])}**")
            st.write(entry["detail"])

        if "RESEARCH" not in [e["step"] for e in final_state.get("trace", [])]:
            st.markdown(f"**{step_labels['RESEARCH']}**")
            st.write("*Étape sautée : aucune anomalie détectée, pas besoin de chercher de bonne pratique.*")
