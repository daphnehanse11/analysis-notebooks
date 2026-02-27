"""NJ UI Baseline — interactive Plotly charts with PolicyEngine style."""
import sys; sys.path.insert(0, "/tmp")
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pe_chart_utils import *
from policyengine_us import CountryTaxBenefitSystem
from policyengine_core.simulations import SimulationBuilder

system = CountryTaxBenefitSystem()

def calc(base_weeks, base_wages, weeks_claimed, num_dependents=0, year=2026):
    people = {"adult": {"age": {year: 35}, "is_tax_unit_dependent": {year: False}}}
    for i in range(num_dependents):
        people[f"child_{i}"] = {"age": {year: 10 - i}, "is_tax_unit_dependent": {year: True}}
    members = ["adult"] + [f"child_{i}" for i in range(num_dependents)]
    situation = {
        "people": people,
        "tax_units": {"tax_unit": {"members": members}},
        "spm_units": {"spm_unit": {"members": members}},
        "households": {"household": {"members": members, "state_code": {year: "NJ"}}},
    }
    situation["people"]["adult"]["nj_unemployment_insurance_base_period_weeks"] = {year: base_weeks}
    situation["people"]["adult"]["nj_unemployment_insurance_base_period_wages"] = {year: base_wages}
    situation["people"]["adult"]["nj_unemployment_insurance_weeks_claimed"] = {year: weeks_claimed}
    sim = SimulationBuilder().build_from_dict(system, situation)
    return {
        "wbr": float(sim.calculate("nj_unemployment_insurance_weekly_benefit_rate", year)[0]),
        "weekly": float(sim.calculate("nj_unemployment_insurance_weekly_benefit", year)[0]),
        "annual": float(sim.calculate("nj_unemployment_insurance", year)[0]),
    }

wages = np.arange(5000, 105001, 5000)

# Chart 1: Weekly benefit by wages and dependents
print("Chart 1...")
fig1 = go.Figure()
for deps, color, name in [(0, TEAL, "No dependents"), (1, BLUE, "1 dependent"), (3, TEAL_DARK, "3 dependents")]:
    weekly = [calc(26, w, 26, deps)["weekly"] for w in wages]
    fig1.add_trace(go.Scatter(x=wages, y=weekly, mode="lines", name=name, line=dict(color=color, width=2.5),
                              hovertemplate="Wages: $%{x:,.0f}<br>Weekly benefit: $%{y:,.2f}<extra>%{fullData.name}</extra>"))
fig1.add_hline(y=905, line_dash="dot", line_color=GRAY_LIGHTER, annotation_text="$905 cap", annotation_position="top right")
fig1 = format_fig(fig1, "Weekly benefit by wages and dependents")
fig1.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig1.update_yaxes(title="Weekly benefit", tickformat="$,.0f")
fig1.write_html("/tmp/nj_ui_baseline_1.html")

# Chart 2: Annual benefit by weeks worked
print("Chart 2...")
fig2 = go.Figure()
weeks_range = list(range(20, 53, 2))
for wage, color, name in [(30_000, TEAL, "$30k wages"), (50_000, BLUE, "$50k wages"), (80_000, TEAL_DARK, "$80k wages")]:
    annual = [calc(w, wage, 26)["annual"] for w in weeks_range]
    fig2.add_trace(go.Scatter(x=weeks_range, y=annual, mode="lines", name=name, line=dict(color=color, width=2.5),
                              hovertemplate="Base weeks: %{x}<br>Annual benefit: $%{y:,.0f}<extra>%{fullData.name}</extra>"))
fig2.add_vline(x=26, line_dash="dot", line_color=GRAY_LIGHTER, annotation_text="26-week cap")
fig2 = format_fig(fig2, "Annual benefit by weeks worked")
fig2.update_xaxes(title="Base period weeks worked")
fig2.update_yaxes(title="Annual benefit", tickformat="$,.0f")
fig2.write_html("/tmp/nj_ui_baseline_2.html")

# Chart 3: Replacement rate
print("Chart 3...")
fig3 = go.Figure()
wages2 = np.arange(10000, 120001, 5000)
replacement = [calc(26, w, 26)["weekly"] / (w / 26) * 100 for w in wages2]
fig3.add_trace(go.Scatter(x=wages2, y=replacement, mode="lines", line=dict(color=TEAL, width=2.5), name="Replacement rate",
                          hovertemplate="Wages: $%{x:,.0f}<br>Replacement: %{y:.1f}%<extra></extra>"))
fig3.add_hline(y=60, line_dash="dot", line_color=GRAY_LIGHTER, annotation_text="60% statutory rate")
fig3 = format_fig(fig3, "Wage replacement rate (26 base weeks, no dependents)")
fig3.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig3.update_yaxes(title="Replacement rate (%)", ticksuffix="%", range=[0, 70])
fig3.write_html("/tmp/nj_ui_baseline_3.html")

# Chart 4: Dependency bump
print("Chart 4...")
fig4 = go.Figure()
wages3 = np.arange(10000, 105001, 5000)
base_vals = [calc(26, w, 26, 0)["weekly"] for w in wages3]
bump_1 = [calc(26, w, 26, 1)["weekly"] - b for w, b in zip(wages3, base_vals)]
bump_3 = [calc(26, w, 26, 3)["weekly"] - b for w, b in zip(wages3, base_vals)]
fig4.add_trace(go.Scatter(x=wages3, y=bump_3, fill="tozeroy", fillcolor="rgba(49,151,149,0.15)", line=dict(color=TEAL_DARK, width=2), name="3 dependents",
                          hovertemplate="Wages: $%{x:,.0f}<br>Bonus: $%{y:,.2f}/week<extra>3 dependents</extra>"))
fig4.add_trace(go.Scatter(x=wages3, y=bump_1, fill="tozeroy", fillcolor="rgba(14,165,233,0.2)", line=dict(color=BLUE, width=2), name="1 dependent",
                          hovertemplate="Wages: $%{x:,.0f}<br>Bonus: $%{y:,.2f}/week<extra>1 dependent</extra>"))
fig4 = format_fig(fig4, "Dependency allowance bump over base benefit")
fig4.update_xaxes(title="Base year wages", tickformat="$,.0f")
fig4.update_yaxes(title="Additional weekly benefit", tickformat="$,.0f")
fig4.write_html("/tmp/nj_ui_baseline_4.html")

print("Done — 4 charts saved")
