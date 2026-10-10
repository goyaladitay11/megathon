"""
Green Home Score Pydantic Schemas
Step 3: Documented 7-Component Explainable Scoring
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


ClassificationEnum = Literal["Highly efficient", "Good", "Moderate", "Poor", "Very poor"]


class ComponentScore(BaseModel):
    component_name: str = Field(..., description="Name of the evaluated aspect")
    raw_sub_score: float = Field(..., ge=0.0, le=100.0, description="Raw sub-score out of 100")
    weight: float = Field(..., ge=0.0, le=1.0, description="Component weight fraction (sum=1.00)")
    contribution: float = Field(..., ge=0.0, le=100.0, description="Weighted contribution to total score (weight * sub_score)")
    input_value: str = Field(..., description="Observed input value or metric used")
    explanation: str = Field(..., description="Clear explanation of the sub-score determination")


class GreenHomeScoreResult(BaseModel):
    property_id: str
    final_score: int = Field(..., ge=0, le=100, description="Rounded integer Green Home Score (0-100)")
    exact_score: float = Field(..., ge=0.0, le=100.0, description="Exact unrounded weighted score")
    classification: ClassificationEnum = Field(..., description="Performance band classification")
    is_poor_performing: bool = Field(..., description="True if classification is 'Poor' or 'Very poor'")
    components: List[ComponentScore] = Field(..., description="Breakdown of all 7 components")
    methodology_summary: str = Field(..., description="Documented scoring formulation reference")
