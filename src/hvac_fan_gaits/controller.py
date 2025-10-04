import numpy as np

def operating_point_Q(fan, k, rpm, n_grid=800):
    """Find operating airflow Q_op for given (k, rpm) by intersecting fan Δp(Q,rpm) with k*Q^2."""
    Q_free = fan.free_delivery_cfm(rpm)
    if Q_free <= 1e-9:
        return 0.0
    Q = np.linspace(0.0, Q_free, n_grid)
    dP_fan = fan.dP_at(Q, rpm)
    dP_sys = k * Q**2
    i = int(np.argmin(np.abs(dP_fan - dP_sys)))
    return float(Q[i])

def solve_rpm_for_Q(fan, k, Q_target, rpm_lo, rpm_hi, eps_cfm=10.0, iters=24):
    """
    Variable-speed: choose rpm so operating Q ≈ Q_target within ±eps_cfm, by bisection.
    Clamped to [rpm_lo, rpm_hi].
    """
    from math import isfinite
    Q_lo = operating_point_Q(fan, k, rpm_lo)
    Q_hi = operating_point_Q(fan, k, rpm_hi)
    # If target is below/above feasible range, clamp
    if Q_target <= Q_lo + eps_cfm: return rpm_lo, Q_lo
    if Q_target >= Q_hi - eps_cfm: return rpm_hi, Q_hi

    lo, hi = rpm_lo, rpm_hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        Qm  = operating_point_Q(fan, k, mid)
        if Qm < (Q_target - eps_cfm):
            lo = mid
        elif Qm > (Q_target + eps_cfm):
            hi = mid
        else:
            return mid, Qm  # within tolerance
    rpm = 0.5 * (lo + hi)
    Qop = operating_point_Q(fan, k, rpm)
    return rpm, Qop

def choose_mode_min_power(fan, k, speeds_rpm, Q_target, eps_cfm, power_fn, P_bep_ref_W, N_ref_rpm):
    # Build (rpm, Qop, P) for all modes
    triples = []
    for rpm in speeds_rpm:
        Qop = operating_point_Q(fan, k, rpm)
        P   = power_fn(fan, Qop, rpm, P_bep_ref_W, N_ref_rpm)
        triples.append((rpm, Qop, P))
    # Feasible = meets demand within tolerance (Qop >= Qd - eps)
    feas = [(rpm, Qop, P) for (rpm, Qop, P) in triples if Qop >= (Q_target - eps_cfm)]
    if feas:
        # among feasible, choose minimal power
        rpm, Qop, P = min(feas, key=lambda z: z[2])
        return rpm, Qop
    # else pick maximal Q (minimize shortfall)
    rpm, Qop, P = max(triples, key=lambda z: z[1])
    return rpm, Qop
