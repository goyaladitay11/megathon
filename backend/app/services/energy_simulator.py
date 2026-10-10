"""
Interaction-Aware Energy Simulation Engine
Step 6: Separate Electricity & Gas Baselines, Thermal Disaggregation, and Sequential Interactions
"""

from typing import List, Dict, Tuple, Optional, Any
from backend.app.schemas.property import PropertySummary
from backend.app.schemas.simulation import EnergySimulationResult
from backend.app.models.catalogue import RETROFIT_CATALOGUE, RetrofitItem
from backend.app.services.poor_home_detector import calculate_improvement_potential_metric


def simulate_energy_impact(
    summary: PropertySummary,
    selected_retrofit_ids: List[str],
) -> EnergySimulationResult:
    """
    Simulates energy impact with rigorous physical fuel disaggregation:
    1. Separates electricity and gas baselines.
    2. Disaggregates space heating from baseload and domestic hot water.
    3. Sequentially applies insulation, glazing, and smart controls to space heating load.
    4. Models heat pump fuel switching: completely eliminates heating gas, increases electric input with SPF 3.0.
    5. Models solar PV as reduction in grid imports, floored at zero.
    6. Ensures rerun of whole package with interactions, never naive summation.
    """
    base_elec = float(summary.annual_electricity_kwh)
    base_gas = float(summary.annual_gas_kwh)
    base_purchased = base_elec + base_gas

    # Disaggregate gas consumption into space heating and hot water
    # In UK homes with gas boilers, ~82% of gas is space heating, ~18% is hot water
    gas_boiler_efficiency = 0.85
    if summary.heating in ["gas_boiler", "oil_boiler"]:
        base_space_gas = base_gas * 0.82
        base_hot_water_gas = base_gas * 0.18
        delivered_space_heat = base_space_gas * gas_boiler_efficiency
        delivered_hot_water = base_hot_water_gas * gas_boiler_efficiency
    elif summary.heating == "electric_resistive":
        # Space heating is drawn from electricity
        base_space_gas = 0.0
        base_hot_water_gas = 0.0
        # Estimate space heat portion of electricity (~60% of total electric)
        delivered_space_heat = base_elec * 0.60
        delivered_hot_water = base_elec * 0.15
        base_elec_non_heating = base_elec * 0.25
    else:  # already heat pump
        base_space_gas = 0.0
        base_hot_water_gas = 0.0
        delivered_space_heat = (base_elec * 0.50) * 3.0
        delivered_hot_water = (base_elec * 0.15) * 3.0
        base_elec_non_heating = base_elec * 0.35

    current_space_heat = delivered_space_heat
    curtailed_solar = 0.0

    # Sequential thermal fabric improvements on remaining space heating load
    # Step 1: Roof / Loft Insulation (15% reduction)
    if "roof_insulation" in selected_retrofit_ids and summary.insulation != "good":
        reduction = RETROFIT_CATALOGUE["roof_insulation"].space_heating_reduction_pct
        current_space_heat *= (1.0 - reduction)

    # Step 2: Double Glazing (10% reduction on remaining space heat)
    if "double_glazing" in selected_retrofit_ids and summary.glazing == "single":
        reduction = RETROFIT_CATALOGUE["double_glazing"].space_heating_reduction_pct
        current_space_heat *= (1.0 - reduction)

    # Step 3: Smart Thermostat (7.5% reduction on remaining heating)
    if "smart_thermostat" in selected_retrofit_ids and not summary.smart_controls:
        reduction = RETROFIT_CATALOGUE["smart_thermostat"].space_heating_reduction_pct
        current_space_heat *= (1.0 - reduction)

    # Heating system transformation: Heat Pump vs Gas/Oil Boiler
    if "heat_pump" in selected_retrofit_ids and summary.heating != "heat_pump":
        # Full gas displacement for space & water heating!
        after_gas = 0.0
        # Heat pump provides remaining space heat + hot water with COP = 3.0
        total_delivered_heat = current_space_heat + delivered_hot_water
        hp_cop = RETROFIT_CATALOGUE["heat_pump"].heat_pump_cop
        hp_electricity_kwh = total_delivered_heat / hp_cop

        if summary.heating in ["gas_boiler", "oil_boiler"]:
            # Baseline electricity was appliances/lights; now adds heat pump power
            after_elec = base_elec + hp_electricity_kwh
        else:
            # Replaced resistive electric
            after_elec = base_elec_non_heating + hp_electricity_kwh
    else:
        # Boiler retained: space heating gas scales with remaining load
        if summary.heating in ["gas_boiler", "oil_boiler"]:
            after_space_gas = current_space_heat / gas_boiler_efficiency
            after_gas = after_space_gas + base_hot_water_gas
            after_elec = base_elec
        elif summary.heating == "electric_resistive":
            after_gas = 0.0
            after_elec = base_elec_non_heating + current_space_heat + delivered_hot_water
        else:
            after_gas = 0.0
            after_elec = base_elec_non_heating + (current_space_heat + delivered_hot_water) / 3.0

    # Solar PV generation: reduces purchased grid electricity imports, floored at 0
    if "solar_pv" in selected_retrofit_ids and summary.solar != "4kw":
        solar_factor = RETROFIT_CATALOGUE["solar_pv"].grid_import_reduction_pct
        raw_solar_offset = after_elec * solar_factor
        
        # Floor grid imports at 0.0
        if after_elec - raw_solar_offset < 0.0:
            curtailed_solar = raw_solar_offset - after_elec
            after_elec = 0.0
        else:
            after_elec = after_elec - raw_solar_offset

    # Calculate exact savings (positive = reduction; negative = increase)
    elec_savings = base_elec - after_elec
    gas_savings = base_gas - after_gas
    after_purchased = after_elec + after_gas
    total_purchased_savings = base_purchased - after_purchased

    # Improvement potential percentage
    improvement_pct, is_avail, reason = calculate_improvement_potential_metric(
        base_purchased,
        after_purchased,
    )

    return EnergySimulationResult(
        baseline_electricity_kwh=round(base_elec, 1),
        baseline_gas_kwh=round(base_gas, 1),
        baseline_purchased_kwh=round(base_purchased, 1),
        after_electricity_kwh=round(after_elec, 1),
        after_gas_kwh=round(after_gas, 1),
        after_purchased_kwh=round(after_purchased, 1),
        electricity_savings_kwh=round(elec_savings, 1),
        gas_savings_kwh=round(gas_savings, 1),
        total_purchased_energy_savings_kwh=round(total_purchased_savings, 1),
        improvement_potential_percent=improvement_pct,
        is_improvement_potential_available=is_avail,
        unavailable_reason=reason,
        baseline_space_heating_kwh=round(delivered_space_heat, 1),
        after_space_heating_kwh=round(current_space_heat, 1),
        solar_generation_curtailed_kwh=round(curtailed_solar, 1),
        applied_retrofit_ids=selected_retrofit_ids,
        simulation_method="Interaction-Aware Thermal & Fuel Disaggregation Simulator v1.0",
        disclaimer="All savings are modelled estimates, not guarantees. Actual energy use depends on occupancy, comfort setpoints, and seasonal climate variation.",
    )
