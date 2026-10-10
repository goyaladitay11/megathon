"""
Property Valuation Impact Engine
Step 8: Indicative Property Value Uplift Range Model
Documented according to Lloyds Megathon X Problem Statement 2 (Section 7)
"""

from typing import List, Optional, Tuple
from backend.app.schemas.property import PropertySummary
from backend.app.schemas.valuation import PropertyValuationResult


# Indicative EPC band upgrade market uplift ranges based on UK HM Land Registry & BEIS hedonic studies
# Source: UK Department for Business, Energy & Industrial Strategy (BEIS) - "Property Capital Value & Energy Efficiency"
EPC_BAND_ORDER = ["G", "F", "E", "D", "C", "B", "A"]


def estimate_post_retrofit_epc(
    current_rating: str,
    selected_retrofit_ids: List[str],
) -> str:
    """
    Estimates realistic EPC band progression following retrofit installations.
    """
    clean_rating = str(current_rating).upper().strip()
    if clean_rating not in EPC_BAND_ORDER:
        return clean_rating

    current_idx = EPC_BAND_ORDER.index(clean_rating)
    steps = 0

    if "roof_insulation" in selected_retrofit_ids:
        steps += 1
    if "double_glazing" in selected_retrofit_ids:
        steps += 1
    if "heat_pump" in selected_retrofit_ids:
        steps += 2
    if "solar_pv" in selected_retrofit_ids:
        steps += 1
    if "smart_thermostat" in selected_retrofit_ids and steps == 0:
        steps += 1

    # Max realistic jump capped at Band A
    new_idx = min(len(EPC_BAND_ORDER) - 1, current_idx + steps)
    return EPC_BAND_ORDER[new_idx]


def estimate_property_value_uplift(
    summary: PropertySummary,
    selected_retrofit_ids: List[str],
) -> PropertyValuationResult:
    """
    Estimates potential change in property value as an indicative range [min, max].
    Holds location, size, property type constant while evaluating efficiency enhancements.
    
    Adheres strictly to Problem Statement 2 Section 7:
    - Reports a range, never a single deterministic number.
    - If baseline valuation is missing/zero, flags is_available=False with clear documentation.
    - Features explicit causal disclaimer and observational market notes.
    """
    baseline_val = summary.current_property_value_gbp

    # Scenario handling: missing or non-positive baseline property value
    if baseline_val is None or baseline_val <= 0.0:
        return PropertyValuationResult(
            baseline_value_gbp=None,
            indicative_uplift_pct_min=None,
            indicative_uplift_pct_max=None,
            indicative_value_min_gbp=None,
            indicative_value_max_gbp=None,
            uplift_range_label="Unavailable (Missing Baseline Property Value)",
            is_available=False,
            unavailable_reason=(
                "Baseline property value is missing or unrecorded for this property. "
                "Per Problem Statement 2 Section 7 & 11, valuation impact requires an established baseline valuation to avoid arbitrary speculation."
            ),
            model_version="UK-Hedonic-Uplift-v1.0",
            caveat=(
                "Valuation impact requires a baseline property value. Observational historical associations "
                "cannot establish a price change without an initial appraisal."
            ),
            methodology_notes="Hedonic property-level differential requires baseline price.",
        )

    if not selected_retrofit_ids:
        return PropertyValuationResult(
            baseline_value_gbp=round(baseline_val, 2),
            indicative_uplift_pct_min=0.0,
            indicative_uplift_pct_max=0.0,
            indicative_value_min_gbp=round(baseline_val, 2),
            indicative_value_max_gbp=round(baseline_val, 2),
            uplift_range_label="0.0%",
            is_available=True,
            unavailable_reason=None,
            model_version="UK-Hedonic-Uplift-v1.0",
            caveat="No retrofits selected; baseline property value maintained.",
            methodology_notes="No alterations evaluated.",
        )

    # Determine simulated EPC transition
    current_epc = summary.energy_rating
    new_epc = estimate_post_retrofit_epc(current_epc, selected_retrofit_ids)
    
    current_idx = EPC_BAND_ORDER.index(current_epc) if current_epc in EPC_BAND_ORDER else 3
    new_idx = EPC_BAND_ORDER.index(new_epc) if new_epc in EPC_BAND_ORDER else current_idx
    band_jump = max(0, new_idx - current_idx)

    # Base uplift per band jump: 1.5% - 2.5% conservative per EPC band upgrade
    # Additional premium for renewables & modern low-carbon heating
    min_pct = round(band_jump * 1.5, 1)
    max_pct = round(band_jump * 2.8, 1)

    # Specific technology premiums observed in UK market studies:
    if "solar_pv" in selected_retrofit_ids:
        min_pct += 0.8
        max_pct += 1.5
    if "heat_pump" in selected_retrofit_ids:
        min_pct += 0.7
        max_pct += 1.8

    # Ensure non-trivial positive range for active improvements
    min_pct = max(1.0, min_pct)
    max_pct = max(min_pct + 1.5, min_pct * 1.8, max_pct)
    
    # Cap indicative ceiling to prevent inflated speculative claims
    min_pct = min(12.0, min_pct)
    max_pct = min(16.0, max_pct)

    min_pct = round(min_pct, 1)
    max_pct = round(max_pct, 1)

    val_min = round(baseline_val * (1.0 + min_pct / 100.0), -2)
    val_max = round(baseline_val * (1.0 + max_pct / 100.0), -2)

    range_label = f"+{min_pct:.1f}% to +{max_pct:.1f}%"

    return PropertyValuationResult(
        baseline_value_gbp=round(baseline_val, 2),
        indicative_uplift_pct_min=min_pct,
        indicative_uplift_pct_max=max_pct,
        indicative_value_min_gbp=val_min,
        indicative_value_max_gbp=val_max,
        uplift_range_label=range_label,
        is_available=True,
        unavailable_reason=None,
        model_version="UK-Hedonic-Uplift-v1.0",
        caveat=(
            "Estimated potential property-value impact based on historical and market relationships "
            "in UK residential transaction data. Indicative estimate only, holding structural features, "
            "location, and market conditions constant. Does not guarantee market increase or constitute a formal valuation."
        ),
        methodology_notes=(
            f"Evaluates transition from EPC Band {current_epc} to indicative Band {new_epc} "
            f"with selected retrofit improvements. Baseline value: £{baseline_val:,.0f}."
        ),
    )
