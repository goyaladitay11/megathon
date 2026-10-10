"""
UK Residential Data Pipeline & Synthetic Dataset Generator
Lloyds Megathon X PS2: Green Home Score & Retrofit Recommendation Engine
"""

import os
import random
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from backend.app.schemas.property import PropertyInput, PropertySummary, MonthlyEnergyRecord


UK_REGIONS = [
    "London",
    "South East",
    "South West",
    "East of England",
    "West Midlands",
    "East Midlands",
    "North West",
    "Yorkshire and the Humber",
    "North East",
    "Wales",
    "Scotland",
]

PROPERTY_TYPES = ["detached", "semi_detached", "terraced", "flat"]
EPC_RATINGS = ["A", "B", "C", "D", "E", "F", "G"]
INSULATION_LEVELS = ["poor", "average", "good"]
HEATING_SYSTEMS = ["gas_boiler", "electric_resistive", "oil_boiler", "heat_pump"]
GLAZING_TYPES = ["single", "double", "triple"]
SOLAR_OPTIONS = ["none", "2kw", "4kw"]


def annualise_monthly_energy(
    monthly_records: Optional[List[MonthlyEnergyRecord]],
    direct_annual_elec: Optional[float] = None,
    direct_annual_gas: Optional[float] = None,
) -> Tuple[float, float, List[str]]:
    """
    Annualises partial monthly energy data consistently, flags coverage,
    and avoids treating missing records as zero.
    """
    flags: List[str] = []

    if monthly_records and len(monthly_records) > 0:
        valid_elec_months = [r.electricity_kwh for r in monthly_records if r.electricity_kwh is not None]
        valid_gas_months = [r.gas_kwh for r in monthly_records if r.gas_kwh is not None]

        elec_count = len(valid_elec_months)
        gas_count = len(valid_gas_months)

        if elec_count == 0:
            elec_annual = direct_annual_elec if direct_annual_elec is not None else 3500.0
            flags.append("Missing electricity meter data: defaulted to UK average benchmark (3,500 kWh/yr)")
        elif elec_count == 12:
            elec_annual = float(sum(valid_elec_months))
            flags.append("Full 12-month electricity meter coverage")
        else:
            # Consistent proportional annualisation
            elec_annual = float((sum(valid_elec_months) / elec_count) * 12.0)
            flags.append(f"Partial electricity coverage ({elec_count}/12 months) proportionally annualised")

        if gas_count == 0:
            gas_annual = direct_annual_gas if direct_annual_gas is not None else 12000.0
            flags.append("Missing gas meter data: defaulted to UK average benchmark (12,000 kWh/yr)")
        elif gas_count == 12:
            gas_annual = float(sum(valid_gas_months))
            flags.append("Full 12-month gas meter coverage")
        else:
            gas_annual = float((sum(valid_gas_months) / gas_count) * 12.0)
            flags.append(f"Partial gas coverage ({gas_count}/12 months) proportionally annualised")

        return elec_annual, gas_annual, flags

    # Direct annual inputs provided
    elec_annual = direct_annual_elec if (direct_annual_elec is not None and direct_annual_elec >= 0) else 3500.0
    gas_annual = direct_annual_gas if (direct_annual_gas is not None and direct_annual_gas >= 0) else 12000.0

    if direct_annual_elec is None:
        flags.append("Annual electricity consumption not specified: imputed with UK typical domestic profile (3,500 kWh/yr)")
    if direct_annual_gas is None:
        flags.append("Annual gas consumption not specified: imputed with UK typical domestic profile (12,000 kWh/yr)")

    return float(elec_annual), float(gas_annual), flags


def validate_and_summarize_property(prop: PropertyInput) -> PropertySummary:
    """
    Validates property inputs, checks for physical contradictions,
    and produces a standardized PropertySummary.
    """
    elec_kwh, gas_kwh, flags = annualise_monthly_energy(
        prop.monthly_records,
        prop.annual_electricity_kwh,
        prop.annual_gas_kwh,
    )

    # Contradiction check: heat pump property reporting huge gas consumption
    if prop.heating == "heat_pump" and gas_kwh > 2000.0:
        flags.append(
            f"Physical contradiction detected: Property specifies heat pump heating but reports {gas_kwh:.0f} kWh/yr gas. "
            "Residual gas attributed to cooking/secondary flame or dual fuel."
        )

    # Contradiction check: Gas boiler with zero gas consumption
    if prop.heating == "gas_boiler" and gas_kwh <= 50.0:
        flags.append(
            "Data anomaly: Gas boiler specified as primary heating but metered gas is near zero. "
            "Property may be unoccupied or miscategorized."
        )

    # Contradiction check: EPC A/B property with single glazing and poor insulation
    if prop.energy_rating in ["A", "B"] and (prop.glazing == "single" or prop.insulation == "poor"):
        flags.append(
            f"Contradictory rating: EPC band {prop.energy_rating} recorded despite {prop.glazing} glazing and {prop.insulation} insulation."
        )

    total_purchased = elec_kwh + gas_kwh
    floor_area = max(prop.floor_area_m2, 10.0)
    intensity = total_purchased / floor_area

    return PropertySummary(
        property_id=prop.property_id,
        customer_id=prop.customer_id,
        property_type=prop.property_type,
        age=prop.age,
        floor_area_m2=floor_area,
        region=prop.region,
        bedrooms=prop.bedrooms,
        energy_rating=prop.energy_rating,
        insulation=prop.insulation,
        heating=prop.heating,
        glazing=prop.glazing,
        solar=prop.solar,
        smart_controls=prop.smart_controls,
        current_property_value_gbp=prop.current_property_value_gbp,
        annual_electricity_kwh=round(elec_kwh, 1),
        annual_gas_kwh=round(gas_kwh, 1),
        total_purchased_energy_kwh=round(total_purchased, 1),
        energy_intensity_kwh_m2=round(intensity, 1),
        data_quality_flags=flags,
    )


def generate_synthetic_uk_dataset(
    num_properties: int = 500,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates plausible synthetic, explicitly documented UK residential property records,
    monthly energy consumption, and historical sales observations.
    
    Guarantees:
    - Seeded for exact reproducibility
    - Customer and property grouping maintained for leakage-free splitting
    - Reflects UK housing stock characteristics (English Housing Survey & NEED distributions)
    """
    random.seed(seed)
    np.random.seed(seed)

    property_rows = []
    monthly_rows = []
    sales_rows = []

    # UK seasonal monthly energy distribution factors (colder in winter, higher gas)
    # Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
    gas_monthly_weights = [0.18, 0.16, 0.13, 0.08, 0.05, 0.02, 0.01, 0.01, 0.03, 0.08, 0.11, 0.14]
    elec_monthly_weights = [0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.06, 0.06, 0.07, 0.09, 0.10, 0.11]

    # Normalize weights
    gas_monthly_weights = [w / sum(gas_monthly_weights) for w in gas_monthly_weights]
    elec_monthly_weights = [w / sum(elec_monthly_weights) for w in elec_monthly_weights]

    num_customers = int(num_properties * 0.85)  # Some customers own >1 property (landlords)
    customer_ids = [f"C{1000 + i}" for i in range(num_customers)]

    for i in range(1, num_properties + 1):
        prop_id = f"P{10000 + i}"
        customer_id = random.choice(customer_ids)

        # Correlated property characteristics based on UK building eras
        year_built = random.choice([
            random.randint(1890, 1929), # Victorian/Edwardian
            random.randint(1930, 1966), # Inter-war / post-war
            random.randint(1967, 1982), # 70s
            random.randint(1983, 2002), # Modern
            random.randint(2003, 2022), # Recent
        ])

        prop_type = random.choices(
            PROPERTY_TYPES,
            weights=[0.24, 0.32, 0.28, 0.16],  # UK distribution approx
            k=1
        )[0]

        bedrooms = random.choices([1, 2, 3, 4, 5], weights=[0.10, 0.30, 0.40, 0.15, 0.05])[0]

        # Floor area based on bedrooms & type
        base_area = {1: 48.0, 2: 70.0, 3: 95.0, 4: 135.0, 5: 180.0}[bedrooms]
        type_multiplier = {"flat": 0.85, "terraced": 0.95, "semi_detached": 1.05, "detached": 1.25}[prop_type]
        floor_area = round(float(np.random.normal(base_area * type_multiplier, 8.0)), 1)
        floor_area = max(35.0, min(380.0, floor_area))

        region = random.choices(
            UK_REGIONS,
            weights=[0.15, 0.18, 0.10, 0.10, 0.10, 0.08, 0.11, 0.08, 0.04, 0.03, 0.03],
            k=1
        )[0]

        # Older homes have worse insulation and single glazing unless upgraded
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

        # Correlated EPC Rating
        score_hint = 0
        score_hint += {"poor": 15, "average": 45, "good": 80}[insulation]
        score_hint += {"single": 10, "double": 45, "triple": 70}[glazing]
        score_hint += {"gas_boiler": 40, "electric_resistive": 35, "oil_boiler": 25, "heat_pump": 80}[heating]
        score_hint += 15 if smart_controls else 0
        score_hint += 20 if solar != "none" else 0

        if score_hint >= 220:
            energy_rating = random.choices(["A", "B"], weights=[0.3, 0.7])[0]
        elif score_hint >= 170:
            energy_rating = random.choices(["B", "C"], weights=[0.3, 0.7])[0]
        elif score_hint >= 130:
            energy_rating = random.choices(["C", "D"], weights=[0.4, 0.6])[0]
        elif score_hint >= 90:
            energy_rating = random.choices(["D", "E"], weights=[0.4, 0.6])[0]
        elif score_hint >= 60:
            energy_rating = random.choices(["E", "F"], weights=[0.5, 0.5])[0]
        else:
            energy_rating = random.choices(["F", "G"], weights=[0.4, 0.6])[0]

        # Realistic Energy Consumption (NEED benchmarks)
        # Base electricity: lights, appliances ~2,200 to 4,500 kWh/yr depending on area & bedrooms
        base_elec = 1800.0 + (bedrooms * 500.0) + (floor_area * 8.0)
        if solar == "2kw":
            base_elec = max(1000.0, base_elec - 1600.0)
        elif solar == "4kw":
            base_elec = max(800.0, base_elec - 3000.0)

        # Space heating and water heating demand
        heat_loss_factor = {"poor": 1.45, "average": 1.0, "good": 0.65}[insulation]
        glazing_factor = {"single": 1.25, "double": 1.0, "triple": 0.85}[glazing]
        control_factor = 0.92 if smart_controls else 1.0

        space_heating_need_kwh = floor_area * 115.0 * heat_loss_factor * glazing_factor * control_factor
        water_heating_kwh = 1800.0 + (bedrooms * 400.0)

        if heating == "gas_boiler":
            # Gas boiler efficiency ~85%
            annual_gas = (space_heating_need_kwh + water_heating_kwh) / 0.85
            annual_elec = base_elec
        elif heating == "heat_pump":
            # Heat pump SPF ~3.0, replaces gas
            annual_gas = 0.0  # Fully electrified
            heat_delivered_kwh = space_heating_need_kwh + water_heating_kwh
            heat_pump_elec_kwh = heat_delivered_kwh / 3.0
            annual_elec = base_elec + heat_pump_elec_kwh
        elif heating == "electric_resistive":
            annual_gas = 0.0
            annual_elec = base_elec + space_heating_need_kwh + water_heating_kwh
        else:  # oil boiler
            annual_gas = (space_heating_need_kwh + water_heating_kwh) / 0.80
            annual_elec = base_elec

        # Add Gaussian noise
        annual_elec = max(800.0, float(np.random.normal(annual_elec, annual_elec * 0.07)))
        annual_gas = max(0.0, float(np.random.normal(annual_gas, annual_gas * 0.08)))

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

        # Energy premium in valuation
        epc_premium = {"A": 1.10, "B": 1.06, "C": 1.02, "D": 1.00, "E": 0.96, "F": 0.92, "G": 0.88}[energy_rating]
        property_val = round(floor_area * regional_price_m2 * epc_premium * random.uniform(0.95, 1.05), -2)

        property_rows.append({
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
            "annual_electricity_kwh": round(annual_elec, 1),
            "annual_gas_kwh": round(annual_gas, 1),
            "current_property_value_gbp": property_val,
        })

        # Generate monthly energy records
        for m in range(1, 13):
            monthly_rows.append({
                "property_id": prop_id,
                "month": m,
                "electricity_kwh": round(annual_elec * elec_monthly_weights[m - 1] * random.uniform(0.96, 1.04), 1),
                "gas_kwh": round(annual_gas * gas_monthly_weights[m - 1] * random.uniform(0.95, 1.05), 1),
            })

        # Historical sales observations
        sales_rows.append({
            "property_id": prop_id,
            "sale_date": f"{random.randint(2018, 2023)}-{random.randint(1, 12):02d}-15",
            "sale_price_gbp": round(property_val * random.uniform(0.80, 0.98), -2),
            "energy_rating_at_sale": energy_rating,
        })

    df_properties = pd.DataFrame(property_rows)
    df_monthly = pd.DataFrame(monthly_rows)
    df_sales = pd.DataFrame(sales_rows)

    return df_properties, df_monthly, df_sales


def split_dataset_by_customer_and_property(
    df_properties: pd.DataFrame,
    test_size: float = 0.20,
    val_size: float = 0.15,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits property data strictly by customer_id (group split) to prevent leakage
    across multiple properties owned by the same customer.
    """
    random.seed(seed)
    unique_customers = list(df_properties["customer_id"].unique())
    random.shuffle(unique_customers)

    n_cust = len(unique_customers)
    n_test = int(n_cust * test_size)
    n_val = int(n_cust * val_size)

    test_cust = set(unique_customers[:n_test])
    val_cust = set(unique_customers[n_test : n_test + n_val])
    train_cust = set(unique_customers[n_test + n_val :])

    df_train = df_properties[df_properties["customer_id"].isin(train_cust)].copy()
    df_val = df_properties[df_properties["customer_id"].isin(val_cust)].copy()
    df_test = df_properties[df_properties["customer_id"].isin(test_cust)].copy()

    # Integrity verification: Zero customer or property overlap
    assert len(set(df_train["property_id"]).intersection(set(df_val["property_id"]))) == 0
    assert len(set(df_train["property_id"]).intersection(set(df_test["property_id"]))) == 0
    assert len(set(df_val["property_id"]).intersection(set(df_test["property_id"]))) == 0

    return df_train, df_val, df_test
