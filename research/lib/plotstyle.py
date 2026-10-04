"""Shared matplotlib style for all report figures (print, light surface).
Palette: validated reference categorical order (dataviz skill, light mode). Rules for every figure:
- Categorical colors in this fixed order by ENTITY (same series -> same color in every figure); never cycle past 8.
  Scatter/small-multiple forms: at most 3 colors (all-pairs safe), otherwise facet.
- One y-axis per panel (no dual axes). Two measures of different scale -> two panels.
- Thin lines (1.5pt), recessive grid, no top/right spines. Legend whenever >= 2 series; direct-label <= 4 series
  sparingly (end-of-line labels), never a number on every point. Text in ink colors, not series colors.
- Sequential magnitude: one-hue blue ramp. Diverging (e.g. t-stats, correlations): blue <-> red with gray midpoint (use DIVERGING cmap, centered at 0).
- Yellow/magenta/aqua are low-contrast on white: when used, direct-label or pair with a table.
- Save both PDF (for LaTeX) and PNG (dpi 200) via savefig(fig, name).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from common import FIGURES

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = SERIES
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#ffffff"
NEUTRAL_MID = "#f0efec"
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQUENTIAL = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
DIVERGING = LinearSegmentedColormap.from_list("div_blue_red", ["#184f95", "#6da7ec", NEUTRAL_MID, "#f09a99", "#b52f2f"])
# Fixed entity colors so the same concept looks the same across the whole report
ENTITY = {"green": GREEN, "brown": ORANGE, "green_minus_brown": BLUE, "strategy": BLUE, "benchmark": MUTED,
          "emv": ORANGE, "vix": MUTED, "mccc": AQUA, "cpu": VIOLET, "momentum": BLUE, "carbon_constrained": GREEN}

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.labelsize": 9, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "text.color": INK, "axes.edgecolor": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "lines.linewidth": 1.5, "lines.markersize": 5,
    "legend.frameon": False, "legend.fontsize": 8, "axes.prop_cycle": matplotlib.cycler(color=SERIES),
    "figure.constrained_layout.use": True,
})

def savefig(fig, name: str):
    """Save <name>.pdf and <name>.png into outputs/figures. name should be prefixed by module id, e.g. 'M1_emv_vs_vix'."""
    fig.savefig(FIGURES / f"{name}.pdf"); fig.savefig(FIGURES / f"{name}.png")
    plt.close(fig)
