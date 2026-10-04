"""Fact-check computations for exchange 3 (robustness design).

Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/03_robustness_design/checks/fc03_checks.py
Writes CSVs next to this file (checks/out/). Touches no pre-1970 strategy return: the only pre-1970
quantities computed are data-availability counts (which industries have a return), not return moments.
"""
from __future__ import annotations
import pathlib, sys, json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats, integrate

ROOT = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(ROOT / "lib"))
from common import load_ff5_mom, load_kf_ff3, load_team  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
T = ROOT / "outputs" / "tables"
EG = 0.5772156649015329
res = {}


def moments(x):
    x = pd.Series(x).dropna()
    return dict(T=len(x), sr_m=x.mean() / x.std(ddof=1), sr_a=np.sqrt(12) * x.mean() / x.std(ddof=1),
                skew=stats.skew(x, bias=False), kurt_raw=stats.kurtosis(x, fisher=False, bias=False),
                skew_b=stats.skew(x), kurt_raw_b=stats.kurtosis(x, fisher=False))


def emax_approx(N):
    if N <= 1:
        return 0.0
    return (1 - EG) * stats.norm.ppf(1 - 1 / N) + EG * stats.norm.ppf(1 - 1 / (N * np.e))


def emax_exact(N):
    if N <= 1:
        return 0.0
    f = lambda z: z * N * stats.norm.pdf(z) * stats.norm.cdf(z) ** (N - 1)
    return integrate.quad(f, -10, 10, limit=200)[0]


def psr(sr_m, T_, skew, kurt, sr0):
    den = np.sqrt(1 - skew * sr_m + (kurt - 1) / 4 * sr_m ** 2)
    return stats.norm.cdf((sr_m - sr0) * np.sqrt(T_ - 1) / den)


def dsr(sr_m, T_, skew, kurt, N, V=None, exact=False):
    V = 1 / (T_ - 1) if V is None else V
    e = emax_exact(N) if exact else emax_approx(N)
    return psr(sr_m, T_, skew, kurt, np.sqrt(V) * e)


def nw_t_mean(x, lags=6):
    x = pd.Series(x).dropna()
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return m.tvalues[0]


def reg(y, X, lags=6):
    df = pd.concat([y.rename("y"), X], axis=1, sort=True).dropna()
    m = sm.OLS(df["y"], sm.add_constant(df.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return m, df


def nyholt(R):
    lam = np.linalg.eigvalsh(np.asarray(R))
    M = R.shape[0]
    return 1 + (M - 1) * (1 - np.var(lam, ddof=1) / M), lam


# ------------------------------------------------------------------ data
fac = load_ff5_mom()
opt = pd.read_csv(T / "M5_industry_momentum_optimizer_returns_monthly.csv", parse_dates=["date"]).set_index("date")
ew = pd.read_csv(T / "M5_industry_momentum_returns_monthly.csv", parse_dates=["date"]).set_index("date")
gb = pd.read_csv(T / "M4_emissions_gb_monthly_returns.csv", parse_dates=["date"]).set_index("date")
book = opt["X_unc"]
post = slice("2010-01-31", "2026-07-31")
hold = slice("2022-08-31", "2026-07-31")

# ------------------------------------------------------------------ 1. summary statistics quoted in the prompt
rows = []
for name, s in [("book_full", book), ("book_post2010", book[post]), ("epa5_post2010", gb["epa5"][post]),
                ("ew_book_full", ew["net"]), ("book_holdout", book[hold])]:
    mo = moments(s)
    mo["t_iid"] = mo["sr_m"] * np.sqrt(mo["T"])
    mo["t_nw6"] = nw_t_mean(s)
    x = pd.Series(s).dropna()
    for k in range(1, 7):
        mo[f"rho{k}"] = x.autocorr(k)
    # Lo (2002) annualization factor for q = 12 from monthly autocorrelations (rho_k, k<=11)
    rho = [x.autocorr(k) for k in range(1, 12)]
    q = 12
    eta = q / np.sqrt(q + 2 * sum((q - k) * rho[k - 1] for k in range(1, q)))
    mo["lo_eta12"] = eta
    mo["sr_a_lo"] = eta * mo["sr_m"]
    mo["name"] = name
    rows.append(mo)
mom = pd.DataFrame(rows).set_index("name")
mom.to_csv(OUT / "moments.csv")
res["moments"] = mom.round(4).to_dict(orient="index")

# ------------------------------------------------------------------ 2. PSR / DSR grid as in ChatGPT's table
grid = []
for name, sr_a, T_, sk, ku in [("book_full_prompt", 0.555, 679, -0.28, 5.77), ("book_post2010_prompt", 0.70, 199, 0.29, 3.66),
                              ("epa_post2010_prompt", 0.52, 199, 0.35, 4.77)]:
    srm = sr_a / np.sqrt(12)
    r = dict(series=name, psr0=psr(srm, T_, sk, ku, 0.0))
    for N in [2, 5, 7, 10, 100, 1000]:
        r[f"dsr_N{N}"] = dsr(srm, T_, sk, ku, N)
        r[f"dsr_N{N}_exactEmax"] = dsr(srm, T_, sk, ku, N, exact=True)
    # largest N with DSR >= 0.95
    Ns = np.arange(1, 5001)
    ok = [n for n in Ns if dsr(srm, T_, sk, ku, n) >= 0.95]
    r["maxN_dsr95"] = max(ok) if ok else 0
    grid.append(r)
grid = pd.DataFrame(grid).set_index("series")
grid.to_csv(OUT / "dsr_grid.csv")
res["dsr_grid"] = grid.round(4).to_dict(orient="index")
res["emax"] = {N: (round(emax_approx(N), 4), round(emax_exact(N), 4)) for N in [2, 5, 7, 10, 100, 1000]}

# ------------------------------------------------------------------ 3. optimizer book: loadings, appraisal ratio, DSR on AR
cols6 = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]
ar_rows = []
for lab, sl in [("full", slice("1970-01-31", "2026-07-31")), ("post2010", post), ("holdout", hold)]:
    for model, cols in [("FF5+UMD", cols6), ("FF3+UMD", ["Mkt-RF", "SMB", "HML", "UMD"]), ("FF5", cols6[:5])]:
        m, df = reg(book[sl], fac[cols][sl])
        e = m.resid
        a = 12 * m.params["const"]
        ar = a / (np.sqrt(12) * e.std(ddof=len(cols) + 1))
        yrs = len(df) / 12
        r = dict(window=lab, model=model, n=len(df), alpha=a, t_alpha=m.tvalues["const"], resid_vol=np.sqrt(12) * e.std(ddof=len(cols) + 1),
                 AR=ar, t_over_sqrt_years=m.tvalues["const"] / np.sqrt(yrs), resid_skew=stats.skew(e, bias=False),
                 resid_kurt=stats.kurtosis(e, fisher=False, bias=False), r2=m.rsquared,
                 **{f"b_{c}": m.params.get(c, np.nan) for c in cols6}, t_UMD=m.tvalues.get("UMD", np.nan),
                 se_alpha=a / m.tvalues["const"])
        # DSR on AR (monthly AR, residual moments), largest N with DSR >= 0.95
        arm = ar / np.sqrt(12)
        r["psr0_AR"] = psr(arm, len(df), r["resid_skew"], r["resid_kurt"], 0)
        ok = [n for n in range(1, 2001) if dsr(arm, len(df), r["resid_skew"], r["resid_kurt"], n) >= 0.95]
        r["maxN_dsr95_AR"] = max(ok) if ok else 0
        # same with the NW t in place of the iid AR (ChatGPT's route: t / sqrt(years))
        arm2 = r["t_over_sqrt_years"] / np.sqrt(12)
        ok2 = [n for n in range(1, 2001) if dsr(arm2, len(df), 0, 3, n) >= 0.95]
        r["maxN_dsr95_tNW_normal"] = max(ok2) if ok2 else 0
        ar_rows.append(r)
ar = pd.DataFrame(ar_rows)
ar.to_csv(OUT / "book_regressions.csv", index=False)
res["book_regressions"] = ar.round(4).to_dict(orient="records")

# equal-weight primary book loadings, to check whose UMD beta is 0.99
m, df = reg(ew["net"], fac[cols6])
res["ew_book_FF5UMD"] = dict(alpha=12 * m.params["const"], t=m.tvalues["const"], b_UMD=m.params["UMD"], r2=m.rsquared)
res["corr_book_ew"] = float(pd.concat([book, ew["net"]], axis=1).dropna().corr().iloc[0, 1])
res["corr_book_UMD"] = float(pd.concat([book, fac["UMD"]], axis=1).dropna().corr().iloc[0, 1])

# ------------------------------------------------------------------ 4. power of a frozen pre-1970 run (no pre-1970 returns touched)
pw = []
m, df = reg(book, fac[["Mkt-RF", "SMB", "HML", "UMD"]])
rv = np.sqrt(12) * m.resid.std(ddof=5)
se_nw_full = 12 * m.bse["const"]
nw_inflation = se_nw_full / (rv / np.sqrt(len(df) / 12))
for months, lab in [(510, "1927-07..1969-12 (EW book)"), (462, "1931-07..1969-12 (optimizer: 60m window)")]:
    for mult in [1.0, 1.5, 2.0]:
        se = mult * rv / np.sqrt(months / 12) * nw_inflation
        for a_true in [0.015, 0.02, 0.0217]:
            pw.append(dict(window=lab, months=months, resid_vol_mult=mult, resid_vol=mult * rv, se_alpha=se, true_alpha=a_true,
                           expected_t=a_true / se, power_t2=1 - stats.norm.cdf(2 - a_true / se),
                           min_alpha_for_t2=2 * se))
pw = pd.DataFrame(pw)
pw.to_csv(OUT / "power_pre1970.csv", index=False)
res["power"] = pw.round(4).to_dict(orient="records")
res["resid_vol_FF3UMD_1970_2026"] = rv
res["nw_inflation_alpha_se"] = nw_inflation

# ------------------------------------------------------------------ 5. data availability before 1970 (counts only)
team = load_team()
ind = team["industries"]
emis = team["emissions"]
pre = ind.loc[:"1969-12-31"]
first = pre.apply(lambda c: c.first_valid_index())
avail = pre.notna().sum(axis=1)
res["ff49_first_month"] = str(ind.index.min().date())
res["n_ind_available"] = {d: int(avail.loc[d]) for d in ["1926-07-31", "1927-07-31", "1931-07-31", "1940-01-31", "1950-01-31", "1960-01-31", "1969-12-31"]}
late = first[first > pd.Timestamp("1926-07-31")].sort_values()
res["late_starters"] = {k: str(v.date()) if pd.notna(v) else "none before 1970" for k, v in late.items()}
nostart = [c for c in ind.columns if pd.isna(first.get(c))]
res["no_return_before_1970"] = nostart
covered = list(emis.index)
res["covered41_missing_at_1931_07"] = [c for c in covered if pd.isna(ind.loc["1931-07-31", c])]
res["covered41_missing_at_1927_07"] = [c for c in covered if pd.isna(ind.loc["1927-07-31", c])]
res["umd_first"] = str(fac["UMD"].first_valid_index().date())
res["ff5_first"] = str(fac["RMW"].first_valid_index().date())
ff3 = load_kf_ff3()
res["ff3_first"] = str(ff3.index.min().date())

# ------------------------------------------------------------------ 6. TOST / equivalence on holdout alphas
tost = []
# team six variants: team pipeline, FF3 alpha, holdout (same-month EMV, team defaults)
sys.path.insert(0, str(ROOT / "lib"))
from team_pipeline import run_pipeline  # noqa: E402
tp = run_pipeline(bootstrap_reps=0)
strat = tp["strategies"]
ff3team = team["ff3"]
for k, s in strat.items():
    if k.startswith("Benchmark"):
        continue
    y = s["net_return"].loc["2022-08-31":"2026-07-31"]
    m, df = reg(y, ff3team[["Mkt-RF", "SMB", "HML"]].loc[y.index])
    a = 12 * m.params["const"]; se = 12 * m.bse["const"]
    tost.append(dict(series=f"team: {k}", n=len(df), alpha=a, se=se, t=a / se))
for lab, a, t_ in [("optimizer book FF5+UMD (M5)", -0.0034, -0.15), ("EW momentum book FF5+UMD (M5)", -0.0448, -0.84),
                   ("EPA 5v5 FF5+UMD (M4)", 0.039, 0.70)]:
    tost.append(dict(series=lab, n=48, alpha=a, se=a / t_, t=t_))
tost = pd.DataFrame(tost)
z = stats.norm.ppf(0.95)
tost["ci90_lo"] = tost.alpha - z * tost.se
tost["ci90_hi"] = tost.alpha + z * tost.se
tost["inside_pm2pct"] = (tost.ci90_lo > -0.02) & (tost.ci90_hi < 0.02)
tost["p_alpha_ge_2pct"] = stats.norm.cdf((tost.alpha - 0.02) / tost.se)  # one-sided test of H0: alpha >= 2%
tost["mde_80pct_power"] = (stats.norm.ppf(0.95) + stats.norm.ppf(0.80)) * tost.se
tost.to_csv(OUT / "holdout_tost.csv", index=False)
res["tost"] = tost.round(4).to_dict(orient="records")

# ------------------------------------------------------------------ 7. Nyholt M_eff on families of near-duplicates
def meff_block(df, label, resid=False):
    X = df.dropna()
    if resid:
        F = fac[cols6].loc[X.index]
        X = pd.DataFrame({c: sm.OLS(X[c], sm.add_constant(F)).fit().resid for c in X.columns})
    R = X.corr().values
    me_, lam = nyholt(R)
    return dict(family=label, resid=resid, M=R.shape[0], n=len(X), meff_nyholt=me_,
                meff_liji=float(sum((l >= 1) + (l - np.floor(l)) for l in np.clip(lam, 0, None))),
                min_corr=float(R[np.triu_indices_from(R, 1)].min()))


team6 = pd.DataFrame({k: v["net_return"] for k, v in strat.items() if not k.startswith("Benchmark")}).loc["2010-01-31":"2026-07-31"]
res["team_pre1970_nonzero"] = {k: int(((v["net_return"].fillna(0) != 0) & (v.index < "1970-01-01")).sum()) for k, v in strat.items()}
fams = [(opt, "M5 optimizer paths (24)"), (gb.drop(columns=["epa5_minus_team5"]), "M4 GB variants (15)"), (team6, "team strategies post-2010")]
mrows = []
for df_, lab in fams:
    for rsd in [False, True]:
        mrows.append(meff_block(df_, lab, rsd))
meff = pd.DataFrame(mrows)
meff.to_csv(OUT / "meff.csv", index=False)
res["meff"] = meff.round(3).to_dict(orient="records")
res["team6_names"] = list(team6.columns)

# ------------------------------------------------------------------ 8. EPA spread with real-time MCCC shock control (exploratory fact-check only)
att = pd.read_csv(ROOT / "data" / "derived" / "attention_measures.csv", parse_dates=["date"]).set_index("date")
y = gb["epa5"].loc["2010-01-31":"2026-07-31"]
X = fac[cols6].loc[y.index]
m0, d0 = reg(y, X)
X1 = X.join(att["MCCC_shock"])
m1, d1 = reg(y, X1)
m0c, _ = reg(y.loc[d1.index], X.loc[d1.index])
res["epa_mccc"] = dict(n_with_mccc=len(d1), end=str(d1.index.max().date()),
                       alpha_base_same_sample=12 * m0c.params["const"], t_base_same_sample=m0c.tvalues["const"],
                       alpha_with_shock=12 * m1.params["const"], t_with_shock=m1.tvalues["const"],
                       b_shock=m1.params["MCCC_shock"], t_shock=m1.tvalues["MCCC_shock"],
                       mean_shock=float(d1["MCCC_shock"].mean()), sd_shock=float(d1["MCCC_shock"].std()))

# ------------------------------------------------------------------ 9. M2 grid: largest positive t and a crude max-t calculation
led = pd.read_csv(T / "M2_christhian_tests_tests_ledger.csv")
g = led[led.test_id.str.endswith("|alpha")]
res["m2_grid_rows_alpha_suffix"] = len(g)
top = g.sort_values("statistic", ascending=False).head(5)[["test_id", "statistic", "p_value_two_sided", "n_obs"]]
res["m2_top_positive"] = top.to_dict(orient="records")
p1 = top.iloc[0]["p_value_two_sided"] / 2
res["rw_needed_Neff_for_best_positive"] = {"one_sided_p": p1, "Neff_at_which_sidak_p_0.05": float(np.log(0.95) / np.log(1 - p1))}

# ------------------------------------------------------------------ 10. BY constant
m_ = 8091
res["BY_c_m"] = float(sum(1 / i for i in range(1, m_ + 1)))
res["ln_m_plus_gamma"] = float(np.log(m_) + EG)

pathlib.Path(OUT / "fc03_results.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
