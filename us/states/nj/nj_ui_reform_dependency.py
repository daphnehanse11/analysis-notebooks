"""
NJ UI Reform: double dependency allowance rates.

Compares baseline (7%/4%/15% cap) against a reform doubling all
dependency parameters to 14%/8%/30% cap. This reform exclusively
helps parents and is most impactful for low-to-mid earners with
multiple children.
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
        "dep_rate": float(
            sim.calculate(
                "nj_unemployment_insurance_dependency_allowance", year
            )[0]
        ),
        "wbr": float(
            sim.calculate(
                "nj_unemployment_insurance_weekly_benefit_rate", year
            )[0]
        ),
    }


def make_dep_reform_system():
    s = CountryTaxBenefitSystem()
    p = s.parameters.gov.states.nj.dol.unemployment_insurance
    p.dependency_allowance_first.update(
        period="year:2026:10", value=0.14
    )
    p.dependency_allowance_additional.update(
        period="year:2026:10", value=0.08
    )
    p.max_dependency_allowance.update(
        period="year:2026:10", value=0.30
    )
    return s


BLUE = "#1a73e8"
RED = "#d93025"
ORANGE = "#e8710a"
GREEN = "#0d904f"
PURPLE = "#7b2ff7"
GRAY = "#333333"
LIGHT_GRAY = "#999999"

base_sys = make_system()
ref_sys = make_dep_reform_system()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(
    "NJ UI reform: double dependency allowance (7/4/15% → 14/8/30%)",
    fontsize=14,
    fontweight="bold",
    color=GRAY,
    y=0.97,
)

# Chart 1: Weekly benefit by wages for 0 vs 3 dependents
print("Chart 1...")
ax = axes[0, 0]
wages = np.arange(10000, 105001, 5000)
bl_0dep = [calc(base_sys, 26, w, 26, 0)["weekly"] for w in wages]
bl_3dep = [calc(base_sys, 26, w, 26, 3)["weekly"] for w in wages]
rf_3dep = [calc(ref_sys, 26, w, 26, 3)["weekly"] for w in wages]

ax.plot(
    wages,
    bl_0dep,
    color=LIGHT_GRAY,
    linewidth=2,
    linestyle="--",
    label="No dependents (unchanged)",
)
ax.plot(
    wages,
    bl_3dep,
    color=BLUE,
    linewidth=2,
    label="3 deps — baseline (15%)",
)
ax.plot(
    wages,
    rf_3dep,
    color=RED,
    linewidth=2,
    label="3 deps — reform (30%)",
)
ax.fill_between(wages, bl_3dep, rf_3dep, alpha=0.12, color=RED)
ax.axhline(
    y=905, color=LIGHT_GRAY, linestyle=":", linewidth=1, alpha=0.5
)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Weekly benefit", color=GRAY)
ax.set_title(
    "Weekly benefit: 3 dependents, baseline vs reform",
    fontsize=12,
    color=GRAY,
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.legend(frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)

# Chart 2: Annual increase by dependents at different wage levels
print("Chart 2...")
ax = axes[0, 1]
dep_counts = [0, 1, 2, 3]
wage_levels = [
    (20_000, BLUE, "$20k wages"),
    (35_000, ORANGE, "$35k wages"),
    (50_000, GREEN, "$50k wages"),
    (80_000, PURPLE, "$80k wages"),
]
x = np.arange(len(dep_counts))
width = 0.18
for i, (wage, color, label) in enumerate(wage_levels):
    increases = []
    for deps in dep_counts:
        bl = calc(base_sys, 26, wage, 26, deps)["annual"]
        rf = calc(ref_sys, 26, wage, 26, deps)["annual"]
        increases.append(rf - bl)
    ax.bar(
        x + (i - 1.5) * width,
        increases,
        width,
        color=color,
        alpha=0.75,
        label=label,
    )

ax.set_xticks(x)
ax.set_xticklabels(["0", "1", "2", "3"])
ax.set_xlabel("Number of dependents", color=GRAY)
ax.set_ylabel("Annual benefit increase", color=GRAY)
ax.set_title(
    "Dollar increase by dependents and wage level",
    fontsize=12,
    color=GRAY,
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.legend(frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)

# Chart 3: Same worker, varying family size
print("Chart 3...")
ax = axes[1, 0]
archetypes = [
    ("Single,\nno kids", 40, 40_000, 26, 0),
    ("Single,\n1 kid", 40, 40_000, 26, 1),
    ("Single,\n2 kids", 40, 40_000, 26, 2),
    ("Single,\n3 kids", 40, 40_000, 26, 3),
]
labels = [a[0] for a in archetypes]
bl_vals = [calc(base_sys, *a[1:])["annual"] for a in archetypes]
rf_vals = [calc(ref_sys, *a[1:])["annual"] for a in archetypes]

y = np.arange(len(labels))
ax.barh(y + 0.15, bl_vals, 0.3, color=BLUE, alpha=0.8, label="Baseline")
ax.barh(y - 0.15, rf_vals, 0.3, color=RED, alpha=0.8, label="Reform")
for i, (b, r) in enumerate(zip(bl_vals, rf_vals)):
    ax.text(
        b + 150,
        i + 0.15,
        f"${b:,.0f}",
        va="center",
        fontsize=9,
        color=GRAY,
    )
    ax.text(
        r + 150,
        i - 0.15,
        f"${r:,.0f} (+${r-b:,.0f})",
        va="center",
        fontsize=9,
        color=RED,
    )
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=10)
ax.set_xlabel("Annual UI benefit", color=GRAY)
ax.set_title(
    "Same $40k worker — effect of family size",
    fontsize=12,
    color=GRAY,
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.legend(frameon=False, fontsize=9, loc="lower right")
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(0, max(rf_vals) * 1.25)

# Chart 4: Dependency bonus in weekly dollars
print("Chart 4...")
ax = axes[1, 1]
wages2 = np.arange(10000, 90001, 5000)
bl_bonus_1, rf_bonus_1, bl_bonus_3, rf_bonus_3 = [], [], [], []
for w in wages2:
    b0 = calc(base_sys, 26, w, 26, 0)["weekly"]
    b1 = calc(base_sys, 26, w, 26, 1)["weekly"]
    b3 = calc(base_sys, 26, w, 26, 3)["weekly"]
    r1 = calc(ref_sys, 26, w, 26, 1)["weekly"]
    r3 = calc(ref_sys, 26, w, 26, 3)["weekly"]
    bl_bonus_1.append(b1 - b0)
    bl_bonus_3.append(b3 - b0)
    rf_bonus_1.append(r1 - b0)
    rf_bonus_3.append(r3 - b0)

ax.fill_between(
    wages2, rf_bonus_3, color=RED, alpha=0.15, label="3 deps reform"
)
ax.fill_between(
    wages2, bl_bonus_3, color=BLUE, alpha=0.15, label="3 deps baseline"
)
ax.plot(wages2, rf_bonus_3, color=RED, linewidth=2)
ax.plot(wages2, bl_bonus_3, color=BLUE, linewidth=2)
ax.plot(wages2, rf_bonus_1, color=RED, linewidth=1.5, linestyle="--")
ax.plot(wages2, bl_bonus_1, color=BLUE, linewidth=1.5, linestyle="--")
ax.text(55000, 45, "3 deps", fontsize=9, color=GRAY)
ax.text(55000, 12, "1 dep", fontsize=9, color=GRAY)
ax.set_xlabel("Base year wages", color=GRAY)
ax.set_ylabel("Weekly $ bonus over no-dependent baseline", color=GRAY)
ax.set_title(
    "Dependency bonus: extra $/week (solid=3, dashed=1)",
    fontsize=12,
    color=GRAY,
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.legend(frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
output = "us/states/nj/nj_ui_reform_dependency.png"
plt.savefig(output, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Saved to {output}")
