"""
Unit Tests for Strict Monotonicity Across All Sub-Score Mappings
"""

import pytest
from backend.src.scoring_engine import (
    compute_intensity_sub_score,
    EPC_MAPPING,
    INSULATION_MAPPING,
    GLAZING_MAPPING,
    SOLAR_MAPPING,
)


def test_epc_sub_scores_strictly_monotonic():
    bands = ["A", "B", "C", "D", "E", "F", "G"]
    scores = [EPC_MAPPING[b][0] for b in bands]
    for i in range(len(scores) - 1):
        assert scores[i] > scores[i + 1], f"EPC band {bands[i]} must score higher than {bands[i+1]}"


def test_intensity_sub_score_strictly_monotonic():
    # Lower intensity must NEVER produce a lower score
    test_intensities = [20.0, 45.0, 50.0, 80.0, 120.0, 150.0, 180.0, 220.0, 260.0, 310.0, 360.0, 450.0]
    sub_scores = [compute_intensity_sub_score(x)[0] for x in test_intensities]
    for i in range(len(sub_scores) - 1):
        assert sub_scores[i] >= sub_scores[i + 1], (
            f"Intensity {test_intensities[i]} kWh/m² scored {sub_scores[i]} which is lower than "
            f"worse intensity {test_intensities[i+1]} kWh/m² ({sub_scores[i+1]})"
        )


def test_insulation_strictly_monotonic():
    assert INSULATION_MAPPING["good"][0] > INSULATION_MAPPING["average"][0] > INSULATION_MAPPING["poor"][0]


def test_glazing_strictly_monotonic():
    assert GLAZING_MAPPING["triple"][0] > GLAZING_MAPPING["double"][0] > GLAZING_MAPPING["single"][0]


def test_renewables_strictly_monotonic():
    assert SOLAR_MAPPING["4kw"][0] > SOLAR_MAPPING["2kw"][0] > SOLAR_MAPPING["none"][0]
