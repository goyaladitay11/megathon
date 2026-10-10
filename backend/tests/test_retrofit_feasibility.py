"""
Unit Tests for Retrofit Eligibility and Feasibility Checks
"""

import pytest
from backend.src.schemas import PropertyData
from backend.src.retrofit_engine import check_feasibility_and_suitability, recommend_retrofits


def test_already_installed_measures_are_ineligible():
    fully_upgraded = PropertyData(
        property_id="P_UPGRADED",
        property_type="detached",
        property_age=2018,
        floor_area_m2=140.0,
        bedrooms=4,
        energy_rating="B",
        heating_system="heat_pump",
        insulation_type="good",
        glazing_type="double",
        solar_installed="4kw",
        smart_controls=True,
        region="London",
        current_property_value=550000.0,
        annual_electricity_kwh=4200.0,
        annual_gas_kwh=0.0,
    )
    # Check individual feasibilities
    assert check_feasibility_and_suitability(fully_upgraded, "roof_insulation")[0] is False
    assert check_feasibility_and_suitability(fully_upgraded, "double_glazing")[0] is False
    assert check_feasibility_and_suitability(fully_upgraded, "smart_thermostat")[0] is False
    assert check_feasibility_and_suitability(fully_upgraded, "heat_pump")[0] is False
    assert check_feasibility_and_suitability(fully_upgraded, "solar_pv")[0] is False

    recs = recommend_retrofits(fully_upgraded)
    assert len(recs) == 0, "No retrofits should be recommended for a fully upgraded home."


def test_fabric_first_heat_pump_condition():
    poor_home = PropertyData(
        property_id="P_POOR",
        property_type="terraced",
        property_age=1910,
        floor_area_m2=85.0,
        bedrooms=3,
        energy_rating="E",
        heating_system="gas_boiler",
        insulation_type="poor",
        glazing_type="single",
        solar_installed="none",
        smart_controls=False,
        region="North West",
        current_property_value=195000.0,
        annual_electricity_kwh=3600.0,
        annual_gas_kwh=16000.0,
    )
    feasible, suit, reason, note = check_feasibility_and_suitability(poor_home, "heat_pump")
    assert feasible is True
    assert suit == "Medium"
    assert "insulate" in note.lower() or "fabric" in note.lower()
