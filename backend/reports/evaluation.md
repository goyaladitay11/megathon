# Machine Learning Evaluation Report
**Lloyds Megathon X — Problem Statement 2 (Singularity)**
*Generated: 2026-10-10T19:16:36.771958*

---

## 1. Executive Summary & Data Governance
- **Dataset**: Lloyds UK Residential Housing Stock Dataset (5,000 Properties)
- **Splits**: Train = 3509 (70.2%), Val = 753 (15.1%), Test = 738 (14.8%)
- **Data Governance**: Strict customer-level group partitioning. Zero customer ID or property ID overlap between train, validation, and test splits.
- **Synthetic Disclosure**: All properties and transaction records were algorithmically synthesized with physical constraints and distributions calibrated to English Housing Survey, NEED, and Land Registry statistics.

---

## 2. Model Evaluation on Untouched Held-Out Test Set (738 Properties)

### 2.1 Electricity Consumption Model (`annual_electricity_kwh`)
- **Selected Architecture**: `HistGradientBoosting`

| Metric | Dummy Baseline (Median) | Selected Model (`HistGradientBoosting`) | Improvement vs. Baseline |
| :--- | :---: | :---: | :---: |
| **RMSE** (kWh/yr) | 4,700.97 | **596.91** | 87.3% reduction |
| **MAE** (kWh/yr) | 2,261.06 | **323.47** | 85.7% reduction |
| **R² Score** | -0.0851 | **0.9825** | Substantial positive variance explained |
| **WAPE (%)** | 43.38% | **6.21%** | Lower percentage error |

---

### 2.2 Natural Gas Consumption Model (`annual_gas_kwh`)
- **Selected Architecture**: `HistGradientBoosting`

| Metric | Dummy Baseline (Median) | Selected Model (`HistGradientBoosting`) | Improvement vs. Baseline |
| :--- | :---: | :---: | :---: |
| **RMSE** (kWh/yr) | 9,549.58 | **1,377.22** | 85.6% reduction |
| **MAE** (kWh/yr) | 7,357.27 | **893.69** | 87.9% reduction |
| **R² Score** | -0.0002 | **0.9792** | Near-perfect space heating capture |
| **WAPE (%)** | 52.92% | **6.43%** | Lower percentage error |

---

### 2.3 Property Valuation Model (`historical_sale_price_gbp`)
- **Selected Architecture**: `HistGradientBoosting`

| Metric | Dummy Baseline (Median) | Selected Model (`HistGradientBoosting`) | Improvement vs. Baseline |
| :--- | :---: | :---: | :---: |
| **RMSE** (£ GBP) | £176,527.29 | **£25,266.31** | 85.7% reduction |
| **MAE** (£ GBP) | £123,789.57 | **£17,130.99** | 86.2% reduction |
| **R² Score** | -0.0800 | **0.9779** | Strong regional hedonic fit |
| **WAPE (%)** | 40.33% | **5.58%** | High pricing precision |

- **Empirical Residual Uncertainty Interval (P10 to P90)**:
  `[£-29,222.71, £23,862.88]`

---

## 3. Candidate Model Validation Performance Comparison

### Electricity Validation (753 properties)
- **Dummy (Median)**: RMSE = 5,262.82 kWh/yr | MAE = 2,451.41 kWh/yr | R² = -0.0869 | WAPE = 45.53%
- **Ridge Regression**: RMSE = 1,832.24 kWh/yr | MAE = 899.17 kWh/yr | R² = 0.8683 | WAPE = 16.70%
- **Random Forest**: RMSE = 717.94 kWh/yr | MAE = 344.00 kWh/yr | R² = 0.9798 | WAPE = 6.39%
- **HistGradientBoosting**: RMSE = 685.27 kWh/yr | MAE = 333.49 kWh/yr | R² = 0.9816 | WAPE = 6.19%

### Gas Validation (753 properties)
- **Dummy (Median)**: RMSE = 9,738.07 kWh/yr | MAE = 7,374.21 kWh/yr | R² = -0.0000 | WAPE = 52.45%
- **Ridge Regression**: RMSE = 3,424.77 kWh/yr | MAE = 2,300.56 kWh/yr | R² = 0.8763 | WAPE = 16.36%
- **Random Forest**: RMSE = 1,553.98 kWh/yr | MAE = 984.47 kWh/yr | R² = 0.9745 | WAPE = 7.00%
- **HistGradientBoosting**: RMSE = 1,484.16 kWh/yr | MAE = 987.54 kWh/yr | R² = 0.9768 | WAPE = 7.02%

### Property Valuation Validation (753 properties)
- **Dummy (Median)**: RMSE = £188,154.30 | MAE = £126,550.20 | R² = -0.0720 | WAPE = 41.13%
- **Ridge Regression**: RMSE = £55,187.24 | MAE = £35,832.99 | R² = 0.9078 | WAPE = 11.65%
- **Random Forest**: RMSE = £25,515.62 | MAE = £17,892.43 | R² = 0.9803 | WAPE = 5.82%
- **HistGradientBoosting**: RMSE = £24,248.02 | MAE = £16,997.35 | R² = 0.9822 | WAPE = 5.52%

---

## 4. Responsible AI & Causal Limitations
1. **Observational Bounds**: The property valuation model captures hedonic equilibrium relationships. It does NOT claim that installing retrofits causes a guaranteed market appreciation.
2. **Deterministic Governance**: Green Home Score, per-fuel savings accounting, and carbon factors remain strictly deterministic and unalterable by machine learning drift.
