"""
Deterministic Carbon Reduction Engine
Step 7: Per-fuel UK Emissions Factor Calculations
Documented according to Lloyds Megathon X Problem Statement 2 (Section 6)
"""

from typing import Dict, Any
from backend.app.core.config import settings
from backend.app.schemas.carbon import CarbonSavingsResult
from backend.app.schemas.simulation import EnergySimulationResult


def calculate_carbon_reduction(
    simulation: EnergySimulationResult,
    custom_elec_factor: float = None,
    custom_gas_factor: float = None,
) -> CarbonSavingsResult:
    """
    Computes per-fuel emissions reduction using UK DESNZ / DEFRA GHG Conversion Factors:
    Delta C = Delta E_elec * EF_elec + Delta E_gas * EF_gas
    
    Crucial per-fuel behaviour:
    When a heat pump is installed, Delta E_elec is negative (electricity increases),
    producing negative electricity carbon savings, while Delta E_gas is positive
    (gas eliminated), producing net positive carbon reduction.
    """
    ef_elec = custom_elec_factor if custom_elec_factor is not None else settings.ELECTRICITY_EMISSION_FACTOR_KG
    ef_gas = custom_gas_factor if custom_gas_factor is not None else settings.GAS_EMISSION_FACTOR_KG

    delta_elec = simulation.electricity_savings_kwh  # baseline_elec - after_elec
    delta_gas = simulation.gas_savings_kwh          # baseline_gas - after_gas

    elec_carbon_kg = delta_elec * ef_elec
    gas_carbon_kg = delta_gas * ef_gas
    net_carbon_kg = elec_carbon_kg + gas_carbon_kg
    net_carbon_tonnes = net_carbon_kg / 1000.0

    return CarbonSavingsResult(
        delta_electricity_kwh=round(delta_elec, 1),
        delta_gas_kwh=round(delta_gas, 1),
        electricity_factor_kg_kwh=round(ef_elec, 5),
        gas_factor_kg_kwh=round(ef_gas, 5),
        electricity_carbon_saving_kg=round(elec_carbon_kg, 1),
        gas_carbon_saving_kg=round(gas_carbon_kg, 1),
        net_carbon_saving_kg=round(net_carbon_kg, 1),
        net_carbon_saving_tonnes=round(net_carbon_tonnes, 2),
        factor_year=settings.EMISSION_FACTORS_YEAR,
        factor_source=settings.EMISSION_FACTORS_SOURCE,
        disclaimer=(
            "Calculated in accordance with UK DESNZ / DEFRA 2024 emissions factors. "
            "Per-fuel accounting accounts for electricity import changes vs gas combustion elimination."
        ),
    )
