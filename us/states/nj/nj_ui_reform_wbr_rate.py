"""
NJ UI Reform: raise WBR rate from 60% to 70%.

Compares baseline (60% WBR) against a reform raising the weekly
benefit rate to 70% of average weekly wage. Shows how different
household archetypes are affected and demonstrates that the reform
is progressive — it helps low-to-mid earners but has no effect on
high earners who already hit the $905 cap.
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
        "wbr": float(
            sim.calculate(
                "nj_unemployment_insurance_weekly_benefit_rate", year
            )[0]
        ),
        "weekly": float(
            sim.calculate(
                "nj_unemployment_insurance_weekly_benefit", year
            )[0]
        ),
        "annual": float(
            sim.calculate("nj_unemployment_insurance", year)[0]
        ),
        "dep_rate": float(
            sim.calculate(
                "nj_unemployment_insurance_dependency_allowance", year
            )[0]
        ),
    }


def make_reform_system():
    s = CountryTaxBenefitSystem()
    p = s.parameters.gov.states.nj.dol.unemployment_insurance
    p.wbr_rate.update(period="year:2026:10", value=0.70)
    return s


BLUE = "#1a73e8"
RED = "#d93025"
ORANGE = "#e8710a"
GREEN = "#0d904f"
PURPLE = "#7b2ff7"
GRAY = "#333333"
LIGHT_GRAY = "#999999"

base_sys = make_system()
ref_sys = make_reform_system()

# Household archetypes
households = [
    ("Part-time\nretail", 22, 14_000, 22, 0),
    ("Seasonal\nconstruction", 30, 36_000, 20, 2),
    ("Single parent\nservice", 40, 28_000, 26, 1),
    ("Office\nworker", 48, 52_000, 26, 0),
    ("Parent of 3\nmid-career", 50, 65_000, 26, 3),
    ("Tech\nworker", 52, 104_000, 26, 0),
]

print("Computing households...")
bl_results = [calc(base_sys, *h[1:]) for h in households]
rf_results = [calc(ref_sys, *h[1:]) for h in households]

fig = plt.figure(figsize=(16, 12))
fig.suptitle(
    "NJ UI across household types — baseline vs. reform (WBR 60% → 70%)",
    fontsize=15,
    fontweight="bold",
    color=GRAY,
    y=0.97,
)

# Top: Horizontal bar comparing baseline vs reform annual benefit
ax1 = fig.add_subplot(2, 1, 1)
labels = [h[0] for h in households]
bl_annual = [r["annual"] for r in bl_results]
rf_annual = [r["annual"] for r in rf_results]

y_pos = np.arange(len(labels))
ax1.barh(
    y_pos + 0.15,
    bl_annual,
    0.3,
    color=BLUE,
    alpha=0.8,
    label="Baseline (60% WBR)",
)
ax1.barh(
    y_pos - 0.15,
    rf_annual,
    0.3,
    color=RED,
    alpha=0.8,
    label="Reform (70% WBR)",
)

for i, (b, r) in enumerate(zip(bl_annual, rf_annual)):
    ax1.text(
        b + 200,
        i + 0.15,
        f"${b:,.0f}",
        va="center",
        fontsize=9,
        color=GRAY,
    )
    inc = r - b
    ax1.text(
        r + 200,
        i - 0.15,
        f"${r:,.0f} (+${inc:,.0f})",
        va="center",
        fontsize=9,
        color=RED,
    )

ax1.set_yticks(y_pos)
ax1.set_yticklabels(labels, fontsize=10)
ax1.set_xlabel("Annual UI benefit", color=GRAY)
ax1.set_title(
    "Annual benefit by household type", fontsize=12, color=GRAY
)
ax1.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax1.legend(frameon=False, loc="lower right")
ax1.spines[["top", "right"]].set_visible(False)
ax1.set_xlim(0, max(rf_annual) * 1.35)

# Bottom left: Breakdown for single parent
ax2 = fig.add_subplot(2, 2, 3)
idx = 2
h = households[idx]
bl = bl_results[idx]
rf = rf_results[idx]

categories = [
    "Avg weekly\nwage",
    "WBR\n(60%→70%)",
    "Dep allowance\n(+7%)",
    "Weekly\nbenefit",
    f"× {min(h[1], 26)} weeks\n= Annual",
]
bl_vals = [
    bl["wbr"] / 0.6,
    bl["wbr"],
    bl["weekly"] - bl["wbr"],
    bl["weekly"],
    bl["annual"],
]
rf_vals = [
    rf["wbr"] / 0.7,
    rf["wbr"],
    rf["weekly"] - rf["wbr"],
    rf["weekly"],
    rf["annual"],
]

x = np.arange(len(categories))
ax2.bar(x - 0.17, bl_vals, 0.3, color=BLUE, alpha=0.8, label="Baseline")
ax2.bar(x + 0.17, rf_vals, 0.3, color=RED, alpha=0.8, label="Reform")
for i, (b, r) in enumerate(zip(bl_vals, rf_vals)):
    ax2.text(
        i - 0.17,
        b + max(bl_vals) * 0.02,
        f"${b:,.0f}",
        ha="center",
        va="bottom",
        fontsize=8,
        color=GRAY,
    )
    ax2.text(
        i + 0.17,
        r + max(rf_vals) * 0.02,
        f"${r:,.0f}",
        ha="center",
        va="bottom",
        fontsize=8,
        color=RED,
    )

ax2.set_xticks(x)
ax2.set_xticklabels(categories, fontsize=9)
ax2.set_title(
    "Calculation breakdown: Single parent, service",
    fontsize=12,
    color=GRAY,
)
ax2.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax2.legend(frameon=False, fontsize=9)
ax2.spines[["top", "right"]].set_visible(False)

# Bottom right: Percent increase
ax3 = fig.add_subplot(2, 2, 4)
pct_inc = [
    (r - b) / b * 100 if b > 0 else 0
    for r, b in zip(rf_annual, bl_annual)
]
colors = [
    RED if p > 10 else ORANGE if p > 5 else BLUE for p in pct_inc
]
ax3.barh(y_pos, pct_inc, color=colors, alpha=0.7)
for i, p in enumerate(pct_inc):
    ax3.text(
        p + 0.3, i, f"{p:.1f}%", va="center", fontsize=10, color=GRAY
    )

ax3.set_yticks(y_pos)
ax3.set_yticklabels(labels, fontsize=10)
ax3.set_xlabel("Percent increase in annual benefit", color=GRAY)
ax3.set_title(
    "Who benefits most from 70% WBR?", fontsize=12, color=GRAY
)
ax3.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"{x:.0f}%")
)
ax3.spines[["top", "right"]].set_visible(False)
ax3.set_xlim(0, max(pct_inc) * 1.3)

plt.tight_layout(rect=[0, 0, 1, 0.94])
output = "us/states/nj/nj_ui_reform_wbr_rate.png"
plt.savefig(output, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Saved to {output}")
