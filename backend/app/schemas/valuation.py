"""
Property Valuation Pydantic Schemas
Step 8: Indicative Property Value Uplift Range Model
"""

from typing import Optional
from pydantic import BaseModel, Field


class PropertyValuationResult(BaseModel):
    baseline_value_gbp: Optional[float] = Field(..., description="Baseline property valuation before retrofit (£)")
    indicative_uplift_pct_min: Optional[float] = Field(..., description="Conservative indicative value uplift percentage (e.g. 2.0%)")
    indicative_uplift_pct_max: Optional[float] = Field(..., description="Optimistic indicative value uplift percentage (e.g. 5.0%)")
    indicative_value_min_gbp: Optional[float] = Field(..., description="Estimated lower bound post-retrofit valuation (£)")
    indicative_value_max_gbp: Optional[float] = Field(..., description="Estimated upper bound post-retrofit valuation (£)")
    uplift_range_label: str = Field(..., description="Formatted string range (e.g. '+2.0% to +5.0%')")
    is_available: bool = Field(True, description="Whether sufficient valuation signals were present")
    unavailable_reason: Optional[str] = Field(None, description="Explanation if valuation is unavailable")
    model_version: str = Field(default="UK-Hedonic-Uplift-v1.0")
    caveat: str = Field(
        default="Indicative range based on observational UK market relationships. Does not constitute a formal RICS red-book valuation or guaranteed market increase."
    )
    methodology_notes: str = Field(
        default="Compares hedonic property price expectation holding floor area, location, and structural features constant while evaluating improved EPC rating and energy performance."
    )
