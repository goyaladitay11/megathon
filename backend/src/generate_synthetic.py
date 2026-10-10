"""
Synthetic UK Residential Dataset Generator & Leakage-Free Splitter (5,000 Properties)
Lloyds Megathon X PS2 (Phase 2 & Phase 3)
"""

import os
import sys
import json
import random
from pathlib import Path
import numpy as np
import pandas as pd

script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
repo_root = backend_dir.parent
for p in [str(backend_dir), str(repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.src.schemas import PropertyData
from backend.src.scoring_engine import score_home
from backend.src.retrofit_engine import recommend_retrofits, simulate_retrofit, RETROFIT_SPECS
from backend.src.carbon_engine import calculate_carbon

UK_REGIONS = [
    "London", "South East", "South West", "East of England",
    "West Midlands", "East Midlands", "North West",
    "Yorkshire and the Humber", "North East", "Wales", "Scotland"
]
PROPERTY_TYPES = ["detached", "semi_detached", "terraced", "flat"]
INSULATION_LEVELS = ["poor", "average", "good"]
HEATING_SYSTEMS = ["gas_boiler", "electric_resistive", "oil_boiler", "heat_pump"]
GLAZING_TYPES = ["single", "double", "triple"]
SOLAR_OPTIONS = ["none", "2kw", "4kw"]


def generate_dataset(num_properties: int = 5000, seed: int = 42, output_dir: str = None):
    print(f"Generating comprehensive dataset: {num_properties} properties (seed={seed})...")
    random.seed(seed)
    np.random.seed(seed)

    if output_dir is None:
        output_dir = str(backend_dir / "data" / "processed")
    synth_dir = str(backend_dir / "data" / "synthetic")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(synth_dir, exist_ok=True)

    gas_weights = [0.18, 0.16, 0.13, 0.08, 0.05, 0.02, 0.01, 0.01, 0.03, 0.08, 0.11, 0.14]
    elec_weights = [0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.06, 0.06, 0.07, 0.09, 0.10, 0.11]
    gas_weights = [w / sum(gas_weights) for w in gas_weights]
    elec_weights = [w / sum(elec_weights) for w in elec_weights]

    num_customers = int(num_properties * 0.80)
    customer_ids = [f"C{1000 + i}" for i in range(num_customers)]

    prop_rows = []
    energy_rows = []
    sales_rows = []
    retrofit_hist_rows = []
    reference_labels_rows = []

    for i in range(1, num_properties + 1):
        prop_id = f"P{10000 + i}"
        customer_id = random.choice(customer_ids)

        year_built = random.choice([
            random.randint(1890, 1929),
            random.randint(1930, 1964),
            random.randint(1965, 1982),
            random.randint(1983, 2002),
            random.randint(2003, 2022),
        ])

        prop_type = random.choices(PROPERTY_TYPES, weights=[0.24, 0.32, 0.28, 0.16], k=1)[0]
        bedrooms = random.choices([1, 2, 3, 4, 5], weights=[0.10, 0.30, 0.40, 0.15, 0.05])[0]

        base_area = {1: 48.0, 2: 70.0, 3: 95.0, 4: 135.0, 5: 180.0}[bedrooms]
        type_mult = {"flat": 0.85, "terraced": 0.95, "semi_detached": 1.05, "detached": 1.25}[prop_type]
        floor_area = round(float(np.random.normal(base_area * type_mult, 8.0)), 1)
        floor_area = max(35.0, min(360.0, floor_area))

        region = random.choices(
            UK_REGIONS,
            weights=[0.15, 0.18, 0.10, 0.10, 0.10, 0.08, 0.11, 0.08, 0.04, 0.03, 0.03],
            k=1
        )[0]

        if year_built < 1960:
            insulation = random.choices(INSULATION_LEVELS, weights=[0.55, 0.35, 0.10])[0]
            glazing = random.choices(GLAZING_TYPES, weights=[0.25, 0.70, 0.05])[0]
            heating = random.choices(HEATING_SYSTEMS, weights=[0.75, 0.10, 0.10, 0.05])[0]
            solar = random.choices(SOLAR_OPTIONS, weights=[0.88, 0.08, 0.04])[0]
            smart_controls = random.choices([False, True], weights=[0.70, 0.30])[0]
        elif year_built < 1995:
            insulation = random.choices(INSULATION_LEVELS, weights=[0.30, 0.50, 0.20])[0]
            glazing = random.choices(GLAZING_TYPES, weights=[0.10, 0.85, 0.05])[0]
            heating = random.choices(HEATING_SYSTEMS, weights=[0.82, 0.08, 0.04, 0.06])[0]
            solar = random.choices(SOLAR_OPTIONS, weights=[0.82, 0.12, 0.06])[0]
            smart_controls = random.choices([False, True], weights=[0.55, 0.45])[0]
        else:
            insulation = random.choices(INSULATION_LEVELS, weights=[0.05, 0.35, 0.60])[0]
            glazing = random.choices(GLAZING_TYPES, weights=[0.02, 0.80, 0.18])[0]
            heating = random.choices(HEATING_SYSTEMS, weights=[0.70, 0.05, 0.02, 0.23])[0]
            solar = random.choices(SOLAR_OPTIONS, weights=[0.70, 0.18, 0.12])[0]
            smart_controls = random.choices([False, True], weights=[0.30, 0.70])[0]

        # Correlated EPC band
        epc_pts = 0
        epc_pts += {"poor": 15, "average": 45, "good": 80}[insulation]
        epc_pts += {"single": 10, "double": 45, "triple": 70}[glazing]
        epc_pts += {"gas_boiler": 40, "electric_resistive": 35, "oil_boiler": 25, "heat_pump": 80}[heating]
        epc_pts += 15 if smart_controls else 0
        epc_pts += 20 if solar != "none" else 0

        if epc_pts >= 220:
            energy_rating = random.choices(["A", "B"], weights=[0.3, 0.7])[0]
        elif epc_pts >= 170:
            energy_rating = random.choices(["B", "C"], weights=[0.3, 0.7])[0]
        elif epc_pts >= 130:
            energy_rating = random.choices(["C", "D"], weights=[0.4, 0.6])[0]
        elif epc_pts >= 90:
            energy_rating = random.choices(["D", "E"], weights=[0.4, 0.6])[0]
        elif epc_pts >= 60:
            energy_rating = random.choices(["E", "F"], weights=[0.5, 0.5])[0]
        else:
            energy_rating = random.choices(["F", "G"], weights=[0.4, 0.6])[0]

        # Realistic Energy Consumption (NEED & Ofgem distributions)
        base_elec = 1800.0 + (bedrooms * 500.0) + (floor_area * 8.0)
        if solar == "2kw":
            base_elec = max(1000.0, base_elec - 1600.0)
        elif solar == "4kw":
            base_elec = max(800.0, base_elec - 3000.0)

        heat_loss_factor = {"poor": 1.45, "average": 1.0, "good": 0.65}[insulation]
        glazing_factor = {"single": 1.25, "double": 1.0, "triple": 0.85}[glazing]
        control_factor = 0.92 if smart_controls else 1.0

        space_heat_kwh = floor_area * 115.0 * heat_loss_factor * glazing_factor * control_factor
        water_heat_kwh = 1800.0 + (bedrooms * 400.0)

        if heating == "gas_boiler":
            annual_gas = (space_heat_kwh + water_heat_kwh) / 0.85
            annual_elec = base_elec
        elif heating == "heat_pump":
            annual_gas = 0.0
            annual_elec = base_elec + (space_heat_kwh + water_heat_kwh) / 3.0
        elif heating == "electric_resistive":
            annual_gas = 0.0
            annual_elec = base_elec + space_heat_kwh + water_heat_kwh
        else:
            annual_gas = (space_heat_kwh + water_heat_kwh) / 0.80
            annual_elec = base_elec

        annual_elec = max(800.0, float(np.random.normal(annual_elec, annual_elec * 0.06)))
        annual_gas = max(0.0, float(np.random.normal(annual_gas, annual_gas * 0.07)))

        # Regional Property Valuation (HM Land Registry UK levels)
        regional_price_m2 = {
            "London": 6800.0, "South East": 4200.0, "South West": 3600.0,
            "East of England": 3800.0, "West Midlands": 2700.0, "East Midlands": 2600.0,
            "North West": 2400.0, "Yorkshire and the Humber": 2300.0, "North East": 1900.0,
            "Wales": 2200.0, "Scotland": 2300.0,
        }[region]

        epc_premium = {"A": 1.10, "B": 1.06, "C": 1.02, "D": 1.00, "E": 0.96, "F": 0.92, "G": 0.88}[energy_rating]
        property_val = round(floor_area * regional_price_m2 * epc_premium * random.uniform(0.96, 1.04), -2)

        prop_data = PropertyData(
            property_id=prop_id,
            customer_id=customer_id,
            property_type=prop_type,
            property_age=year_built,
            floor_area_m2=floor_area,
            bedrooms=bedrooms,
            energy_rating=energy_rating,
            heating_system=heating,
            insulation_type=insulation,
            glazing_type=glazing,
            solar_installed=solar,
            smart_controls=smart_controls,
            region=region,
            current_property_value=property_val,
            annual_electricity_kwh=round(annual_elec, 1),
            annual_gas_kwh=round(annual_gas, 1),
        )

        # Ground truth evaluation
        score_res = score_home(prop_data)
        feasible_recs = recommend_retrofits(prop_data)
        package_ids = [r.retrofit_id for r in feasible_recs]
        sim_res = simulate_retrofit(prop_data, package_ids)
        carb_res = calculate_carbon(
            {"electricity_kwh": sim_res.baseline_electricity_kwh, "gas_kwh": sim_res.baseline_gas_kwh},
            {"electricity_kwh": sim_res.after_electricity_kwh, "gas_kwh": sim_res.after_gas_kwh},
        )

        prop_rows.append({
            "property_id": prop_id,
            "customer_id": customer_id,
            "property_type": prop_type,
            "property_age": year_built,
            "floor_area_m2": floor_area,
            "bedrooms": bedrooms,
            "energy_rating": energy_rating,
            "heating_system": heating,
            "insulation_type": insulation,
            "glazing_type": glazing,
            "solar_installed": solar,
            "smart_controls": smart_controls,
            "region": region,
            "current_property_value": property_val,
            "annual_electricity_kwh": round(annual_elec, 1),
            "annual_gas_kwh": round(annual_gas, 1),
        })

        reference_labels_rows.append({
            "property_id": prop_id,
            "customer_id": customer_id,
            "green_home_score": score_res.green_home_score,
            "classification": score_res.classification,
            "is_poor_performing": score_res.is_poor_performing,
            "baseline_purchased_kwh": sim_res.baseline_purchased_kwh,
            "post_retrofit_electricity_kwh": sim_res.after_electricity_kwh,
            "post_retrofit_gas_kwh": sim_res.after_gas_kwh,
            "post_retrofit_purchased_kwh": sim_res.after_purchased_kwh,
            "electricity_saving_kwh": sim_res.electricity_saving_kwh,
            "gas_saving_kwh": sim_res.gas_saving_kwh,
            "net_purchased_energy_saving_kwh": sim_res.net_purchased_energy_saving_kwh,
            "improvement_potential_pct": sim_res.improvement_potential_pct,
            "net_carbon_reduction_kg": carb_res.net_carbon_reduction_kg,
            "net_carbon_reduction_tonnes": carb_res.net_carbon_reduction_tonnes,
            "recommended_package_retrofits": ",".join(package_ids),
            "feasible_retrofit_count": len(feasible_recs),
        })

        # Monthly meter usage
        for m in range(1, 13):
            energy_rows.append({
                "property_id": prop_id,
                "month": m,
                "electricity_kwh": round(annual_elec * elec_weights[m - 1] * random.uniform(0.96, 1.04), 1),
                "gas_kwh": round(annual_gas * gas_weights[m - 1] * random.uniform(0.95, 1.05), 1),
            })

        # Sales history (holding historical sale prices distinct from current valuation!)
        past_year = random.randint(2017, 2023)
        sales_rows.append({
            "property_id": prop_id,
            "sale_date": f"{past_year}-{random.randint(1, 12):02d}-15",
            "historical_sale_price_gbp": round(property_val * random.uniform(0.78, 0.95), -2),
            "energy_rating_at_sale": energy_rating,
        })

        if random.random() < 0.20:
            hist_retro = random.choice(["roof_insulation", "double_glazing", "smart_thermostat"])
            retrofit_hist_rows.append({
                "customer_id": customer_id,
                "property_id": prop_id,
                "retrofit_id": hist_retro,
                "completion_date": f"{random.randint(2022, 2024)}-{random.randint(1, 12):02d}-01",
            })

    df_properties = pd.DataFrame(prop_rows)
    df_energy = pd.DataFrame(energy_rows)
    df_sales = pd.DataFrame(sales_rows)
    df_retrofit_hist = pd.DataFrame(retrofit_hist_rows)
    df_labels = pd.DataFrame(reference_labels_rows)

    # Split dataset: 70% train, 15% validation, 15% untouched test grouped strictly by customer_id
    unique_customers = list(df_properties["customer_id"].unique())
    random.shuffle(unique_customers)

    n_cust = len(unique_customers)
    n_test = int(n_cust * 0.15)
    n_val = int(n_cust * 0.15)

    test_cust = set(unique_customers[:n_test])
    val_cust = set(unique_customers[n_test : n_test + n_val])
    train_cust = set(unique_customers[n_test + n_val :])

    df_train = df_properties[df_properties["customer_id"].isin(train_cust)].copy()
    df_val = df_properties[df_properties["customer_id"].isin(val_cust)].copy()
    df_test = df_properties[df_properties["customer_id"].isin(test_cust)].copy()

    # Leakage assertions
    assert len(set(df_train["customer_id"]).intersection(set(df_val["customer_id"]))) == 0
    assert len(set(df_train["customer_id"]).intersection(set(df_test["customer_id"]))) == 0
    assert len(set(df_val["customer_id"]).intersection(set(df_test["customer_id"]))) == 0

    assert len(set(df_train["property_id"]).intersection(set(df_val["property_id"]))) == 0
    assert len(set(df_train["property_id"]).intersection(set(df_test["property_id"]))) == 0
    assert len(set(df_val["property_id"]).intersection(set(df_test["property_id"]))) == 0

    # Save to both synthetic and processed
    for d in [synth_dir, output_dir]:
        df_properties.to_csv(os.path.join(d, "properties.csv"), index=False)
        df_energy.to_csv(os.path.join(d, "energy_usage.csv"), index=False)
        df_sales.to_csv(os.path.join(d, "sales_history.csv"), index=False)
        df_retrofit_hist.to_csv(os.path.join(d, "retrofit_history.csv"), index=False)
        df_labels.to_csv(os.path.join(d, "reference_labels.csv"), index=False)
        df_train.to_csv(os.path.join(d, "train_properties.csv"), index=False)
        df_val.to_csv(os.path.join(d, "val_properties.csv"), index=False)
        df_test.to_csv(os.path.join(d, "test_properties.csv"), index=False)

    manifest = {
        "dataset_name": "Lloyds UK Residential Housing Stock Dataset (5,000 Properties)",
        "num_properties": len(df_properties),
        "num_customers": n_cust,
        "splits": {
            "train": {"count": len(df_train), "customers": len(train_cust), "pct": round(len(df_train)/len(df_properties)*100, 1)},
            "validation": {"count": len(df_val), "customers": len(val_cust), "pct": round(len(df_val)/len(df_properties)*100, 1)},
            "test": {"count": len(df_test), "customers": len(test_cust), "pct": round(len(df_test)/len(df_properties)*100, 1)},
        },
        "leakage_verification": "Passed: Zero customer_id or property_id overlap across train, val, and test splits.",
        "distributions": {
            "epc_ratings": df_properties["energy_rating"].value_counts().to_dict(),
            "property_types": df_properties["property_type"].value_counts().to_dict(),
            "heating_systems": df_properties["heating_system"].value_counts().to_dict(),
            "mean_floor_area_m2": round(float(df_properties["floor_area_m2"].mean()), 1),
            "mean_baseline_electricity_kwh": round(float(df_properties["annual_electricity_kwh"].mean()), 1),
            "mean_baseline_gas_kwh": round(float(df_properties["annual_gas_kwh"].mean()), 1),
            "poor_performing_pct": round(float(df_labels["is_poor_performing"].mean() * 100), 1),
        },
    }
    with open(os.path.join(output_dir, "data_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"5,000 Property Dataset Generated Successfully!")
    print(f"- Train: {len(df_train)} ({manifest['splits']['train']['pct']}%)")
    print(f"- Val: {len(df_val)} ({manifest['splits']['validation']['pct']}%)")
    print(f"- Test: {len(df_test)} ({manifest['splits']['test']['pct']}%)")
    return manifest


if __name__ == "__main__":
    generate_dataset()
