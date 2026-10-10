"""
Deterministic Carbon Engine
Lloyds Megathon X PS2 (Section 6 & Phase 9)

Formula:
Delta C = Delta E_elec * EF_elec + Delta E_gas * EF_gas
where Delta E_f = E_f,baseline - E_f,after (positive = saving, negative = increase)

Official Emissions Factors (UK Government GHG Conversion Factors for Company Reporting 2024):
- Grid Electricity (Scope 2): 0.20707 kg CO2e/kWh
- Natural Gas Mains (Scope 1): 0.18254 kg CO2e/kWh
"""

from typing import Dict, Any, Optional
from backend.src.schemas import CarbonResult, EnergyResult

DEFAULT_EF_ELECTRICITY = 0.20707
DEFAULT_EF_GAS = 0.18254
FACTOR_SOURCE = "UK Government GHG Conversion Factors for Company Reporting 2024 (DESNZ / DEFRA)"
FACTOR_YEAR = 2024


def calculate_carbon(
    baseline_energy: Dict[str, float],
    scenario_energy: Dict[str, float],
    emissions_factors: Optional[Dict[str, float]] = None,
) -> CarbonResult:
    """
    Computes per-fuel and net greenhouse gas emissions reductions.
    Handles fuel switching where electricity increases while gas decreases.
    """
    ef_elec = (
        emissions_factors.get("electricity", DEFAULT_EF_ELECTRICITY)
        if emissions_factors
        else DEFAULT_EF_ELECTRICITY
    )
    ef_gas = (
        emissions_factors.get("gas", DEFAULT_EF_GAS)
        if emissions_factors
        else DEFAULT_EF_GAS
    )

    base_elec = baseline_energy.get("electricity_kwh", 0.0)
    base_gas = baseline_energy.get("gas_kwh", 0.0)
    after_elec = scenario_energy.get("electricity_kwh", 0.0)
    after_gas = scenario_energy.get("gas_kwh", 0.0)

    delta_elec = base_elec - after_elec
    delta_gas = base_gas - after_gas

    elec_carbon_kg = delta_elec * ef_elec
    gas_carbon_kg = delta_gas * ef_gas
    net_carbon_kg = elec_carbon_kg + gas_carbon_kg
    net_carbon_tonnes = net_carbon_kg / 1000.0

    return CarbonResult(
        electricity_delta_kwh=round(delta_elec, 1),
        gas_delta_kwh=round(delta_gas, 1),
        electricity_factor_kg_kwh=round(ef_elec, 5),
        gas_factor_kg_kwh=round(ef_gas, 5),
        electricity_carbon_saving_kg=round(elec_carbon_kg, 1),
        gas_carbon_saving_kg=round(gas_carbon_kg, 1),
        net_carbon_reduction_kg=round(net_carbon_kg, 1),
        net_carbon_reduction_tonnes=round(net_carbon_tonnes, 2),
        factor_year=FACTOR_YEAR,
        factor_source=FACTOR_SOURCE,
        per_fuel_breakdown={
            "electricity_carbon_delta_kg": round(elec_carbon_kg, 1),
            "gas_carbon_delta_kg": round(gas_carbon_kg, 1),
        },
    )
