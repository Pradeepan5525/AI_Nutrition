# Operational Telemetry: Data & Prediction Drift Report

- **Baseline Population Sample:** 2,111
- **Inference Request Batch:** 400
- **System Drift Status:** **`WARNING_MONITOR`**
- **Features with Severe Drift (PSI ≥ 0.25):** 0
- **Features with Moderate Drift (0.10 ≤ PSI < 0.25):** 1

## Feature Distribution Stability (PSI & KS-Test)

| Feature | Type | PSI | KS-Stat / P-Value | Drift Classification |
| :--- | :--- | :--- | :--- | :--- |
| `Age` | numeric | 0.2106 | 0.1361 (p=0.0) | ⚠️ Warning |
| `FCVC` | numeric | 0.0213 | 0.0432 (p=0.5393) | ✅ Stable |
| `NCP` | numeric | 0.0092 | 0.024 (p=0.9875) | ✅ Stable |
| `CH2O` | numeric | 0.0228 | 0.0484 (p=0.3952) | ✅ Stable |
| `FAF` | numeric | 0.0170 | 0.0297 (p=0.9175) | ✅ Stable |
| `TUE` | numeric | 0.0250 | 0.0528 (p=0.2938) | ✅ Stable |
| `Gender` | categorical | 0.0001 | N/A (discrete) | ✅ Stable |
| `family_history_with_overweight` | categorical | 0.0000 | N/A (discrete) | ✅ Stable |
| `FAVC` | categorical | 0.0008 | N/A (discrete) | ✅ Stable |
| `CAEC` | categorical | 0.0102 | N/A (discrete) | ✅ Stable |
| `SMOKE` | categorical | 0.0043 | N/A (discrete) | ✅ Stable |
| `SCC` | categorical | 0.0005 | N/A (discrete) | ✅ Stable |
| `CALC` | categorical | 0.0045 | N/A (discrete) | ✅ Stable |
| `MTRANS` | categorical | 0.0123 | N/A (discrete) | ✅ Stable |

## Output Prediction Distribution Shift

- **Prediction Drift PSI:** `0.0024` (STABLE)

| Risk Tier | Baseline Share (%) | Operational Batch Share (%) | Shift (%) |
| :--- | :--- | :--- | :--- |
| **Healthy** | 15.7% | 17.0% | +1.3% |
| **Obese** | 44.8% | 45.5% | +0.7% |
| **Overweight** | 26.9% | 25.2% | -1.7% |
| **Underweight** | 12.6% | 12.2% | -0.4% |

> Standard threshold reference: PSI < 0.10 indicates stable distribution; PSI ≥ 0.25 triggers automated pipeline retraining alert.