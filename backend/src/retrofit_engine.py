"""
Retrofit Recommendation & Sequential Physical Interaction Simulator
Lloyds Megathon X PS2 (Section 4, 5 & Phases 6, 7, 8)
"""

from typing import List, Dict, Tuple, Optional, Any
from backend.src.schemas import (
    PropertyData,
    RetrofitRecommendationItem,
    EnergyResult,
    SuitabilityType,
)

# Documented Retrofit Catalogue Specifications
RETROFIT_SPECS = {
    "roof_insulation": {
        "name": "Roof or Loft Insulation (270mm+)",
        "category": "Insulation",
        "space_heating_reduction_pct": 0.15,  # 12-18% reduction (midpoint 15%)
        "cost_min": 600.0,
        "cost_max": 1200.0,
        "cost_avg": 900.0,
        "priority": 1,
        "notes": "Fabric first: Reduces space heating load by 12-18% before heating system sizing.",
    },
    "double_glazing": {
        "name": "High-Performance Double Glazing",
        "category": "Glazing",
        "space_heating_reduction_pct": 0.10,  # 8-12% reduction (midpoint 10%)
        "cost_min": 3500.0,
        "cost_max": 7500.0,
        "cost_avg": 5500.0,
        "priority": 2,
        "notes": "Reduces conductive window heat loss and draughts by 8-12%.",
    },
    "smart_thermostat": {
        "name": "Smart Thermostat & Heating Controls",
        "category": "Smart Controls",
        "space_heating_reduction_pct": 0.075,  # 5-10% reduction (midpoint 7.5%)
        "cost_min": 200.0,
        "cost_max": 350.0,
        "cost_avg": 250.0,
        "priority": 3,
        "notes": "Low-cost high-impact control optimization reducing space heating demand by 5-10%.",
    },
    "heat_pump": {
        "name": "Air Source Heat Pump (ASHP)",
        "category": "Heating",
        "space_heating_reduction_pct": 0.0,
        "heat_pump_cop": 3.0,  # Seasonal Performance Factor ~3.0
        "cost_min": 8000.0,
        "cost_max": 14000.0,
        "cost_avg": 10500.0,
        "priority": 4,
        "notes": "Replaces fossil combustion with SPF 3.0 electric heat pump. Eliminates gas, increases electricity.",
    },
    "solar_pv": {
        "name": "Rooftop Solar PV Array (3.5 - 4.0 kWp)",
        "category": "Renewables",
        "space_heating_reduction_pct": 0.0,
        "grid_import_reduction_pct": 0.28,  # 20-35% grid import reduction (midpoint 28%)
        "cost_min": 5000.0,
        "cost_max": 8500.0,
        "cost_avg": 6500.0,
        "priority": 5,
        "notes": "Generates on-site renewable electricity, offsetting 20-35% of purchased grid imports.",
    },
}


def check_feasibility_and_suitability(
    prop: PropertyData,
    retrofit_id: str,
) -> Tuple[bool, SuitabilityType, str, Optional[str]]:
    """Evaluates feasibility, suitability, and engineering dependencies."""
    if retrofit_id == "roof_insulation":
        if prop.insulation_type == "good":
            return False, "Low", "Property already has modern loft/roof insulation (>=270mm).", None
        elif prop.insulation_type == "poor":
            return True, "High", "Critical priority: Uninsulated roof accounts for up to 25% of heat loss.", "Priority 1 (Fabric first)"
        else:
            return True, "Medium", "Top-up insulation to modern building standards (270mm+).", "Priority 1"

    elif retrofit_id == "double_glazing":
        if prop.glazing_type in ["double", "triple"]:
            return False, "Low", f"Property already features {prop.glazing_type} glazing.", None
        return True, "High", "Single glazing creates severe thermal bridging and condensation.", "Priority 2"

    elif retrofit_id == "smart_thermostat":
        if prop.smart_controls:
            return False, "Low", "Smart heating controls already installed.", None
        return True, "High", "Rapid payback operational control avoiding unnecessary heating.", "Priority 3"

    elif retrofit_id == "heat_pump":
        if prop.heating_system == "heat_pump":
            return False, "Low", "Low-carbon heat pump already operational.", None
        if prop.insulation_type == "poor":
            return (
                True,
                "Medium",
                "High carbon saving, but poor insulation will oversize the heat pump. Upgrade roof insulation first.",
                "Condition: Insulate roof first (Fabric first principle)",
            )
        return True, "High", "Displaces fossil fuel heating with SPF 3.0 electric heat pump.", "Priority 4"

    elif retrofit_id == "solar_pv":
        if prop.solar_installed == "4kw":
            return False, "Low", "Maximum standard domestic rooftop solar (4kW) already installed.", None
        elif prop.solar_installed == "2kw":
            return True, "Medium", "Expand existing 2kW array to full 4kW system.", "Priority 5"
        return True, "High", "Generates clean electricity offsetting grid imports.", "Priority 5"

    return False, "Low", "Unknown retrofit", None


def simulate_retrofit(
    prop: PropertyData,
    selected_retrofits: List[str],
) -> EnergyResult:
    """
    Reruns sequential physical simulation accounting for all thermal and fuel interactions:
    1. Separate electricity and gas baselines.
    2. Disaggregate space heating, water heating, and appliance baseload.
    3. Apply insulation, glazing, and controls sequentially to space heating demand.
    4. Model heat pump fuel switching (eliminates heating gas, increases electricity with SPF 3.0).
    5. Model solar PV as grid import reduction (floored at zero, does not alter home demand).
    6. Increase in consumption is negative saving.
    """
    base_elec = float(prop.annual_electricity_kwh if prop.annual_electricity_kwh is not None else 3500.0)
    base_gas = float(prop.annual_gas_kwh if prop.annual_gas_kwh is not None else 12000.0)
    base_purchased = base_elec + base_gas

    # Disaggregate heating vs hot water vs electricity baseload
    boiler_eff = 0.85
    if prop.heating_system in ["gas_boiler", "oil_boiler"]:
        base_space_gas = base_gas * 0.82
        base_water_gas = base_gas * 0.18
        delivered_space_heat = base_space_gas * boiler_eff
        delivered_water_heat = base_water_gas * boiler_eff
        base_elec_baseload = base_elec
    elif prop.heating_system == "electric_resistive":
        base_space_gas = 0.0
        base_water_gas = 0.0
        delivered_space_heat = base_elec * 0.60
        delivered_water_heat = base_elec * 0.15
        base_elec_baseload = base_elec * 0.25
    else:  # already heat pump
        base_space_gas = 0.0
        base_water_gas = 0.0
        delivered_space_heat = (base_elec * 0.50) * 3.0
        delivered_water_heat = (base_elec * 0.15) * 3.0
        base_elec_baseload = base_elec * 0.35

    curr_space_heat = delivered_space_heat

    # Step 1: Roof / Loft Insulation (15% reduction)
    if "roof_insulation" in selected_retrofits and prop.insulation_type != "good":
        curr_space_heat *= (1.0 - RETROFIT_SPECS["roof_insulation"]["space_heating_reduction_pct"])

    # Step 2: Double Glazing (10% reduction on remaining space heat)
    if "double_glazing" in selected_retrofits and prop.glazing_type == "single":
        curr_space_heat *= (1.0 - RETROFIT_SPECS["double_glazing"]["space_heating_reduction_pct"])

    # Step 3: Smart Thermostat (7.5% reduction on remaining heating)
    if "smart_thermostat" in selected_retrofits and not prop.smart_controls:
        curr_space_heat *= (1.0 - RETROFIT_SPECS["smart_thermostat"]["space_heating_reduction_pct"])

    # Step 4: Heating System Fuel Switching (Heat Pump vs Boiler)
    if "heat_pump" in selected_retrofits and prop.heating_system != "heat_pump":
        after_gas = 0.0  # Gas eliminated
        hp_total_delivered = curr_space_heat + delivered_water_heat
        hp_elec_kwh = hp_total_delivered / 3.0  # SPF 3.0

        if prop.heating_system in ["gas_boiler", "oil_boiler"]:
            after_elec = base_elec_baseload + hp_elec_kwh
        else:
            after_elec = base_elec_baseload + hp_elec_kwh
    else:
        if prop.heating_system in ["gas_boiler", "oil_boiler"]:
            after_space_gas = curr_space_heat / boiler_eff
            after_gas = after_space_gas + base_water_gas
            after_elec = base_elec
        elif prop.heating_system == "electric_resistive":
            after_gas = 0.0
            after_elec = base_elec_baseload + curr_space_heat + delivered_water_heat
        else:
            after_gas = 0.0
            after_elec = base_elec_baseload + (curr_space_heat + delivered_water_heat) / 3.0

    # Step 5: Solar PV (reduces purchased grid imports, floored at 0)
    curtailed_solar = 0.0
    if "solar_pv" in selected_retrofits and prop.solar_installed != "4kw":
        solar_factor = RETROFIT_SPECS["solar_pv"]["grid_import_reduction_pct"]
        solar_gen_offset = after_elec * solar_factor
        if after_elec - solar_gen_offset < 0.0:
            curtailed_solar = solar_gen_offset - after_elec
            after_elec = 0.0
        else:
            after_elec -= solar_gen_offset

    elec_savings = base_elec - after_elec
    gas_savings = base_gas - after_gas
    after_purchased = after_elec + after_gas
    net_savings = base_purchased - after_purchased

    # Improvement potential: 100 * (E_baseline - E_after) / E_baseline
    if base_purchased > 0:
        imp_pot = round((net_savings / base_purchased) * 100.0, 2)
        is_avail = True
        unavail_reason = None
    else:
        imp_pot = None
        is_avail = False
        unavail_reason = "Baseline purchased energy is zero or invalid."

    return EnergyResult(
        baseline_electricity_kwh=round(base_elec, 1),
        baseline_gas_kwh=round(base_gas, 1),
        baseline_purchased_kwh=round(base_purchased, 1),
        after_electricity_kwh=round(after_elec, 1),
        after_gas_kwh=round(after_gas, 1),
        after_purchased_kwh=round(after_purchased, 1),
        electricity_saving_kwh=round(elec_savings, 1),
        gas_saving_kwh=round(gas_savings, 1),
        net_purchased_energy_saving_kwh=round(net_savings, 1),
        improvement_potential_pct=imp_pot,
        is_improvement_potential_available=is_avail,
        unavailable_reason=unavail_reason,
        baseline_space_heating_kwh=round(delivered_space_heat, 1),
        after_space_heating_kwh=round(curr_space_heat, 1),
        solar_generation_curtailed_kwh=round(curtailed_solar, 1),
        applied_retrofits=selected_retrofits,
    )


def recommend_retrofits(prop: PropertyData) -> List[RetrofitRecommendationItem]:
    """
    Evaluates feasibility and returns prioritized list of feasible retrofits.
    Calculates standalone savings for each retrofit individually.
    """
    recs: List[RetrofitRecommendationItem] = []
    ordered = ["roof_insulation", "double_glazing", "smart_thermostat", "heat_pump", "solar_pv"]

    for r_id in ordered:
        feasible, suit, reason, notes = check_feasibility_and_suitability(prop, r_id)
        if not feasible:
            continue

        item = RETROFIT_SPECS[r_id]
        standalone_sim = simulate_retrofit(prop, [r_id])

        recs.append(
            RetrofitRecommendationItem(
                retrofit_id=r_id,
                name=item["name"],
                category=item["category"],
                feasibility=True,
                suitability=suit,
                priority_order=item["priority"],
                standalone_electricity_saving_kwh=standalone_sim.electricity_saving_kwh,
                standalone_gas_saving_kwh=standalone_sim.gas_saving_kwh,
                standalone_net_energy_saving_kwh=standalone_sim.net_purchased_energy_saving_kwh,
                estimated_cost_gbp_min=item["cost_min"],
                estimated_cost_gbp_max=item["cost_max"],
                estimated_cost_gbp_avg=item["cost_avg"],
                reason=reason,
                prerequisites_note=notes,
            )
        )

    return recs
