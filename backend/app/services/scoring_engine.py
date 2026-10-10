"""
Deterministic Green Home Scoring Engine
Step 3: Documented 7-Component Explainable Scoring Formulation
"""

from typing import List, Tuple
from backend.app.core.config import settings
from backend.app.schemas.property import PropertySummary
from backend.app.schemas.scoring import ComponentScore, GreenHomeScoreResult, ClassificationEnum


def calculate_epc_sub_score(rating: str) -> Tuple[float, str]:
    mapping = {
        "A": (95.0, "EPC Band A: Exceptional certified building envelope and building fabric performance"),
        "B": (85.0, "EPC Band B: High efficiency standard matching modern UK Building Regulations"),
        "C": (70.0, "EPC Band C: Good domestic standard meeting UK 2035 Clean Growth target"),
        "D": (50.0, "EPC Band D: Median UK domestic average; significant retrofit potential"),
        "E": (35.0, "EPC Band E: Sub-standard thermal efficiency; high vulnerability to fuel poverty"),
        "F": (20.0, "EPC Band F: Poor efficiency; fails UK Minimum Energy Efficiency Standards (MEES)"),
        "G": (5.0, "EPC Band G: Very poor efficiency; severe heat loss and carbon intensity"),
    }
    clean_rating = str(rating).upper().strip()
    return mapping.get(clean_rating, (50.0, f"Unrecognized rating '{rating}', assigned default baseline"))


def calculate_intensity_sub_score(intensity_kwh_m2: float) -> Tuple[float, str]:
    """
    Monotonically decreasing score with respect to metered energy consumption intensity (kWh/m2/yr).
    Uses continuous piecewise interpolation to guarantee strict monotonicity.
    Benchmarks from UK Ofgem & National Energy Efficiency Data-Framework (NEED).
    """
    x = max(0.0, float(intensity_kwh_m2))
    if x <= 50.0:
        score = 100.0 - (x / 50.0) * 10.0  # 100.0 -> 90.0
        desc = f"Ultra-low consumption intensity ({x:.1f} kWh/m²): exemplary domestic usage"
    elif x <= 120.0:
        # 90.0 -> 75.0
        score = 90.0 - ((x - 50.0) / 70.0) * 15.0
        desc = f"Efficient consumption intensity ({x:.1f} kWh/m²): well below UK domestic average (~160 kWh/m²)"
    elif x <= 180.0:
        # 75.0 -> 55.0
        score = 75.0 - ((x - 120.0) / 60.0) * 20.0
        desc = f"Moderate consumption intensity ({x:.1f} kWh/m²): near typical UK dual-fuel consumption"
    elif x <= 260.0:
        # 55.0 -> 35.0
        score = 55.0 - ((x - 180.0) / 80.0) * 20.0
        desc = f"Elevated consumption intensity ({x:.1f} kWh/m²): above typical domestic range"
    elif x <= 360.0:
        # 35.0 -> 15.0
        score = 35.0 - ((x - 260.0) / 100.0) * 20.0
        desc = f"High consumption intensity ({x:.1f} kWh/m²): excessive energy loss per floor area"
    else:
        # Bounded at 5.0 min
        excess = min(x - 360.0, 200.0)
        score = max(5.0, 15.0 - (excess / 200.0) * 10.0)
        desc = f"Severe consumption intensity ({x:.1f} kWh/m²): extreme heat escape or anomalous energy draw"

    return round(score, 1), desc


def calculate_insulation_sub_score(insulation: str) -> Tuple[float, str]:
    mapping = {
        "good": (90.0, "Good insulation: Loft >=270mm and cavity/solid wall insulation verified"),
        "average": (50.0, "Average insulation: Partial loft or standard unfilled cavity; room for fabric upgrades"),
        "poor": (15.0, "Poor insulation: Uninsulated loft/roof and uninsulated solid walls leading to heavy fabric heat loss"),
    }
    clean = str(insulation).lower().strip()
    return mapping.get(clean, (50.0, "Average standard assumed"))


def calculate_heating_sub_score(heating: str) -> Tuple[float, str]:
    mapping = {
        "heat_pump": (95.0, "Heat pump: Zero direct fossil combustion; high seasonal coefficient of performance (SPF ~3.0)"),
        "electric_resistive": (45.0, "Electric direct resistive: Decarbonising grid source, but high running cost and 1:1 COP"),
        "gas_boiler": (40.0, "Mains gas boiler: High carbon fossil combustion; subject to future boiler phase-out targets"),
        "oil_boiler": (15.0, "Oil boiler: Heavy carbon intensity and high local air pollutant emissions"),
    }
    clean = str(heating).lower().strip()
    return mapping.get(clean, (40.0, "Standard heating system assumed"))


def calculate_glazing_sub_score(glazing: str) -> Tuple[float, str]:
    mapping = {
        "triple": (95.0, "Triple glazing: Exceptional acoustic and thermal transmittance U-value (<0.8 W/m²K)"),
        "double": (75.0, "Double glazing: Standard UK multi-chamber thermal insulation barrier"),
        "single": (20.0, "Single glazing: Severe conductive window heat loss and condensation vulnerability"),
    }
    clean = str(glazing).lower().strip()
    return mapping.get(clean, (75.0, "Standard double glazing assumed"))


def calculate_renewables_sub_score(solar: str) -> Tuple[float, str]:
    mapping = {
        "4kw": (95.0, "4kW+ Solar PV: Substantial on-site renewable generation offsetting 25-35% of electricity imports"),
        "2kw": (60.0, "2kW Solar PV: Modest on-site renewable solar generation offsetting baseline baseload"),
        "none": (5.0, "No renewable generation: 100% reliant on grid power and external gas infrastructure"),
    }
    clean = str(solar).lower().strip()
    return mapping.get(clean, (5.0, "No on-site renewables verified"))


def calculate_smart_controls_sub_score(smart_controls: bool) -> Tuple[float, str]:
    if smart_controls:
        return (90.0, "Smart controls present: Programmable scheduling, weather compensation, or zone temperature control active")
    return (20.0, "Standard manual controls: Lacks automated scheduling and temperature optimisation")


def compute_green_home_score(summary: PropertySummary) -> GreenHomeScoreResult:
    """
    Computes the 7-component weighted Green Home Score.
    Guarantees strict monotonicity: a better state never lowers a sub-score.
    Rounds final score to the nearest integer.
    """
    # 1. Energy Efficiency (25%)
    s_epc, desc_epc = calculate_epc_sub_score(summary.energy_rating)
    w_epc = settings.WEIGHT_ENERGY_EFFICIENCY

    # 2. Consumption Intensity (20%)
    s_intensity, desc_intensity = calculate_intensity_sub_score(summary.energy_intensity_kwh_m2)
    w_intensity = settings.WEIGHT_CONSUMPTION_INTENSITY

    # 3. Insulation (15%)
    s_insulation, desc_insulation = calculate_insulation_sub_score(summary.insulation)
    w_insulation = settings.WEIGHT_INSULATION

    # 4. Heating System (15%)
    s_heating, desc_heating = calculate_heating_sub_score(summary.heating)
    w_heating = settings.WEIGHT_HEATING_SYSTEM

    # 5. Glazing (10%)
    s_glazing, desc_glazing = calculate_glazing_sub_score(summary.glazing)
    w_glazing = settings.WEIGHT_GLAZING

    # 6. Renewables (10%)
    s_solar, desc_solar = calculate_renewables_sub_score(summary.solar)
    w_solar = settings.WEIGHT_RENEWABLES

    # 7. Smart Controls (5%)
    s_smart, desc_smart = calculate_smart_controls_sub_score(summary.smart_controls)
    w_smart = settings.WEIGHT_SMART_CONTROLS

    components = [
        ComponentScore(
            component_name="Energy efficiency (EPC)",
            raw_sub_score=s_epc,
            weight=w_epc,
            contribution=round(s_epc * w_epc, 2),
            input_value=f"EPC Band {summary.energy_rating}",
            explanation=desc_epc,
        ),
        ComponentScore(
            component_name="Metered energy consumption intensity",
            raw_sub_score=s_intensity,
            weight=w_intensity,
            contribution=round(s_intensity * w_intensity, 2),
            input_value=f"{summary.energy_intensity_kwh_m2:.1f} kWh/m²",
            explanation=desc_intensity,
        ),
        ComponentScore(
            component_name="Insulation",
            raw_sub_score=s_insulation,
            weight=w_insulation,
            contribution=round(s_insulation * w_insulation, 2),
            input_value=summary.insulation.capitalize(),
            explanation=desc_insulation,
        ),
        ComponentScore(
            component_name="Heating system",
            raw_sub_score=s_heating,
            weight=w_heating,
            contribution=round(s_heating * w_heating, 2),
            input_value=summary.heating.replace("_", " ").capitalize(),
            explanation=desc_heating,
        ),
        ComponentScore(
            component_name="Windows and glazing",
            raw_sub_score=s_glazing,
            weight=w_glazing,
            contribution=round(s_glazing * w_glazing, 2),
            input_value=f"{summary.glazing.capitalize()} glazing",
            explanation=desc_glazing,
        ),
        ComponentScore(
            component_name="Renewable energy",
            raw_sub_score=s_solar,
            weight=w_solar,
            contribution=round(s_solar * w_solar, 2),
            input_value=f"{summary.solar.upper()} Solar PV",
            explanation=desc_solar,
        ),
        ComponentScore(
            component_name="Smart energy management",
            raw_sub_score=s_smart,
            weight=w_smart,
            contribution=round(s_smart * w_smart, 2),
            input_value="Installed" if summary.smart_controls else "None",
            explanation=desc_smart,
        ),
    ]

    exact_score = sum(c.contribution for c in components)
    final_score = int(round(exact_score))
    final_score = max(0, min(100, final_score))

    # Official classification boundaries (from Problem Statement Section 2)
    if final_score >= 80:
        classification: ClassificationEnum = "Highly efficient"
    elif final_score >= 65:
        classification = "Good"
    elif final_score >= 50:
        classification = "Moderate"
    elif final_score >= 30:
        classification = "Poor"
    else:
        classification = "Very poor"

    is_poor = classification in ["Poor", "Very poor"]

    return GreenHomeScoreResult(
        property_id=summary.property_id,
        final_score=final_score,
        exact_score=round(exact_score, 2),
        classification=classification,
        is_poor_performing=is_poor,
        components=components,
        methodology_summary=(
            "Green Home Score S = sum(w_k * s_k) across 7 documented components: "
            "Energy Efficiency (25%), Metered Intensity (20%), Insulation (15%), "
            "Heating (15%), Glazing (10%), Renewables (10%), Smart Controls (5%). "
            "Final score rounded to nearest integer."
        ),
    )


calculate_green_home_score = compute_green_home_score
