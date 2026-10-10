"""
Unit Tests for End-to-End Inference API
"""

import pytest
from backend.src.schemas import PropertyData
from backend.src.inference import analyse_home, predict_property_value_range


def test_analyse_home_end_to_end():
    unseen_property = PropertyData(
        property_id="P_UNSEEN_1",
        property_type="terraced",
        property_age=1925,
        floor_area_m2=88.0,
        bedrooms=3,
        energy_rating="E",
        heating_system="gas_boiler",
        insulation_type="poor",
        glazing_type="single",
        solar_installed="none",
        smart_controls=False,
        region="North West",
        current_property_value=210000.0,
        annual_electricity_kwh=3800.0,
        annual_gas_kwh=16500.0,
    )
    result = analyse_home(unseen_property)

    assert result.property_id == "P_UNSEEN_1"
    assert 0 <= result.green_home_score <= 100
    assert result.is_poor_performing is True
    assert result.classification in ["Poor", "Very poor"]
    assert len(result.recommended_retrofits) > 0
    assert result.baseline["total_purchased_kwh"] == 3800.0 + 16500.0
    assert result.estimated_energy_saving_kwh > 0.0
    assert result.estimated_carbon_reduction_tonnes > 0.0
    assert result.property_value_impact_range["is_available"] is True
    assert "+" in result.property_value_impact_range["range_label"]


def test_predict_property_value_range_missing_baseline():
    missing_val_property = PropertyData(
        property_id="P_NO_VAL",
        property_type="flat",
        property_age=1980,
        floor_area_m2=60.0,
        bedrooms=2,
        energy_rating="D",
        heating_system="gas_boiler",
        insulation_type="average",
        glazing_type="double",
        solar_installed="none",
        smart_controls=False,
        region="London",
        current_property_value=None,  # Missing baseline!
        annual_electricity_kwh=2800.0,
        annual_gas_kwh=8500.0,
    )
    res = predict_property_value_range(missing_val_property, ["roof_insulation", "solar_pv"])
    assert res.is_available is False
    assert "Unavailable" in res.range_label
