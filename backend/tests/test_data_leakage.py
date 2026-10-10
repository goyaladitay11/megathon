"""
Unit Tests for Data Leakage Prevention and Customer-Group Isolation
"""

import os
from pathlib import Path
import pandas as pd
import pytest

backend_dir = Path(__file__).resolve().parent.parent


def test_customer_level_split_isolation():
    data_dir = backend_dir / "data" / "processed"
    df_train = pd.read_csv(data_dir / "train_properties.csv")
    df_val = pd.read_csv(data_dir / "val_properties.csv")
    df_test = pd.read_csv(data_dir / "test_properties.csv")

    train_custs = set(df_train["customer_id"])
    val_custs = set(df_val["customer_id"])
    test_custs = set(df_test["customer_id"])

    # Zero overlap between any pair of splits
    assert len(train_custs.intersection(val_custs)) == 0, "Data leakage detected: Customer overlap between Train and Val"
    assert len(train_custs.intersection(test_custs)) == 0, "Data leakage detected: Customer overlap between Train and Test"
    assert len(val_custs.intersection(test_custs)) == 0, "Data leakage detected: Customer overlap between Val and Test"


def test_property_level_split_isolation():
    data_dir = backend_dir / "data" / "processed"
    df_train = pd.read_csv(data_dir / "train_properties.csv")
    df_val = pd.read_csv(data_dir / "val_properties.csv")
    df_test = pd.read_csv(data_dir / "test_properties.csv")

    train_props = set(df_train["property_id"])
    val_props = set(df_val["property_id"])
    test_props = set(df_test["property_id"])

    assert len(train_props.intersection(val_props)) == 0, "Property overlap between Train and Val"
    assert len(train_props.intersection(test_props)) == 0, "Property overlap between Train and Test"
    assert len(val_props.intersection(test_props)) == 0, "Property overlap between Val and Test"
