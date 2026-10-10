"""
Preprocessing Pipelines & Feature Schemas
Lloyds Megathon X PS2 (Phase 3 & Phase 5)
"""

from typing import List, Dict, Any
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

# Energy Regression Feature Sets
ENERGY_CATEGORICAL_FEATURES = [
    "property_type",
    "energy_rating",
    "heating_system",
    "insulation_type",
    "glazing_type",
    "solar_installed",
    "region",
]

ENERGY_NUMERIC_FEATURES = [
    "property_age",
    "floor_area_m2",
    "bedrooms",
    "smart_controls",
]

# Property Valuation Feature Sets
VALUATION_CATEGORICAL_FEATURES = [
    "property_type",
    "energy_rating_at_sale",
    "region",
]

VALUATION_NUMERIC_FEATURES = [
    "property_age",
    "floor_area_m2",
    "bedrooms",
    "sale_year",
]


def build_energy_preprocessor(scale_numeric: bool = True) -> ColumnTransformer:
    """Creates scikit-learn ColumnTransformer for energy features."""
    cat_transformer = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    
    if scale_numeric:
        num_transformer = StandardScaler()
    else:
        num_transformer = "passthrough"

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, ENERGY_NUMERIC_FEATURES),
            ("cat", cat_transformer, ENERGY_CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def build_valuation_preprocessor(scale_numeric: bool = True) -> ColumnTransformer:
    """Creates scikit-learn ColumnTransformer for property valuation features."""
    cat_transformer = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    
    if scale_numeric:
        num_transformer = StandardScaler()
    else:
        num_transformer = "passthrough"

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, VALUATION_NUMERIC_FEATURES),
            ("cat", cat_transformer, VALUATION_CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor
