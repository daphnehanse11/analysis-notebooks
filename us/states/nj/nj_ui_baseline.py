"""
New Jersey Unemployment Insurance — Baseline exploration.

Generates four charts showing how NJ UI benefits vary across:
1. Weekly benefit by wages and dependents
2. Annual benefit by weeks worked
3. Wage replacement rate
4. Dependency allowance bump
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from policyengine_us import CountryTaxBenefitSystem
from policyengine_core.simulations import SimulationBuilder

system = CountryTaxBenefitSystem()


def calc_nj_ui(
    base_weeks, base_wages, weeks_claimed, num_dependents=0, year=2026
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
    }


BLUE = "#1a73e8"
ORANGE = "#e8710a"
GREEN = "#0d904f"
PURPLE = "#7b2ff7"
GRAY = "#333333"
LIGHT_GRAY = "#999999"

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(
    "New Jersey Unemployment Insurance — 2026",
    fontsize=16,
    fontweight="bold",
    color=GRAY,
    y=0.97,
)

# Chart 1: Weekly benefit by wages
print("Chart 1...")
ax = axes[0, 0]
wages = np.arange(5000, 105001, 5000)
for deps, color, label in [
    (0, BLUE, "No dependents"),
    (1, ORANGE, "1 dependent"),
    (3, GREEN, "3 dependents"),
]:
    weekly = [calc_nj_ui(26, w, 26, deps)["weekly"] for w in wages]
    ax.plot(wages, weekly, color=color, linewidth=2, label=label)
ax.axhline(y=905, color=LIGHT_GRAY, linestyle="--", linewidth=1, alpha=0.7)
ax.text(106000, 905, "$905 cap", va="center", fontsize=9, color=LIGHT_GRAY)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Weekly benefit", color=GRAY)
ax.set_title(
    "Weekly benefit by wages and dependents", fontsize=12, color=GRAY
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# Chart 2: Annual benefit by base weeks
print("Chart 2...")
ax = axes[0, 1]
weeks_range = list(range(20, 53, 2))
for wage, color, label in [
    (30_000, BLUE, "$30k"),
    (50_000, ORANGE, "$50k"),
    (80_000, GREEN, "$80k"),
]:
    annual = [calc_nj_ui(w, wage, 26)["annual"] for w in weeks_range]
    ax.plot(weeks_range, annual, color=color, linewidth=2, label=label)
ax.axvline(
    x=26, color=LIGHT_GRAY, linestyle="--", linewidth=1, alpha=0.7
)
ax.text(
    26.5,
    5000,
    "26-week cap",
    fontsize=9,
    color=LIGHT_GRAY,
    rotation=90,
    va="bottom",
)
ax.set_xlabel("Base period weeks worked", color=GRAY)
ax.set_ylabel("Annual benefit", color=GRAY)
ax.set_title("Annual benefit by weeks worked", fontsize=12, color=GRAY)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.legend(title="Base wages", frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# Chart 3: Replacement rate
print("Chart 3...")
ax = axes[1, 0]
wages2 = np.arange(10000, 120001, 5000)
replacement = []
for w in wages2:
    r = calc_nj_ui(26, w, 26, 0)
    weekly_wage = w / 26
    replacement.append(
        r["weekly"] / weekly_wage * 100 if weekly_wage > 0 else 0
    )
ax.plot(wages2, replacement, color=PURPLE, linewidth=2)
ax.axhline(y=60, color=LIGHT_GRAY, linestyle="--", linewidth=1, alpha=0.7)
ax.text(121000, 60, "60%", va="center", fontsize=9, color=LIGHT_GRAY)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Replacement rate (%)", color=GRAY)
ax.set_title(
    "Wage replacement rate (26 base weeks, no dependents)",
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
ax.set_ylim(0, 70)

# Chart 4: Dependency bump
print("Chart 4...")
ax = axes[1, 1]
wages3 = np.arange(10000, 105001, 5000)
base_vals = [calc_nj_ui(26, w, 26, 0)["weekly"] for w in wages3]
bump_1 = [
    calc_nj_ui(26, w, 26, 1)["weekly"] - b
    for w, b in zip(wages3, base_vals)
]
bump_3 = [
    calc_nj_ui(26, w, 26, 3)["weekly"] - b
    for w, b in zip(wages3, base_vals)
]
ax.fill_between(
    wages3, bump_3, color=GREEN, alpha=0.3, label="3 dependents"
)
ax.fill_between(
    wages3, bump_1, color=ORANGE, alpha=0.4, label="1 dependent"
)
ax.plot(wages3, bump_1, color=ORANGE, linewidth=1.5)
ax.plot(wages3, bump_3, color=GREEN, linewidth=1.5)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Additional weekly benefit", color=GRAY)
ax.set_title(
    "Dependency allowance bump over base benefit",
    fontsize=12,
    color=GRAY,
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
output = "us/states/nj/nj_ui_baseline.png"
plt.savefig(output, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Saved to {output}")
