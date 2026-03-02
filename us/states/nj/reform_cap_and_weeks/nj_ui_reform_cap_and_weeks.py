"""NJ UI Reform 1: raise cap to $1,000 and extend to 30 weeks.

Generates 4 charts comparing baseline vs reform:
  1. Weekly benefit baseline vs $1,000 cap
  2. Annual benefit 26 weeks vs 30 weeks
  3. Dollar increase from reform
  4. Percent increase from reform
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
    p.max_weekly_benefit.update(
        period="year:2026:10", value=1000
    )
    p.max_benefit_weeks.update(period="year:2026:10", value=30)
    return s


def calc(system, bw, bwg, wc):
    sit = {
        "people": {
            "a": {
                "age": {YEAR: 35},
                "is_tax_unit_dependent": {YEAR: False},
                "nj_unemployment_insurance_base_period_weeks": {
                    YEAR: bw
                },
                "nj_unemployment_insurance_base_period_wages": {
                    YEAR: bwg
                },
                "nj_unemployment_insurance_weeks_claimed": {
                    YEAR: wc
                },
            }
        },
        "tax_units": {"t": {"members": ["a"]}},
        "spm_units": {"s": {"members": ["a"]}},
        "households": {
            "h": {"members": ["a"], "state_code": {YEAR: "NJ"}}
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


wages = np.arange(5000, 120001, 5000)
base_sys, ref_sys = make_system(), make_reform()
print("Computing...")
bl_w = [calc(base_sys, 30, w, 30)["weekly"] for w in wages]
rf_w = [calc(ref_sys, 30, w, 30)["weekly"] for w in wages]
bl_a = [calc(base_sys, 40, w, 40)["annual"] for w in wages]
rf_a = [calc(ref_sys, 40, w, 40)["annual"] for w in wages]

# Chart 1: Weekly benefit
fig1 = go.Figure()
fig1.add_trace(
    go.Scatter(
        x=wages,
        y=bl_w,
        mode="lines",
        name="Baseline ($905 cap)",
        line=dict(color=GRAY, width=2.5),
    )
)
fig1.add_trace(
    go.Scatter(
        x=wages,
        y=rf_w,
        mode="lines",
        name="Reform ($1,000 cap)",
        line=dict(color=TEAL, width=2.5),
        fill="tonexty",
        fillcolor="rgba(49,151,149,0.12)",
    )
)
fig1 = format_fig(fig1, "Weekly benefit: baseline vs. reform")
fig1.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig1.update_yaxes(title="Weekly benefit", tickformat="$,.0f")
fig1.write_html(
    os.path.join(OUT, "weekly_benefit_baseline_vs_1000_cap.html")
)

# Chart 2: Annual benefit
fig2 = go.Figure()
fig2.add_trace(
    go.Scatter(
        x=wages,
        y=bl_a,
        mode="lines",
        name="Baseline (26 wks)",
        line=dict(color=GRAY, width=2.5),
    )
)
fig2.add_trace(
    go.Scatter(
        x=wages,
        y=rf_a,
        mode="lines",
        name="Reform (30 wks)",
        line=dict(color=TEAL, width=2.5),
        fill="tonexty",
        fillcolor="rgba(49,151,149,0.12)",
    )
)
fig2 = format_fig(
    fig2, "Annual benefit (40 base weeks, claiming max)"
)
fig2.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig2.update_yaxes(title="Annual benefit", tickformat="$,.0f")
fig2.write_html(
    os.path.join(OUT, "annual_benefit_26_vs_30_weeks.html")
)

# Chart 3: Dollar increase
inc = [r - b for r, b in zip(rf_a, bl_a)]
fig3 = go.Figure()
fig3.add_trace(
    go.Bar(
        x=wages,
        y=inc,
        marker_color=TEAL,
        name="Increase",
        hovertemplate=(
            "Wages: $%{x:,.0f}<br>"
            "Increase: $%{y:,.0f}<extra></extra>"
        ),
    )
)
fig3 = format_fig(
    fig3, "Dollar increase from reform (40 base weeks)"
)
fig3.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig3.update_yaxes(
    title="Additional annual benefit", tickformat="$,.0f"
)
fig3.write_html(
    os.path.join(OUT, "dollar_increase_from_cap_and_weeks_reform.html")
)

# Chart 4: Percent increase
pct = [
    (r - b) / b * 100 if b > 0 else 0
    for r, b in zip(rf_a, bl_a)
]
fig4 = go.Figure()
fig4.add_trace(
    go.Bar(
        x=wages,
        y=pct,
        marker_color=TEAL,
        name="% increase",
        hovertemplate=(
            "Wages: $%{x:,.0f}<br>"
            "Increase: %{y:.1f}%<extra></extra>"
        ),
    )
)
fig4 = format_fig(
    fig4, "Percent increase from reform (40 base weeks)"
)
fig4.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig4.update_yaxes(title="Percent increase", ticksuffix="%")
fig4.write_html(
    os.path.join(OUT, "percent_increase_from_cap_and_weeks_reform.html")
)

print("Done — 4 reform 1 charts saved")
