"""
Carbon Emission Pydantic Schemas
Step 7: Per-fuel UK Emissions Factor Calculations
"""

from typing import Optional
from pydantic import BaseModel, Field


class CarbonSavingsResult(BaseModel):
    delta_electricity_kwh: float = Field(..., description="Electricity consumption reduction (kWh/yr, negative if increased)")
    delta_gas_kwh: float = Field(..., description="Gas consumption reduction (kWh/yr)")
    electricity_factor_kg_kwh: float = Field(..., description="Grid electricity emissions factor (kg CO2e/kWh)")
    gas_factor_kg_kwh: float = Field(..., description="Natural gas emissions factor (kg CO2e/kWh)")
    electricity_carbon_saving_kg: float = Field(..., description="Carbon delta from electricity (kg CO2e/yr, negative if heat pump draws more grid power)")
    gas_carbon_saving_kg: float = Field(..., description="Carbon delta from gas displaced (kg CO2e/yr)")
    net_carbon_saving_kg: float = Field(..., description="Total net emissions reduction (kg CO2e/yr)")
    net_carbon_saving_tonnes: float = Field(..., description="Total net emissions reduction in metric tonnes (t CO2e/yr)")
    factor_year: int = Field(2024, description="Year of published DEFRA / DESNZ emissions factors")
    factor_source: str = Field(..., description="Official government reference document")
    disclaimer: str = Field(default="Estimates reflect UK grid average intensity (Scope 2) and natural gas combustion (Scope 1).")
