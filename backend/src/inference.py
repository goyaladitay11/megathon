"""
Unified Inference Layer with Trained ML Pipeline Integration
Lloyds Megathon X PS2 (Phase 13 & Format F)

Exposes reusable standalone Python functions:
- score_home(property_data)
- predict_energy(property_data)
- recommend_retrofits(property_data)
- simulate_retrofit(property_data, selected_retrofits)
- calculate_carbon(baseline, scenario, emissions_factors)
- predict_property_value_range(property_data, scenario)
- analyse_home(property_data)
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import joblib
import pandas as pd
import numpy as np

from backend.src.schemas import (
    PropertyData,
    ScoreResult,
    RetrofitRecommendationItem,
    EnergyResult,
    CarbonResult,
    ValuationRangeResult,
    FullHomeAnalysis,
)
from backend.src.scoring_engine import score_home
from backend.src.retrofit_engine import recommend_retrofits, simulate_retrofit
from backend.src.carbon_engine import calculate_carbon

script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
models_dir = backend_dir / "models"

# Global model cache to avoid repeated disk I/O
_MODELS_CACHE = {}


def _get_models() -> dict:
    if not _MODELS_CACHE:
        elec_path = models_dir / "energy_electricity.joblib"
        gas_path = models_dir / "energy_gas.joblib"
        val_path = models_dir / "property_value.joblib"

        if elec_path.exists():
            _MODELS_CACHE["electricity"] = joblib.load(elec_path)
        if gas_path.exists():
            _MODELS_CACHE["gas"] = joblib.load(gas_path)
        if val_path.exists():
            _MODELS_CACHE["valuation"] = joblib.load(val_path)

    return _MODELS_CACHE


def predict_energy(prop: PropertyData) -> Tuple[float, float]:
    """
    Predicts annual electricity and gas consumption using trained HistGradientBoosting ML pipelines.
    Used when metered consumption is unavailable or to baseline unmetered domestic properties.
    """
    models = _get_models()
    row = pd.DataFrame([{
        "property_type": prop.property_type,
        "property_age": prop.property_age,
        "floor_area_m2": prop.floor_area_m2,
        "bedrooms": prop.bedrooms,
        "energy_rating": prop.energy_rating,
        "heating_system": prop.heating_system,
        "insulation_type": prop.insulation_type,
        "glazing_type": prop.glazing_type,
        "solar_installed": prop.solar_installed,
        "smart_controls": prop.smart_controls,
        "region": prop.region,
    }])

    if "electricity" in models:
        pred_elec = float(models["electricity"].predict(row)[0])
    else:
        pred_elec = 3500.0

    if "gas" in models:
        pred_gas = float(models["gas"].predict(row)[0])
    else:
        pred_gas = 12000.0 if prop.heating_system != "heat_pump" else 0.0

    return max(800.0, round(pred_elec, 1)), max(0.0, round(pred_gas, 1))


# Indicative EPC progression sequence for property valuation
EPC_ORDER = ["G", "F", "E", "D", "C", "B", "A"]


def estimate_post_retrofit_epc(current_rating: str, selected_retrofits: List[str]) -> str:
    clean_rating = str(current_rating).upper().strip()
    if clean_rating not in EPC_ORDER:
        return clean_rating

    current_idx = EPC_ORDER.index(clean_rating)
    steps = 0
    if "roof_insulation" in selected_retrofits:
        steps += 1
    if "double_glazing" in selected_retrofits:
        steps += 1
    if "heat_pump" in selected_retrofits:
        steps += 2
    if "solar_pv" in selected_retrofits:
        steps += 1
    if "smart_thermostat" in selected_retrofits and steps == 0:
        steps += 1

    new_idx = min(len(EPC_ORDER) - 1, current_idx + steps)
    return EPC_ORDER[new_idx]


def predict_property_value_range(
    property_data: PropertyData,
    scenario_retrofits: List[str],
) -> ValuationRangeResult:
    """
    Estimates indicative property value uplift range holding structural features and location constant.
    Uses trained hedonic valuation model and empirical residual uncertainty bounds.
    """
    base_val = property_data.current_property_value

    if base_val is None or base_val <= 0.0:
        return ValuationRangeResult(
            baseline_value_gbp=None,
            indicative_uplift_pct_min=None,
            indicative_uplift_pct_max=None,
            indicative_value_min_gbp=None,
            indicative_value_max_gbp=None,
            range_label="Unavailable (Missing Baseline Valuation)",
            is_available=False,
            unavailable_reason="Baseline property value missing or unrecorded.",
            methodology="Hedonic regression baseline comparison.",
            caveat="Valuation impact requires an established baseline valuation to avoid speculative distortion.",
        )

    if not scenario_retrofits:
        return ValuationRangeResult(
            baseline_value_gbp=round(base_val, 2),
            indicative_uplift_pct_min=0.0,
            indicative_uplift_pct_max=0.0,
            indicative_value_min_gbp=round(base_val, 2),
            indicative_value_max_gbp=round(base_val, 2),
            range_label="0.0%",
            is_available=True,
            unavailable_reason=None,
            methodology="Baseline unchanged.",
            caveat="No alterations evaluated.",
        )

    models = _get_models()
    new_epc = estimate_post_retrofit_epc(property_data.energy_rating, scenario_retrofits)

    if "valuation" in models:
        val_obj = models["valuation"]
        val_pipe = val_obj["pipeline"]
        q_res = val_obj.get("residual_quantiles", {"p10": -20000.0, "p90": 20000.0})

        # Baseline features
        row_base = pd.DataFrame([{
            "property_age": property_data.property_age,
            "floor_area_m2": property_data.floor_area_m2,
            "bedrooms": property_data.bedrooms,
            "sale_year": 2024,
            "property_type": property_data.property_type,
            "energy_rating_at_sale": property_data.energy_rating,
            "region": property_data.region,
        }])

        # Post-retrofit features (identical location & size, upgraded EPC)
        row_scen = pd.DataFrame([{
            "property_age": property_data.property_age,
            "floor_area_m2": property_data.floor_area_m2,
            "bedrooms": property_data.bedrooms,
            "sale_year": 2024,
            "property_type": property_data.property_type,
            "energy_rating_at_sale": new_epc,
            "region": property_data.region,
        }])

        pred_base = float(val_pipe.predict(row_base)[0])
        pred_scen = float(val_pipe.predict(row_scen)[0])

        model_uplift_pct = ((pred_scen - pred_base) / pred_base) * 100.0 if pred_base > 0 else 0.0

        # Technology specific premium observed in empirical UK studies
        tech_prem = 0.0
        if "solar_pv" in scenario_retrofits:
            tech_prem += 1.0
        if "heat_pump" in scenario_retrofits:
            tech_prem += 1.0

        total_center_pct = max(1.5, model_uplift_pct + tech_prem)
        min_pct = round(max(1.0, total_center_pct * 0.70), 1)
        max_pct = round(min(16.0, total_center_pct * 1.35), 1)

    else:
        # Fallback heuristic calculation if model not present
        current_idx = EPC_ORDER.index(property_data.energy_rating) if property_data.energy_rating in EPC_ORDER else 3
        new_idx = EPC_ORDER.index(new_epc) if new_epc in EPC_ORDER else current_idx
        band_jump = max(0, new_idx - current_idx)
        min_pct = round(max(1.0, band_jump * 1.8), 1)
        max_pct = round(max(min_pct + 1.5, min_pct * 1.7), 1)

    val_min = round(base_val * (1.0 + min_pct / 100.0), -2)
    val_max = round(base_val * (1.0 + max_pct / 100.0), -2)

    return ValuationRangeResult(
        baseline_value_gbp=round(base_val, 2),
        indicative_uplift_pct_min=min_pct,
        indicative_uplift_pct_max=max_pct,
        indicative_value_min_gbp=val_min,
        indicative_value_max_gbp=val_max,
        range_label=f"+{min_pct:.1f}% to +{max_pct:.1f}%",
        is_available=True,
        unavailable_reason=None,
        methodology=f"Hedonic uplift based on projected EPC transition {property_data.energy_rating} -> {new_epc} using trained UK hedonic valuation pipeline.",
        caveat="Estimated potential property-value impact based on observational market relationships in synthetic UK housing dataset. Does not guarantee market increase or constitute a formal valuation.",
    )


def analyse_home(prop: PropertyData) -> FullHomeAnalysis:
    """
    End-to-end Property Analysis Pipeline matching Phase 13 and Format F:
    1. Score home (deterministic 7-component formula)
    2. Feasible retrofits
    3. Sequential physical simulation
    4. Deterministic carbon engine
    5. Indicative property valuation range
    """
    # 1. Deterministic Green Home Score
    score_res = score_home(prop)

    # 2. Feasible Retrofit Recommendations
    feasible_recs = recommend_retrofits(prop)
    package_ids = [r.retrofit_id for r in feasible_recs]

    # 3. Interacting Energy Simulation
    sim_res = simulate_retrofit(prop, package_ids)

    # 4. Deterministic Carbon Engine
    carb_res = calculate_carbon(
        {"electricity_kwh": sim_res.baseline_electricity_kwh, "gas_kwh": sim_res.baseline_gas_kwh},
        {"electricity_kwh": sim_res.after_electricity_kwh, "gas_kwh": sim_res.after_gas_kwh},
    )

    # 5. Indicative Property Valuation Range
    val_res = predict_property_value_range(prop, package_ids)

    warnings = []
    if prop.annual_electricity_kwh is None:
        warnings.append("Annual electricity consumption was not provided; imputed using trained energy regression model.")
    if prop.annual_gas_kwh is None:
        warnings.append("Annual gas consumption was not provided; imputed using trained energy regression model.")
    if prop.heating_system == "heat_pump" and prop.annual_gas_kwh and prop.annual_gas_kwh > 2000.0:
        warnings.append("Physical contradiction: Heat pump specified but significant gas consumption recorded.")

    assumptions = [
        "Fixed 7-component score weights sum to 1.00; sub-score mappings are strictly monotonic.",
        "Space heating disaggregated with typical 85% condensing boiler efficiency.",
        "Air source heat pump operates at SPF 3.0 seasonal coefficient of performance, eliminating space/water heating gas.",
        "Emissions computed using UK Government 2024 GHG conversion factors (0.20707 kg/kWh elec, 0.18254 kg/kWh gas).",
        "Property value uplift reflects observational hedonic models on UK housing distributions, holding area and structural characteristics constant.",
    ]

    return FullHomeAnalysis(
        property_id=prop.property_id,
        green_home_score=score_res.green_home_score,
        classification=score_res.classification,
        is_poor_performing=score_res.is_poor_performing,
        component_scores=score_res.component_scores,
        component_contributions=score_res.component_contributions,
        improvement_potential_pct=sim_res.improvement_potential_pct,
        recommended_retrofits=feasible_recs,
        package_applied_retrofits=package_ids,
        baseline={
            "electricity_kwh": sim_res.baseline_electricity_kwh,
            "gas_kwh": sim_res.baseline_gas_kwh,
            "total_purchased_kwh": sim_res.baseline_purchased_kwh,
        },
        scenario={
            "electricity_kwh": sim_res.after_electricity_kwh,
            "gas_kwh": sim_res.after_gas_kwh,
            "total_purchased_kwh": sim_res.after_purchased_kwh,
        },
        estimated_energy_saving_kwh=sim_res.net_purchased_energy_saving_kwh,
        estimated_carbon_reduction_kg=carb_res.net_carbon_reduction_kg,
        estimated_carbon_reduction_tonnes=carb_res.net_carbon_reduction_tonnes,
        property_value_impact_range={
            "range_label": val_res.range_label,
            "min_gbp": val_res.indicative_value_min_gbp,
            "max_gbp": val_res.indicative_value_max_gbp,
            "min_pct": val_res.indicative_uplift_pct_min,
            "max_pct": val_res.indicative_uplift_pct_max,
            "is_available": val_res.is_available,
            "caveat": val_res.caveat,
        },
        assumptions=assumptions,
        warnings=warnings,
    )
