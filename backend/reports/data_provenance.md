# Data Provenance and Integrity Documentation
**Lloyds Megathon X — Problem Statement 2: Green Home Score & Retrofit Recommendation Engine**

---

## 1. Overview and Provenance
To satisfy the evaluation standards of Lloyds PS2 without using proprietary customer personal data, this project employs a **physically-anchored, empirically-calibrated synthetic dataset** of 5,000 UK residential properties.

All distributions, thermal characteristics, seasonal weights, regional price levels, and emissions factors are calibrated directly against official UK public benchmarks.

| Source Entity | Benchmark / Reference Document | Governing Agency | Licence / Availability |
| :--- | :--- | :--- | :--- |
| **Housing Stock Characteristics** | English Housing Survey (EHS) 2022–2023 | Department for Levelling Up, Housing and Communities (DLUHC) | Open Government Licence v3.0 |
| **Energy Consumption Profiles** | National Energy Efficiency Data-Framework (NEED) 2023 | Department for Energy Security and Net Zero (DESNZ) | Open Government Licence v3.0 |
| **Seasonal Energy Profiles** | London Smart Meter Energy Consumption Dataset (2011–2014) | UK Data Service / UK Power Networks | Creative Commons / OGL |
| **Property Valuation Levels** | HM Land Registry Price Paid Data 2024 | HM Land Registry | Open Government Licence v3.0 |
| **GHG Conversion Factors** | UK Government GHG Conversion Factors for Company Reporting 2024 | DESNZ / DEFRA | Open Government Licence v3.0 |

---

## 2. Dataset Entities and Schema

The synthetic dataset generates 6 relational entities:

### 2.1 Properties (`properties.csv`)
- `property_id`: Unique identifier (e.g., `P10001` to `P15000`).
- `customer_id`: Owner identifier (e.g., `C1001` to `C4999`), modeling single-property owners and multi-property landlords.
- `property_type`: `detached` (24%), `semi_detached` (32%), `terraced` (28%), `flat` (16%).
- `property_age`: Year of construction (1890–2022), segmented by UK building eras.
- `floor_area_m2`: Usable floor area in m² (35.0 m² to 360.0 m²).
- `bedrooms`: Number of bedrooms (1 to 5).
- `energy_rating`: Official EPC Band (`A` through `G`).
- `heating_system`: `gas_boiler`, `heat_pump`, `electric_resistive`, `oil_boiler`.
- `insulation_type`: `poor`, `average`, `good`.
- `glazing_type`: `single`, `double`, `triple`.
- `solar_installed`: `none`, `2kw`, `4kw`.
- `smart_controls`: Boolean flag.
- `region`: 11 UK regions (London, South East, West Midlands, North West, Wales, Scotland, etc.).
- `current_property_value`: Estimated baseline market valuation in GBP (£).
- `annual_electricity_kwh`: Annual grid electricity consumption in kWh/year.
- `annual_gas_kwh`: Annual natural gas consumption in kWh/year.

### 2.2 Monthly Energy Usage (`energy_usage.csv`)
- 12 monthly observations per property with seasonal weightings:
  - Natural gas heating demand concentrated in winter months (Jan 18%, Feb 16%, Dec 14%, Jul 1%).
  - Electricity demand reflects consistent baseload with winter lighting/appliance uptick.

### 2.3 Historical Sales Transactions (`sales_history.csv`)
- Past recorded sale transactions (2017–2023) with `historical_sale_price_gbp` and `energy_rating_at_sale`.
- **Methodological distinction**: Historical sale prices are held strictly distinct from the baseline valuation estimate.

### 2.4 Retrofit History (`retrofit_history.csv`)
- Records completed retrofits and installation dates for a subset of customers to support persistent customer memory.

### 2.5 Emissions Factors (`factors/emissions_factors.csv`)
- UK DESNZ / DEFRA 2024 official conversion factors:
  - Electricity: **0.20707 kg CO₂e / kWh** (Scope 2, Grid average)
  - Natural gas: **0.18254 kg CO₂e / kWh** (Scope 1, Gross calorific value)

### 2.6 Reference Ground Truth Labels (`reference_labels.csv`)
- Generated using the interaction-aware physics simulator and deterministic scoring engine:
  - `green_home_score`, `classification`, `is_poor_performing`.
  - `post_retrofit_electricity_kwh`, `post_retrofit_gas_kwh`, `post_retrofit_purchased_kwh`.
  - `electricity_saving_kwh`, `gas_saving_kwh`, `net_purchased_energy_saving_kwh`.
  - `improvement_potential_pct`, `net_carbon_reduction_kg`, `net_carbon_reduction_tonnes`.

---

## 3. Data Leakage Prevention and Splitting Protocol

1. **Customer-Grouped Split**:
   - Total properties: 5,000.
   - Unique customers: 4,000.
   - **Training Set**: 3,509 properties (70.2%) across 2,800 customers.
   - **Validation Set**: 753 properties (15.1%) across 600 customers.
   - **Held-Out Test Set**: 738 properties (14.8%) across 600 customers.
2. **Zero Overlap Guarantee**:
   - `len(train_customers ∩ val_customers) == 0`
   - `len(train_customers ∩ test_customers) == 0`
   - `len(val_customers ∩ test_customers) == 0`
   - Properties owned by the same customer never span multiple splits.
3. **Preprocessing Isolation**:
   - All transformations, standard scalers, and encoders are fit strictly on the training partition and evaluated out-of-fold.

---

## 4. Limitations and Synthetic Disclosure
- All data records in `data/synthetic/` and `data/processed/` are algorithmically synthesized.
- Evaluation metrics against reference labels measure agreement with the engineering simulation and labelling rules, rather than empirical observational certainty.
