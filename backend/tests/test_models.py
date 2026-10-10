"""
Unit Tests for Trained Model Artifacts and Inference Loading
"""

import pytest
from pathlib import Path
import joblib
import pandas as pd
from backend.src.schemas import PropertyData
from backend.src.inference import predict_energy, predict_property_value_range, analyse_home

backend_dir = Path(__file__).resolve().parent.parent
models_dir = backend_dir / "models"


def test_model_artifacts_exist_and_loadable():
    elec_path = models_dir / "energy_electricity.joblib"
    gas_path = models_dir / "energy_gas.joblib"
    val_path = models_dir / "property_value.joblib"

    assert elec_path.exists(), "Missing energy_electricity.joblib"
    assert gas_path.exists(), "Missing energy_gas.joblib"
    assert val_path.exists(), "Missing property_value.joblib"

    m_elec = joblib.load(elec_path)
    m_gas = joblib.load(gas_path)
    m_val = joblib.load(val_path)

    assert hasattr(m_elec, "predict")
    assert hasattr(m_gas, "predict")
    assert "pipeline" in m_val
    assert hasattr(m_val["pipeline"], "predict")


def test_predict_energy_pipeline():
    prop = PropertyData(
        property_id="P_TEST_ML",
        property_type="detached",
        property_age=1988,
        floor_area_m2=125.0,
        bedrooms=4,
        energy_rating="C",
        heating_system="gas_boiler",
        insulation_type="average",
        glazing_type="double",
        solar_installed="none",
        smart_controls=True,
        region="South West",
        current_property_value=385000.0,
    )
    pred_elec, pred_gas = predict_energy(prop)

    assert pred_elec > 0.0, "Electricity prediction must be positive"
    assert pred_gas > 0.0, "Gas prediction must be positive for gas boiler"
    assert pred_elec < 25000.0
    assert pred_gas < 60000.0


def test_property_valuation_uplift_model():
    prop = PropertyData(
        property_id="P_VAL_ML",
        property_type="semi_detached",
        property_age=1965,
        floor_area_m2=105.0,
        bedrooms=3,
        energy_rating="E",
        heating_system="gas_boiler",
        insulation_type="poor",
        glazing_type="single",
        solar_installed="none",
        smart_controls=False,
        region="West Midlands",
        current_property_value=240000.0,
        annual_electricity_kwh=3800.0,
        annual_gas_kwh=16000.0,
    )
    res = predict_property_value_range(prop, ["roof_insulation", "heat_pump", "solar_pv"])

    assert res.is_available is True
    assert res.indicative_value_min_gbp > 240000.0
    assert res.indicative_value_max_gbp >= res.indicative_value_min_gbp
    assert res.indicative_uplift_pct_min > 0.0
    assert res.indicative_uplift_pct_max >= res.indicative_uplift_pct_min
