"""NJ UI Reform 3: double dependency allowance rates.

Reform: first dependent 7% -> 14%, additional 4% -> 8%, cap 15% -> 30%.

Generates 3 charts:
  1. Weekly benefit with 3 dependents: baseline vs reform
  2. Dollar increase by number of dependents and wage level
  3. Same $40k worker — effect of family size
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotly.graph_objects as go
import numpy as np
from pe_chart_utils import *
from policyengine_us import CountryTaxBenefitSystem
from policyengine_core.simulations import SimulationBuilder

YEAR = 2026
OUT = os.path.dirname(os.path.abspath(__file__))


def make_system():
    return CountryTaxBenefitSystem()


def make_reform():
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


def calc(system, bw, bwg, wc, deps=0):
    people = {
        "a": {
            "age": {YEAR: 35},
            "is_tax_unit_dependent": {YEAR: False},
            "nj_unemployment_insurance_base_period_weeks": {
                YEAR: bw
            },
            "nj_unemployment_insurance_base_period_wages": {
                YEAR: bwg
            },
            "nj_unemployment_insurance_weeks_claimed": {YEAR: wc},
        }
    }
    for i in range(deps):
        people[f"c{i}"] = {
            "age": {YEAR: 10 - i},
            "is_tax_unit_dependent": {YEAR: True},
        }
    members = ["a"] + [f"c{i}" for i in range(deps)]
    sit = {
        "people": people,
        "tax_units": {"t": {"members": members}},
        "spm_units": {"s": {"members": members}},
        "households": {
            "h": {"members": members, "state_code": {YEAR: "NJ"}}
        },
    }
    sim = SimulationBuilder().build_from_dict(system, sit)
    return {
        "weekly": float(
            sim.calculate(
                "nj_unemployment_insurance_weekly_benefit", YEAR
            )[0]
        ),
        "annual": float(
            sim.calculate("nj_unemployment_insurance", YEAR)[0]
        ),
    }


base_sys, ref_sys = make_system(), make_reform()

# Chart 1: Weekly benefit with 3 dependents
print("Chart 1: Weekly benefit, 3 deps baseline vs reform...")
wages = np.arange(10000, 105001, 5000)
bl_0 = [calc(base_sys, 26, w, 26, 0)["weekly"] for w in wages]
bl_3 = [calc(base_sys, 26, w, 26, 3)["weekly"] for w in wages]
rf_3 = [calc(ref_sys, 26, w, 26, 3)["weekly"] for w in wages]

fig1 = go.Figure()
fig1.add_trace(
    go.Scatter(
        x=wages,
        y=bl_0,
        mode="lines",
        name="No dependents",
        line=dict(color=GRAY_LIGHTER, width=2, dash="dot"),
    )
)
fig1.add_trace(
    go.Scatter(
        x=wages,
        y=bl_3,
        mode="lines",
        name="3 deps — baseline (15%)",
        line=dict(color=GRAY, width=2.5),
    )
)
fig1.add_trace(
    go.Scatter(
        x=wages,
        y=rf_3,
        mode="lines",
        name="3 deps — reform (30%)",
        line=dict(color=TEAL, width=2.5),
        fill="tonexty",
        fillcolor="rgba(49,151,149,0.12)",
    )
)
fig1 = format_fig(
    fig1, "Weekly benefit: 3 dependents, baseline vs reform"
)
fig1.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig1.update_yaxes(title="Weekly benefit", tickformat="$,.0f")
fig1.write_image(
    os.path.join(OUT, "weekly_benefit_3deps_baseline_vs_doubled.png"), scale=2
)

# Chart 2: Dollar increase by deps and wage level
print("Chart 2: Dollar increase by deps and wage level...")
dep_counts = [0, 1, 2, 3]
wage_levels = [
    (20_000, TEAL, "$20k"),
    (35_000, BLUE, "$35k"),
    (50_000, TEAL_DARK, "$50k"),
    (80_000, GRAY, "$80k"),
]
fig2 = go.Figure()
for wage, color, name in wage_levels:
    increases = [
        calc(ref_sys, 26, wage, 26, d)["annual"]
        - calc(base_sys, 26, wage, 26, d)["annual"]
        for d in dep_counts
    ]
    fig2.add_trace(
        go.Bar(
            x=[str(d) for d in dep_counts],
            y=increases,
            name=f"{name} wages",
            marker_color=color,
            hovertemplate=(
                "Dependents: %{x}<br>"
                "Increase: $%{y:,.0f}"
                "<extra>%{fullData.name}</extra>"
            ),
        )
    )
fig2.update_layout(barmode="group")
fig2 = format_fig(
    fig2, "Dollar increase by dependents and wage level"
)
fig2.update_xaxes(title="Number of dependents")
fig2.update_yaxes(
    title="Annual benefit increase", tickformat="$,.0f"
)
fig2.write_image(
    os.path.join(OUT, "dollar_increase_by_deps_and_wages.png"), scale=2
)

# Chart 3: Same $40k worker, varying family size
print("Chart 3: $40k worker by family size...")
fam = [("No kids", 0), ("1 kid", 1), ("2 kids", 2), ("3 kids", 3)]
bl_v = [
    calc(base_sys, 40, 40_000, 26, d)["annual"] for _, d in fam
]
rf_v = [
    calc(ref_sys, 40, 40_000, 26, d)["annual"] for _, d in fam
]
fig3 = go.Figure()
fig3.add_trace(
    go.Bar(
        y=[f[0] for f in fam],
        x=bl_v,
        orientation="h",
        name="Baseline",
        marker_color=GRAY_LIGHTER,
        text=[f"${v:,.0f}" for v in bl_v],
        textposition="outside",
    )
)
fig3.add_trace(
    go.Bar(
        y=[f[0] for f in fam],
        x=rf_v,
        orientation="h",
        name="Reform",
        marker_color=TEAL,
        text=[
            f"${v:,.0f} (+${r - b:,.0f})"
            for v, r, b in zip(rf_v, rf_v, bl_v)
        ],
        textposition="outside",
    )
)
fig3.update_layout(barmode="group")
fig3 = format_fig(
    fig3,
    "Same $40k worker — effect of family size",
    height=400,
    width=900,
)
fig3.update_xaxes(
    title="Annual UI benefit",
    tickformat="$,.0f",
    range=[0, max(rf_v) * 1.35],
)
fig3.write_image(
    os.path.join(OUT, "family_size_effect_on_40k_worker.png"), scale=2
)

print("Done — 3 reform 3 charts saved")
