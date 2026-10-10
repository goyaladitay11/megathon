"""
Unit Tests for Deterministic Green Home Scoring Engine
"""

import pytest
from backend.src.schemas import PropertyData
from backend.src.scoring_engine import score_home, WEIGHTS, classify_score


def test_official_weights_sum_to_one():
    total_weight = sum(WEIGHTS.values())
    assert abs(total_weight - 1.00) < 1e-6, "Weights must sum exactly to 1.00"


def test_score_bounds_and_rounding():
    # Test extreme low-efficiency property
    poor_prop = PropertyData(
        property_id="P_POOR",
        property_type="terraced",
        property_age=1900,
        floor_area_m2=80.0,
        bedrooms=2,
        energy_rating="G",
        heating_system="oil_boiler",
        insulation_type="poor",
        glazing_type="single",
        solar_installed="none",
        smart_controls=False,
        region="North East",
        current_property_value=120000.0,
        annual_electricity_kwh=4500.0,
        annual_gas_kwh=22000.0,
    )
    res_poor = score_home(poor_prop)
    assert 0 <= res_poor.green_home_score <= 100
    assert res_poor.classification == "Very poor"
    assert res_poor.is_poor_performing is True

    # Test extreme high-efficiency property
    eco_prop = PropertyData(
        property_id="P_ECO",
        property_type="detached",
        property_age=2021,
        floor_area_m2=160.0,
        bedrooms=4,
        energy_rating="A",
        heating_system="heat_pump",
        insulation_type="good",
        glazing_type="triple",
        solar_installed="4kw",
        smart_controls=True,
        region="East of England",
        current_property_value=600000.0,
        annual_electricity_kwh=3200.0,
        annual_gas_kwh=0.0,
    )
    res_eco = score_home(eco_prop)
    assert 0 <= res_eco.green_home_score <= 100
    assert res_eco.green_home_score >= 80
    assert res_eco.classification == "Highly efficient"
    assert res_eco.is_poor_performing is False


def test_component_contributions_reconcile():
    prop = PropertyData(
        property_id="P_TEST",
        property_type="semi_detached",
        property_age=1975,
        floor_area_m2=95.0,
        bedrooms=3,
        energy_rating="D",
        heating_system="gas_boiler",
        insulation_type="average",
        glazing_type="double",
        solar_installed="none",
        smart_controls=False,
        region="West Midlands",
        current_property_value=250000.0,
        annual_electricity_kwh=3500.0,
        annual_gas_kwh=12000.0,
    )
    res = score_home(prop)
    exact_sum = sum(res.component_scores[k] * WEIGHTS[k] for k in WEIGHTS)
    assert round(exact_sum, 2) == res.exact_score
    assert int(round(exact_sum)) == res.green_home_score
