"""
Data Validation and Leakage Prevention Checks
Lloyds Megathon X PS2 (Phase 3)
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent


def validate_dataset(data_dir: str = None) -> dict:
    if data_dir is None:
        data_dir = str(backend_dir / "data" / "processed")

    df_all = pd.read_csv(os.path.join(data_dir, "properties.csv"))
    df_train = pd.read_csv(os.path.join(data_dir, "train_properties.csv"))
    df_val = pd.read_csv(os.path.join(data_dir, "val_properties.csv"))
    df_test = pd.read_csv(os.path.join(data_dir, "test_properties.csv"))
    df_energy = pd.read_csv(os.path.join(data_dir, "energy_usage.csv"))
    df_sales = pd.read_csv(os.path.join(data_dir, "sales_history.csv"))

    checks = {}

    # 1. Uniqueness
    checks["unique_property_ids"] = df_all["property_id"].is_unique
    checks["unique_train_properties"] = df_train["property_id"].is_unique
    checks["unique_val_properties"] = df_val["property_id"].is_unique
    checks["unique_test_properties"] = df_test["property_id"].is_unique

    # 2. Leakage Prevention (Customer & Property level)
    train_custs = set(df_train["customer_id"])
    val_custs = set(df_val["customer_id"])
    test_custs = set(df_test["customer_id"])

    checks["no_train_val_cust_overlap"] = len(train_custs.intersection(val_custs)) == 0
    checks["no_train_test_cust_overlap"] = len(train_custs.intersection(test_custs)) == 0
    checks["no_val_test_cust_overlap"] = len(val_custs.intersection(test_custs)) == 0

    train_props = set(df_train["property_id"])
    val_props = set(df_val["property_id"])
    test_props = set(df_test["property_id"])

    checks["no_train_val_prop_overlap"] = len(train_props.intersection(val_props)) == 0
    checks["no_train_test_prop_overlap"] = len(train_props.intersection(test_props)) == 0
    checks["no_val_test_prop_overlap"] = len(val_props.intersection(test_props)) == 0

    # 3. Value Constraints
    checks["positive_floor_area"] = (df_all["floor_area_m2"] > 0).all()
    checks["positive_bedrooms"] = (df_all["bedrooms"] > 0).all()
    checks["non_negative_elec"] = (df_all["annual_electricity_kwh"] >= 0).all()
    checks["non_negative_gas"] = (df_all["annual_gas_kwh"] >= 0).all()
    checks["non_negative_monthly_elec"] = (df_energy["electricity_kwh"] >= 0).all()
    checks["non_negative_monthly_gas"] = (df_energy["gas_kwh"] >= 0).all()

    # 4. Valid Categorical Values
    valid_epc = {"A", "B", "C", "D", "E", "F", "G"}
    valid_types = {"detached", "semi_detached", "terraced", "flat"}
    valid_heat = {"gas_boiler", "electric_resistive", "oil_boiler", "heat_pump"}
    valid_insul = {"poor", "average", "good"}
    valid_glaze = {"single", "double", "triple"}

    checks["valid_epc_ratings"] = set(df_all["energy_rating"]).issubset(valid_epc)
    checks["valid_property_types"] = set(df_all["property_type"]).issubset(valid_types)
    checks["valid_heating_systems"] = set(df_all["heating_system"]).issubset(valid_heat)
    checks["valid_insulation_levels"] = set(df_all["insulation_type"]).issubset(valid_insul)
    checks["valid_glazing_types"] = set(df_all["glazing_type"]).issubset(valid_glaze)

    # 5. Split Proportions
    total_len = len(df_all)
    checks["train_ratio_approx_70"] = 0.65 <= (len(df_train) / total_len) <= 0.75
    checks["val_ratio_approx_15"] = 0.12 <= (len(df_val) / total_len) <= 0.18
    checks["test_ratio_approx_15"] = 0.12 <= (len(df_test) / total_len) <= 0.18

    all_passed = all(checks.values())
    print("Dataset Validation Results:")
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"Overall Status: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")

    return checks


if __name__ == "__main__":
    validate_dataset()
