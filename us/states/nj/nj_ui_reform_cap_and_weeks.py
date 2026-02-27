"""
NJ UI Reform: raise weekly cap to $1,000 and extend to 30 weeks.

Compares baseline ($905 cap, 26 weeks max) against a reform that
raises the weekly benefit cap to $1,000 and extends max duration
to 30 weeks. Shows weekly/annual benefit comparison, dollar
increase, and percent increase by wage level.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from policyengine_us import CountryTaxBenefitSystem
from policyengine_core.simulations import SimulationBuilder


def make_system():
    return CountryTaxBenefitSystem()


def calc(
    system,
    base_weeks,
    base_wages,
    weeks_claimed,
    num_dependents=0,
    year=2026,
):
    people = {
        "adult": {
            "age": {year: 35},
            "is_tax_unit_dependent": {year: False},
        }
    }
    for i in range(num_dependents):
        people[f"child_{i}"] = {
            "age": {year: 10 - i},
            "is_tax_unit_dependent": {year: True},
        }
    members = ["adult"] + [f"child_{i}" for i in range(num_dependents)]
    situation = {
        "people": people,
        "tax_units": {"tax_unit": {"members": members}},
        "spm_units": {"spm_unit": {"members": members}},
        "households": {
            "household": {
                "members": members,
                "state_code": {year: "NJ"},
            }
        },
    }
    situation["people"]["adult"][
        "nj_unemployment_insurance_base_period_weeks"
    ] = {year: base_weeks}
    situation["people"]["adult"][
        "nj_unemployment_insurance_base_period_wages"
    ] = {year: base_wages}
    situation["people"]["adult"][
        "nj_unemployment_insurance_weeks_claimed"
    ] = {year: weeks_claimed}
    sim = SimulationBuilder().build_from_dict(system, situation)
    return {
        "weekly": float(
            sim.calculate(
                "nj_unemployment_insurance_weekly_benefit", year
            )[0]
        ),
        "annual": float(
            sim.calculate("nj_unemployment_insurance", year)[0]
        ),
    }


def make_reform_system():
    s = CountryTaxBenefitSystem()
    p = s.parameters.gov.states.nj.dol.unemployment_insurance
    p.max_weekly_benefit.update(period="year:2026:10", value=1000)
    p.max_benefit_weeks.update(period="year:2026:10", value=30)
    return s


BLUE = "#1a73e8"
RED = "#d93025"
GRAY = "#333333"

wages = np.arange(5000, 120001, 5000)

# Compute all baseline first with a clean system
print("Computing baseline...")
base_sys = make_system()
bl_weekly = [calc(base_sys, 30, w, 30)["weekly"] for w in wages]
bl_annual = [calc(base_sys, 40, w, 40)["annual"] for w in wages]

# Then reform with a separate system
print("Computing reform...")
ref_sys = make_reform_system()
rf_weekly = [calc(ref_sys, 30, w, 30)["weekly"] for w in wages]
rf_annual = [calc(ref_sys, 40, w, 40)["annual"] for w in wages]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(
    "NJ UI reform: raise weekly cap to $1,000 and extend to 30 weeks",
    fontsize=14,
    fontweight="bold",
    color=GRAY,
    y=0.97,
)

# Chart 1: Weekly benefit
ax = axes[0, 0]
ax.plot(
    wages,
    bl_weekly,
    color=BLUE,
    linewidth=2,
    label="Baseline ($905 cap)",
)
ax.plot(
    wages,
    rf_weekly,
    color=RED,
    linewidth=2,
    label="Reform ($1,000 cap)",
)
ax.fill_between(wages, bl_weekly, rf_weekly, alpha=0.15, color=RED)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Weekly benefit", color=GRAY)
ax.set_title(
    "Weekly benefit comparison (30 base weeks)", fontsize=12, color=GRAY
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# Chart 2: Annual benefit
ax = axes[0, 1]
ax.plot(
    wages,
    bl_annual,
    color=BLUE,
    linewidth=2,
    label="Baseline (26 wks max)",
)
ax.plot(
    wages,
    rf_annual,
    color=RED,
    linewidth=2,
    label="Reform (30 wks max)",
)
ax.fill_between(wages, bl_annual, rf_annual, alpha=0.15, color=RED)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Annual benefit", color=GRAY)
ax.set_title(
    "Annual benefit (40 base weeks, claiming max)",
    fontsize=12,
    color=GRAY,
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.1f}k")
)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# Chart 3: Dollar increase
ax = axes[1, 0]
annual_inc = [r - b for r, b in zip(rf_annual, bl_annual)]
ax.bar(wages, annual_inc, width=4000, color=RED, alpha=0.6)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Additional annual benefit", color=GRAY)
ax.set_title(
    "Dollar increase from reform (40 base weeks)",
    fontsize=12,
    color=GRAY,
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.spines[["top", "right"]].set_visible(False)

# Chart 4: Percent increase
ax = axes[1, 1]
pct_inc = [
    (r - b) / b * 100 if b > 0 else 0
    for r, b in zip(rf_annual, bl_annual)
]
ax.bar(wages, pct_inc, width=4000, color=RED, alpha=0.6)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Percent increase", color=GRAY)
ax.set_title(
    "Percent increase from reform (40 base weeks)",
    fontsize=12,
    color=GRAY,
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"{x:.0f}%")
)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
output = "us/states/nj/nj_ui_reform_cap_and_weeks.png"
plt.savefig(output, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Saved to {output}")
