"""Independent verification of M2_christhian_tests.

Does NOT import modules/M2_christhian_tests/{run,helpers}.py. Uses only lib/common.py (loaders, holm/bh) and
lib/team_pipeline.py (team_controls, build_signals, Config: the verified signal machinery) plus its own code for
COMEQ, the corrected baseline, the raw signal, the rolling hedge, positions, P&L, costs, NW(6) regressions,
t(n-k) p-values, the HML decomposition, the break-even costs and the grid-wide multiple-testing counts.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M2_christhian_tests/verify/verify_m2.py
Writes modules/M2_christhian_tests/verify/verify_results.csv (one row per recomputed number vs the module's CSV).
"""
from __future__ import annotations

import pathlib
import sys
import warnings

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
from scipy import stats  # noqa: E402

from common import load_team, load_ff5_mom, load_fred, load_kf_industries, holm, bh, TABLES  # noqa: E402
from team_pipeline import team_controls, build_signals, Config  # noqa: E402

warnings.filterwarnings("ignore")
OUT = pathlib.Path(__file__).resolve().parent
M = "M2_christhian_tests"
END = "2026-07-31"
WIN = {"post2010": ("2010-01-31", END), "validation": ("2010-01-31", "2022-07-31"), "holdout": ("2022-08-31", END),
       "full_1970": ("1970-01-31", END)}
RES = []


def rec(check, item, mine, theirs, tol, note=""):
    ok = (np.isnan(mine) and np.isnan(theirs)) if (isinstance(mine, float) and isinstance(theirs, float) and np.isnan(mine)) else abs(mine - theirs) <= tol
    RES.append(dict(check=check, item=item, mine=mine, module=theirs, abs_diff=abs(mine - theirs), tol=tol, match=bool(ok), note=note))


def T(name):
    return pd.read_csv(TABLES / f"{M}_{name}.csv")


# ============================================================================ my own NW(6) OLS, t(n-k) p
def nw(y: pd.Series, X: pd.DataFrame | None, lags=6, demean=None):
    d = pd.concat([y.rename("__y")] + ([X] if X is not None else []), axis=1).dropna()
    if demean:
        d[demean] = d[demean] - d[demean].mean()
    Y = d["__y"].to_numpy()
    Z = np.column_stack([np.ones(len(d))] + ([d.drop(columns="__y").to_numpy()] if X is not None else []))
    n, k = Z.shape
    b = np.linalg.solve(Z.T @ Z, Z.T @ Y)
    u = Y - Z @ b
    S = (Z * u[:, None]).T @ (Z * u[:, None])
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = (Z[L:] * u[L:, None]).T @ (Z[:-L] * u[:-L, None])
        S += w * (G + G.T)
    Q = np.linalg.inv(Z.T @ Z)
    se = np.sqrt(np.diag(Q @ S @ Q))
    t = b / se
    p = 2 * stats.t.sf(np.abs(t), n - k)
    names = ["const"] + (list(d.columns[1:]) if X is not None else [])
    return pd.DataFrame({"b": b, "t": t, "p": p}, index=names), n, k


# statsmodels cross-check of my NW (no small-sample correction)
def nw_sm(y, X, lags=6):
    d = pd.concat([y.rename("__y"), X], axis=1).dropna()
    r = sm.OLS(d["__y"], sm.add_constant(d.drop(columns="__y"))).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    return r


# ============================================================================ data built from scratch
TM = load_team()
ind, ff3, mac, emis = TM["industries"], TM["ff3"], TM["macro"], TM["emissions"]
f5 = load_ff5_mom()
rf = ff3["RF"]
COMEQ = (ind[["Oil", "Coal", "Mines", "Gold"]].mean(axis=1, skipna=False) - rf).rename("COMEQ")
FF3 = ff3[["Mkt-RF", "SMB", "HML"]]
FF5U = f5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].loc[:END]
FF5UC = FF5U.join(COMEQ, how="inner").dropna()
RF5 = f5["RF"].loc[:END]
wti = np.log(load_fred("MCOILWTICO")).diff().rename("WTI")
imf = np.log(load_fred("PALLFNFINDEXM")).diff().rename("IMF")

srt = emis.sort_values()
G5, B5 = list(srt.index[:5]), list(srt.index[::-1][:5])
G8, B8 = list(srt.index[:8]), list(srt.index[::-1][:8])
assert G5 == ["Fun", "RlEst", "Drugs", "Telcm", "Fin"] and B5 == ["Util", "Ships", "Aero", "Steel", "BldMt"], (G5, B5)
print("8-and-8 Green:", G8, "Brown:", B8, "| 8th/9th Green intensities:", srt.iloc[7], srt.iloc[8], srt.index[7], srt.index[8])

# ---------------------------------------------------------------- V1: COMEQ construction and justification
print("\n[V1] COMEQ")
print("COMEQ first valid:", COMEQ.first_valid_index(), "NaNs after 1963-07:", COMEQ.loc["1963-07-31":END].isna().sum())
rec("V1 COMEQ", "first month", float(COMEQ.first_valid_index().year * 100 + COMEQ.first_valid_index().month), 196307.0, 0)
brown_ex = ind[B5].mean(axis=1) - rf
d = pd.concat([COMEQ, wti, imf, wti.shift(-1).rename("WTI_lead"), imf.shift(-1).rename("IMF_lead"), ff3["Mkt-RF"], brown_ex.rename("brown")], axis=1).loc["1992-02-29":END].dropna()
jus = T("q2_comeq_justification").set_index("series").loc["COMEQ (Oil, Coal, Mines, Gold)"]
for c, col in (("WTI", "corr_WTI"), ("WTI_lead", "corr_WTI_lead"), ("IMF", "corr_IMF"), ("IMF_lead", "corr_IMF_lead"), ("brown", "corr_brown"), ("Mkt-RF", "corr_Mkt-RF")):
    rec("V1 COMEQ", f"corr with {c} (1992-02..2026-06, n={len(d)})", d.COMEQ.corr(d[c]), jus[col], 5e-4)
fc, n_, k_ = nw(COMEQ.loc["1992-02-29":END], FF5U)
r2 = sm.OLS(pd.concat([COMEQ, FF5U], axis=1).loc["1992-02-29":END].dropna()["COMEQ"],
            sm.add_constant(pd.concat([COMEQ, FF5U], axis=1).loc["1992-02-29":END].dropna()[FF5U.columns])).fit().rsquared
rec("V1 COMEQ", "alpha on FF5+UMD (ann)", 12 * fc.loc["const", "b"], jus["ff5u_alpha_ann"], 5e-5)
rec("V1 COMEQ", "t alpha on FF5+UMD", fc.loc["const", "t"], jus["ff5u_t_alpha"], 5e-3)
rec("V1 COMEQ", "R2 on FF5+UMD", r2, jus["ff5u_r2"], 5e-4)

# NW implementation cross-check against statsmodels
r_sm = nw_sm(COMEQ.loc["1992-02-29":END], FF5U)
rec("V0 NW impl", "my NW t vs statsmodels HAC(6, no correction)", fc.loc["const", "t"], r_sm.tvalues["const"], 1e-8)

# ---------------------------------------------------------------- V2: corrected baseline and my own raw signal
print("\n[V2] corrected baseline")
m_corr = mac.copy()
m_corr["cpi"] = m_corr["cpi"].interpolate(limit_area="inside")
att_corr = m_corr["attention"].shift(1)
ctrl_corr = team_controls(m_corr).shift(1)
C = Config()
SIG = {"team": build_signals(mac["attention"], mac, C),
       "corr": build_signals(att_corr, m_corr, C, controls=ctrl_corr)}


def my_raw_state(att):
    z = np.log1p(att)
    z = (z - z.rolling(60, min_periods=36).mean()) / z.rolling(60, min_periods=36).std(ddof=1).replace(0, np.nan)
    thr = z.shift(1).expanding(min_periods=60).quantile(0.8)
    st = z.gt(thr) & thr.notna()
    return z, thr, st


def holds(state, h):
    state = state.astype(bool)
    cross = state & ~state.shift(1, fill_value=False)
    return cross.rolling(h, min_periods=1).max().astype(bool)


for b_, att in (("team", mac["attention"]), ("corr", att_corr)):
    z, thr, st = my_raw_state(att)
    same = (st.reindex(SIG[b_]["state_raw"].index).fillna(False) == SIG[b_]["state_raw"]).all()
    rec("V2 signal", f"{b_}: my raw p80 state == pipeline state_raw (1=yes)", float(same), 1.0, 0)
# raw state under the corrected baseline is exactly the team state lagged one month
lag_ok = (SIG["corr"]["state_raw"].loc["1995":END] == SIG["team"]["state_raw"].shift(1).loc["1995":END]).all()
rec("V2 signal", "corr raw state == team raw state shifted +1 month (1=yes)", float(lag_ok), 1.0, 0)
# CPI gap: pure signal defined in Nov-Dec 2025 only under the corrected baseline
rec("V2 signal", "team pure NaN months in 2025-11..2025-12", float(SIG["team"]["pure"].loc["2025-11-30":"2025-12-31"].isna().sum()), 2.0, 0)
rec("V2 signal", "corr pure NaN months in 2025-11..2026-01", float(SIG["corr"]["pure"].loc["2025-11-30":"2026-01-31"].isna().sum()), 0.0, 0)
# holdout: Pure == Original under the corrected baseline
for h in (3, 6):
    eq = (SIG["corr"]["hold_raw"][h].loc["2022-08-31":END] == SIG["corr"]["hold_pure"][h].loc["2022-08-31":END]).all()
    rec("V2 signal", f"corr holdout hold_raw == hold_pure ({h}m) (1=yes)", float(eq), 1.0, 0)


# ---------------------------------------------------------------- V3: my own P&L engine
def rolling_hedge(y, X, window=60):
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    Y, F = d["y"].to_numpy(), d[X.columns].to_numpy()
    n, k = F.shape
    B, A = np.full((n, k), np.nan), np.full(n, np.nan)
    for e in range(window - 1, n):
        Z = np.column_stack([np.ones(window), F[e - window + 1:e + 1]])
        c = np.linalg.lstsq(Z, Y[e - window + 1:e + 1], rcond=None)[0]
        A[e], B[e] = c[0], c[1:]
    beta = pd.DataFrame(B, index=d.index, columns=X.columns)
    alpha = pd.Series(A, index=d.index)
    eps = d["y"] - (beta.shift(1) * d[X.columns]).sum(axis=1, min_count=k) - alpha.shift(1)
    return d, beta, eps


def strat_pnl(brown_names, Xh, rf_s, pos_signal, kind, costs):
    """kind: 'state' (bool series) or 'cont' (weight). costs: dict asset + per-factor rates."""
    y = ind[brown_names].mean(axis=1) - rf_s
    d, beta, eps = rolling_hedge(y, Xh)
    sig = eps.rolling(36, min_periods=36).std(ddof=1)
    mag = (0.05 / (np.sqrt(12) * sig)).clip(upper=1.0)
    live = mag.first_valid_index()
    if kind == "state":
        s = pos_signal.reindex(d.index).fillna(False).astype(bool)
        pos = (-mag).where(s, 0.0)
    elif kind == "cont":
        w = pos_signal.reindex(d.index).fillna(0).clip(0, 1)
        pos = -mag * w
    else:  # always short
        pos = -mag
    pos = pos.loc[live:]
    idx = pos.index
    beta = beta.loc[idx]
    ov = -beta.mul(pos, axis=0)
    gross = pos.shift(1) * d["y"].loc[idx] + (ov.shift(1) * d[Xh.columns].loc[idx]).sum(axis=1, min_count=Xh.shape[1])
    dpos = pos.diff().abs().fillna(pos.abs())
    dov = ov.diff().abs().fillna(ov.abs())
    inc = costs["asset"] * dpos + sum(costs[c] * dov[c] for c in Xh.columns)
    net = gross - inc.shift(1).fillna(0)
    to = dpos + dov.sum(axis=1)
    return pd.DataFrame({"pos": pos, "gross": gross, "net": net, "turnover": to, "ov_turnover": dov.sum(axis=1)})


def team_costs(cols):
    return {"asset": 10e-4, **{c: (5e-4 if c == "Mkt-RF" else 25e-4) for c in cols}}


def uni_costs(cols, bp):
    return {"asset": bp * 1e-4, **{c: bp * 1e-4 for c in cols}}


STRATS = [("Original 3m", "raw", "state", 3), ("Pure 3m", "pure", "state", 3), ("Original 6m", "raw", "state", 6),
          ("Pure 6m", "pure", "state", 6), ("Continuous raw", "raw", "cont", None), ("Continuous pure", "pure", "cont", None),
          ("Always-short Brown", None, "always", None)]


def run_all(base, brown_names, Xh, rf_s, costs):
    out = {}
    S = SIG[base]
    for nm, key, kind, h in STRATS:
        sigl = S[f"hold_{key}"][h] if kind == "state" else (S[f"w_{key}"] if kind == "cont" else None)
        out[nm] = strat_pnl(brown_names, Xh, rf_s, sigl, kind, costs)
    return out


def family(strs, Xeval, periods=("post2010", "holdout")):
    rows = []
    for p in periods:
        a, e = WIN[p]
        for nm, *_ in STRATS:
            f, n, k = nw(strs[nm]["net"].loc[a:e], Xeval)
            rows.append({"strat": nm, "period": p, "alpha_ann": 12 * f.loc["const", "b"], "t": f.loc["const", "t"],
                         "p": f.loc["const", "p"], "n": n, "k": k, "b_HML": f.loc["HML", "b"]})
    df = pd.DataFrame(rows)
    df["holm"] = holm(df.p).values
    return df


def compare_family(tag, mine, theirs_csv):
    th = T(theirs_csv)
    for _, r in mine.iterrows():
        t_ = th[(th.strat == r.strat) & (th.period == r.period)].iloc[0]
        rec(tag, f"{r.strat} {r.period} alpha", r.alpha_ann, t_.alpha_ann, 5e-5)
        rec(tag, f"{r.strat} {r.period} t", r.t, t_.t_alpha, 5e-3)
        rec(tag, f"{r.strat} {r.period} p t(n-k)", r.p, t_.p_alpha, 5e-4)
        rec(tag, f"{r.strat} {r.period} Holm p", r.holm, t_.holm_p, 5e-4)
    pos_sig = int(((mine.alpha_ann > 0) & (mine.holm < 0.05)).sum())
    rec(tag, "positive Holm survivors (of 14)", float(pos_sig), float(th.positive_and_holm_sig.sum()), 0)
    print(mine.assign(alpha_pct=lambda x: 100 * x.alpha_ann).round(4).to_string())


# ---------------------------------------------------------------- V4: Q2 primary (corr, 5/5, FF5+UMD+COMEQ hedge and eval, team costs)
print("\n[V4] Q2 primary")
Q2 = run_all("corr", B5, FF5UC, RF5, team_costs(FF5UC.columns))
Q2F = family(Q2, FF5UC)
compare_family("V4 Q2 primary", Q2F, "q2_primary")

# ---------------------------------------------------------------- V5: Q1 primary (corr, 8/8 Hardw, FF3 hedge/eval, team costs)
print("\n[V5] Q1 primary")
Q1 = run_all("corr", B8, FF3, rf, team_costs(FF3.columns))
Q1F = family(Q1, FF3)
compare_family("V5 Q1 primary", Q1F, "q1_primary")
# the tie-break only changes the Green leg: strategies trade the Brown leg only, so 8/8 H and 8/8 M strategies are identical
# (verified structurally: strat_pnl never reads the Green leg); record the Green-leg difference for the unhedged spread
G8M = [x if x != "Hardw" else "MedEq" for x in G8]
gbH = ind[G8].mean(axis=1) - ind[B8].mean(axis=1)
gbM = ind[G8M].mean(axis=1) - ind[B8].mean(axis=1)
sgrid = T("strategy_grid")
x = sgrid[(sgrid.costs != "u0")]
xh = x[x.legs == "L8H"].set_index(["baseline", "hedge", "costs", "strat", "period", "eval_id"]).alpha_ann
xm = x[x.legs == "L8M"].set_index(["baseline", "hedge", "costs", "strat", "period", "eval_id"]).alpha_ann
rec("V5 Q1 tie-break", "max |alpha(8/8 H) - alpha(8/8 M)| over strategy grid", float((xh - xm.reindex(xh.index)).abs().max()), 0.0, 1e-12)
for p in ("post2010", "holdout"):
    a, e = WIN[p]
    fH, _, _ = nw(gbH.loc[a:e], FF3)
    fM, _, _ = nw(gbM.loc[a:e], FF3)
    sp = T("q2_spread_controls")
    rec("V5 Q1 spread", f"8/8 H GB FF3 alpha {p}", 12 * fH.loc["const", "b"], sp[(sp.legs == "L8H") & (sp.period == p) & (sp.eval_id == "E:FF3")].alpha_ann.iloc[0], 5e-5)
    rec("V5 Q1 spread", f"8/8 M GB FF3 alpha {p}", 12 * fM.loc["const", "b"], sp[(sp.legs == "L8M") & (sp.period == p) & (sp.eval_id == "E:FF3")].alpha_ann.iloc[0], 5e-5)

# ---------------------------------------------------------------- V6: Q3 HML loadings and decomposition
print("\n[V6] Q3")
GB5 = ind[G5].mean(axis=1) - ind[B5].mean(axis=1)
q3 = T("q3_primary")
for p in ("full_1970", "post2010"):
    a, e = WIN[p]
    for mdl, X in (("E:FF3", FF3), ("E:FF5U", FF5U)):
        f, n, k = nw(GB5.loc[a:e], X)
        r_ = q3[(q3.period == p) & (q3.eval_id == mdl)].iloc[0]
        rec("V6 Q3 primary", f"GB b_HML {p} {mdl}", f.loc["HML", "b"], r_.b_HML, 5e-5)
        rec("V6 Q3 primary", f"GB t_HML {p} {mdl}", f.loc["HML", "t"], r_.t_HML, 5e-3)
dec = T("q3_hml_decomposition")
for p in ("post2010", "full_1970", "holdout"):
    a, e = WIN[p]
    contrib = {}
    for nm in G5:
        contrib[nm] = nw(ind[nm].loc[a:e] - rf, FF3)[0].loc["HML", "b"] / 5
    for nm in B5:
        contrib[nm] = -nw(ind[nm].loc[a:e] - rf, FF3)[0].loc["HML", "b"] / 5
    gsum, bsum = sum(contrib[n] for n in G5), sum(contrib[n] for n in B5)
    direct = nw(GB5.loc[a:e], FF3)[0].loc["HML", "b"]
    rec("V6 Q3 decomposition", f"{p} FF3 sum of contributions == direct GB loading", gsum + bsum, direct, 1e-10)
    dd = dec[(dec.legs == "L5") & (dec.model == "FF3") & (dec.period == p)]
    rec("V6 Q3 decomposition", f"{p} FF3 Brown side", bsum, dd[dd.side == "Brown"].contribution.sum(), 5e-5)
    rec("V6 Q3 decomposition", f"{p} FF3 Green side", gsum, dd[dd.side == "Green"].contribution.sum(), 5e-5)
    if p == "post2010":
        for nm in ("Steel", "Ships", "Aero", "RlEst", "Fin"):
            rec("V6 Q3 decomposition", f"post2010 FF3 contribution {nm}", contrib[nm], dd.set_index("industry").contribution[nm], 5e-5)
        drivers = sorted(contrib, key=lambda k_: -abs(contrib[k_]))[:2]
        print("drivers:", drivers, {k_: round(v, 4) for k_, v in contrib.items()})
        rec("V6 Q3 decomposition", "drivers are Steel, Ships (1=yes)", float(drivers == ["Steel", "Ships"]), 1.0, 0)
# rolling 60m FF3 GB HML beta: share negative 1975-2026
dgb = pd.concat([GB5.rename("y"), FF3], axis=1).dropna()
bl = []
for e in range(59, len(dgb)):
    Z = np.column_stack([np.ones(60), dgb[FF3.columns].to_numpy()[e - 59:e + 1]])
    bl.append((dgb.index[e], np.linalg.lstsq(Z, dgb["y"].to_numpy()[e - 59:e + 1], rcond=None)[0][3]))
rb = pd.Series(dict(bl))
rsum = T("q3_rolling_summary")
rr = rsum[(rsum.model == "FF3") & (rsum.series == "Green-Brown")].set_index("era")
rec("V6 Q3 rolling", "share of 60m windows with negative GB HML beta, 1975-2026", float((rb.loc["1975-01-31":END] < 0).mean()), rr.loc["1975-2026", "share_negative"], 1e-3)
rec("V6 Q3 rolling", "share negative, holdout windows", float((rb.loc["2022-08-31":END] < 0).mean()), rr.loc["2022-08-2026", "share_negative"], 1e-3)
# characteristic: GB relative log BE/ME negative share, 1975-2026
bm = load_kf_industries("be_me_sum")
lbm = np.log(bm.where(bm > 0))
rel = lbm.sub(lbm.median(axis=1), axis=0)
gbrel = (rel[G5].mean(axis=1) - rel[B5].mean(axis=1)).loc["1975":"2026"]
link = T("q3_bm_link").set_index("series")
rec("V6 Q3 BE/ME", "share of years GB relative log BE/ME < 0 (1975-2026)", float((gbrel < 0).mean()), link.loc["Green-Brown", "share_rel_logbm_negative"], 1e-3)

# ---------------------------------------------------------------- V7: Q4 break-even and gross holdout alpha
print("\n[V7] Q4 break-evens")
be = T("q4_breakeven")
q4p = T("q4_primary")
for base in ("corr", "team"):
    for hname, Xh, rfs in (("FF3", FF3, rf), ("FF5UC", FF5UC, RF5)):
        g0 = run_all(base, B5, Xh, rfs, uni_costs(Xh.columns, 0))
        g10 = run_all(base, B5, Xh, rfs, uni_costs(Xh.columns, 10))
        for nm, *_ in STRATS:
            row = be[(be.baseline == base) & (be.hedge == hname) & (be.strategy == nm)].iloc[0]
            for p in ("validation", "holdout"):
                a, e = WIN[p]
                a0 = 12 * nw(g0[nm]["net"].loc[a:e], Xh)[0].loc["const", "b"]
                a10 = 12 * nw(g10[nm]["net"].loc[a:e], Xh)[0].loc["const", "b"]
                s = (a0 - a10) / 10
                if p == "validation":
                    rec("V7 Q4 break-even", f"{base} {hname} {nm} validation break-even bp", a0 / s if a0 > 0 else np.nan,
                        row.validation_breakeven_bp, 0.05)
                    if base == "corr" and hname == "FF3":
                        rec("V7 Q4 turnover", f"{nm} validation annual turnover", 12 * g10[nm]["turnover"].loc[a:e].mean(),
                            row.validation_ann_turnover, 5e-3)
                else:
                    rec("V7 Q4 gross holdout", f"{base} {hname} {nm} gross holdout alpha", a0, row.holdout_gross_alpha, 5e-5,
                        "claim: negative for every strategy/baseline/hedge")
                    rec("V7 Q4 gross holdout", f"{base} {hname} {nm} gross holdout alpha < 0 (1=yes)", float(a0 < 0), 1.0, 0)
        if base == "corr" and hname == "FF3":
            g5 = run_all(base, B5, Xh, rfs, uni_costs(Xh.columns, 5))
            q4mine = family(g5, FF3)
            compare_family("V7 Q4 primary", q4mine, "q4_primary")

# ---------------------------------------------------------------- V8: team-baseline replication and hedge-cost claim
print("\n[V8] team baseline Table 1 anchors and hedge cost")
TB = run_all("team", B5, FF3, rf, team_costs(FF3.columns))
f, _, _ = nw(TB["Pure 6m"]["net"].loc["2010-01-31":"2022-07-31"], FF3)
rec("V8 team Table 1", "team Pure 6m validation FF3 alpha (writeup 2.51%)", 12 * f.loc["const", "b"], 0.0251, 5e-5)
f, _, _ = nw(TB["Original 3m"]["net"].loc["2022-08-31":END], FF3)
rec("V8 team Table 1", "team Original 3m holdout FF3 alpha t (writeup -2.19)", f.loc["const", "t"], -2.19, 5e-3)
CF3 = run_all("corr", B5, FF3, rf, team_costs(FF3.columns))
hc = T("q2_hedge_cost_post2010")
for hname, strs in (("FF3", CF3), ("FF5UC", Q2)):
    for nm in ("Original 3m", "Always-short Brown"):
        s = strs[nm].loc["2010-01-31":END]
        r_ = hc[(hc.baseline == "corr") & (hc.hedge == hname) & (hc.strategy == nm)].iloc[0]
        rec("V8 hedge cost", f"{hname} {nm} post2010 annual turnover", 12 * s["turnover"].mean(), r_.ann_turnover, 5e-3)
        rec("V8 hedge cost", f"{hname} {nm} post2010 cost drag", 12 * (s["gross"].mean() - s["net"].mean()), r_.ann_cost_drag, 5e-5)
        rec("V8 hedge cost", f"{hname} {nm} post2010 gross", 12 * s["gross"].mean(), r_.ann_gross, 5e-5)
# corrected FF3-hedged validation/holdout table (FINDINGS Q1 table 5/5 columns)
t1 = T("q1_table1")
for nm in ("Original 3m", "Pure 6m", "Always-short Brown"):
    for p in ("validation", "holdout"):
        a, e = WIN[p]
        f, _, _ = nw(CF3[nm]["net"].loc[a:e], FF3)
        r_ = t1[(t1.legs == "L5") & (t1.baseline == "corr") & (t1.period == p) & (t1.strategy == nm)].iloc[0]
        rec("V8 corr 5/5 FF3", f"{nm} {p} alpha %", 1200 * f.loc["const", "b"], r_.alpha_ff3_pct, 5e-3)

# ---------------------------------------------------------------- V9: grid-wide multiple testing from the ledger + claim checks
print("\n[V9] grid")
L = T("tests_ledger")
fam = L[(L.statistic_name == "t_alpha_NW6") & ~L.note.str.contains("gross zero-cost") & L.test_id.str.match(r"^(strat|spread)\|")
        & L.p_value_two_sided.notna()].copy()
fam["holm"] = holm(fam.p_value_two_sided)
fam["bh"] = bh(fam.p_value_two_sided)
fam["pos"] = fam.note.str.extract(r"alpha_ann=(-?[0-9.]+)%")[0].astype(float) > 0
rec("V9 grid", "number of grid alpha tests", float(len(fam)), 8091.0, 0)
rec("V9 grid", "positive Holm survivors", float((fam.pos & (fam.holm < 0.05)).sum()), 0.0, 0)
rec("V9 grid", "positive BH survivors", float((fam.pos & (fam.bh < 0.05)).sum()), 0.0, 0)
rec("V9 grid", "negative BH survivors", float((~fam.pos & (fam.bh < 0.05)).sum()), 27.0, 0)
rec("V9 grid", "min Holm-adjusted p", float(fam.holm.min()), 0.0818, 5e-4)
rec("V9 grid", "min-Holm test is negative (1=yes)", float(not fam.loc[fam.holm.idxmin(), "pos"]), 1.0, 0)
rec("V9 grid", "positive tests with p<0.05", float((fam.pos & (fam.p_value_two_sided < 0.05)).sum()), 368.0, 0)
# ledger completeness: every non-gross strategy-grid regression and every spread regression is in the family
spc = T("q2_spread_controls")
n_expected = int(((sgrid.costs != "u0") & sgrid.p_alpha.notna()).sum() + spc.p_alpha.notna().sum())
rec("V9 ledger", "family size == non-gross strategy regressions + spread regressions", float(len(fam)), float(n_expected), 0)
rec("V9 ledger", "primary tests in ledger (14*3 + 4)", float((L.primary_or_exploratory == "primary").sum()), 46.0, 0)
rec("V9 ledger", "ledger test_id unique (1=yes)", float(L.test_id.is_unique), 1.0, 0)
# claim: "every hedged strategy has a negative holdout alpha under every leg design, control set and cost level"
h = sgrid[sgrid.period == "holdout"]
rec("V9 claim", "holdout strategy regressions with alpha > 0 (claim implies 0)", float((h.alpha_ann > 0).sum()), 0.0, 0,
    "positives: " + "; ".join(sorted(set(h[h.alpha_ann > 0].apply(lambda r: f"{r.strat}|{r.legs}|{r.hedge}|{r.eval_id}", axis=1)))))
sig_rules = h[h.strat != "Always-short Brown"]
rec("V9 claim", "holdout alpha > 0 among the 6 attention-timed rules", float((sig_rules.alpha_ann > 0).sum()), 0.0, 0)
rec("V9 claim", "zero-cost (u0) runs exist for 8-and-8 legs (1=yes)", float(((sgrid.costs == "u0") & (sgrid.legs != "L5")).any()), 1.0, 0,
    "FINDINGS says negative holdout alpha 'under every leg design ... including zero cost'")

# ---------------------------------------------------------------- V11: random sample of the whole grid recomputed with my engine
print("\n[V11] random grid sample")
FF3U = FF3.join(f5["UMD"], how="inner").dropna()
COMEQX = (ind[["Oil", "Coal", "Mines"]].mean(axis=1, skipna=False) - rf).rename("COMEQx")
FF5UCX = FF5U.join(COMEQX, how="inner").dropna()
HEDGE = {"FF3": (FF3, rf), "FF3U": (FF3U, rf), "FF5U": (FF5U.dropna(), RF5), "FF5UC": (FF5UC, RF5), "FF5UCx": (FF5UCX, RF5)}
NT = pd.concat([wti, imf, wti.shift(-1).rename("WTI_lead"), imf.shift(-1).rename("IMF_lead")], axis=1)
EVAL = {"E:FF3": ("FF3", []), "E:FF3U": ("FF3U", []), "E:FF5U": ("FF5U", []), "E:FF5UC": ("FF5UC", []), "E:FF5UCx": ("FF5UCx", []),
        "E:FF3+cmdty": ("FF3", ["WTI", "IMF"]), "E:FF3U+cmdty": ("FF3U", ["WTI", "IMF"]), "E:FF5U+cmdty": ("FF5U", ["WTI", "IMF"]),
        "E:FF5UC+cmdty": ("FF5UC", ["WTI", "IMF"]), "E:FF5UCx+cmdty": ("FF5UCx", ["WTI", "IMF"]),
        "E:FF5UC+cmdty+lead": ("FF5UC", ["WTI", "IMF", "WTI_lead", "IMF_lead"])}
LEGB = {"L5": B5, "L8H": B8, "L8M": B8}
PER = {"post2010": WIN["post2010"], "validation": WIN["validation"], "holdout": WIN["holdout"], "pre_covid": ("2010-01-31", "2019-12-31"),
       "covid": ("2020-01-31", "2021-12-31"), "inflation_rates": ("2022-01-31", "2024-12-31"), "last18": ("2025-02-28", END),
       "last12": ("2025-08-31", END)}
FIRST = {"Original 3m": "threshold_raw", "Original 6m": "threshold_raw", "Always-short Brown": "threshold_raw", "Pure 3m": "threshold_pure",
         "Pure 6m": "threshold_pure", "Continuous raw": "w_raw", "Continuous pure": "w_pure"}
rng = np.random.default_rng(20260926)
samp = sgrid.iloc[rng.choice(len(sgrid), 90, replace=False)]
cache = {}
for _, r in samp.iterrows():
    key = (r.legs, r.baseline, r.hedge, r.costs)
    if key not in cache:
        Xh, rfs = HEDGE[r.hedge]
        cst = team_costs(Xh.columns) if r.costs == "team" else uni_costs(Xh.columns, int(r.costs[1:]))
        cache[key] = run_all(r.baseline, LEGB[r.legs], Xh, rfs, cst)
    net = cache[key][r.strat]["net"]
    if r.period == "full_live":
        a = SIG[r.baseline][FIRST[r.strat]].first_valid_index() + pd.offsets.MonthEnd(1)
        e = pd.Timestamp(END)
    else:
        a, e = PER[r.period]
    xh, ntc = EVAL[r.eval_id]
    X = HEDGE[xh][0]
    if ntc:
        X = X.join(NT[ntc], how="left")
    f, n, k = nw(net.loc[a:e], X, demean=ntc if ntc else None)
    tag = f"{r.legs}|{r.baseline}|{r.hedge}|{r.costs}|{r.strat}|{r.period}|{r.eval_id}"
    rec("V11 grid sample", f"{tag} alpha", 12 * f.loc["const", "b"], r.alpha_ann, 5e-5)
    rec("V11 grid sample", f"{tag} t", f.loc["const", "t"], r.t_alpha, 5e-3)
    rec("V11 grid sample", f"{tag} p", f.loc["const", "p"], r.p_alpha, 5e-4)
    rec("V11 grid sample", f"{tag} n", float(n), float(r.n), 0)
# raw spread sample with non-traded controls
spc2 = spc.iloc[rng.choice(len(spc), 25, replace=False)]
GBL = {"L5": GB5, "L8H": gbH, "L8M": gbM}
for _, r in spc2.iterrows():
    a, e = (WIN["full_1970"] if r.period == "full_1970" else PER[r.period])
    xh, ntc = EVAL[r.eval_id]
    X = HEDGE[xh][0]
    if ntc:
        X = X.join(NT[ntc], how="left")
    f, n, k = nw(GBL[r.legs].loc[a:e], X, demean=ntc if ntc else None)
    tag = f"spread|{r.legs}|{r.period}|{r.eval_id}"
    rec("V11 spread sample", f"{tag} alpha", 12 * f.loc["const", "b"], r.alpha_ann, 5e-5)
    rec("V11 spread sample", f"{tag} t", f.loc["const", "t"], r.t_alpha, 5e-3)
    rec("V11 spread sample", f"{tag} n", float(n), float(r.n), 0)

# ---------------------------------------------------------------- V10: reproducibility of the module rerun vs pre-rerun snapshot
snap = pathlib.Path("/tmp/claude-1000/-home-hashim-projects-GA/5d56c5f1-d319-48cb-b466-4daeaca6ed67/scratchpad/m2_before")
if snap.exists():
    for nm in ("q2_primary", "q1_primary", "q4_primary", "q3_primary", "q4_breakeven", "key_numbers"):
        a_ = pd.read_csv(snap / f"{M}_{nm}.csv")
        b_ = T(nm)
        if nm == "key_numbers":  # round 2: the fixer added keys; compare the keys present in the round-1 snapshot
            b_ = b_.set_index("key").loc[a_.key].reset_index()
            a_ = a_[~a_.key.isin(["n_ledger_tests"])].reset_index(drop=True)  # ledger grew by 30 comeq rows (item 13)
            b_ = b_[~b_.key.isin(["n_ledger_tests"])].reset_index(drop=True)
        num = a_.select_dtypes("number")
        dmax = float((num - b_[num.columns]).abs().max().max()) if len(num.columns) else 0.0
        same_str = bool((a_.select_dtypes(exclude="number").astype(str) == b_[a_.select_dtypes(exclude="number").columns].astype(str)).all().all())
        rec("V10 rerun", f"{nm}: max numeric diff vs pre-rerun output", dmax, 0.0, 1e-9, f"string cells identical: {same_str}")

R = pd.DataFrame(RES)
R.to_csv(OUT / "verify_results.csv", index=False, float_format="%.8g")
print(f"\n{len(R)} checks, {int(R.match.sum())} match, {int((~R.match).sum())} mismatch")
print(R[~R.match].to_string())
