"""Smoke tests for the Green UI's FastAPI contract.

These cover custom properties submitted by the Assessment and Renovation Studio
screens, as well as property-grounded conversational questions.
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

HOME = {
    "property_id": "UI-HOME-1",
    "customer_id": "C-UI-1",
    "property_type": "terraced",
    "age": 1910,
    "floor_area_m2": 92,
    "region": "North West",
    "bedrooms": 3,
    "energy_rating": "E",
    "insulation": "poor",
    "heating": "gas_boiler",
    "glazing": "single",
    "solar": "none",
    "smart_controls": False,
    "current_property_value_gbp": 210000,
    "annual_electricity_kwh": 3800,
    "annual_gas_kwh": 16500,
}

def test_assessment_endpoint_returns_property_specific_score():
    response = client.post("/api/v1/analyze", json=HOME)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["property"]["property_id"] == HOME["property_id"]
    assert 0 <= data["score_details"]["final_score"] <= 100
    assert len(data["score_details"]["components"]) == 7
    assert "grounded_explanation" in data

def test_renovation_simulation_changes_the_property_scenario():
    baseline = client.post("/api/v1/simulate", json={
        "property_input": HOME, "selected_retrofit_ids": []
    })
    upgraded = client.post("/api/v1/simulate", json={
        "property_input": HOME, "selected_retrofit_ids": ["roof_insulation", "solar_pv"]
    })
    assert baseline.status_code == 200, baseline.text
    assert upgraded.status_code == 200, upgraded.text
    b, a = baseline.json(), upgraded.json()
    assert a["property_id"] == HOME["property_id"]
    assert a["energy"]["after_purchased_kwh"] < b["energy"]["after_purchased_kwh"]
    assert set(a["applied_retrofit_ids"]) == {"roof_insulation", "solar_pv"}

def test_advisor_uses_submitted_property_instead_of_demo_fallback():
    response = client.post("/api/v1/chat", json={
        "property_input": HOME,
        "query": "What if I add roof insulation?"
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["property_id"] == HOME["property_id"]
    assert "roof_insulation" in data["parsed_retrofit_ids"]
    assert data["explanation"]["summary"]
