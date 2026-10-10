"""
Energy Simulation Pydantic Schemas
Step 6: Interaction-Aware Energy Simulator with Fuel Disaggregation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EnergySimulationResult(BaseModel):
    # Baseline fuel consumption
    baseline_electricity_kwh: float = Field(..., description="Annual baseline grid electricity imports (kWh/yr)")
    baseline_gas_kwh: float = Field(..., description="Annual baseline gas consumption (kWh/yr)")
    baseline_purchased_kwh: float = Field(..., description="Total baseline purchased energy (elec + gas) (kWh/yr)")

    # Post-retrofit fuel consumption
    after_electricity_kwh: float = Field(..., description="Annual post-retrofit grid electricity imports (kWh/yr)")
    after_gas_kwh: float = Field(..., description="Annual post-retrofit gas consumption (kWh/yr)")
    after_purchased_kwh: float = Field(..., description="Total post-retrofit purchased energy (kWh/yr)")

    # Deltas and savings (Positive = saving; Negative = increased consumption, e.g. heat pump)
    electricity_savings_kwh: float = Field(..., description="Annual electricity saved (can be negative with heat pump)")
    gas_savings_kwh: float = Field(..., description="Annual gas saved (kWh/yr)")
    total_purchased_energy_savings_kwh: float = Field(..., description="Net annual purchased energy savings (kWh/yr)")

    # Improvement potential percentage: 100 * (E_baseline - E_after) / E_baseline
    improvement_potential_percent: Optional[float] = Field(None, description="Achievable percentage reduction in annual purchased energy")
    is_improvement_potential_available: bool = Field(True, description="False if baseline is zero or unavailable")
    unavailable_reason: Optional[str] = Field(None, description="Explanation if metric is unavailable")

    # Space heating breakdown
    baseline_space_heating_kwh: float = Field(..., description="Estimated baseline space heating portion (kWh/yr)")
    after_space_heating_kwh: float = Field(..., description="Estimated post-retrofit space heating load (kWh/yr)")
    solar_generation_curtailed_kwh: float = Field(0.0, description="Solar energy generation exceeding household demand if floored")

    # Simulation metadata
    applied_retrofit_ids: List[str] = Field(default_factory=list, description="IDs of retrofits simulated")
    simulation_method: str = Field(default="Interaction-Aware Thermal & Fuel Disaggregation Simulator v1.0")
    disclaimer: str = Field(default="All savings are modelled estimates, not guaranteed outcomes. Actual consumption depends on occupant behaviour and weather.")


class SimulateRequest(BaseModel):
    property_id: Optional[str] = Field(None, example="P10001", description="ID of existing property")
    property_input: Optional[Any] = Field(None, description="Optional full inline property input object")
    selected_retrofit_ids: List[str] = Field(..., example=["roof_insulation", "heat_pump"], description="List of retrofit IDs to evaluate")
    property_override: Optional[Dict[str, Any]] = Field(None, description="Optional override of property attributes for what-if scenarios")
