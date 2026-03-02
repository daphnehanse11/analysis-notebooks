"""NJ UI Reform 2: WBR 60% to 70% with household archetypes.

Generates 2 charts:
  1. Annual benefit by household type: 60% vs 70% WBR
  2. Percent increase by household type
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
    s.parameters.gov.states.nj.dol.unemployment_insurance.wbr_rate.update(
        period="year:2026:10", value=0.70
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
        "annual": float(
            sim.calculate("nj_unemployment_insurance", YEAR)[0]
        )
    }


base_sys, ref_sys = make_system(), make_reform()
households = [
    ("Part-time retail", 22, 14_000, 22, 0),
    ("Seasonal construction", 30, 36_000, 20, 2),
    ("Single parent, service", 40, 28_000, 26, 1),
    ("Office worker", 48, 52_000, 26, 0),
    ("Parent of 3, mid-career", 50, 65_000, 26, 3),
    ("Tech worker", 52, 104_000, 26, 0),
]
print("Computing...")
bl = [calc(base_sys, *h[1:])["annual"] for h in households]
rf = [calc(ref_sys, *h[1:])["annual"] for h in households]
labels = [h[0] for h in households]

# Chart 1: Annual benefit by household type
fig1 = go.Figure()
fig1.add_trace(
    go.Bar(
        y=labels,
        x=bl,
        orientation="h",
        name="Baseline (60% WBR)",
        marker_color=GRAY_LIGHTER,
        text=[f"${v:,.0f}" for v in bl],
        textposition="outside",
        textfont=dict(size=11),
    )
)
fig1.add_trace(
    go.Bar(
        y=labels,
        x=rf,
        orientation="h",
        name="Reform (70% WBR)",
        marker_color=TEAL,
        text=[
            f"${v:,.0f} (+${r - b:,.0f})"
            for v, r, b in zip(rf, rf, bl)
        ],
        textposition="outside",
        textfont=dict(size=11),
    )
)
fig1.update_layout(barmode="group", bargap=0.3)
fig1 = format_fig(
    fig1,
    "Annual benefit by household type: 60% vs 70% WBR",
    height=500,
    width=900,
)
fig1.update_xaxes(title="Annual UI benefit", tickformat="$,.0f")
fig1.write_image(
    os.path.join(OUT, "annual_benefit_by_household_60_vs_70_wbr.png"), scale=2
)

# Chart 2: Percent increase
pct = [
    (r - b) / b * 100 if b > 0 else 0
    for r, b in zip(rf, bl)
]
fig2 = go.Figure()
fig2.add_trace(
    go.Bar(
        y=labels,
        x=pct,
        orientation="h",
        marker_color=[
            TEAL if p > 5 else GRAY_LIGHT for p in pct
        ],
        text=[f"{p:.1f}%" for p in pct],
        textposition="outside",
    )
)
fig2 = format_fig(
    fig2,
    "Who benefits most from 70% WBR?",
    height=450,
    width=800,
)
fig2.update_xaxes(
    title="Percent increase in annual benefit", ticksuffix="%"
)
fig2.write_image(
    os.path.join(OUT, "percent_increase_by_household_70_wbr.png"), scale=2
)

print("Done — 2 reform 2 charts saved")
