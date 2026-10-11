from backend.app.api.v1.routes import SAMPLE_PROPERTIES
from backend.app.services.chat_intents import detect_chat_intent, build_retrofit_advice
from backend.app.services.data_pipeline import validate_and_summarize_property


def test_recommendation_and_simulation_have_different_intents():
    assert detect_chat_intent("suggest me some roof insulation") == "recommend"
    assert detect_chat_intent("What if I install roof insulation?") == "simulate"
    assert detect_chat_intent("which type of roof insulation is best?") == "recommend"
    assert detect_chat_intent("How much energy would roof insulation save?") == "simulate"


def test_roof_insulation_advice_is_grounded_and_has_no_fake_simulation():
    summary = validate_and_summarize_property(SAMPLE_PROPERTIES[0])
    result = build_retrofit_advice(summary, ["roof_insulation"], [])
    assert "Mineral-wool" in " ".join(result.explanation.reasons)
    assert "Blown-in cellulose" in " ".join(result.explanation.reasons)
    assert "Rigid PIR" in " ".join(result.explanation.reasons)
    assert result.simulated_energy is None
    assert result.simulated_carbon is None
    assert result.simulated_valuation is None
    assert "no retrofit simulated" in result.scenario_recognized.lower()


def test_already_well_insulated_home_is_not_recommended_upgrade():
    summary = validate_and_summarize_property(SAMPLE_PROPERTIES[3])
    result = build_retrofit_advice(summary, ["roof_insulation"], [])
    assert "not recommended" in result.explanation.summary.lower()
