import pandas as pd
import numpy as np

def load_demand_csv(path: str) -> pd.DataFrame:
    """Expect columns: time_s, airflow_demand_cfm"""
    df = pd.read_csv(path)
    if "time_s" not in df.columns or "airflow_demand_cfm" not in df.columns:
        raise ValueError("CSV must have columns: time_s, airflow_demand_cfm")
    return df.sort_values("time_s").reset_index(drop=True)

def build_profiles(horizon_s=3600.0, dt_s=1.0,
                   Q_base_cfm=280.0, Q_amp_cfm=60.0,  # demand ~ base ± amp
                   foul_start=0.15, foul_end=0.85, k_clean=2.0e-4, k_fouled=4.0e-4):
    """
    Returns t, Q_demand(t), k(t) over [0, horizon].
    - Demand: smooth sinusoid around Q_base with amplitude Q_amp.
    - Fouling: k ramps linearly from clean to fouled between [foul_start, foul_end] * horizon.
    """
    t = np.arange(0.0, horizon_s + 1e-9, dt_s)
    # Demand: 1 full period over the horizon (nice visual)
    Q_dem = Q_base_cfm + Q_amp_cfm * np.sin(2*np.pi * t / horizon_s)

    # k(t): piecewise linear ramp
    k = np.full_like(t, k_clean, dtype=float)
    t0 = foul_start * horizon_s
    t1 = foul_end   * horizon_s
    ramp_mask = (t >= t0) & (t <= t1)
    k[ramp_mask] = k_clean + (k_fouled - k_clean) * (t[ramp_mask] - t0) / max(t1 - t0, 1e-9)
    k[t > t1] = k_fouled
    return t, Q_dem, k