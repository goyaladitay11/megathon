"""
Deterministic Green Home Score Engine
Lloyds Megathon X PS2 (Section 2 & Phase 4)

Formula:
S = round(sum_{k} w_k * s_k)
Weights (fixed):
- Energy Efficiency: 25% (0.25)
- Consumption Intensity: 20% (0.20)
- Insulation: 15% (0.15)
- Heating System: 15% (0.15)
- Windows & Glazing: 10% (0.10)
- Renewable Energy: 10% (0.10)
- Smart Energy Management: 5% (0.05)
Total Weight = 1.00 (100%)
"""

from typing import Dict, Tuple, List, Optional
from backend.src.schemas import PropertyData, ScoreResult, ComponentScoreDetail, ClassificationType

WEIGHTS = {
    "energy_efficiency": 0.25,
    "consumption_intensity": 0.20,
    "insulation": 0.15,
    "heating": 0.15,
    "glazing": 0.10,
    "renewables": 0.10,
    "smart_controls": 0.05,
}

# Monotonic Sub-Score Mappings calibrated to UK residential housing benchmarks
EPC_MAPPING: Dict[str, Tuple[float, str]] = {
    "A": (100.0, "EPC Band A: Exceptional certified building fabric & SAP rating (92-100)"),
    "B": (85.0, "EPC Band B: High energy performance meeting modern UK Building Regulations (81-91)"),
    "C": (70.0, "EPC Band C: Good domestic standard meeting UK 2035 Clean Growth target (69-80)"),
    "D": (55.0, "EPC Band D: Median UK domestic average; standard retrofit potential (55-68)"),
    "E": (40.0, "EPC Band E: Sub-standard thermal efficiency; high fuel poverty risk (39-54)"),
    "F": (20.0, "EPC Band F: Poor efficiency; fails UK Minimum Energy Efficiency Standards (21-38)"),
    "G": (0.0, "EPC Band G: Severe heat loss and extreme carbon intensity (1-20)"),
}

INSULATION_MAPPING: Dict[str, Tuple[float, str]] = {
    "good": (90.0, "Good insulation: Loft >=270mm and cavity/solid wall insulation verified"),
    "average": (50.0, "Average insulation: Partial loft or standard unfilled cavity; room for upgrades"),
    "poor": (15.0, "Poor insulation: Uninsulated loft/roof and uninsulated solid walls leading to heavy fabric heat loss"),
}

HEATING_MAPPING: Dict[str, Tuple[float, str]] = {
    "heat_pump": (95.0, "Heat pump: Zero direct fossil combustion; high seasonal coefficient of performance (SPF ~3.0)"),
    "electric_resistive": (45.0, "Electric direct resistive: Decarbonising grid source, but high running cost and 1:1 COP"),
    "gas_boiler": (40.0, "Mains gas boiler: High carbon fossil combustion; subject to future boiler phase-out targets"),
    "oil_boiler": (15.0, "Oil boiler: Heavy carbon intensity and high local air pollutant emissions"),
}

GLAZING_MAPPING: Dict[str, Tuple[float, str]] = {
    "triple": (95.0, "Triple glazing: Exceptional acoustic and thermal transmittance U-value (<0.8 W/m²K)"),
    "double": (75.0, "Double glazing: Standard UK multi-chamber thermal insulation barrier"),
    "single": (20.0, "Single glazing: Severe conductive window heat loss and condensation vulnerability"),
}

SOLAR_MAPPING: Dict[str, Tuple[float, str]] = {
    "4kw": (95.0, "4kW+ Solar PV: Substantial on-site renewable generation offsetting 25-35% of electricity imports"),
    "2kw": (60.0, "2kW Solar PV: Modest on-site renewable solar generation offsetting baseline baseload"),
    "none": (5.0, "No renewable generation: 100% reliant on grid power and external gas infrastructure"),
}


def compute_intensity_sub_score(intensity_kwh_m2: float) -> Tuple[float, str]:
    """
    Monotonically decreasing sub-score with respect to metered energy intensity (kWh/m2/yr).
    Lower consumption intensity MUST NEVER produce a lower score.
    Piecewise linear interpolation calibrated to UK Ofgem Typical Domestic Consumption Values (TDCV) & NEED.
    """
    x = max(0.0, float(intensity_kwh_m2))
    if x <= 50.0:
        score = 100.0 - (x / 50.0) * 10.0  # 100.0 -> 90.0
        desc = f"Ultra-low consumption intensity ({x:.1f} kWh/m²): exemplary domestic usage"
    elif x <= 120.0:
        score = 90.0 - ((x - 50.0) / 70.0) * 15.0  # 90.0 -> 75.0
        desc = f"Efficient consumption intensity ({x:.1f} kWh/m²): well below UK domestic average (~160 kWh/m²)"
    elif x <= 180.0:
        score = 75.0 - ((x - 120.0) / 60.0) * 20.0  # 75.0 -> 55.0
        desc = f"Moderate consumption intensity ({x:.1f} kWh/m²): near typical UK dual-fuel consumption"
    elif x <= 260.0:
        score = 55.0 - ((x - 180.0) / 80.0) * 20.0  # 55.0 -> 35.0
        desc = f"Elevated consumption intensity ({x:.1f} kWh/m²): above typical domestic range"
    elif x <= 360.0:
        score = 35.0 - ((x - 260.0) / 100.0) * 20.0  # 35.0 -> 15.0
        desc = f"High consumption intensity ({x:.1f} kWh/m²): excessive energy loss per floor area"
    else:
        excess = min(x - 360.0, 200.0)
        score = max(5.0, 15.0 - (excess / 200.0) * 10.0)  # 15.0 -> 5.0 min
        desc = f"Severe consumption intensity ({x:.1f} kWh/m²): extreme heat escape or anomalous energy draw"

    return round(score, 1), desc


def classify_score(score: int) -> Tuple[ClassificationType, bool]:
    """
    Classifies integer score into official bands:
    80–100 Highly efficient
    65–79 Good
    50–64 Moderate
    30–49 Poor
    0–29 Very poor
    """
    if score >= 80:
        return "Highly efficient", False
    elif score >= 65:
        return "Good", False
    elif score >= 50:
        return "Moderate", False
    elif score >= 30:
        return "Poor", True
    else:
        return "Very poor", True


def score_home(prop: PropertyData) -> ScoreResult:
    """
    Computes the official 7-component Green Home Score deterministically.
    Guarantee: Fully reproducible, explainable, monotonic, zero random numbers.
    """
    # 1. Energy Efficiency (25%)
    epc_clean = str(prop.energy_rating).upper().strip()
    s_epc, desc_epc = EPC_MAPPING.get(epc_clean, (55.0, f"Unrecognized rating '{epc_clean}', assigned median D"))

    # 2. Consumption Intensity (20%)
    elec = prop.annual_electricity_kwh if prop.annual_electricity_kwh is not None else 3500.0
    gas = prop.annual_gas_kwh if prop.annual_gas_kwh is not None else 12000.0
    floor_area = max(prop.floor_area_m2, 10.0)
    intensity = (elec + gas) / floor_area
    s_int, desc_int = compute_intensity_sub_score(intensity)

    # 3. Insulation (15%)
    ins_clean = str(prop.insulation_type).lower().strip()
    s_ins, desc_ins = INSULATION_MAPPING.get(ins_clean, (50.0, "Average insulation assumed"))

    # 4. Heating (15%)
    heat_clean = str(prop.heating_system).lower().strip()
    s_heat, desc_heat = HEATING_MAPPING.get(heat_clean, (40.0, "Standard heating assumed"))

    # 5. Glazing (10%)
    glaz_clean = str(prop.glazing_type).lower().strip()
    s_glaz, desc_glaz = GLAZING_MAPPING.get(glaz_clean, (75.0, "Standard double glazing assumed"))

    # 6. Renewables (10%)
    sol_clean = str(prop.solar_installed).lower().strip()
    s_sol, desc_sol = SOLAR_MAPPING.get(sol_clean, (5.0, "No renewables assumed"))

    # 7. Smart Controls (5%)
    if prop.smart_controls:
        s_smart = 95.0
        desc_smart = "Smart thermostat / zone heating controls installed"
    else:
        s_smart = 15.0
        desc_smart = "Manual or standard mechanical controls without zoning/setback"

    sub_scores = {
        "energy_efficiency": s_epc,
        "consumption_intensity": s_int,
        "insulation": s_ins,
        "heating": s_heat,
        "glazing": s_glaz,
        "renewables": s_sol,
        "smart_controls": s_smart,
    }

    contributions = {
        k: round(sub_scores[k] * WEIGHTS[k], 2)
        for k in WEIGHTS
    }

    exact_sum = sum(sub_scores[k] * WEIGHTS[k] for k in WEIGHTS)
    final_score = int(round(exact_sum))
    final_score = max(0, min(100, final_score))

    classification, is_poor = classify_score(final_score)

    details = [
        ComponentScoreDetail(
            name="Energy Efficiency",
            raw_sub_score=s_epc,
            weight=WEIGHTS["energy_efficiency"],
            contribution=contributions["energy_efficiency"],
            input_value=f"EPC Band {epc_clean}",
            explanation=desc_epc,
        ),
        ComponentScoreDetail(
            name="Energy Consumption Intensity",
            raw_sub_score=s_int,
            weight=WEIGHTS["consumption_intensity"],
            contribution=contributions["consumption_intensity"],
            input_value=f"{intensity:.1f} kWh/m²/year",
            explanation=desc_int,
        ),
        ComponentScoreDetail(
            name="Insulation",
            raw_sub_score=s_ins,
            weight=WEIGHTS["insulation"],
            contribution=contributions["insulation"],
            input_value=prop.insulation_type,
            explanation=desc_ins,
        ),
        ComponentScoreDetail(
            name="Heating System",
            raw_sub_score=s_heat,
            weight=WEIGHTS["heating"],
            contribution=contributions["heating"],
            input_value=prop.heating_system,
            explanation=desc_heat,
        ),
        ComponentScoreDetail(
            name="Windows & Glazing",
            raw_sub_score=s_glaz,
            weight=WEIGHTS["glazing"],
            contribution=contributions["glazing"],
            input_value=prop.glazing_type,
            explanation=desc_glaz,
        ),
        ComponentScoreDetail(
            name="Renewable Energy",
            raw_sub_score=s_sol,
            weight=WEIGHTS["renewables"],
            contribution=contributions["renewables"],
            input_value=prop.solar_installed,
            explanation=desc_sol,
        ),
        ComponentScoreDetail(
            name="Smart Energy Management",
            raw_sub_score=s_smart,
            weight=WEIGHTS["smart_controls"],
            contribution=contributions["smart_controls"],
            input_value="Enabled" if prop.smart_controls else "Disabled",
            explanation=desc_smart,
        ),
    ]

    return ScoreResult(
        property_id=prop.property_id,
        green_home_score=final_score,
        exact_score=round(exact_sum, 2),
        classification=classification,
        is_poor_performing=is_poor,
        component_scores=sub_scores,
        component_contributions=contributions,
        component_details=details,
        reconciliation_valid=True,
    )
