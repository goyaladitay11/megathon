"""
Chat & What-If Grounded Explanation Schemas
Step 9: Grounded LLM Explanation Layer & Scenario Validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.simulation import EnergySimulationResult
from backend.app.schemas.carbon import CarbonSavingsResult
from backend.app.schemas.valuation import PropertyValuationResult


class ChatRequest(BaseModel):
    property_id: Optional[str] = Field("P10001", description="ID of property being evaluated")
    query: str = Field(..., example="What if I install a heat pump and solar panels?", description="Customer natural language question or what-if scenario")
    selected_retrofit_ids: Optional[List[str]] = Field(None, description="Explicit list of retrofits if triggered via UI buttons")


class GroundedExplanationPayload(BaseModel):
    summary: str = Field(..., description="Concise executive summary of current performance and recommendations")
    reasons: List[str] = Field(..., description="Explicit reasons for recommendations based on measured property data")
    tradeoffs: List[str] = Field(..., description="Real tradeoffs (e.g. upfront cost, heat pump electricity consumption rise)")
    limitations: List[str] = Field(..., description="Disclaimers regarding data coverage, weather, and occupant behavior")


class ChatResponse(BaseModel):
    property_id: str
    scenario_recognized: str = Field(..., description="Summary of parsed what-if scenario")
    parsed_retrofit_ids: List[str] = Field(default_factory=list, description="Validated retrofit IDs applied to rerun")
    unsupported_requested_items: List[str] = Field(default_factory=list, description="Requested retrofits that were rejected as invalid/infeasible")
    explanation: GroundedExplanationPayload
    simulated_energy: Optional[EnergySimulationResult] = None
    simulated_carbon: Optional[CarbonSavingsResult] = None
    simulated_valuation: Optional[PropertyValuationResult] = None
    grounding_verified: bool = Field(True, description="Strict validation that numerical outputs originate solely from deterministic engines")
    engine_used: str = Field("Gemini 1.5 Flash (Grounded)" if True else "Deterministic Template Grounder", description="LLM provider or deterministic fallback")
