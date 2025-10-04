# Fan Gait Switching — Result Sheet
_Generated: 2025-10-04 10:05_

## Summary
- Mode-switch reduces energy by **11%** vs fixed (this run).
- Variable reduces energy by **22%** vs fixed and achieves **100%** compliance.

## Key Results (1 hour)
| Strategy | Energy (Wh) | SFP (W/CFM) | Compliance | Delivered (CFM·h) | Shortfall (CFM·h) | Oversupply (CFM·h) | Savings vs Fixed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fixed | 28.4 | 0.085 | 6% | 332.4 | 3.0 | 33.0 | 0% |
| Mode-switch | 25.4 | 0.081 | 20% | 314.3 | 0.0 | 10.2 | 11% |
| Variable | 22.1 | 0.074 | 100% | 300.1 | 0.0 | 0.0 | 22% |

## Parameters
```json
{
  "fan": {
    "name": "DemoFan-200mm",
    "Q_bep_cfm": 300.0,
    "dP_bep_Pa": 120.0,
    "P_bep_W": 40.0,
    "N_ref_rpm": 1200.0
  },
  "system": {
    "k_clean": 6e-05,
    "k_fouled": 0.0004
  },
  "sim": {
    "dt_s": 1.0,
    "eps_cfm": 5,
    "fixed_rpm": 900.0,
    "horizon_s": 3600.0,
    "lambda_shortfall": 0.4,
    "rpm_bounds": [
      500.0,
      2000.0
    ],
    "show": false,
    "speeds_rpm": [
      700.0,
      800.0,
      900.0,
      1000.0
    ]
  }
}
```
