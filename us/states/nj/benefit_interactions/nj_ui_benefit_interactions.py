"""NJ UI benefit interactions — how job loss affects the full benefit stack.

Models a single parent with 2 children (ages 8, 5), head of household.
Compares employed vs unemployed (on NJ UI) across wage levels.

Note: nj_unemployment_insurance doesn't feed into unemployment_compensation,
so we compute NJ UI separately and pass it as unemployment_compensation input.

Generates 4 charts:
  1. Employed: income + benefits stack
  2. Unemployed on UI: benefits stack
  3. Net income gap from job loss
  4. How other benefits shift when you lose your job
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


def calc_ui(base_wages):
    system = make_system()
    sit = {
        "people": {
            "a": {
                "age": {YEAR: 35},
                "is_tax_unit_dependent": {YEAR: False},
                "nj_unemployment_insurance_base_period_weeks": {
                    YEAR: 26
                },
                "nj_unemployment_insurance_base_period_wages": {
                    YEAR: base_wages
                },
                "nj_unemployment_insurance_weeks_claimed": {
                    YEAR: 26
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
    return float(
        sim.calculate("nj_unemployment_insurance", YEAR)[0]
    )


def make_hh(employment_income=0, unemployment_comp=0):
    system = make_system()
    sit = {
        "people": {
            "parent": {
                "age": {YEAR: 35},
                "is_tax_unit_dependent": {YEAR: False},
                "employment_income": {YEAR: employment_income},
                "unemployment_compensation": {
                    YEAR: unemployment_comp
                },
            },
            "child1": {
                "age": {YEAR: 8},
                "is_tax_unit_dependent": {YEAR: True},
            },
            "child2": {
                "age": {YEAR: 5},
                "is_tax_unit_dependent": {YEAR: True},
            },
        },
        "tax_units": {
            "t": {
                "members": ["parent", "child1", "child2"],
                "filing_status": {YEAR: "HEAD_OF_HOUSEHOLD"},
            }
        },
        "families": {
            "f": {"members": ["parent", "child1", "child2"]}
        },
        "spm_units": {
            "s": {"members": ["parent", "child1", "child2"]}
        },
        "households": {
            "h": {
                "members": ["parent", "child1", "child2"],
                "state_code": {YEAR: "NJ"},
            }
        },
    }
    sim = SimulationBuilder().build_from_dict(system, sit)
    return {
        "ui": unemployment_comp,
        "emp": employment_income,
        "eitc": float(sim.calculate("eitc", YEAR)[0]),
        "ctc": float(sim.calculate("ctc", YEAR)[0]),
        "snap": float(sim.calculate("snap", YEAR)[0]),
        "meals": float(
            sim.calculate("free_school_meals", YEAR)[0]
        )
        + float(
            sim.calculate("reduced_price_school_meals", YEAR)[0]
        ),
        "hh_net": float(
            sim.calculate("household_net_income", YEAR)[0]
        ),
    }


wages = list(range(15000, 90001, 5000))
print("Computing UI amounts...")
ui_amts = {w: calc_ui(w) for w in wages}
print("Computing employed households...")
emp = [make_hh(employment_income=w) for w in wages]
print("Computing unemployed households...")
unemp = [make_hh(unemployment_comp=ui_amts[w]) for w in wages]

# Chart 1: Stacked employed
fig1 = go.Figure()
layers = [
    ([e["emp"] for e in emp], "rgba(49,151,149,0.8)", "Earnings"),
    ([e["eitc"] for e in emp], "rgba(34,197,94,0.8)", "EITC"),
    ([e["ctc"] for e in emp], "rgba(14,165,233,0.8)", "CTC"),
    ([e["snap"] for e in emp], "rgba(40,94,97,0.8)", "SNAP"),
    (
        [e["meals"] for e in emp],
        "rgba(107,114,128,0.8)",
        "School meals",
    ),
]
for vals, color, name in layers:
    fig1.add_trace(
        go.Scatter(
            x=wages,
            y=vals,
            stackgroup="one",
            name=name,
            line=dict(width=0.5, color=color),
            fillcolor=color,
            hovertemplate=f"{name}: $%{{y:,.0f}}<extra></extra>",
        )
    )
fig1 = format_fig(fig1, "Employed: income + benefits stack")
fig1.update_xaxes(title="Annual wages", tickformat="$,.0f")
fig1.update_yaxes(title="Total resources", tickformat="$,.0f")
fig1.write_html(
    os.path.join(OUT, "employed_income_and_benefits_stack.html")
)

# Chart 2: Stacked unemployed
fig2 = go.Figure()
layers2 = [
    (
        [u["ui"] for u in unemp],
        "rgba(239,68,68,0.8)",
        "NJ UI",
    ),
    (
        [u["eitc"] for u in unemp],
        "rgba(34,197,94,0.8)",
        "EITC",
    ),
    (
        [u["ctc"] for u in unemp],
        "rgba(14,165,233,0.8)",
        "CTC",
    ),
    (
        [u["snap"] for u in unemp],
        "rgba(40,94,97,0.8)",
        "SNAP",
    ),
    (
        [u["meals"] for u in unemp],
        "rgba(107,114,128,0.8)",
        "School meals",
    ),
]
for vals, color, name in layers2:
    fig2.add_trace(
        go.Scatter(
            x=wages,
            y=vals,
            stackgroup="one",
            name=name,
            line=dict(width=0.5, color=color),
            fillcolor=color,
            hovertemplate=f"{name}: $%{{y:,.0f}}<extra></extra>",
        )
    )
fig2 = format_fig(fig2, "Unemployed on UI: benefits stack")
fig2.update_xaxes(title="Prior annual wages", tickformat="$,.0f")
fig2.update_yaxes(title="Total resources", tickformat="$,.0f")
fig2.write_html(
    os.path.join(OUT, "unemployed_benefits_stack.html")
)

# Chart 3: Net income gap
fig3 = go.Figure()
e_net = [e["hh_net"] for e in emp]
u_net = [u["hh_net"] for u in unemp]
fig3.add_trace(
    go.Scatter(
        x=wages,
        y=e_net,
        mode="lines",
        name="Employed",
        line=dict(color=TEAL, width=2.5),
    )
)
fig3.add_trace(
    go.Scatter(
        x=wages,
        y=u_net,
        mode="lines",
        name="Unemployed (on UI)",
        line=dict(color=RED, width=2.5),
        fill="tonexty",
        fillcolor="rgba(239,68,68,0.1)",
    )
)
for idx in [1, 5, 10, 14]:
    if idx < len(wages):
        pct = (
            u_net[idx] / e_net[idx] * 100
            if e_net[idx] > 0
            else 0
        )
        fig3.add_annotation(
            x=wages[idx],
            y=(e_net[idx] + u_net[idx]) / 2,
            text=f"{pct:.0f}%",
            showarrow=False,
            font=dict(color=RED, size=12, family=FONT),
        )
fig3 = format_fig(fig3, "Net income: the gap from job loss")
fig3.update_xaxes(
    title="Annual wages / prior wages", tickformat="$,.0f"
)
fig3.update_yaxes(
    title="Household net income", tickformat="$,.0f"
)
fig3.write_html(
    os.path.join(OUT, "net_income_gap_employed_vs_unemployed.html")
)

# Chart 4: Benefit deltas
fig4 = go.Figure()
d_eitc = [
    u["eitc"] - e["eitc"] for u, e in zip(unemp, emp)
]
d_snap = [
    u["snap"] - e["snap"] for u, e in zip(unemp, emp)
]
d_ctc = [u["ctc"] - e["ctc"] for u, e in zip(unemp, emp)]
d_meals = [
    u["meals"] - e["meals"] for u, e in zip(unemp, emp)
]
fig4.add_trace(
    go.Scatter(
        x=wages,
        y=d_eitc,
        mode="lines",
        name="EITC",
        line=dict(color=RED, width=2.5),
    )
)
fig4.add_trace(
    go.Scatter(
        x=wages,
        y=d_snap,
        mode="lines",
        name="SNAP",
        line=dict(color=TEAL, width=2.5),
    )
)
fig4.add_trace(
    go.Scatter(
        x=wages,
        y=d_ctc,
        mode="lines",
        name="CTC",
        line=dict(color=BLUE, width=2.5),
    )
)
fig4.add_trace(
    go.Scatter(
        x=wages,
        y=d_meals,
        mode="lines",
        name="School meals",
        line=dict(color=GRAY_LIGHT, width=2.5),
    )
)
fig4.add_hline(y=0, line_dash="dot", line_color=GRAY_LIGHTER)
fig4 = format_fig(
    fig4, "How other benefits shift when you lose your job"
)
fig4.update_xaxes(title="Wage level", tickformat="$,.0f")
fig4.update_yaxes(
    title="Change in benefit (unemployed \u2212 employed)",
    tickformat="$,.0f",
)
fig4.write_html(
    os.path.join(OUT, "benefit_deltas_from_job_loss.html")
)

print("Done — 4 interaction charts saved")
