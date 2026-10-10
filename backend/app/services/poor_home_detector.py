"""
Poor Home Detection & Issue Diagnostic Engine
Step 4: Identification of Sub-standard Homes & Prioritisation
"""

from typing import List, Tuple, Optional
from backend.app.schemas.property import PropertySummary
from backend.app.schemas.scoring import GreenHomeScoreResult


def detect_key_issues(summary: PropertySummary, score_result: GreenHomeScoreResult) -> List[str]:
    """
    Identifies concrete improvement issues based strictly on measured property features.
    Does not penalize larger homes solely for total consumption.
    """
    issues: List[str] = []

    # 1. Thermal Fabric / Insulation
    if summary.insulation == "poor":
        issues.append("Uninsulated or deficient roof/loft and wall fabric leading to severe space heat loss.")
    elif summary.insulation == "average":
        issues.append("Sub-optimal insulation below modern building regulation depth (270mm+).")

    # 2. Glazing
    if summary.glazing == "single":
        issues.append("Single glazing creates thermal bridging, condensation, and rapid window heat transmission.")

    # 3. Heating System
    if summary.heating in ["gas_boiler", "oil_boiler"]:
        issues.append(f"Fossil-fuel dependent {summary.heating.replace('_', ' ')} contributes direct Scope 1 carbon emissions.")
    elif summary.heating == "electric_resistive":
        issues.append("Direct electric resistive heating operates at 1:1 COP, causing elevated running costs.")

    # 4. Energy Consumption Intensity per m2 (normalized, not raw total)
    if summary.energy_intensity_kwh_m2 > 220.0:
        issues.append(
            f"Excessive consumption intensity ({summary.energy_intensity_kwh_m2:.1f} kWh/m² vs UK benchmark ~150 kWh/m²)."
        )
    elif summary.energy_intensity_kwh_m2 > 175.0:
        issues.append(
            f"Above-average consumption intensity ({summary.energy_intensity_kwh_m2:.1f} kWh/m²)."
        )

    # 5. Renewable Generation
    if summary.solar == "none":
        issues.append("Zero on-site renewable generation; 100% dependent on purchased grid electricity.")

    # 6. Controls
    if not summary.smart_controls:
        issues.append("Lack of smart heating controls/thermostat prevents automated temperature zoning and setbacks.")

    # 7. EPC Certification
    if summary.energy_rating in ["E", "F", "G"]:
        issues.append(f"Statutory EPC Band {summary.energy_rating} falls below the UK 2035 Clean Growth target (Band C).")

    return issues


def calculate_improvement_potential_metric(
    baseline_purchased_kwh: float,
    post_purchased_kwh: float,
) -> Tuple[Optional[float], bool, Optional[str]]:
    """
    Calculates improvement potential: 100 * (E_baseline - E_after) / E_baseline.
    Purchased energy = grid electricity imported + gas consumed in kWh/year.
    
    If baseline energy is zero or unavailable, reports metric as unavailable and documents handling.
    """
    if baseline_purchased_kwh is None or baseline_purchased_kwh <= 0.0:
        return None, False, "Baseline purchased energy is zero or unavailable; percentage improvement cannot be calculated."

    if post_purchased_kwh < 0.0:
        post_purchased_kwh = 0.0

    delta = baseline_purchased_kwh - post_purchased_kwh
    improvement_pct = (delta / baseline_purchased_kwh) * 100.0
    return round(float(improvement_pct), 2), True, None
