"""
API Endpoints v1
Lloyds Megathon X PS2: Green Home Score & Retrofit Recommendation Engine
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body

from backend.app.schemas.property import PropertyInput, PropertySummary
from backend.app.schemas.response import (
    AnalysisResponse,
    SimulationResponse,
    RecommendationResponse,
    LeaderboardResponse,
    ModelMetricsResponse,
)
from backend.app.schemas.simulation import SimulateRequest, EnergySimulationResult
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.models.catalogue import RETROFIT_CATALOGUE
from backend.app.services.data_pipeline import validate_and_summarize_property
from backend.app.services.scoring_engine import calculate_green_home_score
from backend.app.services.poor_home_detector import detect_key_issues
from backend.app.services.retrofit_recommender import (
    get_feasible_recommendations,
    build_recommended_package,
)
from backend.app.services.energy_simulator import simulate_energy_impact
from backend.app.services.carbon_service import calculate_carbon_reduction
from backend.app.services.valuation_service import estimate_property_value_uplift
from backend.app.services.explanation_service import (
    generate_grounded_explanation_with_gemini,
    handle_what_if_interaction,
)
from backend.app.services.customer_memory_service import (
    get_customer_memory,
    update_customer_preferences,
    add_completed_retrofit,
    record_customer_feedback,
    adapt_recommendations_with_memory,
    CustomerPreference,
)

router = APIRouter(prefix="/v1", tags=["Green Home Engine"])

# Preloaded Archetype Properties representing England & Wales housing stock
SAMPLE_PROPERTIES: List[PropertyInput] = [
    PropertyInput(
        property_id="P10001",
        customer_id="C1001",
        property_type="terraced",
        age=1910,
        floor_area_m2=92.0,
        region="North West",
        bedrooms=3,
        energy_rating="E",
        insulation="poor",
        heating="gas_boiler",
        glazing="single",
        solar="none",
        smart_controls=False,
        current_property_value_gbp=210000.0,
        annual_electricity_kwh=3800.0,
        annual_gas_kwh=16500.0,
    ),
    PropertyInput(
        property_id="P10002",
        customer_id="C1002",
        property_type="semi_detached",
        age=1974,
        floor_area_m2=110.0,
        region="West Midlands",
        bedrooms=3,
        energy_rating="D",
        insulation="average",
        heating="gas_boiler",
        glazing="double",
        solar="none",
        smart_controls=False,
        current_property_value_gbp=285000.0,
        annual_electricity_kwh=3400.0,
        annual_gas_kwh=12800.0,
    ),
    PropertyInput(
        property_id="P10003",
        customer_id="C1003",
        property_type="detached",
        age=1998,
        floor_area_m2=145.0,
        region="South East",
        bedrooms=4,
        energy_rating="C",
        insulation="good",
        heating="gas_boiler",
        glazing="double",
        solar="none",
        smart_controls=True,
        current_property_value_gbp=475000.0,
        annual_electricity_kwh=4200.0,
        annual_gas_kwh=11500.0,
    ),
    PropertyInput(
        property_id="P10004",
        customer_id="C1004",
        property_type="detached",
        age=2015,
        floor_area_m2=160.0,
        region="East of England",
        bedrooms=4,
        energy_rating="B",
        insulation="good",
        heating="heat_pump",
        glazing="triple",
        solar="4kw",
        smart_controls=True,
        current_property_value_gbp=560000.0,
        annual_electricity_kwh=4800.0,
        annual_gas_kwh=0.0,
    ),
    PropertyInput(
        property_id="P10005",
        customer_id="C1005",
        property_type="detached",
        age=1935,
        floor_area_m2=175.0,
        region="South West",
        bedrooms=5,
        energy_rating="F",
        insulation="poor",
        heating="oil_boiler",
        glazing="single",
        solar="none",
        smart_controls=False,
        current_property_value_gbp=420000.0,
        annual_electricity_kwh=5100.0,
        annual_gas_kwh=22000.0,
    ),
    # Edge case: Missing gas meter data (requires imputation)
    PropertyInput(
        property_id="P10006",
        customer_id="C1006",
        property_type="flat",
        age=1985,
        floor_area_m2=58.0,
        region="London",
        bedrooms=2,
        energy_rating="D",
        insulation="average",
        heating="electric_resistive",
        glazing="double",
        solar="none",
        smart_controls=False,
        current_property_value_gbp=340000.0,
        annual_electricity_kwh=6200.0,
        annual_gas_kwh=None,  # All electric home with missing gas
    ),
    # Edge case: Physical contradiction (Heat pump but huge gas consumption)
    PropertyInput(
        property_id="P10007",
        customer_id="C1007",
        property_type="semi_detached",
        age=1960,
        floor_area_m2=105.0,
        region="Yorkshire and the Humber",
        bedrooms=3,
        energy_rating="E",
        insulation="poor",
        heating="heat_pump",
        glazing="single",
        solar="none",
        smart_controls=False,
        current_property_value_gbp=230000.0,
        annual_electricity_kwh=3900.0,
        annual_gas_kwh=14000.0,  # Contradiction flag triggered
    ),
]


@router.get("/properties", response_model=List[PropertyInput])
def list_sample_properties() -> List[PropertyInput]:
    """Returns archetype UK residential properties for instant testing."""
    return SAMPLE_PROPERTIES


@router.get("/properties/{property_id}", response_model=PropertyInput)
def get_property(property_id: str) -> PropertyInput:
    """Retrieves specific property by ID."""
    for p in SAMPLE_PROPERTIES:
        if p.property_id == property_id:
            return p
    raise HTTPException(status_code=404, detail=f"Property '{property_id}' not found.")


@router.get("/catalogue")
def get_retrofit_catalogue():
    """Returns the documented retrofit catalogue with costs, impacts and prerequisites."""
    return list(RETROFIT_CATALOGUE.values())


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_property(prop: PropertyInput) -> AnalysisResponse:
    """
    End-to-end Property Evaluation Pipeline:
    Property Data -> Data Pipeline -> Green Home Score -> Issue Detector ->
    Retrofit Engine -> Sequential Energy Simulation -> Carbon Engine ->
    Property Valuation Model -> Grounded LLM Explanation.
    """
    # 1. Validation & Data Standardization
    summary = validate_and_summarize_property(prop)

    # 2. Green Home Score
    score_result = calculate_green_home_score(summary)

    # 3. Issue Detection & Diagnostics
    issues = detect_key_issues(summary, score_result)

    # 4. Feasible Retrofits
    base_recs = get_feasible_recommendations(summary)

    # 5. Customer Memory Adaptation (Section 10)
    adapted_recs, rec_package, memory_notes = adapt_recommendations_with_memory(summary, base_recs)

    # 6. Interaction-Aware Energy Simulation for the package
    energy_sim = simulate_energy_impact(summary, rec_package.included_retrofit_ids)

    # 7. Per-Fuel Carbon Reduction
    carbon = calculate_carbon_reduction(energy_sim)

    # 8. Indicative Property Valuation Range
    valuation = estimate_property_value_uplift(summary, rec_package.included_retrofit_ids)

    # 9. Grounded LLM Explanation
    explanation = await generate_grounded_explanation_with_gemini(
        summary,
        score_result,
        energy_sim,
        carbon,
        valuation,
        rec_package.included_retrofit_ids,
    )

    assumptions = [
        "Fixed 7-component score weights sum to 1.00; sub-score mappings are strictly monotonic.",
        "Space heating disaggregated with UK typical 85% gas boiler efficiency.",
        "Air source heat pump operates at SPF 3.0 seasonal coefficient of performance, eliminating space/water heating gas.",
        "Emissions computed using UK Government 2024 GHG conversion factors (0.20707 kg/kWh elec, 0.18254 kg/kWh gas).",
        "Property value uplift reflects observational UK transaction relationships, holding area and location constant.",
    ]

    return AnalysisResponse(
        property=summary,
        score_details=score_result,
        key_issue_flags=issues,
        feasible_retrofits=adapted_recs,
        recommended_package=rec_package,
        energy_simulation=energy_sim,
        carbon_impact=carbon,
        valuation_impact=valuation,
        grounded_explanation=explanation,
        data_quality_warnings=summary.data_quality_flags,
        assumptions_summary=assumptions,
    )


@router.post("/simulate", response_model=SimulationResponse)
def simulate_scenario(req: SimulateRequest) -> SimulationResponse:
    """
    What-If Simulator: Reruns physical simulation, carbon calculations,
    and valuation models for arbitrary user-selected package of retrofits.
    """
    target_prop = None
    if req.property_input:
        if isinstance(req.property_input, dict):
            target_prop = PropertyInput(**req.property_input)
        elif isinstance(req.property_input, PropertyInput):
            target_prop = req.property_input

    if not target_prop and req.property_id:
        for p in SAMPLE_PROPERTIES:
            if p.property_id == req.property_id:
                target_prop = p
                break

    if not target_prop:
        target_prop = SAMPLE_PROPERTIES[0]

    # Apply overrides if provided
    if req.property_override:
        prop_data = target_prop.model_dump()
        prop_data.update(req.property_override)
        target_prop = PropertyInput(**prop_data)

    summary = validate_and_summarize_property(target_prop)
    sim_energy = simulate_energy_impact(summary, req.selected_retrofit_ids)
    sim_carbon = calculate_carbon_reduction(sim_energy)
    sim_val = estimate_property_value_uplift(summary, req.selected_retrofit_ids)

    return SimulationResponse(
        property_id=summary.property_id,
        applied_retrofit_ids=req.selected_retrofit_ids,
        energy=sim_energy,
        carbon=sim_carbon,
        valuation=sim_val,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_what_if(req: ChatRequest) -> ChatResponse:
    """
    Handles natural language what-if queries ("What if I install a heat pump and solar panels?").
    Reruns deterministic calculations and grounds explanations.
    """
    if req.property_input is not None:
        target_prop = req.property_input
    else:
        target_prop = next((p for p in SAMPLE_PROPERTIES if p.property_id == req.property_id), None)
        if target_prop is None:
            raise HTTPException(status_code=404, detail=f"Property '{req.property_id}' not found. Supply property_input for custom homes.")

    summary = validate_and_summarize_property(target_prop)
    return await handle_what_if_interaction(summary, req.query, req.selected_retrofit_ids)


@router.get("/customer-memory/{customer_id}", response_model=CustomerPreference)
def get_memory(customer_id: str) -> CustomerPreference:
    """Retrieves customer state from persistent memory."""
    return get_customer_memory(customer_id)


@router.post("/customer-memory/{customer_id}/preferences", response_model=CustomerPreference)
def set_preferences(
    customer_id: str,
    budget_limit_gbp: Optional[float] = Query(None),
    disliked_retrofits: Optional[List[str]] = Body(None),
) -> CustomerPreference:
    """Updates customer preferences and budget constraints."""
    return update_customer_preferences(
        customer_id=customer_id,
        budget_limit_gbp=budget_limit_gbp,
        disliked_retrofit_ids=disliked_retrofits,
    )


@router.post("/customer-memory/{customer_id}/complete-retrofit", response_model=CustomerPreference)
def record_completed(
    customer_id: str,
    retrofit_id: str = Query(...),
    completion_date: Optional[str] = Query(None),
) -> CustomerPreference:
    """Records a completed retrofit for a customer."""
    return add_completed_retrofit(customer_id, retrofit_id, completion_date)


@router.get("/metrics", response_model=Dict[str, Any])
def get_metrics_and_evaluation() -> Dict[str, Any]:
    """
    Returns held-out validation report, baseline comparisons, and Responsible AI notes.
    """
    import os
    import json
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "artifacts",
        "metrics",
        "evaluation_report.json",
    )
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            return json.load(f)

    # Default documented structure
    return {
        "status": "baseline_ready",
        "note": "Train script can be executed to regenerate held-out validation artifacts.",
        "methodology": "Customer-level grouped split (65% train, 15% val, 20% test) with zero property leakage.",
    }
