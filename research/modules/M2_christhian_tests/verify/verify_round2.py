"""Round-2 independent checks for M2_christhian_tests (numbers that are new or changed in the corrected FINDINGS).

Self-contained: does NOT import modules/M2_christhian_tests/{run,helpers}.py. The P&L engine is a copy of the round-1
engine in verify_m2.py (own COMEQ, corrected baseline, 60m rolling hedge lagged one month, positions, costs, NW(6) OLS,
t(n-k) p-values); only the pure and continuous signals come from team_pipeline.build_signals.

Checks
  R1 holdout sign census: every holdout row of strategy_grid.csv (net-of-cost and zero-cost) recomputed with my engine.
  R2 hedge-cost change FF3 -> FF5+UMD+COMEQ (total and overlay turnover, cost drag, gross), post2010, both baselines.
  R3 rolling 60m FF3 HML betas: positive runs of the GB beta 1975-2026, leg betas at the peaks.
  R4 COMEQ / COMEQx / industries: FF5+UMD spanning alphas and the new ledger rows.
  R5 Q4 cost table (corrected, 5/5, FF3 hedge): alphas at 5/10/25 bp and zero-cost holdout alphas with t.
  R6 residual HML ranges (team FF3 hedge, both baselines; FF5UC hedge) and the 6-month validation alpha range.
  R7 BE/ME above/below-median shares.
  R8 ledger and grid counts (13,482 tests; 42 comeq rows; BH negatives by window).
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M2_christhian_tests/verify/verify_round2.py
Writes verify/verify_round2_results.csv.
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
RES = []


def rec(check, item, mine, theirs, tol, note=""):
    mine, theirs = float(mine), float(theirs)
    ok = (np.isnan(mine) and np.isnan(theirs)) or abs(mine - theirs) <= tol
    RES.append(dict(check=check, item=item, mine=mine, reference=theirs, abs_diff=abs(mine - theirs), tol=tol, match=bool(ok), note=note))


def T(name):
    return pd.read_csv(TABLES / f"{M}_{name}.csv")


def nw(y, X, lags=6, demean=None):
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
    r2 = 1 - (u @ u) / ((Y - Y.mean()) @ (Y - Y.mean()))
    return pd.DataFrame({"b": b, "t": t, "p": p}, index=names), n, k, r2


# ============================================================================ data
TM = load_team()
ind, ff3, mac, emis = TM["industries"], TM["ff3"], TM["macro"], TM["emissions"]
f5 = load_ff5_mom()
rf = ff3["RF"]
COMEQ = (ind[["Oil", "Coal", "Mines", "Gold"]].mean(axis=1, skipna=False) - rf).rename("COMEQ")
COMEQX = (ind[["Oil", "Coal", "Mines"]].mean(axis=1, skipna=False) - rf).rename("COMEQx")
FF3 = ff3[["Mkt-RF", "SMB", "HML"]]
FF5U = f5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].loc[:END].dropna()
FF5UC = FF5U.join(COMEQ, how="inner").dropna()
FF5UCX = FF5U.join(COMEQX, how="inner").dropna()
FF3U = FF3.join(f5["UMD"], how="inner").dropna()
RF5 = f5["RF"].loc[:END]
wti = np.log(load_fred("MCOILWTICO")).diff().rename("WTI")
imf = np.log(load_fred("PALLFNFINDEXM")).diff().rename("IMF")
NT = pd.concat([wti, imf, wti.shift(-1).rename("WTI_lead"), imf.shift(-1).rename("IMF_lead")], axis=1)

srt = emis.sort_values()
G5, B5 = list(srt.index[:5]), list(srt.index[::-1][:5])
G8, B8 = list(srt.index[:8]), list(srt.index[::-1][:8])
HEDGE = {"FF3": (FF3, rf), "FF3U": (FF3U, rf), "FF5U": (FF5U, RF5), "FF5UC": (FF5UC, RF5), "FF5UCx": (FF5UCX, RF5)}
EVAL = {"E:FF3": ("FF3", []), "E:FF3U": ("FF3U", []), "E:FF5U": ("FF5U", []), "E:FF5UC": ("FF5UC", []), "E:FF5UCx": ("FF5UCx", []),
        "E:FF3+cmdty": ("FF3", ["WTI", "IMF"]), "E:FF3U+cmdty": ("FF3U", ["WTI", "IMF"]), "E:FF5U+cmdty": ("FF5U", ["WTI", "IMF"]),
        "E:FF5UC+cmdty": ("FF5UC", ["WTI", "IMF"]), "E:FF5UCx+cmdty": ("FF5UCx", ["WTI", "IMF"]),
        "E:FF5UC+cmdty+lead": ("FF5UC", ["WTI", "IMF", "WTI_lead", "IMF_lead"])}
LEGB = {"L5": B5, "L8H": B8, "L8M": B8}
WIN = {"post2010": ("2010-01-31", END), "validation": ("2010-01-31", "2022-07-31"), "holdout": ("2022-08-31", END)}

# corrected baseline: CPI gap interpolated, attention and the purification controls lagged one month
m_corr = mac.copy()
m_corr["cpi"] = m_corr["cpi"].interpolate(limit_area="inside")
C = Config()
SIG = {"team": build_signals(mac["attention"], mac, C),
       "corr": build_signals(m_corr["attention"].shift(1), m_corr, C, controls=team_controls(m_corr).shift(1))}


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


_HCACHE = {}


def strat_pnl(brown_names, hedge, pos_signal, kind, costs):
    Xh, rf_s = HEDGE[hedge]
    key = (tuple(brown_names), hedge)
    if key not in _HCACHE:
        y = ind[brown_names].mean(axis=1) - rf_s
        _HCACHE[key] = rolling_hedge(y, Xh)
    d, beta, eps = _HCACHE[key]
    sig = eps.rolling(36, min_periods=36).std(ddof=1)
    mag = (0.05 / (np.sqrt(12) * sig)).clip(upper=1.0)
    live = mag.first_valid_index()
    if kind == "state":
        pos = (-mag).where(pos_signal.reindex(d.index).fillna(False).astype(bool), 0.0)
    elif kind == "cont":
        pos = -mag * pos_signal.reindex(d.index).fillna(0).clip(0, 1)
    else:
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
    return pd.DataFrame({"pos": pos, "gross": gross, "net": net, "turnover": dpos + dov.sum(axis=1), "ov_turnover": dov.sum(axis=1)})


def cost_dict(hedge, costs):
    cols = HEDGE[hedge][0].columns
    if costs == "team":
        return {"asset": 10e-4, **{c: (5e-4 if c == "Mkt-RF" else 25e-4) for c in cols}}
    bp = int(costs[1:])
    return {"asset": bp * 1e-4, **{c: bp * 1e-4 for c in cols}}


STRATS = [("Original 3m", "raw", "state", 3), ("Pure 3m", "pure", "state", 3), ("Original 6m", "raw", "state", 6),
          ("Pure 6m", "pure", "state", 6), ("Continuous raw", "raw", "cont", None), ("Continuous pure", "pure", "cont", None),
          ("Always-short Brown", None, "always", None)]
S7 = [s[0] for s in STRATS]
_RCACHE = {}


def run_all(legs, base, hedge, costs):
    key = (legs, base, hedge, costs)
    if key not in _RCACHE:
        S, out = SIG[base], {}
        for nm, k_, kind, h in STRATS:
            sigl = S[f"hold_{k_}"][h] if kind == "state" else (S[f"w_{k_}"] if kind == "cont" else None)
            out[nm] = strat_pnl(LEGB[legs], hedge, sigl, kind, cost_dict(hedge, costs))
        _RCACHE[key] = out
    return _RCACHE[key]


def evaluate(net, a, e, eval_id):
    xh, ntc = EVAL[eval_id]
    X = HEDGE[xh][0]
    if ntc:
        X = X.join(NT[ntc], how="left")
    f, n, k, r2 = nw(net.loc[a:e], X, demean=ntc if ntc else None)
    return f, n


SG = T("strategy_grid")

# ============================================================================ R1 holdout sign census (every holdout row)
print("[R1] holdout census")
H = SG[SG.period == "holdout"].copy()
mine_a, mine_t = [], []
for _, r in H.iterrows():
    net = run_all(r.legs, r.baseline, r.hedge, r.costs)[r.strat]["net"]
    f, n = evaluate(net, *WIN["holdout"], r.eval_id)
    mine_a.append(12 * f.loc["const", "b"])
    mine_t.append(f.loc["const", "t"])
H["my_alpha"], H["my_t"] = mine_a, mine_t
rec("R1 census", "holdout rows recomputed (all)", len(H), 1078, 0)
rec("R1 census", "max |my alpha - grid alpha| over all 1,078 holdout rows", (H.my_alpha - H.alpha_ann).abs().max(), 0, 5e-8)
rec("R1 census", "max |my t - grid t| over all 1,078 holdout rows", (H.my_t - H.t_alpha).abs().max(), 0, 5e-6)
hn, hg = H[H.costs != "u0"], H[H.costs == "u0"]
sig6 = hn[hn.strat != "Always-short Brown"]
ash = hn[hn.strat == "Always-short Brown"]
pos = hn[hn.my_alpha > 0]
rec("R1 census", "net-of-cost holdout regressions", len(hn), 1050, 0)
rec("R1 census", "net-of-cost rows per strategy (min)", hn.groupby("strat").size().min(), 150, 0)
rec("R1 census", "net-of-cost rows per strategy (max)", hn.groupby("strat").size().max(), 150, 0)
rec("R1 census", "six signal rules: rows", len(sig6), 900, 0)
rec("R1 census", "six signal rules: positive", (sig6.my_alpha > 0).sum(), 0, 0)
top = sig6.loc[sig6.my_alpha.idxmax()]
rec("R1 census", "six signal rules: highest holdout alpha %", 100 * top.my_alpha, -0.03, 0.005,
    f"{top.strat}|{top.legs}|{top.baseline}|{top.hedge}|{top.costs}|{top.eval_id}")
rec("R1 census", "six signal rules: t of highest", top.my_t, -0.08, 0.005)
tied = sig6[(sig6.my_alpha - top.my_alpha).abs() < 1e-12]
print("signal-rule max ties:", tied[["strat", "legs", "baseline", "hedge", "costs", "eval_id"]].to_string())
rec("R1 census", "always-short positive (of 150)", (ash.my_alpha > 0).sum(), 24, 0)
rec("R1 census", "positives all Always-short (1=yes)", float((pos.strat == "Always-short Brown").all()), 1, 0)
rec("R1 census", "positives all 8-and-8 legs (1=yes)", float(pos.legs.isin(["L8H", "L8M"]).all()), 1, 0)
rec("R1 census", "positives with L8H", (pos.legs == "L8H").sum(), 12, 0)
rec("R1 census", "positives with L8M", (pos.legs == "L8M").sum(), 12, 0)
rec("R1 census", "positives all team costs (1=yes)", float((pos.costs == "team").all()), 1, 0)
rec("R1 census", "positives span all 5 hedges", pos.hedge.nunique(), 5, 0)
rec("R1 census", "positives span both baselines", pos.baseline.nunique(), 2, 0)
rec("R1 census", "positives on E:FF5UC", (pos.eval_id == "E:FF5UC").sum(), 4, 0)
rec("R1 census", "positives on E:FF5UC+cmdty", (pos.eval_id == "E:FF5UC+cmdty").sum(), 20, 0)
rec("R1 census", "always-short 8-and-8 net-of-cost holdout rows", ash.legs.isin(["L8H", "L8M"]).sum(), 92, 0)
pm = hn.loc[hn.my_alpha.idxmax()]
rec("R1 census", "largest positive holdout alpha %", 100 * pm.my_alpha, 0.42, 0.005,
    f"{pm.strat}|{pm.legs}|{pm.baseline}|{pm.hedge}|{pm.costs}|{pm.eval_id}")
rec("R1 census", "t of largest positive", pm.my_t, 0.22, 0.005)
rec("R1 census", "largest positive config is 8/8 team FF5U hedge on E:FF5UC+cmdty (1=yes)",
    float(pm.baseline == "team" and pm.hedge == "FF5U" and pm.eval_id == "E:FF5UC+cmdty" and pm.legs in ("L8H", "L8M")), 1, 0)
rec("R1 census", "always-short 5/5 highest net-of-cost holdout alpha %", 100 * ash[ash.legs == "L5"].my_alpha.max(), -0.91, 0.005)
rec("R1 census", "zero-cost holdout rows", len(hg), 28, 0)
rec("R1 census", "zero-cost rows are L5 with FF3/FF5UC hedges only (1=yes)",
    float((hg.legs == "L5").all() and set(hg.hedge) == {"FF3", "FF5UC"}), 1, 0)
rec("R1 census", "zero-cost positive", (hg.my_alpha > 0).sum(), 0, 0)
gm = hg.loc[hg.my_alpha.idxmax()]
rec("R1 census", "zero-cost highest holdout alpha %", 100 * gm.my_alpha, -0.39, 0.005, f"{gm.strat}|{gm.legs}|{gm.baseline}|{gm.hedge}|{gm.eval_id}")
rec("R1 census", "zero-cost highest t", gm.my_t, -1.35, 0.005)
rec("R1 census", "zero-cost highest is Continuous pure / team / FF3 (1=yes)",
    float(gm.strat == "Continuous pure" and gm.baseline == "team" and gm.hedge == "FF3"), 1, 0)
x = hg[(hg.strat == "Continuous pure") & (hg.baseline == "team") & (hg.hedge == "FF5UC")].iloc[0]
rec("R1 census", "zero-cost team FF5UC Continuous pure holdout alpha %", 100 * x.my_alpha, -0.47, 0.005)
for nm, v in (("Original 3m", -1.67), ("Always-short Brown", -1.65)):
    x = hg[(hg.strat == nm) & (hg.baseline == "corr") & (hg.hedge == "FF3")].iloc[0]
    rec("R1 census", f"zero-cost corr FF3 {nm} holdout alpha %", 100 * x.my_alpha, v, 0.005)
KN = T("key_numbers").set_index("key")["value"]
rec("R1 census", "key_numbers holdout_net_positive vs mine", float(KN["holdout_net_positive"]), (hn.my_alpha > 0).sum(), 0)
rec("R1 census", "key_numbers holdout_net_max_alpha vs mine", float(KN["holdout_net_max_alpha"]), pm.my_alpha, 5e-8)
rec("R1 census", "key_numbers holdout_gross_max_alpha vs mine", float(KN["holdout_gross_max_alpha"]), gm.my_alpha, 5e-8)
rec("R1 census", "key_numbers holdout_gross_max_alpha_t vs mine", float(KN["holdout_gross_max_alpha_t"]), gm.my_t, 5e-6)
# primary Q2 holdout range across hedge sets (hedge = eval), corrected 5/5 team costs: 'between -0.58% and -3.44% (t -1.01 to -2.27)'
q = hn[(hn.legs == "L5") & (hn.baseline == "corr") & (hn.costs == "team") & hn.hedge.isin(["FF3", "FF3U", "FF5U", "FF5UC"])
       & (hn.eval_id == "E:" + hn.hedge)]
rec("R1 Q2 hedges", "rows (7 x 4 hedge sets)", len(q), 28, 0)
rec("R1 Q2 hedges", "holdout alpha max % (least negative)", 100 * q.my_alpha.max(), -0.58, 0.005)
rec("R1 Q2 hedges", "holdout alpha min %", 100 * q.my_alpha.min(), -3.44, 0.005)
rec("R1 Q2 hedges", "holdout t max", q.my_t.max(), -1.01, 0.005)
rec("R1 Q2 hedges", "holdout t min", q.my_t.min(), -2.27, 0.005)

# ============================================================================ R2 hedge-cost change, post2010
print("[R2] hedge cost change")
HCC = T("q2_hedge_cost_change")
chg = {}
for b in ("corr", "team"):
    for nm in S7:
        a3 = run_all("L5", b, "FF3", "team")[nm].loc["2010-01-31":END]
        a5 = run_all("L5", b, "FF5UC", "team")[nm].loc["2010-01-31":END]
        row = HCC[(HCC.baseline == b) & (HCC.strategy == nm)].iloc[0]
        tot = 100 * (a5.turnover.mean() / a3.turnover.mean() - 1)
        ovl = 100 * (a5.ov_turnover.mean() / a3.ov_turnover.mean() - 1)
        chg[(b, nm)] = (tot, ovl, 12 * a3.turnover.mean(), 12 * a5.turnover.mean(), 12 * (a3.gross.mean() - a3.net.mean()),
                        12 * (a5.gross.mean() - a5.net.mean()), 12 * a3.gross.mean(), 12 * a5.gross.mean())
        rec("R2 hedge cost", f"{b} {nm} total turnover change %", tot, row.total_turnover_change_pct, 1e-4)
        rec("R2 hedge cost", f"{b} {nm} overlay turnover change %", ovl, row.overlay_turnover_change_pct, 1e-4)
        rec("R2 hedge cost", f"{b} {nm} cost drag FF5UC", chg[(b, nm)][5], row.cost_drag_FF5UC, 5e-8)
        rec("R2 hedge cost", f"{b} {nm} gross FF5UC", chg[(b, nm)][7], row.gross_FF5UC, 5e-8)
cs = pd.DataFrame({k[1]: v for k, v in chg.items() if k[0] == "corr"}, index=["tot", "ovl", "to3", "to5", "cd3", "cd5", "g3", "g5"]).T
sr = cs.drop("Always-short Brown")
rec("R2 text", "corr total turnover change, signal rules min %", sr.tot.min(), 24, 0.5)
rec("R2 text", "corr total turnover change, signal rules max %", sr.tot.max(), 37, 0.5)
rec("R2 text", "corr total turnover change, always-short %", cs.loc["Always-short Brown", "tot"], 127, 0.5)
rec("R2 text", "corr overlay turnover change, signal rules min %", sr.ovl.min(), 35, 0.5)
rec("R2 text", "corr overlay turnover change, signal rules max %", sr.ovl.max(), 54, 0.5)
rec("R2 text", "corr overlay turnover change, always-short %", cs.loc["Always-short Brown", "ovl"], 163, 0.5)
rec("R2 text", "corr Original 3m total turnover FF3", cs.loc["Original 3m", "to3"], 4.80, 0.005)
rec("R2 text", "corr Original 3m total turnover FF5UC", cs.loc["Original 3m", "to5"], 5.99, 0.005)
rec("R2 text", "corr Original 3m cost drag FF3 %", 100 * cs.loc["Original 3m", "cd3"], 0.53, 0.005)
rec("R2 text", "corr Original 3m cost drag FF5UC %", 100 * cs.loc["Original 3m", "cd5"], 0.85, 0.005)
rec("R2 text", "corr Always-short gross FF3 %", 100 * cs.loc["Always-short Brown", "g3"], 1.15, 0.005)
rec("R2 text", "corr Always-short gross FF5UC %", 100 * cs.loc["Always-short Brown", "g5"], 0.44, 0.005)

# ============================================================================ R3 rolling 60m FF3 betas and positive runs
print("[R3] rolling runs")


def roll_hml(y, X):
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    Y, F = d["y"].to_numpy(), d[X.columns].to_numpy()
    j = list(X.columns).index("HML") + 1
    out = {}
    for e in range(59, len(d)):
        Z = np.column_stack([np.ones(60), F[e - 59:e + 1]])
        out[d.index[e]] = np.linalg.lstsq(Z, Y[e - 59:e + 1], rcond=None)[0][j]
    return pd.Series(out)


gb = roll_hml(ind[G5].mean(axis=1) - ind[B5].mean(axis=1), FF3).loc["1975-01-31":END]
bl = roll_hml(ind[B5].mean(axis=1) - rf, FF3).loc["1975-01-31":END]
gl = roll_hml(ind[G5].mean(axis=1) - rf, FF3).loc["1975-01-31":END]
grp = gb.le(0).cumsum()
runs = []
for _, seg in gb[gb > 0].groupby(grp[gb > 0]):
    pk = seg.idxmax()
    runs.append(dict(first=seg.index.min(), last=seg.index.max(), n=len(seg), peak=pk, peak_b=seg.max(), brown=bl[pk], green=gl[pk]))
RUNS = pd.DataFrame(runs).sort_values("n", ascending=False).reset_index(drop=True)
print(RUNS.to_string())
for i, (f_, l_, n_, pk_, pb_, bb_) in enumerate((("2008-02", "2013-10", 69, "2008-12", 0.53, -0.12), ("1983-12", "1987-03", 40, "1985-03", 0.25, -0.04))):
    r = RUNS.iloc[i]
    ok = (r["first"].strftime("%Y-%m") == f_) and (r["last"].strftime("%Y-%m") == l_) and (r.peak.strftime("%Y-%m") == pk_)
    rec("R3 rolling", f"run {f_}..{l_}: dates and peak month match (1=yes)", float(ok), 1, 0)
    rec("R3 rolling", f"run {f_}..{l_}: n windows", r.n, n_, 0)
    rec("R3 rolling", f"run {f_}..{l_}: peak GB beta", r.peak_b, pb_, 0.005)
    rec("R3 rolling", f"run {f_}..{l_}: Brown-leg beta at peak", r.brown, bb_, 0.005)
rest = RUNS.iloc[2:]
rec("R3 rolling", "other runs: max n windows", rest.n.max(), 9, 0)
rec("R3 rolling", "other runs: max peak", rest.peak_b.max(), 0.10, 0.005)
rec("R3 rolling", "Brown leg mean beta 1975-2026", bl.mean(), 0.29, 0.005)
rec("R3 rolling", "Brown leg share negative %", 100 * (bl < 0).mean(), 9, 0.5)
rec("R3 rolling", "Green leg mean beta 1975-2026", gl.mean(), 0.10, 0.005)
PR = T("q3_rolling_positive_runs")
pr = PR[PR.model == "FF3"].sort_values("n_windows", ascending=False).reset_index(drop=True)
rec("R3 rolling", "module file FF3 runs == my runs (count)", len(pr), len(RUNS), 0)
rec("R3 rolling", "module file peak betas == mine (max diff)", (pr.peak_gb_beta.to_numpy() - RUNS.peak_b.to_numpy()).__abs__().max(), 0, 1e-8)

# ============================================================================ R4 COMEQ spanning and ledger rows
print("[R4] COMEQ")
J = T("q2_comeq_justification").set_index("series")
L = T("tests_ledger")
ser = {"COMEQ (Oil, Coal, Mines, Gold)": COMEQ, "COMEQ ex-Gold (Oil, Coal, Mines)": COMEQX,
       **{f"{nm} industry": (ind[nm] - rf).rename(nm) for nm in ("Oil", "Coal", "Mines", "Gold")}}
for nm, s in ser.items():
    f, n, k, r2 = nw(s.loc["1992-02-29":END], FF5U)
    j = J.loc[nm]
    rec("R4 COMEQ", f"{nm} FF5U alpha", 12 * f.loc["const", "b"], j.ff5u_alpha_ann, 5e-8)
    rec("R4 COMEQ", f"{nm} FF5U t", f.loc["const", "t"], j.ff5u_t_alpha, 5e-6)
    rec("R4 COMEQ", f"{nm} FF5U p t(n-k)", f.loc["const", "p"], j.ff5u_p_alpha, 5e-6)
    rec("R4 COMEQ", f"{nm} FF5U R2", r2, j.ff5u_r2, 5e-6)
    rec("R4 COMEQ", f"{nm} FF5U n", n, 414, 0)
    lr = L[L.test_id == f"comeq|{nm}|ff5u_alpha"].iloc[0]
    rec("R4 ledger", f"{nm} ledger ff5u_alpha t", lr.statistic, f.loc["const", "t"], 5e-6)
    rec("R4 ledger", f"{nm} ledger ff5u_alpha p", lr.p_value_two_sided, f.loc["const", "p"], 5e-6)
    d = pd.concat([s.rename("s"), wti.shift(-1).rename("WL"), (ind[B5].mean(axis=1) - rf).rename("br")], axis=1).loc["1992-02-29":"2026-06-30"].dropna()
    for col, lid in (("WL", "corr_WTI_lead"), ("br", "corr_brown")):
        rr = d.s.corr(d[col])
        tt = rr * np.sqrt((len(d) - 2) / (1 - rr ** 2))
        lr = L[L.test_id == f"comeq|{nm}|{lid}"].iloc[0]
        rec("R4 ledger", f"{nm} ledger {lid} t_corr_iid", lr.statistic, tt, 5e-5)
rec("R4 text", "COMEQ FF5U alpha %", 100 * J.loc["COMEQ (Oil, Coal, Mines, Gold)", "ff5u_alpha_ann"], -0.89, 0.005)
rec("R4 text", "COMEQ FF5U p", J.loc["COMEQ (Oil, Coal, Mines, Gold)", "ff5u_p_alpha"], 0.81, 0.005)
rec("R4 text", "COMEQx FF5U alpha %", 100 * J.loc["COMEQ ex-Gold (Oil, Coal, Mines)", "ff5u_alpha_ann"], -1.42, 0.005)
rec("R4 text", "COMEQx FF5U t", J.loc["COMEQ ex-Gold (Oil, Coal, Mines)", "ff5u_t_alpha"], -0.35, 0.005)
rec("R4 text", "COMEQx FF5U R2", J.loc["COMEQ ex-Gold (Oil, Coal, Mines)", "ff5u_r2"], 0.45, 0.005)
rec("R4 text", "Gold corr with WTI", J.loc["Gold industry", "corr_WTI"], 0.06, 0.005)
rec("R4 text", "correlation n", J.loc["COMEQ (Oil, Coal, Mines, Gold)", "n"], 413, 0)

# ============================================================================ R5 Q4 cost table (corrected, 5/5, FF3 hedge, FF3 alpha)
print("[R5] Q4 table")
Q4TXT = {  # strategy: (validation 5/10/25 alpha %, validation t at 5/10/25 or None, holdout 5/10/25 alpha %)
    "Original 3m": ((1.92, 1.66, 0.89), (2.31, 2.02, 1.09), (-1.87, -2.08, -2.69)),
    "Pure 3m": ((2.05, 1.76, 0.89), (2.37, 2.06, 1.07), (-1.87, -2.08, -2.69)),
    "Original 6m": ((2.25, 2.12, 1.74), (2.36, 2.22, 1.80), (-1.70, -1.89, -2.47)),
    "Pure 6m": ((2.51, 2.37, 1.98), (2.80, 2.63, 2.13), (-1.70, -1.89, -2.47)),
    "Continuous raw": ((0.54, 0.47, 0.27), None, (-0.51, -0.56, -0.70)),
    "Continuous pure": ((0.60, 0.53, 0.31), None, (-0.52, -0.57, -0.72)),
    "Always-short Brown": ((1.47, 1.43, 1.33), (1.18, None, None), (-1.67, -1.70, -1.78)),
}
for nm, (va, vt, ha) in Q4TXT.items():
    for i, c_ in enumerate(("u5", "u10", "u25")):
        net = run_all("L5", "corr", "FF3", c_)[nm]["net"]
        f, _ = evaluate(net, *WIN["validation"], "E:FF3")
        rec("R5 Q4 table", f"{nm} validation {c_} alpha %", 1200 * f.loc["const", "b"], va[i], 0.005)
        if vt is not None and vt[i] is not None:
            rec("R5 Q4 table", f"{nm} validation {c_} t", f.loc["const", "t"], vt[i], 0.005)
        f, _ = evaluate(net, *WIN["holdout"], "E:FF3")
        rec("R5 Q4 table", f"{nm} holdout {c_} alpha %", 1200 * f.loc["const", "b"], ha[i], 0.005)
# Q4 primary text: post2010 5 bp alphas 0.32..1.61 (t 0.73..1.89), holdout -0.51..-1.87
pa, pt, ha_ = [], [], []
for nm in S7:
    net = run_all("L5", "corr", "FF3", "u5")[nm]["net"]
    f, _ = evaluate(net, *WIN["post2010"], "E:FF3")
    pa.append(1200 * f.loc["const", "b"]); pt.append(f.loc["const", "t"])
    f, _ = evaluate(net, *WIN["holdout"], "E:FF3")
    ha_.append(1200 * f.loc["const", "b"])
rec("R5 Q4 primary", "post2010 u5 alpha min %", min(pa), 0.32, 0.005)
rec("R5 Q4 primary", "post2010 u5 alpha max %", max(pa), 1.61, 0.005)
rec("R5 Q4 primary", "post2010 u5 t min", min(pt), 0.73, 0.005)
rec("R5 Q4 primary", "post2010 u5 t max", max(pt), 1.89, 0.005)
rec("R5 Q4 primary", "holdout u5 alpha max %", max(ha_), -0.51, 0.005)
rec("R5 Q4 primary", "holdout u5 alpha min %", min(ha_), -1.87, 0.005)

# ============================================================================ R6 residual HML and the 6m validation range
print("[R6] residual HML")
for b, hedge, win, (lo, hi), (tlo, thi) in (("corr", "FF3", "post2010", (-0.053, -0.015), (-1.95, -1.19)),
                                             ("team", "FF3", "post2010", (-0.061, -0.019), (-2.36, -1.35)),
                                             ("corr", "FF5UC", "post2010", (-0.079, -0.024), (-1.69, -0.78))):
    bs, ts = [], []
    for nm in S7:
        f, _ = evaluate(run_all("L5", b, hedge, "team")[nm]["net"], *WIN[win], f"E:{hedge}")
        bs.append(f.loc["HML", "b"]); ts.append(f.loc["HML", "t"])
    rec("R6 residual HML", f"{b} {hedge} {win} b_HML min", min(bs), lo, 0.0005)
    rec("R6 residual HML", f"{b} {hedge} {win} b_HML max", max(bs), hi, 0.0005)
    rec("R6 residual HML", f"{b} {hedge} {win} t_HML min", min(ts), tlo, 0.005)
    rec("R6 residual HML", f"{b} {hedge} {win} t_HML max", max(ts), thi, 0.005)
v6 = []
for legs in ("L5", "L8H", "L8M"):
    for b in ("team", "corr"):
        for nm in ("Original 6m", "Pure 6m"):
            f, _ = evaluate(run_all(legs, b, "FF3", "team")[nm]["net"], *WIN["validation"], "E:FF3")
            v6.append(1200 * f.loc["const", "b"])
rec("R6 6m validation", "6m rules validation FF3 alpha min % (FF3 hedge, team costs, both baselines, all legs)", min(v6), 1.80, 0.005)
rec("R6 6m validation", "6m rules validation FF3 alpha max %", max(v6), 2.60, 0.005)
# corrected Q1 table (FF3 hedge, team costs): validation and holdout alpha/t for 5/5 and 8/8
Q1TXT = {"Original 3m": ((1.62, 1.97), (1.30, 1.85), (-2.16, -1.90), (-2.51, -1.81)),
         "Pure 3m": ((1.70, 2.01), (1.36, 1.74), (-2.16, -1.90), (-2.51, -1.81)),
         "Original 6m": ((2.09, 2.18), (1.80, 1.87), (-1.97, -1.30), (-1.24, -0.60)),
         "Pure 6m": ((2.33, 2.59), (2.36, 2.47), (-1.97, -1.30), (-1.24, -0.60)),
         "Continuous raw": ((0.46, 1.40), (0.36, 1.32), (-0.58, -1.33), (-0.44, -0.78)),
         "Continuous pure": ((0.51, 1.46), (0.40, 1.39), (-0.59, -1.33), (-0.41, -0.70)),
         "Always-short Brown": ((1.39, 1.12), (2.05, 1.71), (-1.72, -1.09), (-0.39, -0.19))}
for nm, cells in Q1TXT.items():
    for (legs, win), (a_, t_) in zip((("L5", "validation"), ("L8H", "validation"), ("L5", "holdout"), ("L8H", "holdout")), cells):
        f, _ = evaluate(run_all(legs, "corr", "FF3", "team")[nm]["net"], *WIN[win], "E:FF3")
        rec("R6 Q1 corr table", f"{nm} {legs} {win} alpha %", 1200 * f.loc["const", "b"], a_, 0.005)
        rec("R6 Q1 corr table", f"{nm} {legs} {win} t", f.loc["const", "t"], t_, 0.005)

# ============================================================================ R7 BE/ME shares 1975-2026
print("[R7] BE/ME")
bm = load_kf_industries("be_me_sum")
lbm = np.log(bm.where(bm > 0))
rel = lbm.sub(lbm.median(axis=1), axis=0).loc["1975":"2026"]
for nm, side, v in (("Util", "above", 100), ("Steel", "above", 100), ("Ships", "above", 94), ("Drugs", "below", 98), ("Fun", "below", 69),
                    ("Fin", "above", 96), ("RlEst", "above", 87), ("Telcm", "above", 85)):
    s = rel[nm].dropna()
    sh = 100 * ((s > 0).mean() if side == "above" else (s < 0).mean())
    rec("R7 BE/ME", f"{nm} {side} median % of years", sh, v, 0.5, f"n years {len(s)}; at-median years {(s == 0).sum()}")

# ============================================================================ R8 ledger and grid counts
print("[R8] ledger")
rec("R8 ledger", "n tests", len(L), 13482, 0)
for k_, v in {"primary": 46, "robustness": 5562, "exploratory": 7874}.items():
    rec("R8 ledger", f"n {k_}", (L.primary_or_exploratory == k_).sum(), v, 0)
rec("R8 ledger", "comeq rows", L.test_id.str.startswith("comeq|").sum(), 42, 0)
rec("R8 ledger", "test ids unique (1=yes)", float(L.test_id.is_unique), 1, 0)
fam = L[(L.statistic_name == "t_alpha_NW6") & ~L.note.str.contains("gross zero-cost") & L.test_id.str.match(r"^(strat|spread)\|")
        & L.p_value_two_sided.notna()].copy()
rec("R8 grid", "family size", len(fam), 8091, 0)
rec("R8 grid", "strategy alphas in family", fam.test_id.str.startswith("strat|").sum(), 7938, 0)
rec("R8 grid", "spread alphas in family", fam.test_id.str.startswith("spread|").sum(), 153, 0)
rec("R8 grid", "comeq rows outside family (1=yes)", float(~fam.test_id.str.startswith("comeq").any()), 1, 0)
fam["bh"] = bh(fam.p_value_two_sided).values
fam["holm"] = holm(fam.p_value_two_sided).values
fam["pos"] = fam.note.str.extract(r"alpha_ann=(-?[0-9.]+)%")[0].astype(float) > 0
negbh = fam[~fam.pos & (fam.bh < 0.05)]
rec("R8 grid", "negative BH survivors", len(negbh), 27, 0)
rec("R8 grid", "negative BH survivors in last18", negbh.test_id.str.contains(r"\|last18\|").sum(), 23, 0)
hb = negbh[negbh.test_id.str.contains(r"\|holdout\|")]
rec("R8 grid", "negative BH survivors in holdout", len(hb), 4, 0)
rec("R8 grid", "holdout BH negatives all use +lead evaluation (1=yes)", float(hb.test_id.str.contains("E:FF5UC\\+cmdty\\+lead").all()), 1, 0)
bp = fam[fam.pos].sort_values("p_value_two_sided").iloc[0]
rec("R8 grid", "best positive test is Pure 3m covid corr u5 (1=yes)",
    float(bp.test_id.startswith("strat|L5|corr|") and "|u5|Pure 3m|covid|" in bp.test_id), 1, 0, bp.test_id)
rec("R8 grid", "best positive p", bp.p_value_two_sided, 0.00035, 5e-6)
rec("R8 grid", "best positive BH", bp.bh, 0.062, 0.0005)
rec("R8 grid", "best positive Holm", bp.holm, 1.0, 0.005)

R = pd.DataFrame(RES)
R.to_csv(OUT / "verify_round2_results.csv", index=False, float_format="%.8g")
print(f"\n{len(R)} checks, {int(R.match.sum())} match, {int((~R.match).sum())} mismatch")
print(R[~R.match].to_string())
