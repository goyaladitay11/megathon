"""
Unit Tests for Deterministic Carbon Engine and Fuel Switching
"""

import pytest
from backend.src.carbon_engine import calculate_carbon, DEFAULT_EF_ELECTRICITY, DEFAULT_EF_GAS


def test_standard_gas_and_electricity_savings():
    baseline = {"electricity_kwh": 4000.0, "gas_kwh": 14000.0}
    scenario = {"electricity_kwh": 3000.0, "gas_kwh": 10000.0}

    # Delta elec = +1000, Delta gas = +4000
    res = calculate_carbon(baseline, scenario)
    expected_elec_kg = 1000.0 * DEFAULT_EF_ELECTRICITY
    expected_gas_kg = 4000.0 * DEFAULT_EF_GAS
    expected_net_kg = expected_elec_kg + expected_gas_kg

    assert abs(res.electricity_carbon_saving_kg - round(expected_elec_kg, 1)) < 0.2
    assert abs(res.gas_carbon_saving_kg - round(expected_gas_kg, 1)) < 0.2
    assert abs(res.net_carbon_reduction_kg - round(expected_net_kg, 1)) < 0.2
    assert res.net_carbon_reduction_tonnes > 0.0


def test_heat_pump_fuel_switch_carbon_calculation():
    # Heat pump scenario: electricity increases from 3500 to 5200, gas drops from 12000 to 0
    baseline = {"electricity_kwh": 3500.0, "gas_kwh": 12000.0}
    scenario = {"electricity_kwh": 5200.0, "gas_kwh": 0.0}

    res = calculate_carbon(baseline, scenario)

    # Electricity delta is negative (-1700 kWh)
    assert res.electricity_delta_kwh == -1700.0
    assert res.electricity_carbon_saving_kg < 0.0  # Increased emissions from grid power

    # Gas delta is positive (+12000 kWh)
    assert res.gas_delta_kwh == 12000.0
    assert res.gas_carbon_saving_kg > 0.0  # Displaced Scope 1 fossil gas

    # Net carbon must still be positive because heat pump COP is ~3.0
    assert res.net_carbon_reduction_kg > 0.0
    assert res.net_carbon_reduction_tonnes > 1.0
