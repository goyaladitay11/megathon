"""
Synthetic UK Residential Dataset Generator & Leakage-Free Splitter
Documented according to Lloyds Megathon X Problem Statement 2 (Section 9)

Data Sources & Empirical Anchors:
- English Housing Survey (EHS) 2022-2023 (Housing stock type, age, EPC distribution)
- National Energy Efficiency Data-Framework (NEED) 2023 (Dual-fuel consumption profiles)
- London Smart Meter Energy Consumption (Seasonal electricity profile dynamics)
- HM Land Registry Price Paid Data 2024 (Regional property price benchmarks)
- UK DESNZ / DEFRA GHG Conversion Factors 2024 (Scope 1 Natural Gas, Scope 2 Electricity)
"""

import os
import sys
import json
import random
from pathlib import Path
import numpy as np
import pandas as pd

# Add repo and backend root to sys.path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
repo_root = backend_dir.parent
for p in [str(backend_dir), str(repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.core.config import settings
from backend.app.schemas.property import PropertyInput
from backend.app.services.data_pipeline import (
    validate_and_summarize_property,
    UK_REGIONS,
    PROPERTY_TYPES,
    EPC_RATINGS,
    INSULATION_LEVELS,
    HEATING_SYSTEMS,
    GLAZING_TYPES,
    SOLAR_OPTIONS,
)
from backend.app.services.scoring_engine import compute_green_home_score
from backend.app.services.retrofit_recommender import get_feasible_recommendations, build_recommended_package
from backend.app.services.energy_simulator import simulate_energy_impact
from backend.app.services.carbon_service import calculate_carbon_reduction
from backend.app.services.valuation_service import estimate_property_value_uplift
from backend.app.models.catalogue import RETROFIT_CATALOGUE


def generate_full_synthetic_dataset(
    num_properties: int = 600,
    seed: int = 42,
    output_dir: str = None,
):
    print(f"Generating synthetic UK residential dataset ({num_properties} properties, seed={seed})...")
    random.seed(seed)
    np.random.seed(seed)

    if output_dir is None:
        output_dir = str(backend_dir / "data" / "processed")
    os.makedirs(output_dir, exist_ok=True)

    # Monthly seasonal weight factors in UK (NEED & London Smart Meter benchmarks)
    # Gas: high winter space heating, low summer cooking/hot water
    gas_monthly_weights = [0.18, 0.16, 0.13, 0.08, 0.05, 0.02, 0.01, 0.01, 0.03, 0.08, 0.11, 0.14]
    # Electricity: slight winter lighting/heating bump
    elec_monthly_weights = [0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.06, 0.06, 0.07, 0.09, 0.10, 0.11]
    gas_monthly_weights = [w / sum(gas_monthly_weights) for w in gas_monthly_weights]
    elec_monthly_weights = [w / sum(elec_monthly_weights) for w in elec_monthly_weights]

    # Generate customers (some landlords own multiple properties)
    num_customers = int(num_properties * 0.80)
    customer_ids = [f"C{1000 + i}" for i in range(num_customers)]

    property_records = []
    monthly_records = []
    sales_records = []
    retrofit_history_records = []

    for i in range(1, num_properties + 1):
        prop_id = f"P{10000 + i}"
        customer_id = random.choice(customer_ids)

        # Construction era based on English Housing Survey
        year_built = random.choice([
            random.randint(1890, 1929),  # Pre-1930 Victorian/Edwardian solid walls
            random.randint(1930, 1964),  # Interwar & early post-war
            random.randint(1965, 1982),  # 70s cavity wall
            random.randint(1983, 2002),  # Building regs insulated
            random.randint(2003, 2022),  # Modern high efficiency
        ])

        prop_type = random.choices(
            PROPERTY_TYPES,
            weights=[0.24, 0.32, 0.28, 0.16],  # UK distribution approx
            k=1
        )[0]

        bedrooms = random.choices([1, 2, 3, 4, 5], weights=[0.10, 0.30, 0.40, 0.15, 0.05])[0]

        # Floor area in m2 (EHS averages by bedrooms and archetype)
        base_area = {1: 48.0, 2: 70.0, 3: 95.0, 4: 135.0, 5: 180.0}[bedrooms]
        type_multiplier = {"flat": 0.85, "terraced": 0.95, "semi_detached": 1.05, "detached": 1.25}[prop_type]
        floor_area = round(float(np.random.normal(base_area * type_multiplier, 8.0)), 1)
        floor_area = max(35.0, min(360.0, floor_area))

        region = random.choices(
            UK_REGIONS,
            weights=[0.15, 0.18, 0.10, 0.10, 0.10, 0.08, 0.11, 0.08, 0.04, 0.03, 0.03],
            k=1
        )[0]

        # Fabric & heating characteristics correlated with building era
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
        epc_points = 0
        epc_points += {"poor": 15, "average": 45, "good": 80}[insulation]
        epc_points += {"single": 10, "double": 45, "triple": 70}[glazing]
        epc_points += {"gas_boiler": 40, "electric_resistive": 35, "oil_boiler": 25, "heat_pump": 80}[heating]
        epc_points += 15 if smart_controls else 0
        epc_points += 20 if solar != "none" else 0

        if epc_points >= 220:
            energy_rating = random.choices(["A", "B"], weights=[0.3, 0.7])[0]
        elif epc_points >= 170:
            energy_rating = random.choices(["B", "C"], weights=[0.3, 0.7])[0]
        elif epc_points >= 130:
            energy_rating = random.choices(["C", "D"], weights=[0.4, 0.6])[0]
        elif epc_points >= 90:
            energy_rating = random.choices(["D", "E"], weights=[0.4, 0.6])[0]
        elif epc_points >= 60:
            energy_rating = random.choices(["E", "F"], weights=[0.5, 0.5])[0]
        else:
            energy_rating = random.choices(["F", "G"], weights=[0.4, 0.6])[0]

        # Metered Annual Energy Consumption (NEED benchmarks)
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
        else:  # oil boiler
            annual_gas = (space_heat_kwh + water_heat_kwh) / 0.80
            annual_elec = base_elec

        # Add Gaussian noise
        annual_elec = max(800.0, float(np.random.normal(annual_elec, annual_elec * 0.06)))
        annual_gas = max(0.0, float(np.random.normal(annual_gas, annual_gas * 0.07)))

        # Regional Property Valuation (HM Land Registry UK representative levels)
        regional_price_m2 = {
            "London": 6800.0,
            "South East": 4200.0,
            "South West": 3600.0,
            "East of England": 3800.0,
            "West Midlands": 2700.0,
            "East Midlands": 2600.0,
            "North West": 2400.0,
            "Yorkshire and the Humber": 2300.0,
            "North East": 1900.0,
            "Wales": 2200.0,
            "Scotland": 2300.0,
        }[region]

        epc_premium = {"A": 1.10, "B": 1.06, "C": 1.02, "D": 1.00, "E": 0.96, "F": 0.92, "G": 0.88}[energy_rating]
        property_val = round(floor_area * regional_price_m2 * epc_premium * random.uniform(0.96, 1.04), -2)

        # Build PropertyInput & evaluate using our deterministic pipeline to create Ground Truth reference labels!
        prop_input = PropertyInput(
            property_id=prop_id,
            customer_id=customer_id,
            property_type=prop_type,
            age=year_built,
            floor_area_m2=floor_area,
            region=region,
            bedrooms=bedrooms,
            energy_rating=energy_rating,
            insulation=insulation,
            heating=heating,
            glazing=glazing,
            solar=solar,
            smart_controls=smart_controls,
            current_property_value_gbp=property_val,
            annual_electricity_kwh=round(annual_elec, 1),
            annual_gas_kwh=round(annual_gas, 1),
        )

        summary = validate_and_summarize_property(prop_input)
        score_res = compute_green_home_score(summary)
        feasible_recs = get_feasible_recommendations(summary)
        rec_package = build_recommended_package(summary, feasible_recs)
        sim_res = simulate_energy_impact(summary, rec_package.included_retrofit_ids)
        carb_res = calculate_carbon_reduction(sim_res)
        val_res = estimate_property_value_uplift(summary, rec_package.included_retrofit_ids)

        property_records.append({
            # Identifiers & Features
            "property_id": prop_id,
            "customer_id": customer_id,
            "property_type": prop_type,
            "age": year_built,
            "floor_area_m2": floor_area,
            "region": region,
            "bedrooms": bedrooms,
            "energy_rating": energy_rating,
            "insulation": insulation,
            "heating": heating,
            "glazing": glazing,
            "solar": solar,
            "smart_controls": smart_controls,
            "baseline_property_value_gbp": property_val,
            # Metered Baseline Consumptions
            "baseline_electricity_kwh": round(annual_elec, 1),
            "baseline_gas_kwh": round(annual_gas, 1),
            "baseline_purchased_kwh": round(annual_elec + annual_gas, 1),
            "energy_intensity_kwh_m2": summary.energy_intensity_kwh_m2,
            # Ground Truth Score & Classification
            "green_home_score": score_res.final_score,
            "classification": score_res.classification,
            "is_poor_performing": score_res.is_poor_performing,
            # Ground Truth Reference Targets for ML evaluation
            "feasible_retrofit_count": len(feasible_recs),
            "recommended_package_retrofits": ",".join(rec_package.included_retrofit_ids),
            "package_estimated_cost_avg_gbp": rec_package.total_estimated_cost_gbp_avg,
            "post_retrofit_electricity_kwh": sim_res.after_electricity_kwh,
            "post_retrofit_gas_kwh": sim_res.after_gas_kwh,
            "post_retrofit_purchased_kwh": sim_res.after_purchased_kwh,
            "electricity_savings_kwh": sim_res.electricity_savings_kwh,
            "gas_savings_kwh": sim_res.gas_savings_kwh,
            "net_purchased_energy_savings_kwh": sim_res.total_purchased_energy_savings_kwh,
            "improvement_potential_pct": sim_res.improvement_potential_percent,
            "net_carbon_savings_tonnes": carb_res.net_carbon_saving_tonnes,
            "indicative_uplift_pct_min": val_res.indicative_uplift_pct_min,
            "indicative_uplift_pct_max": val_res.indicative_uplift_pct_max,
            "post_retrofit_value_min_gbp": val_res.indicative_value_min_gbp,
            "post_retrofit_value_max_gbp": val_res.indicative_value_max_gbp,
        })

        # 12-Month Energy Profile
        for m in range(1, 13):
            monthly_records.append({
                "property_id": prop_id,
                "month": m,
                "electricity_kwh": round(annual_elec * elec_monthly_weights[m - 1] * random.uniform(0.96, 1.04), 1),
                "gas_kwh": round(annual_gas * gas_monthly_weights[m - 1] * random.uniform(0.95, 1.05), 1),
            })

        # Historical Sales Transaction (holding past sale price distinct from current baseline value)
        past_sale_year = random.randint(2018, 2023)
        sales_records.append({
            "property_id": prop_id,
            "sale_date": f"{past_sale_year}-{random.randint(1, 12):02d}-15",
            "historical_sale_price_gbp": round(property_val * random.uniform(0.78, 0.95), -2),
            "energy_rating_at_sale": energy_rating,
        })

        # Occasional completed retrofit for customer memory demonstration (~20% of properties)
        if random.random() < 0.20:
            hist_retro = random.choice(["roof_insulation", "double_glazing", "smart_thermostat"])
            retrofit_history_records.append({
                "customer_id": customer_id,
                "property_id": prop_id,
                "retrofit_id": hist_retro,
                "completion_date": f"{random.randint(2022, 2024)}-{random.randint(1, 12):02d}-01",
            })

    df_properties = pd.DataFrame(property_records)
    df_monthly = pd.DataFrame(monthly_records)
    df_sales = pd.DataFrame(sales_records)
    df_retrofit_hist = pd.DataFrame(retrofit_history_records)

    # Emissions factors table
    df_emissions = pd.DataFrame([
        {
            "fuel": "Electricity (Grid)",
            "kg_co2e_per_kwh": settings.ELECTRICITY_EMISSION_FACTOR_KG,
            "year": settings.EMISSION_FACTORS_YEAR,
            "source": settings.EMISSION_FACTORS_SOURCE,
        },
        {
            "fuel": "Natural Gas (Mains)",
            "kg_co2e_per_kwh": settings.GAS_EMISSION_FACTOR_KG,
            "year": settings.EMISSION_FACTORS_YEAR,
            "source": settings.EMISSION_FACTORS_SOURCE,
        },
    ])

    # Retrofit catalogue table
    catalogue_rows = []
    for r in RETROFIT_CATALOGUE.values():
        catalogue_rows.append({
            "retrofit_id": r.id,
            "name": r.name,
            "category": r.category,
            "indicative_impact": r.indicative_impact_description,
            "space_heating_reduction_pct": r.space_heating_reduction_pct,
            "grid_import_reduction_pct": r.grid_import_reduction_pct,
            "heat_pump_cop": r.heat_pump_cop,
            "cost_min_gbp": r.typical_cost_min_gbp,
            "cost_max_gbp": r.typical_cost_max_gbp,
            "cost_avg_gbp": r.typical_cost_avg_gbp,
            "priority_order": r.priority_order,
            "prerequisites": ",".join(r.prerequisite_ids),
            "documentation": r.source_documentation,
        })
    df_catalogue = pd.DataFrame(catalogue_rows)

    # --- Strict Group Split by Customer ID (Leakage-Free) ---
    unique_customers = list(df_properties["customer_id"].unique())
    random.shuffle(unique_customers)

    n_cust = len(unique_customers)
    n_test = int(n_cust * 0.20)
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

    # Save to disk
    df_properties.to_csv(os.path.join(output_dir, "all_properties.csv"), index=False)
    df_train.to_csv(os.path.join(output_dir, "train_properties.csv"), index=False)
    df_val.to_csv(os.path.join(output_dir, "val_properties.csv"), index=False)
    df_test.to_csv(os.path.join(output_dir, "test_properties.csv"), index=False)
    df_monthly.to_csv(os.path.join(output_dir, "monthly_energy.csv"), index=False)
    df_sales.to_csv(os.path.join(output_dir, "sales_history.csv"), index=False)
    df_retrofit_hist.to_csv(os.path.join(output_dir, "retrofit_history.csv"), index=False)
    df_emissions.to_csv(os.path.join(output_dir, "emissions_factors.csv"), index=False)
    df_catalogue.to_csv(os.path.join(output_dir, "retrofit_catalogue.csv"), index=False)

    # Manifest metadata
    manifest = {
        "dataset_name": "Lloyds UK Residential Synthetic Housing Stock",
        "generated_properties": len(df_properties),
        "unique_customers": n_cust,
        "splits": {
            "train": {"count": len(df_train), "customers": len(train_cust), "pct": round(len(df_train)/len(df_properties)*100, 1)},
            "validation": {"count": len(df_val), "customers": len(val_cust), "pct": round(len(df_val)/len(df_properties)*100, 1)},
            "test": {"count": len(df_test), "customers": len(test_cust), "pct": round(len(df_test)/len(df_properties)*100, 1)},
        },
        "leakage_verification": "Passed: Zero customer_id or property_id overlap between splits.",
        "distributions": {
            "epc_ratings": df_properties["energy_rating"].value_counts().to_dict(),
            "property_types": df_properties["property_type"].value_counts().to_dict(),
            "heating_systems": df_properties["heating"].value_counts().to_dict(),
            "mean_floor_area_m2": round(float(df_properties["floor_area_m2"].mean()), 1),
            "mean_baseline_electricity_kwh": round(float(df_properties["baseline_electricity_kwh"].mean()), 1),
            "mean_baseline_gas_kwh": round(float(df_properties["baseline_gas_kwh"].mean()), 1),
            "mean_green_home_score": round(float(df_properties["green_home_score"].mean()), 1),
            "poor_performing_pct": round(float(df_properties["is_poor_performing"].mean() * 100), 1),
        },
        "sources": [
            "English Housing Survey (EHS) 2022-2023",
            "National Energy Efficiency Data-Framework (NEED) 2023",
            "London Smart Meter Energy Consumption (2011-2014)",
            "HM Land Registry Price Paid Data 2024",
            "UK DESNZ / DEFRA GHG Conversion Factors 2024",
        ],
    }

    with open(os.path.join(output_dir, "data_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print("Synthetic dataset generated successfully!")
    print(f"- Total Properties: {len(df_properties)}")
    print(f"- Train split: {len(df_train)} ({manifest['splits']['train']['pct']}%)")
    print(f"- Validation split: {len(df_val)} ({manifest['splits']['validation']['pct']}%)")
    print(f"- Test split: {len(df_test)} ({manifest['splits']['test']['pct']}%)")
    print(f"- Manifest saved to: {output_dir}/data_manifest.json")
    return manifest


if __name__ == "__main__":
    generate_full_synthetic_dataset()
