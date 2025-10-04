import os
import numpy as np
import matplotlib.pyplot as plt
from params import FAN as FAN_SPEC, SYSTEM as SYS_SPEC, SIM as SIM_SPEC
from fan import FanCurve
from system import SystemCurve
from plots import (
    figure_fan_and_system_with_operating_points,
    figure_efficiency_vs_flow,
    figure_time_series_Q,
    figure_time_series_power,
    figure_energy_bar,
    figure_supply_bars,
    figure_energy_savings,
    set_mpl_defaults
)
from demand import build_profiles
from simulate import run_time_sim
from report_summary import console_summary, build_summary_sheet

def main():
    OUTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputs"))
    os.makedirs(OUTDIR, exist_ok=True)

    set_mpl_defaults() # set style

    fan = FanCurve.from_bep(
        Q_bep_cfm=FAN_SPEC.Q_bep_cfm,
        dP_bep_Pa=FAN_SPEC.dP_bep_Pa,
        N_ref_rpm=FAN_SPEC.N_ref_rpm,
        n_shape=2.0,
    )
    sys_clean = SystemCurve(k=SYS_SPEC.k_clean)
    sys_foul  = SystemCurve(k=SYS_SPEC.k_fouled)
    speeds = SIM_SPEC.speeds_rpm

    # ---- Graph 1 ----
    N_hi = max(speeds)
    Q_free_hi = fan.free_delivery_cfm(N_hi)
    Q_max = 1.05 * Q_free_hi
    fig1 = figure_fan_and_system_with_operating_points(fan, sys_clean, sys_foul, speeds, Q_max)
    outpath1 = os.path.join(OUTDIR, "graph1_clean_vs_fouled.png")
    fig1.savefig(outpath1, dpi=300)
    print(f"[OK] Saved: {outpath1}")

    # ---- Graph 2 ----
    fig3 = figure_efficiency_vs_flow(
        fan,
        speeds_rpm=speeds,
        Q_max=1.05 * fan.free_delivery_cfm(max(speeds)),
        P_bep_ref_W=FAN_SPEC.P_bep_W,
        N_ref_rpm=FAN_SPEC.N_ref_rpm,
        x_bep=0.60,
        idle_frac=0.26,
        gamma_free=2.3,
        q_min_frac=0.01,
        q_max_frac=0.99
    )
    outpath3 = os.path.join(OUTDIR, "graph2_efficiency_vs_flow.png")
    fig3.savefig(outpath3, dpi=300)
    print(f"[OK] Saved: {outpath3}")

    # --- Graph 3: Time-series simulation (demand + fouling) ---
    # profiles
    dt_s = getattr(SIM_SPEC, "dt_s", 1.0)
    horizon_s = getattr(SIM_SPEC, "horizon_s", 3600.0)
    t, Qd, k_t = build_profiles(
        horizon_s=horizon_s, dt_s=dt_s,
        Q_base_cfm=FAN_SPEC.Q_bep_cfm,
        Q_amp_cfm=0.25 * FAN_SPEC.Q_bep_cfm,
        foul_start=0.15, foul_end=0.85,
        k_clean=SYS_SPEC.k_clean, k_fouled=SYS_SPEC.k_fouled
    )
    # simulate
    df, metrics = run_time_sim(
        fan, t, Qd, k_t,
        speeds_rpm=SIM_SPEC.speeds_rpm,
        fixed_rpm=SIM_SPEC.fixed_rpm,
        P_bep_ref_W=FAN_SPEC.P_bep_W,
        N_ref_rpm=FAN_SPEC.N_ref_rpm,
        idle_frac=0.22, gamma_free=2.0, x_bep=0.60,
        rpm_bounds=SIM_SPEC.rpm_bounds, eps_cfm=SIM_SPEC.eps_cfm, lambda_shortfall=SIM_SPEC.lambda_shortfall
    )
    # plots
    figQ = figure_time_series_Q(df)
    figP = figure_time_series_power(df)
    figQ.savefig(os.path.join(OUTDIR, "graph3_time_Q.png"), dpi=300)
    figP.savefig(os.path.join(OUTDIR, "graph4_time_P.png"), dpi=300)
    print("[OK] Saved:", os.path.join(OUTDIR, "graph3_time_Q.png"))
    print("[OK] Saved:", os.path.join(OUTDIR, "graph4_time_P.png"))
    figE = figure_energy_bar(metrics)
    figS = figure_supply_bars(metrics)


    # --- Graph 4: energy bars ---
    figE.savefig(os.path.join(OUTDIR, "graph5a_energy_bars.png"), dpi=300)
    figS.savefig(os.path.join(OUTDIR, "graph5b_supply_bars.png"), dpi=300)
    print("[OK] Saved:", os.path.join(OUTDIR, "graph5a_energy_bars.png"))
    print("[OK] Saved:", os.path.join(OUTDIR, "graph5b_supply_bars.png"))

    # --- Graph 5: energy savings ---
    fig5 = figure_energy_savings(metrics)
    fig5.savefig(os.path.join(OUTDIR, "graph6_energy_savings.png"), dpi=300)
    print("[OK] Saved:", os.path.join(OUTDIR, "graph6_energy_savings.png"))


    console_summary(metrics)

    # 2) file outputs
    figs = {
        "g5E": os.path.join(OUTDIR, "graph5_energy_bars.png"),
        "g5S": os.path.join(OUTDIR, "graph5_supply_bars.png"),
    }
    md_path, html_path = build_summary_sheet(
        outdir=OUTDIR,
        metrics=metrics,
        fan_spec=FAN_SPEC, system_spec=SYS_SPEC, sim_spec=SIM_SPEC,
        figs=figs
    )
    print("[OK] Result sheet:")
    print("  -", md_path)
    print("  -", html_path)
if __name__ == "__main__":
    main()
