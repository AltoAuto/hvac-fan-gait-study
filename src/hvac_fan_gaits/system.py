import numpy as np

class SystemCurve:
    """Quadratic system resistance: Δp = k * Q^2  (Q in cfm, Δp in Pa if k units match)"""
    def __init__(self, k: float):
        self.k = float(k)

    def dP_at(self, Q_cfm):
        Q = np.asarray(Q_cfm, dtype=float)
        return self.k * Q**2
