import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

# Brand palette (accessible, consistent)
PALETTE = {
    "fixed":      "#1f77b4",  # blue
    "modes":      "#ff7f0e",  # orange
    "variable":   "#2ca02c",  # green
    "system_clean": "#6c6c6c",  # grey
    "system_foul":  "#000000",  # black
    "fan":        "#9467bd",  # purple (base for multiple RPMs)
}

MARKERS = {
    "clean": "o",
    "foul":  "s",
    "bep":   "o",
}

def set_mpl_defaults():
    # Typography
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",    # swap to Helvetica if you have it
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "lines.linewidth": 2.0,
        "lines.markersize": 6.0,
        "axes.grid": True,
        "grid.alpha": 0.18,
        "grid.linestyle": "-",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.figsize": (7.5, 5.0),
        "figure.autolayout": True,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })

def pro_axes(ax, *, xlabel=None, ylabel=None, title=None, legend=True):
    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)
    if title:  ax.set_title(title)
    ax.minorticks_on()
    ax.tick_params(axis="both", which="major", length=5, width=1.0)
    ax.tick_params(axis="both", which="minor", length=3, width=0.8)
    if legend:
        leg = ax.legend(frameon=True, fancybox=True, framealpha=0.92, borderpad=0.6)
        leg.get_frame().set_linewidth(0)

def pro_annot(ax, text, xy, *, xytext=(0, 18), ha="center"):
    ax.annotate(
        text, xy=xy, xytext=xytext, textcoords="offset points",
        ha=ha, va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.9, lw=0),
        arrowprops=dict(arrowstyle="-", color="#666", lw=1.0),
        fontsize=9
    )


def rpm_color(i: int, n: int, base_rgb=(148, 103, 189)):
    """
    Safe, sleek shading from a base color toward white, always within [0,1].
    Gives distinct, professional-looking colors across speeds.
    """
    base = np.array(base_rgb) / 255.0
    white = np.array([1.0, 1.0, 1.0])
    t = 0.5 if n <= 1 else i / (n - 1)    # 0..1
    shade = 0.35 + 0.55 * t               # in [0.35, 0.90]
    return np.clip((1 - shade) * white + shade * base, 0.0, 1.0)

def legend_outside(ax, ncol=1):
    """
    Puts a compact legend outside the axes (right side), so it never covers the plot.
    """
    leg = ax.legend(
        frameon=True, fancybox=True, framealpha=0.92, borderpad=0.6,
        loc="upper left", bbox_to_anchor=(1.02, 1.0), ncol=ncol
    )
    if leg is not None:
        leg.get_frame().set_linewidth(0)
    return leg

def proxy_marker(marker="o", color="#444", label=""):
    """Convenience for adding one-off legend marker entries (no extra plot)."""
    return Line2D([0], [0], marker=marker, color="none",
                  markerfacecolor=color, markeredgecolor=color,
                  markersize=6, linestyle="none", label=label)

# ---------- Graph 1: Fan + System (Clean vs Fouled) ----------
def figure_fan_and_system_with_operating_points(fan, system_clean, system_foul, speeds_rpm, Q_max):
    """
    Compare fan curves (several RPM) against CLEAN and FOULED system curves.
    Mark operating points (clean: circle, fouled: square) for each speed, but keep legend compact.
    """
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    Q = np.linspace(0.0, Q_max, 600)

    # System curves (single legend entries)
    dP_clean = system_clean.dP_at(Q)
    dP_foul  = system_foul.dP_at(Q)
    ln1, = ax.plot(Q, dP_clean, ls="--", color=PALETTE["system_clean"], lw=2, label=f"System (clean)  k={system_clean.k:.2e}")
    ln2, = ax.plot(Q, dP_foul,  ls="-",  color=PALETTE["system_foul"],  lw=2, label=f"System (fouled) k={system_foul.k:.2e}")

    # Fan curves and operating points (don’t spam legend with every OP label)
    fan_lines = []
    for i, N in enumerate(speeds_rpm):
        color = rpm_color(i, len(speeds_rpm))
        dP_fan = fan.dP_at(Q, N)
        ln, = ax.plot(Q, dP_fan, lw=2, color=color, label=f"Fan @ {N:.0f} rpm")
        fan_lines.append(ln)

        # OP clean
        i_clean = int(np.argmin(np.abs(dP_fan - dP_clean)))
        Qc, Pc = Q[i_clean], dP_fan[i_clean]
        ax.plot(Qc, Pc, MARKERS["clean"], ms=7, color=color)

        # OP fouled
        i_foul = int(np.argmin(np.abs(dP_fan - dP_foul)))
        Qf, Pf = Q[i_foul], dP_fan[i_foul]
        ax.plot(Qf, Pf, MARKERS["foul"], ms=7, color=color)

    # Build a compact legend: systems + one marker entry each + fan speed lines
    handles = [
        ln1, ln2,
        proxy_marker(MARKERS["clean"], "#444", "OP (clean)"),
        proxy_marker(MARKERS["foul"],  "#444", "OP (fouled)"),
        *fan_lines
    ]
    ax.legend(handles=handles, frameon=True, fancybox=True, framealpha=0.92,
              loc="upper left", bbox_to_anchor=(1.02, 1.0), ncol=1)

    pro_axes(ax,
        xlabel="Airflow Q (cfm)",
        ylabel="Static pressure Δp (Pa)",
        title="Fan & System Curves — Clean vs Fouled",
        legend=False,  # legend is already placed
    )
    return fig


# ---------- Graph 2: Efficiency vs Flow (true BEP marked) ----------
def figure_efficiency_vs_flow(
    fan, speeds_rpm, Q_max,  P_bep_ref_W,
    N_ref_rpm=None, x_bep=0.60, idle_frac=0.22, gamma_free=2.0,
    q_min_frac=0.02, q_max_frac=0.96
):
    if N_ref_rpm is None:
        N_ref_rpm = fan.N_ref_rpm

    # power model (same as yours)
    p0 = float(idle_frac)
    denom = x_bep**2 - x_bep if abs(x_bep**2 - x_bep) > 1e-9 else -1e-3
    b2 = (1 - p0 - x_bep*(gamma_free - p0)) / denom
    b1 = (gamma_free - p0) - b2
    if b2 <= 0 or (b1 + 2*b2) <= 0:
        b2 = max(0.2*(gamma_free - 1), 1e-3)
        b1 = (gamma_free - p0) - b2

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    lines = []
    for i, N in enumerate(speeds_rpm):
        color = rpm_color(i, len(speeds_rpm))
        Q_free = fan.free_delivery_cfm(N)
        Q_lo   = max(q_min_frac*Q_free, 1e-6)
        Q_hi   = min(q_max_frac*Q_free, Q_max)
        Q = np.linspace(Q_lo, Q_hi, 700)
        x = Q / max(Q_free, 1e-9)

        dP = fan.dP_at(Q, N)
        P_bep_N = P_bep_ref_W * (N / N_ref_rpm)**3
        P_elec  = P_bep_N * (p0 + b1*x + b2*x**2)

        mask = (dP > 0) & (P_elec > 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            eff = np.where(mask, Q / P_elec, np.nan)

        ln, = ax.plot(Q, eff, lw=2, color=color, label=f"{N:.0f} rpm")
        lines.append(ln)

        if not np.all(np.isnan(eff)):
            j = int(np.nanargmax(eff))
            ax.plot([Q[j]], [eff[j]], MARKERS["bep"], ms=7, color=color)
            pro_annot(ax, f"BEP {N:.0f} rpm\nQ≈{Q[j]:.0f} cfm\nη≈{eff[j]:.2f} CFM/W",
                      xy=(Q[j], eff[j]), xytext=(0, 16))

    pro_axes(ax,
        xlabel="Airflow Q (cfm)",
        ylabel="Efficiency η (CFM/W)  ↑ better",
        title="Efficiency vs Flow — BEP marked (true peak)",
        legend=False,
    )
    # put legend outside so it never covers the hump
    legend_outside(ax, ncol=1)
    return fig


# ---------- Graph 3/4: Time series ----------
def figure_time_series_Q(df, debug=False):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    tmin = df["t"] / 60.0

    # plot with explicit colors, capture handles
    h_d, = ax.plot(tmin, df["Qd"],      ls="--", color="#000000", lw=2, label="Demand")
    h_f, = ax.plot(tmin, df["Q_fixed"], color=PALETTE["fixed"],    lw=2, label="Fixed")
    h_m, = ax.plot(tmin, df["Q_modes"], color=PALETTE["modes"],    lw=2, label="Mode-switch")
    h_v, = ax.plot(tmin, df["Q_var"],   color=PALETTE["variable"], lw=2, label="Variable")

    pro_axes(ax, xlabel="Time (min)", ylabel="Airflow Q (cfm)",
             title="Airflow Tracking — Demand vs Delivered", legend=False)

    # Legend: only these 4 handles (prevents “extra” entries)
    ax.legend(handles=[h_d, h_f, h_m, h_v],
              frameon=True, fancybox=True, framealpha=0.92,
              loc="upper left", bbox_to_anchor=(1.02, 1.0), ncol=1)

    if debug:
        # See exactly what's on the Axes
        for ln in ax.lines:
            print("LINE:", ln.get_label(), ln.get_color(), ln.get_linestyle())

    return fig


def figure_time_series_power(df, debug=False):

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    tmin = df["t"] / 60.0

    h_f, = ax.plot(tmin, df["P_fixed"], color=PALETTE["fixed"],    lw=2, label="Fixed")
    h_m, = ax.plot(tmin, df["P_modes"], color=PALETTE["modes"],    lw=2, label="Mode-switch")
    h_v, = ax.plot(tmin, df["P_var"],   color=PALETTE["variable"], lw=2, label="Variable")

    pro_axes(ax, xlabel="Time (min)", ylabel="Electrical Power (W)",
             title="Electrical Power vs Time", legend=False)

    ax.legend(handles=[h_f, h_m, h_v],
              frameon=True, fancybox=True, framealpha=0.92,
              loc="upper left", bbox_to_anchor=(1.02, 1.0), ncol=1)

    if debug:
        for ln in ax.lines:
            print("LINE:", ln.get_label(), ln.get_color(), ln.get_linestyle())

    return fig



# ---------- Graph 5a: Energy bars ----------
def figure_energy_bar(metrics):
    order  = ["fixed", "modes", "var"]
    labels = ["Fixed", "Mode-switch", "Variable"]
    colors = [PALETTE["fixed"], PALETTE["modes"], PALETTE["variable"]]

    Wh   = np.array([metrics[k]["Wh"] for k in order], dtype=float)
    comp = np.array([metrics[k]["compliance_pct"] for k in order], dtype=float)
    sfp  = np.array([metrics[k]["SFP"] for k in order], dtype=float)

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    x = np.arange(len(order))
    bars = ax.bar(x, Wh, width=0.56, color=colors)

    # axis/labels
    ax.set_xticks(x, labels)
    ymax = (Wh.max() * 1.18) if Wh.size else 1.0
    ax.set_ylim(0, ymax)
    pro_axes(ax, ylabel="Energy (Wh)", title="Energy vs Strategy — 1 hour", legend=False)

    # top labels: compliance %
    for i, b in enumerate(bars):
        ax.text(b.get_x() + b.get_width()/2.0, b.get_height() + ymax*0.02,
                f"{comp[i]:.0f}%", ha="center", va="bottom", fontsize=10)

    # neat SFP box (bottom-right)
    lines = [f"{labels[i]}  SFP: {sfp[i]:.3f} W/CFM" for i in range(len(order))]
    ax.text(0.98, 0.02, "\n".join(lines),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
            bbox=dict(facecolor="white", alpha=0.92, edgecolor="none"))

    # thin grid only on y
    ax.grid(axis="y", alpha=0.18)
    return fig


# ---------- Graph 5b: Shortfall/Oversupply bars ----------
def figure_supply_bars(metrics):
    order  = ["fixed", "modes", "var"]
    labels = ["Fixed", "Mode-switch", "Variable"]

    short  = np.array([metrics[k]["cfmh_shortfall"]  for k in order], float)
    over   = np.array([metrics[k]["cfmh_oversupply"] for k in order], float)
    totals = short + over

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    x = np.arange(len(order))
    width = 0.6


    # stacked bars
    b1 = ax.bar(x, short, width=width, color="#5dade2", label="Shortfall (CFM·h)")
    b2 = ax.bar(x, over,  width=width, color="#1f77b4",  bottom=short, label="Oversupply (CFM·h)")

    # axes/labels
    ax.set_xticks(x, labels)
    ymax = (totals.max() * 1.20) if totals.size else 1.0
    ax.set_ylim(0, ymax)
    pro_axes(ax, ylabel="CFM·h", title="Demand Tracking — Shortfall & Oversupply", legend=False)

    # totals on top
    for i, tot in enumerate(totals):
        ax.text(x[i], tot + ymax*0.02, f"{tot:.1f}", ha="center", va="bottom", fontsize=9)

    # legend outside: exactly these two components
    ax.legend(handles=[b1[0], b2[0]], labels=["Shortfall (CFM·h)", "Oversupply (CFM·h)"],
              frameon=True, fancybox=True, framealpha=0.92,
              loc="upper left", bbox_to_anchor=(1.02, 1.0), ncol=1)

    ax.grid(axis="y", alpha=0.18)
    return fig




# ----------  Graph 6: % Energy savings vs Fixed ----------
def figure_energy_savings(metrics):
    order  = ["fixed", "modes", "var"]
    labels = ["Fixed", "Mode-switch", "Variable"]
    colors = [PALETTE["fixed"], PALETTE["modes"], PALETTE["variable"]]

    Wh_fixed = float(metrics["fixed"]["Wh"])
    Wh   = np.array([metrics[k]["Wh"] for k in order], float)
    comp = np.array([metrics[k]["compliance_pct"] for k in order], float)

    # savings vs fixed (fixed = 0 by definition)
    savings = np.zeros_like(Wh)
    if Wh_fixed > 1e-9:
        savings[1:] = 100.0 * (Wh_fixed - Wh[1:]) / Wh_fixed

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    x = np.arange(len(order))
    bars = ax.bar(x, savings, width=0.56, color=colors)

    # axis/labels
    ax.set_xticks(x, labels)
    top = max(0.0, float(savings.max()))
    ax.set_ylim(0, top*1.20 + (8 if top < 8 else 0))  # headroom
    pro_axes(ax, ylabel="% Energy savings vs Fixed", title="Energy Savings vs Fixed — 1 hour", legend=False)

    # compliance labels above bars
    for i, b in enumerate(bars):
        y = b.get_height()
        ax.text(b.get_x() + b.get_width()/2.0,
                y + (0.02*ax.get_ylim()[1]),
                f"{comp[i]:.0f}%", ha="center", va="bottom", fontsize=10)

    # light grid on y
    ax.grid(axis="y", alpha=0.18)
    return fig
