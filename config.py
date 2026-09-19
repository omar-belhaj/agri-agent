"""
Configuration du projet.
Mets tes clés API ici (ou mieux : dans un fichier .env, voir .env.example).
"""

import os

# --- LLM (Ollama en local, gratuit) ---
OLLAMA_MODEL = "llama3:8b"       # doit être installé via `ollama pull llama3:8b`
OLLAMA_BASE_URL = "http://localhost:11434"

# Le LLM ne sert QU'À RÉDIGER la recommandation finale en langage naturel,
# à partir d'un diagnostic déjà établi par des règles fixes (fiables et
# déterministes). La détection d'anomalie elle-même n'utilise jamais le LLM :
# un petit modèle local peut halluciner sur des chiffres, donc on ne lui
# confie pas la décision, seulement la formulation.
USE_LLM_FOR_WRITING = True

# --- APIs externes (optionnelles) ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")  # laisser vide = mode simulé
SENTINEL_HUB_CLIENT_ID = os.getenv("SENTINEL_HUB_CLIENT_ID", "")
SENTINEL_HUB_CLIENT_SECRET = os.getenv("SENTINEL_HUB_CLIENT_SECRET", "")

# --- Mode simulation ---
# Si True, les tools renvoient des données simulées au lieu d'appeler les vraies APIs.
# Pratique pour développer/démontrer sans clé API ni capteurs physiques.
SIMULATION_MODE = True

# --- Seuils de décision ---
SOIL_MOISTURE_LOW_THRESHOLD = 30.0   # % en dessous duquel on considère un stress hydrique
NDVI_LOW_THRESHOLD = 0.4             # en dessous duquel on suspecte un problème de santé végétale

# --- Parcelles ---
PARCELLES_CSV_PATH = "data/parcelles.csv"
HISTORIQUE_DB_PATH = "data/historique.db"
