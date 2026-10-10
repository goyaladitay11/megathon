"""
API Unified Response Schemas
FastAPI OpenAPI Response Contracts
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.property import PropertySummary, PropertyInput
from backend.app.schemas.scoring import GreenHomeScoreResult
from backend.app.schemas.retrofit import RetrofitRecommendation, RetrofitPackage
from backend.app.schemas.simulation import EnergySimulationResult
from backend.app.schemas.carbon import CarbonSavingsResult
from backend.app.schemas.valuation import PropertyValuationResult
from backend.app.schemas.chat import GroundedExplanationPayload


class AnalysisResponse(BaseModel):
    property: PropertySummary
    score_details: GreenHomeScoreResult
    key_issue_flags: List[str] = Field(..., description="Concrete improvement issues based on measured features")
    feasible_retrofits: List[RetrofitRecommendation] = Field(..., description="Prioritised list of feasible retrofits")
    recommended_package: RetrofitPackage = Field(..., description="Complete recommended retrofit package with interactions accounted for")
    energy_simulation: EnergySimulationResult = Field(..., description="Baseline and post-package energy by fuel")
    carbon_impact: CarbonSavingsResult = Field(..., description="Carbon savings and fuel breakdown")
    valuation_impact: PropertyValuationResult = Field(..., description="Indicative property value uplift range")
    grounded_explanation: GroundedExplanationPayload = Field(..., description="Grounded natural language insights")
    data_quality_warnings: List[str] = Field(default_factory=list, description="Data anomalies or coverage warnings")
    assumptions_summary: List[str] = Field(..., description="Transparent technical and economic assumptions")


class RecommendationResponse(BaseModel):
    property_id: str
    is_poor_performing: bool
    improvement_potential_percent: Optional[float]
    feasible_retrofits: List[RetrofitRecommendation]
    recommended_package: RetrofitPackage


class SimulationResponse(BaseModel):
    property_id: Optional[str]
    applied_retrofit_ids: List[str]
    energy: EnergySimulationResult
    carbon: CarbonSavingsResult
    valuation: PropertyValuationResult


class LeaderboardItem(BaseModel):
    rank: int
    property_id: str
    customer_id: Optional[str]
    region: str
    property_type: str
    floor_area_m2: float
    current_score: int
    classification: str
    baseline_purchased_kwh: float
    post_retrofit_purchased_kwh: float
    improvement_potential_percent: Optional[float]
    net_carbon_savings_tonnes: float
    estimated_investment_gbp: float
    is_poor_performing: bool


class LeaderboardResponse(BaseModel):
    total_properties: int
    page: int
    page_size: int
    items: List[LeaderboardItem]


class ModelMetricDetail(BaseModel):
    metric_name: str
    value: float
    description: str


class ModelMetricsResponse(BaseModel):
    model_name: str
    version: str
    trained_at: str
    train_samples: int
    validation_samples: int
    test_samples: int
    evaluation_metrics: Dict[str, float]
    baseline_comparison: Dict[str, Any]
    feature_importances: Dict[str, float]
    limitations: List[str]
