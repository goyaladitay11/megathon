"""
Retrofit Recommendation Engine
Step 5: Eligibility Filtering, Suitability Scoring, Sequencing & Package Assembly
"""

from typing import List, Tuple, Dict, Any, Optional
from backend.app.schemas.property import PropertySummary
from backend.app.schemas.retrofit import RetrofitRecommendation, RetrofitPackage, SuitabilityEnum
from backend.app.models.catalogue import RETROFIT_CATALOGUE, RetrofitItem
from backend.app.services.energy_simulator import simulate_energy_impact


def evaluate_retrofit_feasibility_and_suitability(
    summary: PropertySummary,
    retrofit_id: str,
) -> Tuple[bool, SuitabilityEnum, str, Optional[str]]:
    """
    Evaluates transparent eligibility rules, technical constraints, and suitability.
    """
    if retrofit_id == "roof_insulation":
        if summary.insulation == "good":
            return False, "Low", "Property already has high-standard roof/loft insulation (>=270mm).", None
        elif summary.insulation == "poor":
            return (
                True,
                "High",
                "High suitability: Uninsulated roof causes ~25% of all domestic heat loss. Rapid payback upgrade.",
                "Priority 1: Must precede heat pump installation (Fabric First principle).",
            )
        else:  # average
            return (
                True,
                "Medium",
                "Medium suitability: Existing insulation depth is sub-optimal; topping up to 270mm+ yields 12-15% space heating reduction.",
                "Priority 1: Recommended before heating system sizing.",
            )

    elif retrofit_id == "double_glazing":
        if summary.glazing in ["double", "triple"]:
            return False, "Low", f"Property already features {summary.glazing} glazing.", None
        return (
            True,
            "High",
            "High suitability: Replacing single glazing eliminates severe conductive window heat losses, draughts, and noise.",
            "Priority 2: Enhances building thermal envelope.",
        )

    elif retrofit_id == "smart_thermostat":
        if summary.smart_controls:
            return False, "Low", "Property already has smart heating controls installed.", None
        return (
            True,
            "High",
            "High suitability: Low upfront cost (£250 avg); provides automated scheduling, occupancy sensing, and setback optimization.",
            "Priority 3: Immediate operational efficiency improvement.",
        )

    elif retrofit_id == "heat_pump":
        if summary.heating == "heat_pump":
            return False, "Low", "Property already uses a low-carbon heat pump.", None

        # Check insulation constraint (Fabric First principle)
        if summary.insulation == "poor":
            return (
                True,
                "Medium",
                "Medium suitability: Replacing fossil fuel heating with a heat pump provides massive carbon reduction, but current poor insulation will require an oversized heat pump and risk higher operating electricity costs. Insulation should be installed first or concurrently.",
                "Priority 4: Conditioned on upgrading roof/loft insulation first.",
            )
        return (
            True,
            "High",
            "High suitability: Property thermal envelope is adequate. Replaces fossil combustion with SPF 3.0 electric heat pump, eliminating direct gas emissions.",
            "Priority 4: Major decarbonisation milestone.",
        )

    elif retrofit_id == "solar_pv":
        if summary.solar == "4kw":
            return False, "Low", "Property already has maximum standard domestic solar PV installed (4kW).", None
        elif summary.solar == "2kw":
            return (
                True,
                "Medium",
                "Medium suitability: Existing 2kW array can be expanded to 4kW to generate additional daytime electricity.",
                "Priority 5: On-site renewable generation.",
            )
        return (
            True,
            "High",
            "High suitability: Generates clean on-site electricity, offsetting 20-35% of purchased grid imports directly.",
            "Priority 5: Long-term electricity bill hedge.",
        )

    return False, "Low", "Unknown retrofit", None


def get_feasible_recommendations(summary: PropertySummary) -> List[RetrofitRecommendation]:
    """
    Returns prioritized list of retrofits feasible for the property.
    Calculates individual standalone savings using the energy simulator.
    """
    recommendations: List[RetrofitRecommendation] = []

    # Process in strict priority order (Insulation -> Glazing -> Controls -> Heat Pump -> Solar)
    ordered_ids = ["roof_insulation", "double_glazing", "smart_thermostat", "heat_pump", "solar_pv"]

    for r_id in ordered_ids:
        feasible, suitability, reason, dep_note = evaluate_retrofit_feasibility_and_suitability(summary, r_id)
        if not feasible:
            continue

        item = RETROFIT_CATALOGUE[r_id]
        # Simulate standalone impact
        sim = simulate_energy_impact(summary, [r_id])

        recommendations.append(
            RetrofitRecommendation(
                retrofit_id=r_id,
                name=item.name,
                category=item.category,
                suitability=suitability,
                is_feasible=True,
                priority_order=item.priority_order,
                estimated_annual_energy_savings_kwh=sim.total_purchased_energy_savings_kwh,
                estimated_annual_electricity_delta_kwh=sim.electricity_savings_kwh,
                estimated_annual_gas_delta_kwh=sim.gas_savings_kwh,
                estimated_cost_gbp_min=item.typical_cost_min_gbp,
                estimated_cost_gbp_max=item.typical_cost_max_gbp,
                estimated_cost_gbp_avg=item.typical_cost_avg_gbp,
                reason=reason,
                dependencies_or_notes=dep_note,
            )
        )

    return recommendations


def build_recommended_package(
    summary: PropertySummary,
    feasible_recommendations: List[RetrofitRecommendation],
) -> RetrofitPackage:
    """
    Assembles all feasible retrofits into a complete package and calculates interaction-aware savings.
    Shows the difference between naive summation and true interactive modeling.
    """
    included_ids = [r.retrofit_id for r in feasible_recommendations]
    
    if not included_ids:
        return RetrofitPackage(
            package_name="No Retrofits Required",
            included_retrofit_ids=[],
            total_estimated_cost_gbp_avg=0.0,
            total_estimated_cost_range="£0",
            standalone_sum_savings_kwh=0.0,
            interaction_aware_savings_kwh=0.0,
            interaction_discount_kwh=0.0,
            interaction_explanation="Property is already at top thermal efficiency standards.",
        )

    # Naive standalone sum
    naive_sum = sum(r.estimated_annual_energy_savings_kwh for r in feasible_recommendations)
    total_cost_avg = sum(r.estimated_cost_gbp_avg for r in feasible_recommendations)
    total_cost_min = sum(r.estimated_cost_gbp_min for r in feasible_recommendations)
    total_cost_max = sum(r.estimated_cost_gbp_max for r in feasible_recommendations)

    # True interaction-aware simulation
    sim_package = simulate_energy_impact(summary, included_ids)
    interactive_savings = sim_package.total_purchased_energy_savings_kwh
    discount = round(naive_sum - interactive_savings, 1)

    explanation = (
        f"Interaction Accounting: Naive sum of individual savings is {naive_sum:,.0f} kWh/yr. "
        f"When simulated sequentially, the actual net purchased energy reduction is {interactive_savings:,.0f} kWh/yr "
        f"({discount:,.0f} kWh interaction overlap accounted for). "
        "Insulation and glazing reduce space heating load before heat pump sizing; heat pump increases electricity consumption while eliminating gas."
    )

    return RetrofitPackage(
        package_name="Complete Recommended Retrofit Package",
        included_retrofit_ids=included_ids,
        total_estimated_cost_gbp_avg=round(total_cost_avg, 0),
        total_estimated_cost_range=f"£{total_cost_min:,.0f} – £{total_cost_max:,.0f}",
        standalone_sum_savings_kwh=round(naive_sum, 1),
        interaction_aware_savings_kwh=round(interactive_savings, 1),
        interaction_discount_kwh=round(discount, 1),
        interaction_explanation=explanation,
    )
