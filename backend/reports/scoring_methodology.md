# Green Home Scoring Methodology
**Lloyds Megathon X — Problem Statement 2 (Section 2 & Phase 4)**

---

## 1. Mathematical Formulation

Each domestic property receives an integer Green Home Score $S \in [0, 100]$ computed as a strictly deterministic weighted sum:

$$S = \text{round}\left( \sum_{k=1}^{7} w_k \cdot s_k \right)$$

where:
- $w_k$ are fixed official fractions satisfying $\sum_{k=1}^{7} w_k = 1.00$.
- $s_k \in [0, 100]$ are documented monotonic component sub-scores.

---

## 2. Official Fixed Component Weights

| Component $k$ | Weight $w_k$ | Description & Inputs |
| :--- | :---: | :--- |
| **Energy Efficiency** | **25%** ($0.25$) | Statutory Energy Performance Certificate (EPC) Band (`A` to `G`) |
| **Consumption Intensity** | **20%** ($0.20$) | Annualised purchased energy per square metre ($\text{kWh} / \text{m}^2 / \text{year}$) |
| **Insulation** | **15%** ($0.15$) | Roof, loft, and wall insulation quality (`poor`, `average`, `good`) |
| **Heating System** | **15%** ($0.15$) | Primary heat generation technology (`heat_pump`, `electric_resistive`, `gas_boiler`, `oil_boiler`) |
| **Windows & Glazing** | **10%** ($0.10$) | Window thermal barrier (`triple`, `double`, `single`) |
| **Renewable Energy** | **10%** ($0.10$) | On-site solar photovoltaic generation (`4kw`, `2kw`, `none`) |
| **Smart Controls** | **5%** ($0.05$) | Automated zoning, smart thermostat, and setback capability |
| **Total** | **100%** ($1.00$) | Strictly normalized |

---

## 3. Documented Monotonic Sub-Score Mappings

### 3.1 Energy Efficiency (25% Weight)
Calibrated to the UK Standard Assessment Procedure (SAP) rating bands:
- **Band A (SAP 92–100)**: Sub-score **100.0**
- **Band B (SAP 81–91)**: Sub-score **85.0**
- **Band C (SAP 69–80)**: Sub-score **70.0** (UK 2035 Clean Growth Target)
- **Band D (SAP 55–68)**: Sub-score **55.0** (UK Median Average)
- **Band E (SAP 39–54)**: Sub-score **40.0**
- **Band F (SAP 21–38)**: Sub-score **20.0**
- **Band G (SAP 1–20)**: Sub-score **0.0**

### 3.2 Energy Consumption Intensity (20% Weight)
Calibrated against UK Ofgem Typical Domestic Consumption Values (TDCV) and NEED benchmarks. Computed as $\text{Intensity} = \frac{E_{\text{elec}} + E_{\text{gas}}}{\text{Floor Area } (\text{m}^2)}$.
Strict continuous piecewise interpolation guarantees **strict monotonicity** (lower consumption intensity never yields a lower sub-score):
- $\le 50.0\text{ kWh/m}^2$: $100.0 \to 90.0$ (Exemplary low-energy performance)
- $50.0 - 120.0\text{ kWh/m}^2$: $90.0 \to 75.0$ (High efficiency)
- $120.0 - 180.0\text{ kWh/m}^2$: $75.0 \to 55.0$ (UK typical dual-fuel average ~160 kWh/m²)
- $180.0 - 260.0\text{ kWh/m}^2$: $55.0 \to 35.0$ (Elevated consumption)
- $260.0 - 360.0\text{ kWh/m}^2$: $35.0 \to 15.0$ (High energy escape)
- $> 360.0\text{ kWh/m}^2$: Floored smoothly to minimum $5.0$

### 3.3 Insulation (15% Weight)
- **Good**: **90.0** (Loft $\ge 270\text{mm}$, cavity/solid wall insulated)
- **Average**: **50.0** (Partial loft or uninsulated cavity; typical UK 1970s stock)
- **Poor**: **15.0** (Uninsulated solid walls, uninsulated loft; heavy conductive loss)

### 3.4 Heating System (15% Weight)
- **Heat Pump**: **95.0** (Zero direct fossil combustion, high seasonal COP ~3.0)
- **Electric Resistive**: **45.0** (Direct resistive heaters; decarbonised grid source, but 1:1 COP and high running cost)
- **Mains Gas Boiler**: **40.0** (Scope 1 fossil fuel combustion)
- **Oil Boiler**: **15.0** (Heavy fossil emissions and localized air pollutants)

### 3.5 Windows and Glazing (10% Weight)
- **Triple Glazing**: **95.0** ($U < 0.8\text{ W/m}^2\text{K}$)
- **Double Glazing**: **75.0** (Standard modern building regulations)
- **Single Glazing**: **20.0** (Severe conductive window heat loss and draughts)

### 3.6 Renewable Energy (10% Weight)
- **4kW+ Solar PV**: **95.0** (Offsets 25–35% of electricity imports)
- **2kW Solar PV**: **60.0** (Offsets baseline baseload)
- **None**: **5.0** (100% reliant on grid power)

### 3.7 Smart Controls (5% Weight)
- **Enabled**: **95.0** (Automated scheduling, occupancy setback, zoning)
- **Disabled**: **15.0** (Manual mechanical thermostat without scheduling)

---

## 4. Score Classification Bands

| Score Range | Classification Band | Poor Performing Flag |
| :---: | :--- | :---: |
| **80 – 100** | **Highly efficient** | False |
| **65 – 79** | **Good** | False |
| **50 – 64** | **Moderate** | False |
| **30 – 49** | **Poor** | **True** |
| **0 – 29** | **Very poor** | **True** |
