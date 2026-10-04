"""Independent fact-check computations for exchange 3 (robustness design), second checker.

Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/03_robustness_design/checks/fc03b_verify.py
Writes CSV/JSON to checks/out_b/. Reads saved module outputs (M4, M5, M7) and the team pipeline.
Computes no new pre-1970 strategy return: the only pre-1970 quantities here are data-availability counts.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import integrate, stats

ROOT = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(ROOT / "lib"))
from common import load_ff5_mom, load_kf_ff3, load_mccc, load_team, nw_ols  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "out_b"
OUT.mkdir(exist_ok=True)
TB = ROOT / "outputs" / "tables"
EG = 0.5772156649015329
R = {}


# ------------------------------------------------------------------ helpers
def emax_bl(N):
    """Bailey-Lopez de Prado approximation of E[max of N iid N(0,1)]."""
    if N <= 1:
        return 0.0
    return (1 - EG) * stats.norm.ppf(1 - 1 / N) + EG * stats.norm.ppf(1 - 1 / (N * np.e))


def emax_exact(N):
    if N <= 1:
        return 0.0
    f = lambda z: z * N * stats.norm.pdf(z) * stats.norm.cdf(z) ** (N - 1)  # noqa: E731
    return integrate.quad(f, -12, 12, limit=400)[0]


def psr(sr, T, g3, g4, sr0):
    den = np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return stats.norm.cdf((sr - sr0) * np.sqrt(T - 1) / den)


def dsr(sr, T, g3, g4, N, V=None, exact=False):
    V = 1 / (T - 1) if V is None else V
    e = emax_exact(N) if exact else emax_bl(N)
    return psr(sr, T, g3, g4, np.sqrt(V) * e)


def max_n_pass(sr, T, g3, g4, bar=0.95, V=None):
    n = 1
    if psr(sr, T, g3, g4, 0.0) < bar:
        return 0
    while n < 10 ** 7 and dsr(sr, T, g3, g4, n + 1, V) >= bar:
        n += 1
    return n


def moments(x):
    x = pd.Series(x).dropna()
    return dict(T=len(x), sr_m=x.mean() / x.std(ddof=1), sr_a=np.sqrt(12) * x.mean() / x.std(ddof=1),
                skew=float(stats.skew(x, bias=False)), kurt=float(stats.kurtosis(x, fisher=False, bias=False)))


def nyholt(corr):
    lam = np.linalg.eigvalsh(np.asarray(corr))
    M = len(lam)
    return 1 + (M - 1) * (1 - np.var(lam, ddof=1) / M)


def li_ji(corr):
    lam = np.abs(np.linalg.eigvalsh(np.asarray(corr)))
    return float(np.sum((lam >= 1).astype(float) + (lam - np.floor(lam))))


def lo_eta(x, q=12):
    x = pd.Series(x).dropna()
    rho = [x.autocorr(k) for k in range(1, q)]
    return q / np.sqrt(q + 2 * sum((q - k) * rho[k - 1] for k in range(1, q)))


# ------------------------------------------------------------------ data
ff5 = load_ff5_mom()
F6 = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]
opt = pd.read_csv(TB / "M5_industry_momentum_optimizer_returns_monthly.csv", parse_dates=["date"]).set_index("date")
ew = pd.read_csv(TB / "M5_industry_momentum_returns_monthly.csv", parse_dates=["date"]).set_index("date")["net"]
gb = pd.read_csv(TB / "M4_emissions_gb_monthly_returns.csv", parse_dates=["date"]).set_index("date")
book = opt["X_unc"]
epa = gb["epa5"]
POST = ("2010-01-31", "2026-07-31")
HOLD = ("2022-08-31", "2026-07-31")

# 1. moments quoted in the prompt ------------------------------------------------------
mrows = []
for name, s in [("book_full", book), ("book_post2010", book.loc[POST[0]:POST[1]]),
                ("epa_post2010", epa.loc[POST[0]:POST[1]]), ("epa_full", epa)]:
    m = moments(s)
    m["series"] = name
    m["iid_t_mean"] = m["sr_m"] * np.sqrt(m["T"])
    m["nw6_t_mean"] = float(nw_ols(s.dropna()).tvalues.iloc[0])
    m["lo_eta12"] = lo_eta(s)
    m["lo_sr_ann"] = m["sr_m"] * lo_eta(s)
    mrows.append(m)
mom = pd.DataFrame(mrows).set_index("series")
mom.to_csv(OUT / "moments.csv")
R["moments"] = mom.round(4).to_dict(orient="index")

# 2. ChatGPT's DSR table, V = 1/(T-1), inputs exactly as the prompt printed them -------------
inputs = {"book_full": (0.555, 679, -0.28, 5.77), "book_post2010": (0.70, 199, 0.29, 3.66),
          "epa_post2010": (0.52, 199, 0.35, 4.77)}
drows = []
for k, (sra, T, g3, g4) in inputs.items():
    sr = sra / np.sqrt(12)
    row = {"series": k, "psr0": psr(sr, T, g3, g4, 0.0)}
    for N in (2, 10, 100, 1000):
        row[f"dsr_N{N}"] = dsr(sr, T, g3, g4, N)
        row[f"dsr_exact_N{N}"] = dsr(sr, T, g3, g4, N, exact=True)
    row["max_N_pass_V_floor"] = max_n_pass(sr, T, g3, g4)
    # wrong-unit check: annualized SR plugged in with monthly T
    row["psr0_if_annualized_sr_used"] = psr(sra, T, g3, g4, 0.0)
    drows.append(row)
dtab = pd.DataFrame(drows).set_index("series")
dtab.to_csv(OUT / "dsr_table.csv")
R["dsr_table"] = dtab.round(4).to_dict(orient="index")
R["emax"] = {N: {"bl": emax_bl(N), "exact": emax_exact(N)} for N in (2, 7, 10, 100, 1000)}

# 3. regressions: UMD betas, appraisal ratios, residual moments, DSR on AR ------------------------
def reg(y, cols, lags=6):
    d = pd.concat([y.rename("y"), ff5[cols]], axis=1).dropna()
    r = sm.OLS(d["y"], sm.add_constant(d[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    r_ols = sm.OLS(d["y"], sm.add_constant(d[cols])).fit()
    e = r.resid
    s_e = np.sqrt((e ** 2).sum() / (len(e) - len(cols) - 1))
    return dict(n=len(d), alpha_ann=12 * r.params["const"], t_nw=r.tvalues["const"], t_ols=r_ols.tvalues["const"],
                resid_vol_ann=np.sqrt(12) * s_e, ar_m=r.params["const"] / s_e,
                ar_ann=np.sqrt(12) * r.params["const"] / s_e,
                resid_skew=float(stats.skew(e, bias=False)), resid_kurt=float(stats.kurtosis(e, fisher=False, bias=False)),
                b_UMD=r.params.get("UMD", np.nan), t_UMD=r.tvalues.get("UMD", np.nan), r2=r.rsquared)


rrows = []
for nm, s in [("EW_book", ew), ("opt_book_X_unc", book), ("EPA5", epa)]:
    for per, (a, b) in {"full_1970": ("1970-01-31", "2026-07-31"), "post2010": POST, "holdout": HOLD}.items():
        for mod, cols in {"FF5+UMD": F6, "FF3+UMD": ["Mkt-RF", "SMB", "HML", "UMD"], "FF5": F6[:5]}.items():
            row = reg(s.loc[a:b], cols)
            row.update(series=nm, period=per, model=mod)
            rrows.append(row)
rtab = pd.DataFrame(rrows)
rtab.to_csv(OUT / "regressions.csv", index=False)
R["regressions_key"] = rtab[rtab.model.eq("FF5+UMD")].set_index(["series", "period"])[
    ["alpha_ann", "t_nw", "t_ols", "ar_ann", "resid_vol_ann", "b_UMD", "t_UMD", "resid_skew", "resid_kurt"]].round(4).reset_index().to_dict(orient="records")

ar_rows = []
for per, T0 in [("full_1970", None), ("post2010", None)]:
    r = rtab[(rtab.series == "opt_book_X_unc") & (rtab.period == per) & (rtab.model == "FF5+UMD")].iloc[0]
    T = int(r.n)
    for label, sr, g3, g4 in [("resid_moments", r.ar_m, r.resid_skew, r.resid_kurt),
                              ("normal", r.ar_m, 0.0, 3.0),
                              ("chatgpt_t_over_sqrt_years", r.t_nw / np.sqrt(T / 12) / np.sqrt(12), 0.0, 3.0)]:
        ar_rows.append(dict(period=per, variant=label, T=T, ar_ann=sr * np.sqrt(12),
                            psr0=psr(sr, T, g3, g4, 0), dsr_N7=dsr(sr, T, g3, g4, 7), dsr_N10=dsr(sr, T, g3, g4, 10),
                            max_N_pass_V_floor=max_n_pass(sr, T, g3, g4)))
artab = pd.DataFrame(ar_rows)
artab.to_csv(OUT / "ar_dsr.csv", index=False)
R["ar_dsr"] = artab.round(4).to_dict(orient="records")

# t needed for DSR >= 0.95 at N trials vs max-t 5% critical (independent trials), normal approx
tn = []
for N in (2, 3, 5, 7, 8, 10, 20, 42, 75, 100):
    tn.append(dict(N=N, emax=emax_bl(N), t_needed_dsr95=emax_bl(N) + 1.645,
                   t_crit_maxt_sidak=stats.norm.ppf((0.95) ** (1 / N))))
pd.DataFrame(tn).to_csv(OUT / "t_needed.csv", index=False)
R["t_needed"] = pd.DataFrame(tn).round(3).to_dict(orient="records")

# 4. BY factor, BH single-rejection threshold -------------------------------------------------
for m in (8091, 8161, 23923):
    R[f"BY_c_m{m}"] = float(np.sum(1 / np.arange(1, m + 1)))
    R[f"lnm_plus_0.58_m{m}"] = float(np.log(m) + 0.5772)
    R[f"BH_first_threshold_m{m}"] = 0.05 / m
R["sidak_N_for_p_0.00018"] = float(np.log(0.95) / np.log(1 - 0.00018))

# 5. team rules: holdout FF3 alphas (team FF3 file), non-inferiority vs +2%, TOST +-2% -------------
res = None
try:
    sys.path.insert(0, str(ROOT / "lib"))
    from team_pipeline import run_pipeline
    res = run_pipeline(bootstrap_reps=0, extras=False)
except Exception as exc:  # pragma: no cover
    R["team_pipeline_error"] = repr(exc)

if res is not None:
    team_ff3 = load_team()["ff3"]
    hrows = []
    series_map = {k: v["net_return"] for k, v in res["strategies"].items()}
    six = [k for k in series_map if not k.startswith("Benchmark")]
    comp = pd.concat([series_map[k] for k in six], axis=1).mean(axis=1)
    series_map["Composite | EW mean of six"] = comp
    for nm, s in series_map.items():
        for per, (a, b) in {"validation": ("2010-01-31", "2022-07-31"), "holdout": HOLD}.items():
            y = s.loc[a:b]
            d = pd.concat([y.rename("y"), team_ff3[["Mkt-RF", "SMB", "HML"]]], axis=1).dropna()
            r = sm.OLS(d["y"], sm.add_constant(d[["Mkt-RF", "SMB", "HML"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
            a_ = 12 * r.params["const"]
            se = 12 * r.bse["const"]
            df = len(d) - 4
            tcrit = stats.t.ppf(0.95, df)
            lo, hi = a_ - tcrit * se, a_ + tcrit * se
            hrows.append(dict(strategy=nm, period=per, n=len(d), alpha_ann=a_, se_ann=se, t=a_ / se,
                              p_two_t=2 * stats.t.sf(abs(a_ / se), df),
                              p_noninf_vs_plus2=stats.t.cdf((a_ - 0.02) / se, df),
                              ci90_lo=lo, ci90_hi=hi, tost_pm2_inside=bool(lo > -0.02 and hi < 0.02)))
    htab = pd.DataFrame(hrows)
    htab.to_csv(OUT / "team_holdout.csv", index=False)
    R["team_holdout"] = htab.round(4).to_dict(orient="records")
    # Nyholt M_eff across the six variants (post-2010 net returns, active or not)
    six_df = pd.concat([series_map[k] for k in six], axis=1).loc[POST[0]:POST[1]]
    six_df.columns = six
    c6 = six_df.corr()
    R["six_variants_corr_min_max"] = [float(c6.values[np.triu_indices(6, 1)].min()), float(c6.values[np.triu_indices(6, 1)].max())]
    R["six_variants_nyholt"] = float(nyholt(c6))
    R["six_variants_liji"] = li_ji(c6)
    c6.to_csv(OUT / "six_variants_corr.csv")

# optimizer holdout TOST
r = rtab[(rtab.series == "opt_book_X_unc") & (rtab.period == "holdout") & (rtab.model == "FF5+UMD")].iloc[0]
se = abs(r.alpha_ann / r.t_nw)
tcrit = stats.t.ppf(0.95, 41)
R["book_holdout"] = dict(alpha=r.alpha_ann, se=se, ci90=(r.alpha_ann - tcrit * se, r.alpha_ann + tcrit * se),
                         mde80=(tcrit + stats.t.ppf(0.8, 41)) * se)

# 6. Nyholt over the 24 optimizer paths --------------------------------------------------------
for nm, cols in [("X_paths_12", [c for c in opt.columns if c.startswith("X_")]),
                 ("all_paths_24", list(opt.columns))]:
    c = opt[cols].corr()
    R[f"nyholt_{nm}"] = float(nyholt(c))
    R[f"liji_{nm}"] = li_ji(c)

# 7. pre-1970 availability (no returns computed) ------------------------------------------------
T_ = load_team()
ind = T_["industries"]
cov41 = list(T_["emissions"].index)
avail = ind.replace([-99.99, -999], np.nan).notna()
first = avail.idxmax().where(avail.any())
first.sort_values().to_csv(OUT / "industry_first_month.csv")
R["industries_first_after_1926_07"] = {k: str(v.date()) for k, v in first.items() if v > pd.Timestamp("1926-07-31")}
cnt41 = avail[[c for c in cov41 if c in avail.columns]].sum(axis=1)
R["covered41_count_1926_07"] = int(cnt41.loc["1926-07-31"])
R["covered41_count_1931_06"] = int(cnt41.loc["1931-06-30"])
R["covered41_count_1969_11"] = int(cnt41.loc["1969-11-30"])
R["all49_count_1926_07"] = int(avail.sum(axis=1).loc["1926-07-31"])
R["kf_ff3_first"] = str(load_kf_ff3().index.min().date())
R["umd_first"] = str(ff5["UMD"].dropna().index.min().date())
R["ff5_first"] = str(ff5["RMW"].dropna().index.min().date())

# power of the frozen pre-1970 run, using post-1970 residual vol only
r = rtab[(rtab.series == "opt_book_X_unc") & (rtab.period == "full_1970") & (rtab.model == "FF3+UMD")].iloc[0]
pw = []
for label, months in [("chatgpt_1927-07_1969-12", 510), ("feasible_1931-07_1969-12", 462)]:
    se = r.resid_vol_ann / np.sqrt(months / 12)
    for true_a in (0.01, 0.015, 0.02, 0.0217):
        pw.append(dict(window=label, months=months, resid_vol=r.resid_vol_ann, se=se, true_alpha=true_a,
                       power_t_ge_2=stats.norm.sf(2 - true_a / se)))
pd.DataFrame(pw).to_csv(OUT / "power_pre1970.csv", index=False)
R["power_pre1970"] = pd.DataFrame(pw).round(4).to_dict(orient="records")

# 8. census of nominal hits by type (M7 classification) and a crude independent classifier ----------------
allt = pd.read_csv(TB / "M7_all_tests.csv", low_memory=False)
mod_rows = allt[~allt["ledger_file"].astype(str).str.contains("M7_")]
R["census_rows"] = int(len(mod_rows))
nom = mod_rows[mod_rows["p_value_two_sided"] < 0.05]
R["census_nominal"] = int(len(nom))
R["census_nominal_by_type"] = nom["type"].value_counts().to_dict()
R["census_labels"] = mod_rows["primary_or_exploratory"].value_counts().to_dict()
pat = re.compile(r"beta|loading|\bb_|coef_(?!const)|slope", re.I)
crude = nom.apply(lambda x: bool(pat.search(str(x["statistic_name"])) or "[loading]" in str(x["note"])
                                or pat.search(str(x["test_id"]))), axis=1)
R["census_crude_loading_like_share"] = float(crude.mean())
rm2 = mod_rows[mod_rows["family"].astype(str).eq("R") & mod_rows["r_subfamily"].astype(str).eq("R-M2")]
if len(rm2):
    best = rm2.sort_values("p1_m7").iloc[0]
    R["RM2_best"] = {k: str(best[k]) for k in ["test_id", "statistic", "p1_m7", "n_obs", "note"]}
    R["RM2_m"] = int(len(rm2))

# 9. EPA spread with MCCC AR(1) innovations (PST 2022 construction: trailing 36-month AR(1)) ----------
mccc = load_mccc()
shock = pd.Series(np.nan, index=mccc.index)
vals = mccc.values
for i in range(37, len(mccc)):
    y = vals[i - 36:i]
    x = vals[i - 37:i - 1]
    X = sm.add_constant(x)
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    shock.iloc[i] = vals[i] - (b[0] + b[1] * vals[i - 1])
shock = shock.rename("MCCC_shock")
e_rows = []
for label, extra in [("base_same_sample", None), ("plus_same_month_shock", shock), ("plus_lagged_shock", shock.shift(1))]:
    d = pd.concat([epa.loc[POST[0]:POST[1]].rename("y"), ff5[F6], shock.rename("s0"), shock.shift(1).rename("s1")], axis=1).dropna(subset=["y"] + F6 + ["s0"])
    cols = F6 + ([] if extra is None else ["s0" if label == "plus_same_month_shock" else "s1"])
    if label == "plus_lagged_shock":
        d = d.dropna(subset=["s1"])
    r = sm.OLS(d["y"], sm.add_constant(d[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    sh = cols[-1] if extra is not None else None
    e_rows.append(dict(spec=label, n=len(d), start=str(d.index.min().date()), end=str(d.index.max().date()),
                       alpha_ann=12 * r.params["const"], t=r.tvalues["const"],
                       shock_coef_per_sd=(r.params[sh] * d[sh].std()) if sh else np.nan,
                       shock_t=r.tvalues[sh] if sh else np.nan))
etab = pd.DataFrame(e_rows)
etab.to_csv(OUT / "epa_mccc.csv", index=False)
R["epa_mccc"] = etab.round(4).to_dict(orient="records")

# 10. ChatGPT reply word count ----------------------------------------------------------------
txt = (ROOT / "exchange/03_robustness_design/chatgpt_response.md").read_text()
words_all = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.,%'’()/≈≥≤±−₀₃₄ₙ]*", txt)
R["reply_tokens_whitespace"] = len(txt.split())
R["reply_words_alnum"] = len(words_all)
body_no_table = "\n".join(l for l in txt.splitlines() if not l.strip().startswith("|"))
R["reply_words_alnum_excl_tables"] = len(re.findall(r"[A-Za-z0-9][^\s]*", body_no_table))

json.dump(R, open(OUT / "fc03b_results.json", "w"), indent=1, default=str)
print(json.dumps(R, indent=1, default=str))
