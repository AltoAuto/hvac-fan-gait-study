from dataclasses import dataclass

@dataclass
class FanSpec:
    name: str = "DemoFan-200mm"
    Q_bep_cfm: float = 300.0        # BEP airflow at nominal speed (cfm)
    dP_bep_Pa: float = 120.0        # BEP static pressure rise (Pa)
    P_bep_W: float = 40.0           # Electrical power at BEP (W) [not used in Plot 1]
    N_ref_rpm: float = 1200.0       # Reference speed (rpm)
@dataclass
class SystemSpec:
    k_clean: float = 6e-5  # from 6.0e-5
    k_fouled: float = 4e-4  # from 1.2e-4
@dataclass
class SimSpec:
    speeds_rpm: tuple = (700.0, 800.0, 900.0, 1000.0)
    fixed_rpm: float = 900.0
    dt_s: float = 1.0
    horizon_s: float = 3600.0
    show: bool = False

    rpm_bounds: tuple = (500.0, 2000.0)   # allowed continuous range
    eps_cfm: float = 5             # demand tolerance for compliance
    lambda_shortfall: float = 0.4         # Wh per CFM·h shortfall penalty

# Export singletons (imported by main.py)
FAN = FanSpec()
SYSTEM = SystemSpec()
SIM = SimSpec()
