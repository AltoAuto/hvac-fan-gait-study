import numpy as np
import pandas as pd
from controller import (operating_point_Q, solve_rpm_for_Q,choose_mode_min_power)


def power_model_convex(fan, Q_cfm, rpm, P_bep_ref_W, N_ref_rpm,
                       idle_frac=0.22, gamma_free=2.0, x_bep=0.60):
    """
    Electrical power vs (Q, rpm): P_elec = P_bep(N) * [ p0 + b1*x + b2*x^2 ],
    with x = Q/Q_free(N); constraints P(x_bep)=P_bep(N) and P(1)=gamma_free*P_bep(N).
    """
    Q_free = max(fan.free_delivery_cfm(rpm), 1e-9)
    x = np.clip(Q_cfm / Q_free, 0.0, 1.0)

    p0 = float(idle_frac)
    denom = x_bep**2 - x_bep if abs(x_bep**2 - x_bep) > 1e-9 else -1e-3
    b2 = (1 - p0 - x_bep*(gamma_free - p0)) / denom
    b1 = (gamma_free - p0) - b2
    if b2 <= 0 or (b1 + 2*b2) <= 0:
        b2 = max(0.2*(gamma_free - 1), 1e-3)
        b1 = (gamma_free - p0) - b2

    P_bep_N = P_bep_ref_W * (rpm / N_ref_rpm) ** 3
    return P_bep_N * (p0 + b1 * x + b2 * x**2)

def run_time_sim(fan, t, Q_demand, k_t, *,
                 speeds_rpm, fixed_rpm,
                 P_bep_ref_W, N_ref_rpm,
                 idle_frac=0.22, gamma_free=2.0, x_bep=0.60,
                 rpm_bounds=None, eps_cfm=10.0, lambda_shortfall=0.3):
    """
    Simulate FIXED / MODES / VARIABLE strategies over time and compute fairness metrics.

    eps_cfm: demand tolerance (cfm) for compliance
    lambda_shortfall: penalty (Wh per CFM·h) for unmet demand, used in 'objective' score
    """

    rpm_lo, rpm_hi = rpm_bounds if rpm_bounds else (min(speeds_rpm), max(speeds_rpm))
    dt = np.median(np.diff(t)) if len(t) > 1 else 1.0
    T = len(t)

    # Storage
    data = {
        "t": t, "Qd": Q_demand, "k": k_t,
        "Q_fixed": np.zeros(T), "rpm_fixed": np.full(T, fixed_rpm, dtype=float), "P_fixed": np.zeros(T),
        "Q_modes": np.zeros(T), "rpm_modes": np.zeros(T), "P_modes": np.zeros(T),
        "Q_var":   np.zeros(T), "rpm_var":   np.zeros(T), "P_var":   np.zeros(T),
        # compliance & shortfall per step
        "c_fixed": np.zeros(T, dtype=bool), "c_modes": np.zeros(T, dtype=bool), "c_var": np.zeros(T, dtype=bool),
        "s_fixed": np.zeros(T), "s_modes": np.zeros(T), "s_var": np.zeros(T),"o_fixed": np.zeros(T),
        "o_modes": np.zeros(T), "o_var":   np.zeros(T),
    }

    for i in range(T):
        k = k_t[i]; Qd = Q_demand[i]

        # FIXED
        Qf = operating_point_Q(fan, k, fixed_rpm)
        Pf = power_model_convex(fan, Qf, fixed_rpm, P_bep_ref_W, N_ref_rpm, idle_frac, gamma_free, x_bep)
        data["Q_fixed"][i] = Qf; data["P_fixed"][i] = Pf
        data["c_fixed"][i] = (abs(Qf - Qd) <= eps_cfm)
        data["s_fixed"][i] = max(0.0, Qd - Qf - eps_cfm)
        data["o_fixed"][i] = max(0.0, Qf - Qd - eps_cfm)

        # MODES (discrete; lowest rpm that meets Qd within eps)
        rpm_m, Qm = choose_mode_min_power(
            fan, k, speeds_rpm, Qd, eps_cfm,
            power_fn=power_model_convex,
            P_bep_ref_W=P_bep_ref_W, N_ref_rpm=N_ref_rpm
        )
        Pm = power_model_convex(fan, Qm, rpm_m, P_bep_ref_W, N_ref_rpm, idle_frac, gamma_free, x_bep)
        data["rpm_modes"][i] = rpm_m; data["Q_modes"][i] = Qm; data["P_modes"][i] = Pm
        data["c_modes"][i] = (abs(Qm - Qd) <= eps_cfm)
        data["s_modes"][i] = max(0.0, Qd - Qm - eps_cfm)
        data["o_modes"][i] = max(0.0, Qm - Qd - eps_cfm)

        # VARIABLE (continuous; bisection to meet Qd within eps)
        rpm_v, Qv = solve_rpm_for_Q(fan, k, Qd, rpm_lo, rpm_hi, eps_cfm=eps_cfm)
        Pv = power_model_convex(fan, Qv, rpm_v, P_bep_ref_W, N_ref_rpm, idle_frac, gamma_free, x_bep)
        data["rpm_var"][i] = rpm_v; data["Q_var"][i] = Qv; data["P_var"][i] = Pv
        data["c_var"][i] = (abs(Qv - Qd) <= eps_cfm)
        data["s_var"][i] = max(0.0, Qd - Qv - eps_cfm)
        data["o_var"][i] = max(0.0, Qv - Qd - eps_cfm)

    df = pd.DataFrame(data)
    df.attrs["dt_s"] = dt

    # Aggregates (per strategy)
    def _agg(prefix):
        P = df[f"P_{prefix}"].to_numpy()
        Q = df[f"Q_{prefix}"].to_numpy()
        c = df[f"c_{prefix}"].to_numpy()
        s = df[f"s_{prefix}"].to_numpy()

        Wh = (P.sum() * dt) / 3600.0
        cfmh_delivered = (Q.sum() * dt) / 3600.0
        s = df[f"s_{prefix}"].to_numpy()
        o = df[f"o_{prefix}"].to_numpy()
        cfmh_shortfall = (s.sum() * dt) / 3600.0
        cfmh_oversupply = (o.sum() * dt) / 3600.0
        compliance_pct = 100.0 * (c.sum() / len(c))
        SFP_W_per_CFM = Wh / max(cfmh_delivered, 1e-9)  # Wh per CFM·h == W/CFM
        objective = Wh + lambda_shortfall * cfmh_shortfall  # penalize unmet demand

        return dict(Wh=Wh,
                    cfmh_delivered=cfmh_delivered,
                    cfmh_shortfall=cfmh_shortfall,
                    cfmh_oversupply=cfmh_oversupply,
                    compliance_pct=compliance_pct,
                    SFP=SFP_W_per_CFM,
                    objective=objective)

    metrics = {
        "fixed": _agg("fixed"),
        "modes": _agg("modes"),
        "var":   _agg("var"),
        "eps_cfm": eps_cfm, "lambda_shortfall": lambda_shortfall,
    }
    return df, metrics
