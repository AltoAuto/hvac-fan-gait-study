# 🐎 **HVAC Fan Gait Study**

### *Horse gait–inspired fan speed control for energy-efficient HVAC systems*

---

## Overview

This project models and visualizes how HVAC fans can switch discrete speed “gaits” just like horses change between walk, trot, and gallop to maintain efficiency as system resistance (e.g., filter fouling) changes.
By operating near the Best Efficiency Point (BEP) rather than staying at a fixed speed, even simple mode-switch fans can capture most of the energy savings of a full variable-speed drive.

---

## Objectives

* Demonstrate that **fixed-speed fans waste energy** when duct resistance changes.
* Show that **mode-switch (2–3 discrete speeds)** maintains airflow and saves energy.
* Compare three control strategies:

  1. Fixed-speed
  2. Mode-switch (low/mid/high “gaits”)
  3. Ideal continuous variable-speed
* Quantify energy savings and airflow compliance.
* Visualize all results in professional, publication-ready figures.

---

## Technical Model

### Fan & System Fundamentals

| Relationship  | Scaling Law | Description                          |
| ------------- | ----------- | ------------------------------------ |
| Flow (Q)      | ∝ N         | Airflow rises linearly with speed.   |
| Pressure (Δp) | ∝ N²        | Static pressure grows quadratically. |
| Power (P)     | ∝ N³        | Power demand grows cubically.        |

**System curve:**

$\Delta p_{\text{sys}}(Q) = k Q^2$

where *k* increases as filters foul → higher resistance.

**Operating point:** Intersection of fan curve and system curve.

**Efficiency metrics:**
* CFM/W (higher = better)
* Specific Fan Power (SFP = W/CFM, lower = better)

**Dynamic conditions in this study:**

The airflow demand is generated procedurally to mimic a realistic 1-hour variation in building airflow needs, while system fouling gradually increases resistance (k) over time.
This setup provides repeatable, controlled test conditions to compare how fixed-speed, mode-switch, and variable-speed fan strategies respond to changing loads.

---

## Simulation Pipeline

1. Build fan curves from BEP data and affinity laws.
2. Build system curves (clean vs fouled).
3. Compute operating points for multiple speeds.
4. Calculate efficiency (CFM/W).
5. Simulate 1-hour demand profile with resistance increasing over time.
6. Compare fixed, mode-switch, and variable strategies.
7. Export all figures to `/outputs`.

---

## Results & Graphs

| Graph        | Description                                                                                    
| ------------ | ---------------------------------------------------------------------------------------------- 
| **Graph 1**  | Fan & System Curves (clean vs fouled) — shows how operating points shift left as filters clog. 
| **Graph 2**  | Efficiency vs Flow — dome-shaped BEP curves, one per speed. 
| **Graph 3**  | Power vs Time — compares electrical power draw per strategy. 
| **Graph 4**  | Airflow Tracking (Demand vs Delivered) — visualizes control accuracy.
| **Graph 5a** | Energy vs Strategy — total Wh with compliance % labels. 
| **Graph 5b** | Shortfall & Oversupply — tolerance-aware CFM·h imbalance.                                      
| **Graph 6**  | Energy Savings vs Fixed — headline efficiency improvement chart.                             
| **Result sheet**  | Summary finding                               

---

## Key Findings

| Strategy        | Energy (Wh) | Compliance | SFP (W/CFM) | Comment                                 
| --------------- | ----------- | ---------- | ----------- | ---------------------------------------- 
| **Fixed**       | Highest     | Low        | Highest     | Oversupplies airflow → inefficient       
| **Mode-switch** | −15–30%     | Medium     | ↓ 10–25%    | Near-BEP operation with discrete “gaits” 
| **Variable**    | −25–40%     | Full       | Lowest      | Upper bound for savings                 

**Conclusion:**
Even **two or three discrete speed modes** achieve most of the savings of continuous variable-speed fans, proving the “gait-switching” analogy.

---

## Analogy Explained

| Biological                     | HVAC Equivalent                          | Meaning                                      
| ------------------------------ | ---------------------------------------- | --------------------------------------------
| Walk / Trot / Gallop           | Low / Medium / High RPM                  | Discrete “gaits” for energy-efficient motion 
| Oxygen per distance            | Watts per airflow                        | Efficiency metric                           
| Gait switch when speed changes | Fan speed switch when resistance changes | Re-optimizing effort                        

> 🐎 *Just like a horse wastes energy if it gallops too slowly or trots too fast, a fan wastes power when operating far from its BEP.*

---

## Repo Structure

```
.
├─ README.md
├─ LICENSE
├─ .gitignore
├─ requirements.txt
├─ outputs/              # generated figures (ignored by git)
│   └─ .gitkeep
├─ HVAC Fan Gait Study Report.pdf
└─ src/
    └─ hvac_fan_gaits/
        ├─ __init__.py
        ├─ params.py
        ├─ demand.py
        ├─ fan.py
        ├─ system.py
        ├─ controller.py
        ├─ simulate.py
        ├─ plots.py
        ├─ report_sumary.py
        └─ main.py
```

---

## Quick Start

### 1. Setup environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run simulation

```bash
python -m src.hvac_fan_gaits.main
```

All figures will be saved under `outputs/`.

---

## Requirements

```txt
numpy==1.26.4
scipy==1.13.1
pandas==2.2.2
matplotlib==3.8.4
pyyaml==6.0.1
```

---

## Example Output (Summary)

```
=== FAIRNESS METRICS ===
 fixed | Wh=63.7 | compliance=0% | SFP=0.149 W/CFM
 modes | Wh=43.6 | compliance=33% | SFP=0.120 W/CFM | 31% energy saved
 var   | Wh=23.8 | compliance=100% | SFP=0.079 W/CFM | 63% energy saved
```

---

## Outputs (figures)

All plots are automatically generated and saved as `.png` and `.svg` under:

```
outputs/
├─ graph1_clean_vs_fouled.png
├─ graph2_efficiency_vs_flow.png
├─ graph3_time_Q.png
├─ graph3_time_P.png
├─ graph5_energy_bar.png
├─ graph5_supply_bars.png
├─ graph6_energy_savings.png
└─ result_sheet.md
```

---

## How to Customize

* Change fan/system constants in `params.py`.
* Adjust simulation duration, tolerance, or speed set in `SimSpec`.
* Set `SIM_SPEC.show = True` to open plots interactively.

---

## Future Work

* Integrate real sensor data (pressure, power, airflow).
* Add simple control loop visualization (mode-switch logic).
* Build low-cost prototype with a PWM PC fan + smart plug + phone anemometer.

---

## Author

**Aiden Wang**
Mechanical Engineering, University of Minnesota

---

* Note: The data used here are synthetic and meant for demonstration only.
The trends are physically accurate, but not calibrated to any real fan.
