"""
Tests unitaires des fonctions tools/.
Vérifient surtout que les données simulées restent dans des bornes réalistes
(un NDVI hors de [-1, 1] ou une humidité négative révélerait un bug).
"""

from tools.soil import get_soil_moisture
from tools.ndvi import get_ndvi
from tools.weather import _simulate_weather
from tools.search import search_best_practices


def test_soil_moisture_within_bounds():
    for _ in range(50):
        value = get_soil_moisture(parcelle_id=1, recent_precipitation_mm=0.0)
        assert 0.0 <= value <= 100.0


def test_soil_moisture_increases_with_rain():
    # Avec beaucoup de pluie récente, l'humidité moyenne doit être nettement
    # plus haute qu'avec zéro pluie (test statistique, pas déterministe).
    dry_samples = [get_soil_moisture(1, recent_precipitation_mm=0.0) for _ in range(100)]
    wet_samples = [get_soil_moisture(1, recent_precipitation_mm=15.0) for _ in range(100)]
    assert sum(wet_samples) / len(wet_samples) > sum(dry_samples) / len(dry_samples)


def test_ndvi_within_bounds():
    for _ in range(50):
        value = get_ndvi(parcelle_id=1)
        assert -1.0 <= value <= 1.0


def test_simulated_weather_has_expected_keys():
    weather = _simulate_weather()
    assert set(weather.keys()) == {"temperature_c", "precipitation_mm", "humidity_pct"}
    assert 0.0 <= weather["humidity_pct"] <= 100.0


def test_search_best_practices_matches_known_keyword():
    advice = search_best_practices("stress hydrique")
    assert "irrigation" in advice.lower()


def test_search_best_practices_fallback_for_unknown_query():
    advice = search_best_practices("mot-clé totalement inconnu xyz123")
    assert "inspection manuelle" in advice.lower()
