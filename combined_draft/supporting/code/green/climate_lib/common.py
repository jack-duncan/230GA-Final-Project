"""Minimal data loaders for the Climate Alpha summary (subset of research/lib/common.py
in 230GA-Final-Project-hashim-research-extension). Reads the team's four input files from data/green."""
from __future__ import annotations
import pathlib
import pandas as pd

DATA = pathlib.Path(__file__).resolve().parents[4] / "data" / "green"   # final_submission_organized/data/green


def me(idx) -> pd.DatetimeIndex:
    """Coerce any date-like index to month-end timestamps."""
    return pd.DatetimeIndex(pd.to_datetime(idx)) + pd.offsets.MonthEnd(0)


def load_team():
    """Return the team's four input files exactly as the team used them."""
    emis = pd.read_csv(DATA / "emissions_ff_industry.csv")
    emis.columns = emis.columns.str.strip().str.lower(); emis["ff"] = emis["ff"].str.strip()
    ind = pd.read_csv(DATA / "ff49_industry_monthly.csv", parse_dates=["date"]).set_index("date")
    ff3 = pd.read_csv(DATA / "ff3_factors_monthly.csv", parse_dates=["date"]).set_index("date")
    macro = pd.read_csv(DATA / "macro_monthly.csv", parse_dates=["date"]).set_index("date")
    for d in (ind, ff3, macro):
        d.index = me(d.index)
    return {"emissions": emis.set_index("ff")["emissions_intensity"].astype(float).sort_values(),
            "industries": ind, "ff3": ff3, "macro": macro}


def corrected_macro():
    """Corrected baseline inputs (extension module M3): the missing October 2025 CPI print is
    linearly interpolated. Attention and purification controls are lagged one month by the caller."""
    mac = load_team()["macro"].copy()
    mac["cpi"] = mac["cpi"].interpolate(limit_area="inside")
    return mac
