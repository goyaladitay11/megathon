"""
Persistent Customer Memory & Adaptive Recommendation Service
Step 10: Optional Extension - Customer Memory (Section 10 of PS2)
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

from backend.app.schemas.property import PropertySummary
from backend.app.schemas.retrofit import RetrofitRecommendation, RetrofitPackage
from backend.app.services.retrofit_recommender import build_recommended_package


class CustomerPreference(BaseModel):
    customer_id: str
    completed_retrofits: List[Dict[str, Any]] = Field(default_factory=list)
    budget_limit_gbp: Optional[float] = None
    disliked_retrofit_ids: List[str] = Field(default_factory=list)
    preferred_categories: List[str] = Field(default_factory=list)
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list)


# In-memory customer state store (with option to sync to database if configured)
CUSTOMER_MEMORY_STORE: Dict[str, CustomerPreference] = {}


def get_customer_memory(customer_id: str) -> CustomerPreference:
    """Retrieves or initializes customer memory state."""
    if customer_id not in CUSTOMER_MEMORY_STORE:
        CUSTOMER_MEMORY_STORE[customer_id] = CustomerPreference(customer_id=customer_id)
    return CUSTOMER_MEMORY_STORE[customer_id]


def update_customer_preferences(
    customer_id: str,
    budget_limit_gbp: Optional[float] = None,
    disliked_retrofit_ids: Optional[List[str]] = None,
    preferred_categories: Optional[List[str]] = None,
) -> CustomerPreference:
    """Updates customer preferences and constraints."""
    mem = get_customer_memory(customer_id)
    if budget_limit_gbp is not None:
        mem.budget_limit_gbp = budget_limit_gbp
    if disliked_retrofit_ids is not None:
        mem.disliked_retrofit_ids = disliked_retrofit_ids
    if preferred_categories is not None:
        mem.preferred_categories = preferred_categories
    mem.interaction_history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "updated_preferences",
        "budget": mem.budget_limit_gbp,
        "disliked": mem.disliked_retrofit_ids,
    })
    return mem


def add_completed_retrofit(
    customer_id: str,
    retrofit_id: str,
    completion_date: Optional[str] = None,
) -> CustomerPreference:
    """Registers a completed retrofit in customer history."""
    mem = get_customer_memory(customer_id)
    date_str = completion_date or datetime.utcnow().strftime("%Y-%m-%d")
    mem.completed_retrofits.append({
        "retrofit_id": retrofit_id,
        "completion_date": date_str,
    })
    mem.interaction_history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "completed_retrofit",
        "retrofit_id": retrofit_id,
        "date": date_str,
    })
    return mem


def record_customer_feedback(
    customer_id: str,
    retrofit_id: str,
    accepted: bool,
    feedback_reason: Optional[str] = None,
) -> CustomerPreference:
    """Records customer response to a recommendation."""
    mem = get_customer_memory(customer_id)
    if not accepted and retrofit_id not in mem.disliked_retrofit_ids:
        mem.disliked_retrofit_ids.append(retrofit_id)
    mem.interaction_history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "recommendation_feedback",
        "retrofit_id": retrofit_id,
        "accepted": accepted,
        "reason": feedback_reason,
    })
    return mem


def adapt_recommendations_with_memory(
    summary: PropertySummary,
    base_recommendations: List[RetrofitRecommendation],
) -> Tuple[List[RetrofitRecommendation], RetrofitPackage, List[str]]:
    """
    Adapts recommendations using customer memory:
    1. Removes already completed retrofits.
    2. Flags/filters retrofits disliked by customer.
    3. Flags retrofits that exceed declared budget limit.
    4. Explains how memory adapted the recommendations.
    """
    customer_id = summary.customer_id or "default_customer"
    mem = get_customer_memory(customer_id)
    adaptation_log = []

    completed_ids = {item["retrofit_id"] for item in mem.completed_retrofits}
    adapted_recs = []

    for rec in base_recommendations:
        # Check if already completed
        if rec.retrofit_id in completed_ids:
            adaptation_log.append(
                f"Filtered out '{rec.name}': Customer completed this improvement on "
                f"{next(item['completion_date'] for item in mem.completed_retrofits if item['retrofit_id'] == rec.retrofit_id)}."
            )
            continue

        # Check if disliked/rejected previously
        if rec.retrofit_id in mem.disliked_retrofit_ids:
            adaptation_log.append(
                f"Suppressed '{rec.name}': Customer previously indicated disinterest or rejection."
            )
            continue

        # Check budget constraint
        if mem.budget_limit_gbp is not None and rec.estimated_cost_gbp_min > mem.budget_limit_gbp:
            adaptation_log.append(
                f"Flagged '{rec.name}' (£{rec.estimated_cost_gbp_min:,.0f} min): Exceeds customer stated budget of £{mem.budget_limit_gbp:,.0f}."
            )
            rec.dependencies_or_notes = (
                f"(Over budget: £{mem.budget_limit_gbp:,.0f} limit) "
                + (rec.dependencies_or_notes or "")
            )

        adapted_recs.append(rec)

    # Reassemble adapted package
    adapted_package = build_recommended_package(summary, adapted_recs)
    
    if adaptation_log:
        adapted_package.package_name = "Personalised Package (Adapted by Customer Memory)"
        adapted_package.interaction_explanation += f" Memory Adaptations: {'; '.join(adaptation_log)}"

    return adapted_recs, adapted_package, adaptation_log
