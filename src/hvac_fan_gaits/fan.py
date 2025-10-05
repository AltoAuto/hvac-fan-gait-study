import numpy as np
from dataclasses import dataclass

@dataclass
class FanCurve:
    """
    Simple, shape-safe fan model at a reference speed (N_ref_rpm).
    Reference curve is monotone decreasing and clipped at free delivery:
        dP_ref(Q) = dP_shut * [ 1 - (Q / Q_free)^n ]_+
    with n >= 2 for a natural fan-like shape.

    Affinity scaling:
        Q ~ N,   dP ~ N^2
    """
    Q_free_ref_cfm: float
    dP_shut_ref_Pa: float
    N_ref_rpm: float
    n_shape: float = 2.0  # quadratic falloff; tweak 2–3 if desired

    @staticmethod
    def from_bep(Q_bep_cfm: float, dP_bep_Pa: float, N_ref_rpm: float, n_shape: float = 2.0) -> "FanCurve":
        """
        Construct a reference curve from BEP heuristics.
        Typical catalog heuristics put BEP near ~60% of Q_free and ~60% of shutoff pressure.
        Solve:
            Q_bep = 0.6 * Q_free  =>  Q_free = Q_bep / 0.6
            dP_bep = 0.6 * dP_shut => dP_shut = dP_bep / 0.6
        """
        Q_free = Q_bep_cfm / 0.6
        dP_shut = dP_bep_Pa / 0.6
        return FanCurve(Q_free_ref_cfm=Q_free, dP_shut_ref_Pa=dP_shut, N_ref_rpm=N_ref_rpm, n_shape=n_shape)

    # ---------- helpers ----------
    def free_delivery_cfm(self, N_rpm: float) -> float:
        return self.Q_free_ref_cfm * (N_rpm / self.N_ref_rpm)

    def shutoff_pressure_Pa(self, N_rpm: float) -> float:
        return self.dP_shut_ref_Pa * (N_rpm / self.N_ref_rpm) ** 2

    # ---------- main API ----------
    def dP_at(self, Q_cfm, N_rpm: float):
        """
        Static pressure rise [Pa] at airflow Q [cfm] and speed N_rpm.
        Clipped to >= 0 (no non-physical negatives).
        """
        Q = np.asarray(Q_cfm, dtype=float)
        Q_free = self.free_delivery_cfm(N_rpm)
        dP_shut = self.shutoff_pressure_Pa(N_rpm)

        # normalized flow
        x = np.clip(Q / max(Q_free, 1e-9), 0.0, 10.0)
        dP = dP_shut * np.maximum(1.0 - x ** self.n_shape, 0.0)
        return dP

    
    def P_at(self, Q_cfm, N_rpm: float, P_bep_ref_W: float, Q_bep_ref_cfm: float):
        """
        Rough electrical power vs flow at a given speed, scaled by affinity.
        Uses a smooth cubic-like rise with flow that matches P_bep at ref BEP.
        Not used for Plot 1; kept for future plots.
        """
        Q = np.asarray(Q_cfm, dtype=float)
        scale_P = (N_rpm / self.N_ref_rpm) ** 3
        # simple shape: P ~ (Q/Q_free)^3 scaled to hit P_bep at Q_bep
        alpha = (Q_bep_ref_cfm / max(self.Q_free_ref_cfm, 1e-9)) ** 3
        base = (Q / max(self.free_delivery_cfm(N_rpm), 1e-9)) ** 3
        return scale_P * (P_bep_ref_W / max(alpha, 1e-9)) * base

