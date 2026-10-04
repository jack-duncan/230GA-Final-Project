"""Shared data loaders and statistics for the MFE 230GA final-project research exercise.

Every module imports from here so definitions (dates, legs, factors, periods, t-stats) are identical.
Conventions: monthly data indexed by month-end Timestamps; returns are decimals (0.01 = 1%);
annualization = 12x mean, sqrt(12)x std. Team baseline inputs are read from the read-only repo clone.
"""
from __future__ import annotations
import io, pathlib, re
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = pathlib.Path(__file__).resolve().parents[1]           # .../project/research
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
TEAM = ROOT.parent / "230GA-Final-Project"                    # read-only clone of the shared repo
if not TEAM.exists() and (ROOT.parent / "notebooks").exists():  # research/ checked into the team repo itself
    TEAM = ROOT.parent
TEAM_DATA = TEAM / "data"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
for p in (DERIVED, TABLES, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------- periods
# Brief asks for full sample, post-2010, and the recent 12-18 months. Team's design windows kept for comparability.
LAST_MONTH = pd.Timestamp("2026-07-31")   # last month with FF49 returns in the team file
PERIODS = {
    "full_1970": ("1970-01-31", "2026-07-31"),
    "post2010": ("2010-01-31", "2026-07-31"),
    "validation": ("2010-01-31", "2022-07-31"),   # team's design sample
    "holdout": ("2022-08-31", "2026-07-31"),      # team's frozen holdout
    "pre_covid": ("2010-01-31", "2019-12-31"),
    "covid": ("2020-01-31", "2021-12-31"),
    "inflation_rates": ("2022-01-31", "2024-12-31"),
    "last18": ("2025-02-28", "2026-07-31"),
    "last12": ("2025-08-31", "2026-07-31"),
}

def me(idx) -> pd.DatetimeIndex:
    """Coerce any date-like index to month-end timestamps."""
    return pd.DatetimeIndex(pd.to_datetime(idx)) + pd.offsets.MonthEnd(0)

# ----------------------------------------------------------------------------- team baseline data
def load_team():
    """Return dict with the team's four input files exactly as the team used them."""
    emis = pd.read_csv(TEAM_DATA / "emissions_ff_industry.csv")
    emis.columns = emis.columns.str.strip().str.lower(); emis["ff"] = emis["ff"].str.strip()
    ind = pd.read_csv(TEAM_DATA / "ff49_industry_monthly.csv", parse_dates=["date"]).set_index("date")
    ff3 = pd.read_csv(TEAM_DATA / "ff3_factors_monthly.csv", parse_dates=["date"]).set_index("date")
    macro = pd.read_csv(TEAM_DATA / "macro_monthly.csv", parse_dates=["date"]).set_index("date")
    for d in (ind, ff3, macro):
        d.index = me(d.index)
    return {"emissions": emis.set_index("ff")["emissions_intensity"].astype(float).sort_values(),
            "industries": ind, "ff3": ff3, "macro": macro}

def legs_by_emissions(n: int = 5, emissions: pd.Series | None = None, exclude=()):
    """Green = n lowest-intensity industries, Brown = n highest (team convention, equal-weighted legs)."""
    e = (emissions if emissions is not None else load_team()["emissions"]).drop(list(exclude), errors="ignore").sort_values()
    return list(e.index[:n]), list(e.index[::-1][:n])

def leg_returns(industries: pd.DataFrame, green, brown):
    g, b = industries[green].mean(axis=1), industries[brown].mean(axis=1)
    return g.rename("green"), b.rename("brown"), (g - b).rename("green_minus_brown")

# ----------------------------------------------------------------------------- Ken French library
def _kf_sections(path):
    """Split a Ken French CSV into {section title: DataFrame}; values -99.99/-999 -> NaN; percent -> decimal."""
    lines = pathlib.Path(path).read_text(errors="ignore").splitlines()
    out, title, buf = {}, "main", []
    def flush():
        if buf and len(buf) > 1:
            df = pd.read_csv(io.StringIO("\n".join(buf)), index_col=0)
            df.columns = [c.strip() for c in df.columns]
            df.index = df.index.astype(str).str.strip()
            out[title] = df.replace([-99.99, -999, -99.990], np.nan)
    for ln in lines:
        s = ln.strip()
        if s.startswith(",") and not buf:
            buf = [ln]; continue
        if buf and re.match(r"^\s*\d{4,6}\s*,", ln):
            buf.append(ln); continue
        if buf:
            flush(); buf = []
        if s and not s.startswith(","):
            title = s
    flush()
    return out

def _kf_monthly(df):
    df = df[df.index.str.len() == 6].copy()
    df.index = pd.to_datetime(df.index, format="%Y%m") + pd.offsets.MonthEnd(0)
    return df.astype(float)

def load_ff5_mom():
    """FF5 + UMD + ST/LT reversal, monthly decimals, month-end index. Columns: Mkt-RF SMB HML RMW CMA RF UMD STREV LTREV."""
    ff5 = _kf_monthly(list(_kf_sections(RAW / "kf_F-F_Research_Data_5_Factors_2x3.csv").values())[0]) / 100
    mom = _kf_monthly(list(_kf_sections(RAW / "kf_F-F_Momentum_Factor.csv").values())[0]) / 100
    st = _kf_monthly(list(_kf_sections(RAW / "kf_F-F_ST_Reversal_Factor.csv").values())[0]) / 100
    lt = _kf_monthly(list(_kf_sections(RAW / "kf_F-F_LT_Reversal_Factor.csv").values())[0]) / 100
    out = ff5.join(mom.iloc[:, 0].rename("UMD"), how="left").join(st.iloc[:, 0].rename("STREV"), how="left").join(lt.iloc[:, 0].rename("LTREV"), how="left")
    return out

def load_kf_ff3():
    return _kf_monthly(list(_kf_sections(RAW / "kf_F-F_Research_Data_Factors.csv").values())[0]) / 100

def load_kf_industries(kind: str = "vw"):
    """49 industries from the Ken French download (Aug 2026 CRSP vintage). kind in {'vw','ew'}: monthly decimals.
    kind in {'nfirms','size'}: monthly levels. kind in {'be_me_sum','be_me_vw'}: annual, indexed at June 30 of the
    formation year (usable from July of that year onward)."""
    secs = _kf_sections(RAW / "kf_49_Industry_Portfolios.csv")
    key = {"vw": "Average Value Weighted Returns -- Monthly", "ew": "Average Equal Weighted Returns -- Monthly",
           "nfirms": "Number of Firms in Portfolios", "size": "Average Firm Size",
           "be_me_sum": "Sum of BE / Sum of ME", "be_me_vw": "Value-Weighted Average of BE/ME"}[kind]
    df = secs[key]
    if kind in ("vw", "ew"):
        return _kf_monthly(df) / 100
    if kind in ("nfirms", "size"):
        return _kf_monthly(df)
    df = df[df.index.str.len() == 4].astype(float)
    # Ken French: the year-Y row is the BE/ME used to form portfolios at the end of June of year Y
    # (BE from fiscal year ending in Y-1, ME at Dec Y-1). Index it at June 30 of Y: known from July Y onward.
    df.index = pd.to_datetime(df.index + "-06-30")
    return df

def kf_industry_sic_map():
    """{FF49 short name: [(sic_lo, sic_hi), ...]} from Siccodes49.txt."""
    out, cur = {}, None
    for ln in (RAW / "kf_Siccodes49.txt").read_text(errors="ignore").splitlines():
        m = re.match(r"^\s*(\d+)\s+(\w+)\s+", ln)
        if m and not re.match(r"^\s*\d{4}-\d{4}", ln):
            cur = m.group(2); out[cur] = []; continue
        m = re.match(r"^\s*(\d{4})-(\d{4})", ln)
        if m and cur:
            out[cur].append((int(m.group(1)), int(m.group(2))))
    return out

# ----------------------------------------------------------------------------- FRED and other macro
def load_fred(series_id: str, how: str = "last") -> pd.Series:
    """Monthly month-end series. Daily series aggregated by 'last' or 'mean'. Monthly FRED dates (1st of month) -> month-end."""
    df = pd.read_csv(RAW / f"fred_{series_id}.csv")
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"]); s = pd.to_numeric(df.set_index("date")[series_id], errors="coerce")
    s = s.resample("ME").mean() if how == "mean" else s.resample("ME").last()
    return s.rename(series_id)

def load_cpu() -> pd.Series:
    """Gavriilidis (2021) Climate Policy Uncertainty index, monthly, 1987-04 onward."""
    df = pd.read_csv(RAW / "cpu_index.csv", skiprows=4)
    df["date"] = pd.to_datetime(df["date"], format="%b-%y") + pd.offsets.MonthEnd(0)
    return df.set_index("date")["cpu_index"].astype(float).rename("CPU")

def load_mccc(column: str = "Aggregate") -> pd.Series:
    """Ardia, Bluteau, Boudt, Inghelbrecht Media Climate Change Concerns index (2025 update), monthly."""
    df = pd.read_csv(RAW / "mccc_monthly.csv", parse_dates=["Date"]).set_index("Date")
    df.index = me(df.index)
    return df[column].astype(float).rename("MCCC" if column == "Aggregate" else column)

def load_emv_env() -> pd.Series:
    """Baker-Bloom-Davis-Kost EMV tracker: Energy and Environmental Regulation. Identical to team 'attention'."""
    return load_fred("EMVENRGYENVREG").rename("EMV_env")

# ----------------------------------------------------------------------------- statistics
def nw_ols(y: pd.Series, X: pd.DataFrame | None = None, lags: int = 6, const: bool = True):
    """OLS with Newey-West HAC standard errors. Returns statsmodels result (params, bse, tvalues, pvalues, nobs)."""
    if X is None:
        X = pd.DataFrame(index=y.index)
    d = pd.concat([y.rename("__y"), X], axis=1).dropna()
    Xm = sm.add_constant(d.drop(columns="__y"), has_constant="add") if const else d.drop(columns="__y")
    return sm.OLS(d["__y"], Xm).fit(cov_type="HAC", cov_kwds={"maxlags": lags})

def perf(r: pd.Series, lags: int = 6) -> dict:
    """Annualized performance summary for a monthly return series (already net if costs applied)."""
    r = r.dropna()
    if len(r) < 3:
        return {"n": len(r)}
    wealth = (1 + r).cumprod(); dd = wealth / wealth.cummax() - 1
    t = nw_ols(r, lags=lags).tvalues.iloc[0] if r.std() > 0 else np.nan
    return {"n": len(r), "ann_ret": 12 * r.mean(), "ann_vol": np.sqrt(12) * r.std(ddof=1),
            "sharpe": (np.sqrt(12) * r.mean() / r.std(ddof=1)) if r.std() > 0 else np.nan,
            "t_mean_nw": t, "max_dd": dd.min(), "hit_rate": (r > 0).mean()}

def alpha_row(r: pd.Series, factors: pd.DataFrame, lags: int = 6) -> dict:
    """Annualized intercept and loadings with NW t-stats."""
    res = nw_ols(r, factors, lags=lags)
    row = {"n": int(res.nobs), "alpha_ann": 12 * res.params["const"], "t_alpha": res.tvalues["const"], "r2": res.rsquared}
    for c in factors.columns:
        row[f"b_{c}"] = res.params[c]; row[f"t_{c}"] = res.tvalues[c]
    return row

def sub(s, period: str):
    a, b = PERIODS[period]
    return s.loc[a:b]

def holm(pvals: pd.Series) -> pd.Series:
    """Holm-Bonferroni adjusted p-values."""
    p = pvals.dropna().sort_values(); m = len(p)
    adj = np.maximum.accumulate([(m - i) * v for i, v in enumerate(p.values)])
    return pd.Series(np.minimum(adj, 1.0), index=p.index).reindex(pvals.index)

def bh(pvals: pd.Series) -> pd.Series:
    """Benjamini-Hochberg adjusted p-values (FDR)."""
    p = pvals.dropna().sort_values(); m = len(p)
    adj = np.minimum.accumulate((p.values * m / np.arange(1, m + 1))[::-1])[::-1]
    return pd.Series(np.minimum(adj, 1.0), index=p.index).reindex(pvals.index)

def rolling_z(s, window=60, min_periods=36):
    """Team convention: rolling z-score over trailing window including the current month."""
    return (s - s.rolling(window, min_periods=min_periods).mean()) / s.rolling(window, min_periods=min_periods).std(ddof=1).replace(0, np.nan)
