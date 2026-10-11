"""
Intent-aware, catalogue-grounded advice for natural-language retrofit questions.

Advice is distinct from a what-if simulation: materials and suitability can be
discussed without pretending a retrofit has been installed or calculating savings.
"""
import re
from typing import List

from backend.app.models.catalogue import RETROFIT_CATALOGUE
from backend.app.schemas.chat import ChatResponse, GroundedExplanationPayload
from backend.app.schemas.property import PropertySummary
from backend.app.services.retrofit_recommender import (
    evaluate_retrofit_feasibility_and_suitability,
    get_feasible_recommendations,
)


def detect_chat_intent(query: str) -> str:
    """Separate advice/product questions from explicit scenario requests."""
    text = query.lower().strip()

    # A requested effect of installing an upgrade needs the physics simulation.
    if re.search(
        r"\bwhat\s+if\b|\bif\s+i\s+(?:install|add|replace|get)\b"
        r"|\b(?:simulate|simulation|scenario)\b"
        r"|\bhow\s+much\b.*\b(?:save|saving|reduce|change|impact)\b"
        r"|\b(?:calculate|estimate)\b.*\b(?:savings|impact|reduction)\b",
        text,
    ):
        return "simulate"

    if re.search(
        r"\b(?:suggest|recommend|recommendation|which|options?|"
        r"types?|materials?|choose|best|buy|products?|prices?|costs?)\b",
        text,
    ):
        return "recommend"

    return "simulate"


def build_retrofit_advice(
    property_summary: PropertySummary,
    requested_ids: List[str],
    unsupported: List[str],
) -> ChatResponse:
    """
    Return factual, property-aware recommendations without applying a scenario.

    Monetary ranges and impact descriptions come from the repository's catalogue.
    Generic material examples are guidance, not seller/product endorsements.
    """
    selected = list(dict.fromkeys(requested_ids))
    if not selected:
        selected = [
            r.retrofit_id for r in get_feasible_recommendations(property_summary)[:3]
        ]

    valid_ids = [rid for rid in selected if rid in RETROFIT_CATALOGUE]
    rejected = list(unsupported) + [
        f"{rid}: not in the supported retrofit catalogue"
        for rid in selected if rid not in RETROFIT_CATALOGUE
    ]

    advice = []
    reasons = []
    tradeoffs = []
    limitations = [
        "These are advisory options, not a completed upgrade or calculated what-if scenario.",
        "Suitability depends on a property survey, construction details and installation quality.",
        "Indicative costs and energy-demand impacts come from the documented project catalogue, not live contractor quotations or independently verified results.",
        "For modelled energy, carbon and valuation changes, ask 'What if I install ...?' to run the calculation engines.",
    ]

    for rid in valid_ids:
        item = RETROFIT_CATALOGUE[rid]
        feasible, suitability, reason, dependency = (
            evaluate_retrofit_feasibility_and_suitability(property_summary, rid)
        )
        if not feasible:
            advice.append(
                f"{item.name}: not recommended for this property's recorded state. {reason}"
            )
            continue

        advice.append(
            f"{item.name} — {suitability} suitability. "
            f"Catalogue budget: £{item.typical_cost_min_gbp:,.0f}–"
            f"£{item.typical_cost_max_gbp:,.0f} (indicative, not a quote). "
            f"Catalogue impact: {item.indicative_impact_description}."
        )
        reasons.append(reason)
        if dependency:
            tradeoffs.append(dependency)

        if rid == "roof_insulation":
            reasons.extend([
                "Option 1 — Mineral-wool loft rolls: commonly used on accessible loft floors when the roof space remains unheated.",
                "Option 2 — Blown-in cellulose: can suit irregular or difficult-to-access loft-floor spaces; professional installation may be appropriate.",
                "Option 3 — Rigid PIR insulation boards: an alternative when insulation is being integrated into a pitched-roof/rafter build-up and space is limited.",
            ])
            tradeoffs.append(
                "Choose the assembly based on whether the loft or roof slope is insulated, "
                "roof ventilation, moisture/condensation risk, access and fire safety. "
                "The stored dataset does not identify this property's actual roof construction."
            )
        elif rid == "heat_pump":
            tradeoffs.append(
                "The preferred heat-pump size and emitter design require a heat-loss survey; "
                "upgrade poor insulation before or alongside heating-system replacement."
            )
        elif rid == "solar_pv":
            tradeoffs.append(
                "Roof condition, orientation, shading and structural suitability must be checked."
            )

    if not advice:
        summary_text = (
            "I couldn't identify a supported, suitable retrofit from this request. "
            "Try asking about roof insulation, glazing, smart thermostats, heat pumps or solar PV."
        )
    else:
        summary_text = (
            f"For property {property_summary.property_id} "
            f"(EPC {property_summary.energy_rating}, {property_summary.insulation} insulation), "
            "these are the relevant improvement options: " + " ".join(advice)
        )

    return ChatResponse(
        property_id=property_summary.property_id,
        scenario_recognized="Home improvement advice (no retrofit simulated)",
        parsed_retrofit_ids=[],
        unsupported_requested_items=rejected,
        explanation=GroundedExplanationPayload(
            summary=summary_text,
            reasons=reasons,
            tradeoffs=tradeoffs,
            limitations=limitations,
        ),
        simulated_energy=None,
        simulated_carbon=None,
        simulated_valuation=None,
        grounding_verified=True,
        engine_used="Documented retrofit catalogue (no LLM; no simulation)",
    )
