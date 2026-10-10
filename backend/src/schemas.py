"""
Pydantic Schemas for Lloyds Green Home Score & Retrofit Recommendation Pipeline
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field

ClassificationType = Literal["Highly efficient", "Good", "Moderate", "Poor", "Very poor"]
SuitabilityType = Literal["High", "Medium", "Low"]


class PropertyData(BaseModel):
    property_id: str = Field(...)
    customer_id: Optional[str] = Field(None)
    property_type: str = Field(..., description="detached, semi_detached, terraced, flat")
    property_age: int = Field(..., description="Year built")
    floor_area_m2: float = Field(..., ge=10.0, le=1000.0)
    bedrooms: int = Field(3, ge=1, le=15)
    energy_rating: str = Field("D", description="EPC Band A, B, C, D, E, F, G")
    heating_system: str = Field("gas_boiler", description="gas_boiler, heat_pump, electric_resistive, oil_boiler")
    insulation_type: str = Field("average", description="poor, average, good")
    glazing_type: str = Field("double", description="single, double, triple")
    solar_installed: str = Field("none", description="none, 2kw, 4kw")
    smart_controls: bool = Field(False)
    region: str = Field("West Midlands")
    current_property_value: Optional[float] = Field(280000.0)
    annual_electricity_kwh: Optional[float] = Field(None)
    annual_gas_kwh: Optional[float] = Field(None)


class ComponentScoreDetail(BaseModel):
    name: str
    raw_sub_score: float
    weight: float
    contribution: float
    input_value: str
    explanation: str


class ScoreResult(BaseModel):
    property_id: str
    green_home_score: int = Field(..., ge=0, le=100)
    exact_score: float
    classification: ClassificationType
    is_poor_performing: bool
    component_scores: Dict[str, float]
    component_contributions: Dict[str, float]
    component_details: List[ComponentScoreDetail]
    reconciliation_valid: bool
    methodology_version: str = "Lloyds-PS2-7Component-v1.0"


class RetrofitRecommendationItem(BaseModel):
    retrofit_id: str
    name: str
    category: str
    feasibility: bool
    suitability: SuitabilityType
    priority_order: int
    standalone_electricity_saving_kwh: float
    standalone_gas_saving_kwh: float
    standalone_net_energy_saving_kwh: float
    estimated_cost_gbp_min: float
    estimated_cost_gbp_max: float
    estimated_cost_gbp_avg: float
    reason: str
    prerequisites_note: Optional[str] = None


class EnergyResult(BaseModel):
    baseline_electricity_kwh: float
    baseline_gas_kwh: float
    baseline_purchased_kwh: float
    after_electricity_kwh: float
    after_gas_kwh: float
    after_purchased_kwh: float
    electricity_saving_kwh: float
    gas_saving_kwh: float
    net_purchased_energy_saving_kwh: float
    improvement_potential_pct: Optional[float]
    is_improvement_potential_available: bool
    unavailable_reason: Optional[str] = None
    baseline_space_heating_kwh: float
    after_space_heating_kwh: float
    solar_generation_curtailed_kwh: float
    applied_retrofits: List[str]


class CarbonResult(BaseModel):
    electricity_delta_kwh: float
    gas_delta_kwh: float
    electricity_factor_kg_kwh: float
    gas_factor_kg_kwh: float
    electricity_carbon_saving_kg: float
    gas_carbon_saving_kg: float
    net_carbon_reduction_kg: float
    net_carbon_reduction_tonnes: float
    factor_year: int
    factor_source: str
    per_fuel_breakdown: Dict[str, float]


class ValuationRangeResult(BaseModel):
    baseline_value_gbp: Optional[float]
    indicative_uplift_pct_min: Optional[float]
    indicative_uplift_pct_max: Optional[float]
    indicative_value_min_gbp: Optional[float]
    indicative_value_max_gbp: Optional[float]
    range_label: str
    is_available: bool
    unavailable_reason: Optional[str] = None
    methodology: str
    caveat: str


class FullHomeAnalysis(BaseModel):
    property_id: str
    green_home_score: int
    classification: ClassificationType
    is_poor_performing: bool
    component_scores: Dict[str, float]
    component_contributions: Dict[str, float]
    improvement_potential_pct: Optional[float]
    recommended_retrofits: List[RetrofitRecommendationItem]
    package_applied_retrofits: List[str]
    baseline: Dict[str, float]
    scenario: Dict[str, float]
    estimated_energy_saving_kwh: float
    estimated_carbon_reduction_kg: float
    estimated_carbon_reduction_tonnes: float
    property_value_impact_range: Dict[str, Any]
    assumptions: List[str]
    warnings: List[str]
    model_version: str = "Lloyds-PS2-Pipeline-v1.0"
