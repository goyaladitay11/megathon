"""
Retrofit Recommendation Schemas
Step 4 & 5: Prioritised Feasible Retrofits and Packages
"""

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


SuitabilityEnum = Literal["High", "Medium", "Low"]


class RetrofitRecommendation(BaseModel):
    retrofit_id: str = Field(..., description="Unique retrofit identifier from catalogue")
    name: str = Field(..., description="Human-readable retrofit title")
    category: str = Field(..., description="Category (Insulation, Heating, Glazing, Renewables, Controls)")
    suitability: SuitabilityEnum = Field(..., description="Suitability rating based on current property state")
    is_feasible: bool = Field(True, description="Whether this retrofit is technically feasible for the property")
    priority_order: int = Field(..., description="Recommended sequence order (e.g. insulation before heat pump)")
    estimated_annual_energy_savings_kwh: float = Field(..., description="Estimated net reduction in purchased kWh/yr")
    estimated_annual_electricity_delta_kwh: float = Field(..., description="Change in electricity (positive = saving, negative = increase)")
    estimated_annual_gas_delta_kwh: float = Field(..., description="Change in gas (positive = saving)")
    estimated_cost_gbp_min: float = Field(..., description="Lower indicative installation cost (£)")
    estimated_cost_gbp_max: float = Field(..., description="Upper indicative installation cost (£)")
    estimated_cost_gbp_avg: float = Field(..., description="Average indicative installation cost (£)")
    reason: str = Field(..., description="Detailed rationale for suitability rating and recommendation")
    dependencies_or_notes: Optional[str] = Field(None, description="Sequencing notes or prerequisites")


class RetrofitPackage(BaseModel):
    package_name: str = Field(default="Complete Recommended Retrofit Package")
    included_retrofit_ids: List[str]
    total_estimated_cost_gbp_avg: float
    total_estimated_cost_range: str
    standalone_sum_savings_kwh: float = Field(..., description="Naive sum of individual savings (illustrative only)")
    interaction_aware_savings_kwh: float = Field(..., description="True interaction-aware package savings")
    interaction_discount_kwh: float = Field(..., description="Difference showing interaction effect accounted for")
    interaction_explanation: str
