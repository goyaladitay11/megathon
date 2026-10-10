"""
Unit Tests for Sequential Physical Retrofit Interactions and Fuel Switching
"""

import pytest
from backend.src.schemas import PropertyData
from backend.src.retrofit_engine import simulate_retrofit


def test_heat_pump_fuel_switching_behaviour():
    prop = PropertyData(
        property_id="P_GAS",
        property_type="semi_detached",
        property_age=1968,
        floor_area_m2=100.0,
        bedrooms=3,
        energy_rating="D",
        heating_system="gas_boiler",
        insulation_type="average",
        glazing_type="double",
        solar_installed="none",
        smart_controls=False,
        region="West Midlands",
        current_property_value=275000.0,
        annual_electricity_kwh=3400.0,
        annual_gas_kwh=13000.0,
    )
    res = simulate_retrofit(prop, ["heat_pump"])

    # 1. Gas consumption drops to zero
    assert res.after_gas_kwh == 0.0
    assert res.gas_saving_kwh == 13000.0

    # 2. Electricity consumption INCREASES
    assert res.after_electricity_kwh > res.baseline_electricity_kwh
    assert res.electricity_saving_kwh < 0.0  # Reported as negative saving!

    # 3. Net purchased energy decreases (because SPF is 3.0 vs boiler 0.85)
    assert res.net_purchased_energy_saving_kwh > 0.0


def test_sequential_interactions_non_additive():
    prop = PropertyData(
        property_id="P_MULTI",
        property_type="detached",
        property_age=1955,
        floor_area_m2=130.0,
        bedrooms=4,
        energy_rating="E",
        heating_system="gas_boiler",
        insulation_type="poor",
        glazing_type="single",
        solar_installed="none",
        smart_controls=False,
        region="Yorkshire and the Humber",
        current_property_value=320000.0,
        annual_electricity_kwh=4200.0,
        annual_gas_kwh=18000.0,
    )
    # Standalone simulations
    sim_ins = simulate_retrofit(prop, ["roof_insulation"])
    sim_glaz = simulate_retrofit(prop, ["double_glazing"])
    sim_hp = simulate_retrofit(prop, ["heat_pump"])

    standalone_sum = (
        sim_ins.net_purchased_energy_saving_kwh
        + sim_glaz.net_purchased_energy_saving_kwh
        + sim_hp.net_purchased_energy_saving_kwh
    )

    # Interactive package simulation
    sim_package = simulate_retrofit(prop, ["roof_insulation", "double_glazing", "heat_pump"])

    # Physical interaction guarantee: package total differs from naive sum
    assert sim_package.net_purchased_energy_saving_kwh != standalone_sum
