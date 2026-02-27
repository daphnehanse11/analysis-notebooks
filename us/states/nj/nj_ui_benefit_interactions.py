"""
NJ UI benefit interactions: what happens to a household's total safety net
when they lose their job?

Compares "employed at wage X" vs "unemployed, receiving NJ UI based on wage X"
for a single parent with 2 kids in NJ. NJ UI is fed into unemployment_compensation
so the income aggregation and means-tested benefits respond correctly.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from policyengine_us import CountryTaxBenefitSystem
from policyengine_core.simulations import SimulationBuilder

YEAR = 2026

def make_system():
    return CountryTaxBenefitSystem()

def calc_ui_amount(base_wages, base_weeks=26, weeks_claimed=26):
    """Compute NJ UI amount for given wages."""
    system = make_system()
    situation = {
        "people": {
            "parent": {
                "age": {YEAR: 35},
                "is_tax_unit_dependent": {YEAR: False},
                "nj_unemployment_insurance_base_period_weeks": {YEAR: base_weeks},
                "nj_unemployment_insurance_base_period_wages": {YEAR: base_wages},
                "nj_unemployment_insurance_weeks_claimed": {YEAR: weeks_claimed},
            },
        },
        "tax_units": {"tax_unit": {"members": ["parent"]}},
        "families": {"family": {"members": ["parent"]}},
        "spm_units": {"spm_unit": {"members": ["parent"]}},
        "households": {"household": {"members": ["parent"], "state_code": {YEAR: "NJ"}}},
    }
    sim = SimulationBuilder().build_from_dict(system, situation)
    return float(sim.calculate("nj_unemployment_insurance", YEAR)[0])

def make_household(employment_income=0, unemployment_comp=0):
    """Single parent with 2 kids in NJ."""
    system = make_system()
    situation = {
        "people": {
            "parent": {
                "age": {YEAR: 35},
                "is_tax_unit_dependent": {YEAR: False},
                "employment_income": {YEAR: employment_income},
                "unemployment_compensation": {YEAR: unemployment_comp},
            },
            "child1": {"age": {YEAR: 8}, "is_tax_unit_dependent": {YEAR: True}},
            "child2": {"age": {YEAR: 5}, "is_tax_unit_dependent": {YEAR: True}},
        },
        "tax_units": {"tax_unit": {"members": ["parent", "child1", "child2"], "filing_status": {YEAR: "HEAD_OF_HOUSEHOLD"}}},
        "families": {"family": {"members": ["parent", "child1", "child2"]}},
        "spm_units": {"spm_unit": {"members": ["parent", "child1", "child2"]}},
        "households": {"household": {"members": ["parent", "child1", "child2"], "state_code": {YEAR: "NJ"}}},
    }
    sim = SimulationBuilder().build_from_dict(system, situation)
    return {
        "ui": unemployment_comp,
        "employment_income": employment_income,
        "eitc": float(sim.calculate("eitc", YEAR)[0]),
        "ctc": float(sim.calculate("ctc", YEAR)[0]),
        "snap": float(sim.calculate("snap", YEAR)[0]),
        "school_meals": float(sim.calculate("free_school_meals", YEAR)[0]) + float(sim.calculate("reduced_price_school_meals", YEAR)[0]),
        "hh_net_income": float(sim.calculate("household_net_income", YEAR)[0]),
        "hh_benefits": float(sim.calculate("household_benefits", YEAR)[0]),
    }

wages = list(range(15000, 90001, 5000))

# Step 1: Compute NJ UI amounts for each wage level
print("Computing NJ UI amounts...")
ui_amounts = {w: calc_ui_amount(w) for w in wages}

# Step 2: Compute employed households
print("Computing employed scenarios...")
employed = [make_household(employment_income=w) for w in wages]

# Step 3: Compute unemployed households with UI as unemployment_compensation
print("Computing unemployed scenarios...")
unemployed = [make_household(unemployment_comp=ui_amounts[w]) for w in wages]

BLUE = "#1a73e8"
RED = "#d93025"
ORANGE = "#e8710a"
GREEN = "#0d904f"
PURPLE = "#7b2ff7"
TEAL = "#00897b"
GRAY = "#333333"
LIGHT_GRAY = "#999999"

fig, axes = plt.subplots(2, 2, figsize=(15, 11))
fig.suptitle(
    "NJ single parent (2 kids): employed vs. unemployed on UI",
    fontsize=15, fontweight="bold", color=GRAY, y=0.97,
)

# Chart 1: Stacked area - Employed
ax = axes[0, 0]
emp_earn = np.array([e["employment_income"] for e in employed])
emp_eitc = np.array([e["eitc"] for e in employed])
emp_ctc = np.array([e["ctc"] for e in employed])
emp_snap = np.array([e["snap"] for e in employed])
emp_meals = np.array([e["school_meals"] for e in employed])

layers_emp = [
    (emp_earn, BLUE, "Earnings"),
    (emp_eitc, GREEN, "EITC"),
    (emp_ctc, ORANGE, "CTC"),
    (emp_snap, PURPLE, "SNAP"),
    (emp_meals, TEAL, "School meals"),
]
bottom = np.zeros(len(wages))
for vals, color, label in layers_emp:
    ax.fill_between(wages, bottom, bottom + vals, alpha=0.7, color=color, label=label)
    bottom += vals

ax.set_xlabel("Annual wages", color=GRAY)
ax.set_ylabel("Total resources", color=GRAY)
ax.set_title("Employed: income + benefits", fontsize=12, color=GRAY)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)

# Chart 2: Stacked area - Unemployed on UI
ax = axes[0, 1]
unemp_ui = np.array([u["ui"] for u in unemployed])
unemp_eitc = np.array([u["eitc"] for u in unemployed])
unemp_ctc = np.array([u["ctc"] for u in unemployed])
unemp_snap = np.array([u["snap"] for u in unemployed])
unemp_meals = np.array([u["school_meals"] for u in unemployed])

layers_unemp = [
    (unemp_ui, RED, "NJ UI"),
    (unemp_eitc, GREEN, "EITC"),
    (unemp_ctc, ORANGE, "CTC"),
    (unemp_snap, PURPLE, "SNAP"),
    (unemp_meals, TEAL, "School meals"),
]
bottom = np.zeros(len(wages))
for vals, color, label in layers_unemp:
    ax.fill_between(wages, bottom, bottom + vals, alpha=0.7, color=color, label=label)
    bottom += vals

ax.set_xlabel("Prior annual wages (base period)", color=GRAY)
ax.set_ylabel("Total resources", color=GRAY)
ax.set_title("Unemployed on UI: benefits stack", fontsize=12, color=GRAY)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)

# Match y-axes
ymax_emp = max(emp_earn + emp_eitc + emp_ctc + emp_snap + emp_meals)
ymax_unemp = max(unemp_ui + unemp_eitc + unemp_ctc + unemp_snap + unemp_meals)
ymax = max(ymax_emp, ymax_unemp) * 1.05
axes[0, 0].set_ylim(0, ymax)
axes[0, 1].set_ylim(0, ymax)

# Chart 3: Net income comparison
ax = axes[1, 0]
emp_net = [e["hh_net_income"] for e in employed]
unemp_net = [u["hh_net_income"] for u in unemployed]

ax.plot(wages, emp_net, color=BLUE, linewidth=2.5, label="Employed")
ax.plot(wages, unemp_net, color=RED, linewidth=2.5, label="Unemployed (on UI)")
ax.fill_between(wages, unemp_net, emp_net, alpha=0.12, color=RED, where=[u < e for u, e in zip(unemp_net, emp_net)])

for w_idx in [1, 5, 10, 14]:
    if w_idx < len(wages):
        w = wages[w_idx]
        e = emp_net[w_idx]
        u = unemp_net[w_idx]
        pct = u / e * 100 if e > 0 else 0
        mid = (e + u) / 2
        ax.annotate(f"{pct:.0f}%", xy=(w, mid), fontsize=9, color=RED, ha="center", fontweight="bold")

ax.set_xlabel("Annual wages / prior wages", color=GRAY)
ax.set_ylabel("Household net income", color=GRAY)
ax.set_title("Net income: the gap from job loss", fontsize=12, color=GRAY)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# Chart 4: Individual benefit changes
ax = axes[1, 1]
delta_eitc = [u["eitc"] - e["eitc"] for u, e in zip(unemployed, employed)]
delta_ctc = [u["ctc"] - e["ctc"] for u, e in zip(unemployed, employed)]
delta_snap = [u["snap"] - e["snap"] for u, e in zip(unemployed, employed)]
delta_meals = [u["school_meals"] - e["school_meals"] for u, e in zip(unemployed, employed)]

ax.plot(wages, delta_eitc, color=GREEN, linewidth=2, label="EITC change")
ax.plot(wages, delta_ctc, color=ORANGE, linewidth=2, label="CTC change")
ax.plot(wages, delta_snap, color=PURPLE, linewidth=2, label="SNAP change")
ax.plot(wages, delta_meals, color=TEAL, linewidth=2, label="School meals change")
ax.axhline(y=0, color=LIGHT_GRAY, linewidth=1, linestyle="--")

ax.set_xlabel("Wage level", color=GRAY)
ax.set_ylabel("Change in benefit (unemployed − employed)", color=GRAY)
ax.set_title("How other benefits shift when you lose your job", fontsize=12, color=GRAY)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:+,.0f}"))
ax.legend(frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig("/tmp/nj_ui_interactions.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved to /tmp/nj_ui_interactions.png")

# Summary table
print("\n" + "=" * 100)
print(f"{'Wage':>8} {'UI Amt':>8} {'Emp Net':>10} {'UI Net':>10} {'Repl%':>7} "
      f"{'dEITC':>8} {'dSNAP':>8} {'dCTC':>8} {'dMeals':>8}")
print("-" * 100)
for i, w in enumerate(wages):
    print(f"${w:>7,} ${ui_amounts[w]:>7,.0f} ${emp_net[i]:>9,.0f} ${unemp_net[i]:>9,.0f} "
          f"{unemp_net[i]/emp_net[i]*100 if emp_net[i]>0 else 0:>6.1f}% "
          f"${delta_eitc[i]:>+7,.0f} ${delta_snap[i]:>+7,.0f} ${delta_ctc[i]:>+7,.0f} ${delta_meals[i]:>+7,.0f}")
