# Engineering and Economic Assumptions
**Lloyds Megathon X — Problem Statement 2 (Section 4, 5, 6, 7 & Phase 15)**

---

## 1. Building Physics and Thermal Disaggregation
- **Space Heating vs. Domestic Hot Water Disaggregation**:
  - In UK homes with gas boilers, approximately **82% of natural gas** is consumed for space heating, and **18%** is consumed for domestic hot water and cooking.
  - Standard gas boiler seasonal efficiency is modeled at **85%** (typical condensing boiler average).
- **Sequential Thermal Improvements**:
  - Insulation, glazing, and smart thermostats reduce space heating demand sequentially.
  - Loft/roof insulation: **15% reduction** in remaining space heating load.
  - Double glazing: **10% reduction** in remaining space heating load.
  - Smart thermostat: **7.5% reduction** in remaining space heating load.
- **Air Source Heat Pump (ASHP)**:
  - Modeled with a Seasonal Performance Factor (SPF / seasonal COP) of **3.0**.
  - Completely displaces space heating and water heating gas ($E_{\text{gas,after}} = 0$).
  - Required electricity imports increase by:
    $$\Delta E_{\text{elec,hp}} = \frac{\text{Remaining Space Heat} + \text{Delivered Water Heat}}{3.0}$$
- **Rooftop Solar PV Array**:
  - A 3.5–4.0 kWp array achieves a **28% reduction** in purchased grid electricity imports.
  - Grid imports are strictly floored at 0 kWh/yr. Solar self-consumption does not alter underlying household appliance load.

---

## 2. Official Emissions Factors
- Sourced from UK Government GHG Conversion Factors for Company Reporting 2024:
  - **Grid Electricity**: $0.20707\text{ kg CO}_2\text{e} / \text{kWh}$ (Scope 2)
  - **Natural Gas Mains**: $0.18254\text{ kg CO}_2\text{e} / \text{kWh}$ (Scope 1)
- Fuel-switching dynamics are preserved:
  - Increases in electricity consumption produce negative carbon savings ($\Delta E_{\text{elec}} < 0$).
  - Displaced gas consumption produces positive carbon savings ($\Delta E_{\text{gas}} > 0$).
  - Net carbon reduction:
    $$\Delta C = \Delta E_{\text{elec}} \cdot 0.20707 + \Delta E_{\text{gas}} \cdot 0.18254$$

---

## 3. Indicative Property Valuation Model
- Observational hedonic analysis holding structural area, bedroom count, location, and market era constant.
- Upgrading EPC ratings and installing renewable generation yields an **indicative percentage range** (e.g., $+2.5\%$ to $+6.0\%$), rather than a deterministic single figure.
- **Explicit Non-Causal Disclaimer**:
  - Market correlations do not prove that retrofits causally guarantee increased property sale prices.
  - Actual property value depends on local market liquidity, neighborhood condition, mortgage interest rates, and buyer preferences.
