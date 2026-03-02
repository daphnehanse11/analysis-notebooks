"""Shared PolicyEngine chart utilities."""
import os
import plotly.graph_objects as go

# PolicyEngine design tokens
TEAL = "#319795"
TEAL_LIGHT = "#38B2AC"
TEAL_DARK = "#285E61"
TEAL_DARKER = "#234E52"
BLUE = "#0EA5E9"
BLUE_DARK = "#026AA2"
GRAY = "#4B5563"
GRAY_LIGHT = "#6B7280"
GRAY_LIGHTER = "#E2E8F0"
RED = "#EF4444"
GREEN = "#22C55E"
WARNING = "#FEC601"

SERIES_COLORS = [TEAL, BLUE, TEAL_DARK, BLUE_DARK, GRAY]
FONT = "Inter"
LOGO_URL = "https://raw.githubusercontent.com/PolicyEngine/policyengine-app-v2/main/app/public/assets/logos/policyengine/teal.png"

def format_fig(fig, title=None, height=600, width=800):
    fig.update_layout(
        font=dict(family=FONT, color="black", size=14),
        plot_bgcolor="white",
        paper_bgcolor="white",
        template="plotly_white",
        height=height,
        width=width,
        margin=dict(l=60, r=40, t=60 if title else 40, b=80),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color="rgba(0,0,0,0)"),
        title=dict(text=title, font=dict(size=18)) if title else None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
    )
    fig.add_layout_image(dict(
        source=LOGO_URL,
        xref="paper", yref="paper",
        x=1.0, y=-0.12,
        sizex=0.10, sizey=0.10,
        xanchor="right", yanchor="bottom",
    ))
    return fig


def save(fig, path):
    """Save figure as PNG (2x scale for retina)."""
    fig.write_image(path, scale=2)
    print(f"  Saved {os.path.basename(path)}")
