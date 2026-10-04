"""Independent verification of M5 industry momentum (core book, costs, crash, robustness, carbon screens, Q4, ledger).

Does NOT import any module code (run.py, m5lib.py, optimizer.py, team_replica.py). Uses only lib/common.py loaders,
lib/team_pipeline.py (the orchestrator's separately tested replication of the team baseline) and my own numpy code:
own momentum ranking, own drift/turnover, own Newey-West (Bartlett, 6 lags, no small-sample correction), own
block bootstrap with a different seed.

Run:  cd /home/hashim/projects/GA/project/research && uv run python modules/M5_industry_momentum/verify/verify_m5.py
Writes verify/verify_core_results.csv (claim, builder value, my value, CSV value, verdict).
"""
from __future__ import annotations
import sys, pathlib
import numpy as np
import pandas as pd
from scipy import stats

RES = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(RES / "lib"))
import common as C  # loaders only
OUT = pathlib.Path(__file__).resolve().parent
TAB = RES / "outputs" / "tables"
tab = lambda n: pd.read_csv(TAB / f"M5_industry_momentum_{n}.csv")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vlib import *  # noqa: F401,F403  own helpers and data
from vlib import nw, ann, mdd, cbb, sr, boot_dsr, book, S, P, R, R_kf, F5, F3, X6, MODELS, cap, emis, T, tab

rows = []
def chk(claim, builder, mine, csv=None, tol=None, note=""):
    """tol: absolute tolerance for 'confirmed' against the builder's (rounded) figure."""
    tol = tol if tol is not None else 0.5 * 10 ** (-max(0, len(str(builder).split(".")[-1])) if "." in str(builder) else 0.5)
    diff = abs(float(mine) - float(builder))
    csv_ok = "" if csv is None else ("csv==mine" if abs(float(csv) - float(mine)) < 1e-6 * max(1, abs(float(mine))) + 1e-9 else f"csv!=mine ({csv})")
    verdict = "confirmed" if diff <= tol + 1e-12 else "DISCREPANCY"
    rows.append({"claim": claim, "builder": builder, "mine": float(mine), "csv": csv, "abs_diff": diff, "tol": tol,
                 "verdict": verdict, "csv_check": csv_ok, "note": note})
    print(f"{verdict:12s} {claim:70s} builder {builder!s:>10} mine {float(mine):12.6f} {csv_ok} {note}")

# ================================================================== 1. primary book
bt, Wh = book(R)
print(f"primary: {len(bt)} months {bt.index[0]:%Y-%m}..{bt.index[-1]:%Y-%m}; eligible min {bt.n_elig.min()} max {bt.n_elig.max()}; "
      f"months with 48 eligible: {(bt.n_elig == 48).sum()}")
rm = tab("returns_monthly").set_index("date"); rm.index = pd.to_datetime(rm.index)
print("max |net - builder net|:", float((bt["net"] - rm["net"]).abs().max()), " max |TO diff|:", float((bt["to"] - rm["turnover"]).abs().max()))
chk("n months full sample", 679, len(bt), tol=0)
m, v, s = ann(bt["net"])
pp = tab("perf_periods").set_index("period")
chk("net return full (ann, %)", 8.52, 100 * m, 100 * pp.loc["full_1970", "net_ret"])
chk("net vol full (%)", 18.00, 100 * v, 100 * pp.loc["full_1970", "vol"])
chk("net Sharpe full", 0.47, s, pp.loc["full_1970", "sharpe_net"])
chk("t NW6 of net mean full", 3.47, nw(bt["net"])["t"]["const"], pp.loc["full_1970", "t_net_mean_nw6"])
chk("turnover x/yr full", 12.47, 12 * bt["to"].mean(), pp.loc["full_1970", "turnover_ann"])
chk("cost drag %/yr full", 1.25, 100 * 12 * 0.001 * bt["to"].mean(), 100 * pp.loc["full_1970", "cost_drag_ann"])
chk("max DD full (%)", -60.3, 100 * mdd(bt["net"]), 100 * pp.loc["full_1970", "max_dd_net"])
for p, (bm, bv, bs, bd) in {"post2010": (6.79, 15.82, 0.43, -29.5), "holdout": (1.86, 16.58, 0.11, -25.4),
                             "last18": (3.90, 19.49, 0.20, -14.2), "last12": (8.58, 23.00, 0.37, -14.2)}.items():
    m, v, s = ann(S(bt["net"], p))
    chk(f"net return {p} (%)", bm, 100 * m, 100 * pp.loc[p, "net_ret"]); chk(f"Sharpe {p}", bs, s, pp.loc[p, "sharpe_net"])
    chk(f"max DD {p} (%)", bd, 100 * mdd(S(bt["net"], p)), 100 * pp.loc[p, "max_dd_net"])

# alphas
al = tab("alphas"); al_net = al[al.series == "net"].set_index(["period", "model"])
for p, pk in (("full", "full_1970"), ("post2010", "post2010"), ("holdout", "holdout")):
    for mname, Xf in MODELS.items():
        r = nw(S(bt["net"], p), Xf)
        ref = al_net.loc[(pk, mname)]
        rows.append({"claim": f"alpha {mname} {p}", "builder": 100 * ref.alpha_ann, "mine": 100 * 12 * r["b"]["const"], "csv": 100 * ref.alpha_ann,
                     "abs_diff": abs(100 * ref.alpha_ann - 100 * 12 * r["b"]["const"]), "tol": 0.005,
                     "verdict": "confirmed" if abs(ref.alpha_ann - 12 * r["b"]["const"]) < 5e-5 else "DISCREPANCY", "csv_check": "",
                     "note": f"t mine {r['t']['const']:.3f} vs csv {ref.t_alpha:.3f}; p mine {r['p']['const']:.3f} vs csv {ref.p_alpha:.3f}"})
r1 = nw(bt["net"], X6); r2 = nw(S(bt["net"], "post2010"), X6); rh = nw(S(bt["net"], "holdout"), X6)
chk("P1 FF5+UMD alpha full (%)", 1.74, 1200 * r1["b"]["const"]); chk("P1 t", 1.09, r1["t"]["const"]); chk("P1 p", 0.274, r1["p"]["const"])
chk("P2 FF5+UMD alpha post2010 (%)", 1.86, 1200 * r2["b"]["const"]); chk("P2 t", 0.71, r2["t"]["const"]); chk("P2 p", 0.481, r2["p"]["const"])
chk("holdout FF5+UMD alpha (%)", -4.48, 1200 * rh["b"]["const"]); chk("holdout t", -0.84, rh["t"]["const"])
chk("UMD beta full", 0.99, r1["b"]["UMD"]); chk("UMD beta t", 30.5, r1["t"]["UMD"]); chk("R2 FF5+UMD full", 0.67, r1["r2"])
chk("corr(net? gross INDMOM, UMD) full", 0.81, pd.concat([bt["gross"], F5["UMD"]], axis=1).dropna().corr().iloc[0, 1])
for mname, (ba, bt_) in {"CAPM": (9.45, 3.92), "FF3": (10.92, 4.60), "FF5": (10.25, 3.96)}.items():
    r = nw(bt["net"], MODELS[mname]); chk(f"{mname} alpha full (%)", ba, 1200 * r["b"]["const"]); chk(f"{mname} alpha t", bt_, r["t"]["const"])
r = nw(bt["net"], MODELS["FF3"]); chk("HML beta FF3 full", -0.32, r["b"]["HML"]); chk("HML t FF3", -2.44, r["t"]["HML"])
r = nw(bt["net"], MODELS["FF5"]); chk("HML beta FF5 full", -0.46, r["b"]["HML"]); chk("HML t FF5", -3.16, r["t"]["HML"])
for p, (ba, bt_, bb) in {"last18": (-2.60, -0.19, 0.55), "last12": (-5.19, -0.26, 0.95)}.items():
    r = nw(S(bt["net"], p), MODELS["CAPM"]); chk(f"CAPM alpha {p} (%)", ba, 1200 * r["b"]["const"]); chk(f"CAPM t {p}", bt_, r["t"]["const"])
    chk(f"CAPM beta {p}", bb, r["b"]["Mkt-RF"])

# costs and break-even (own formula: alpha(c) = alpha_gross - c * 12 * intercept(TO on factors))
for c_bp, (ba, bt_, bs) in {0: (2.99, 1.89, 0.54), 5: (2.36, 1.49, 0.51), 25: (-0.14, -0.09, 0.37)}.items():
    y = bt["gross"] - c_bp / 1e4 * bt["to"]; r = nw(y, X6)
    chk(f"FF5+UMD alpha at {c_bp}bp (%)", ba, 1200 * r["b"]["const"]); chk(f"t at {c_bp}bp", bt_, r["t"]["const"]); chk(f"Sharpe at {c_bp}bp", bs, ann(y)[2])
for p, (b_a, b_m) in {"full": (23.9, 78), "post2010": (24.5, 63)}.items():
    g, to = S(bt["gross"], p), S(bt["to"], p)
    a_g = 12 * nw(g, X6)["b"]["const"]; a_to = 12 * nw(to, X6)["b"]["const"]
    chk(f"break-even bp alpha {p}", b_a, 1e4 * a_g / a_to); chk(f"break-even bp mean {p}", b_m, 1e4 * g.mean() / to.mean())

# crash
wm = bt["net"].idxmin(); chk("worst month net (%)", -38.75, 100 * bt["net"].min(), note=f"month {wm:%Y-%m}")
wlong = Wh.loc[wm]; print("  2009-04 short leg:", list(wlong[wlong < 0].index), " long leg:", list(wlong[wlong > 0].index))
chk("2009-04 short leg return (%)", 39.40, 100 * (R.loc[wm, wlong[wlong < 0].index].mean()))
chk("2009-04 UMD (%)", -34.36, 100 * F5.loc[wm, "UMD"])
w = (1 + bt["net"]).cumprod(); dd = w / w.cummax() - 1
tr = dd.idxmin(); pk = w.loc[:tr].idxmax(); rec = dd.loc[tr:][dd.loc[tr:] >= 0].index.min()
print(f"  max DD peak {pk:%Y-%m} trough {tr:%Y-%m} recovery {rec:%Y-%m}  (builder 2008-06, 2012-01, 2020-04)")
rows.append({"claim": "max DD dates peak/trough/recovery", "builder": "2008-06/2012-01/2020-04",
             "mine": np.nan, "verdict": "confirmed" if (f"{pk:%Y-%m}", f"{tr:%Y-%m}", f"{rec:%Y-%m}") == ("2008-06", "2012-01", "2020-04") else "DISCREPANCY",
             "note": f"{pk:%Y-%m}/{tr:%Y-%m}/{rec:%Y-%m}"})
chk("Mar-May 2009 compounded (%)", -42.88, 100 * ((1 + bt.loc["2009-03-31":"2009-05-31", "net"]).prod() - 1))
chk("rank of 2026-07 among worst months", 6, int((bt["net"] < bt.loc["2026-07-31", "net"]).sum() + 1), tol=0)
# Daniel-Moskowitz, own construction
mkt = F5["Mkt-RF"] + F5["RF"]
bear = (np.log1p(mkt).rolling(24).sum() < 0).astype(float).where(np.log1p(mkt).rolling(24).sum().notna()).shift(1)
d = pd.concat([bt["net"].rename("y"), F5["Mkt-RF"].rename("M"), bear.rename("B")], axis=1).dropna()
d["U"] = (d.M > 0).astype(float)
r = nw(d.y, pd.DataFrame({"B": d.B, "M": d.M, "BxM": d.B * d.M, "BxUxM": d.B * d.U * d.M}))
chk("DM BxM coef", -0.53, r["b"]["BxM"]); chk("DM BxM t", -2.94, r["t"]["BxM"]); chk("DM BxUxM coef", -0.02, r["b"]["BxUxM"])
chk("bear & up-market mean monthly (%)", -2.85, 100 * d.loc[(d.B == 1) & (d.U == 1), "y"].mean(), note=f"n={((d.B == 1) & (d.U == 1)).sum()}")

# ================================================================== 2. robustness (holdout alpha negative in all 9?)
VAR = {"primary": dict(), "1-0": dict(L=1, Skip=0), "6-1": dict(L=6, Skip=1), "12-1": dict(L=12, Skip=1), "12-0": dict(L=12, Skip=0),
       "n5": dict(n=5), "n10": dict(n=10), "capw": dict(capdf=cap), "kf": dict(Rdf=R_kf)}
BUILDER_ROB = {"1-0": (3.29, 1.65, 0.25), "6-1": (-2.70, -1.59, 0.18), "12-1": (1.87, 1.30, 0.48), "12-0": (2.88, 1.87, 0.51),
               "n5": (2.22, 1.04, 0.44), "n10": (0.35, 0.27, 0.40), "capw": (-4.50, -2.44, 0.22), "kf": (1.74, 1.10, 0.47)}
hold_alphas = {}
for k, kw in VAR.items():
    Rdf = kw.pop("Rdf", R)
    b_, _ = book(Rdf, **kw)
    rf = nw(b_["net"], X6); rh = nw(S(b_["net"], "holdout"), X6); hold_alphas[k] = (12 * rh["b"]["const"], rh["t"]["const"])
    if k in BUILDER_ROB:
        ba, bt_, bs = BUILDER_ROB[k]
        chk(f"robust {k} alpha full (%)", ba, 1200 * rf["b"]["const"]); chk(f"robust {k} t", bt_, rf["t"]["const"]); chk(f"robust {k} Sharpe", bs, ann(b_["net"])[2])
    if k == "1-0":
        chk("robust 1-0 turnover x/yr", 38.4, 12 * b_["to"].mean())
print("  holdout FF5+UMD alphas:", {k: (round(100 * a, 2), round(t, 2)) for k, (a, t) in hold_alphas.items()})
rows.append({"claim": "holdout FF5+UMD alpha negative in all 9 variants", "builder": "all negative; min -10.79 (t=-3.02) for 6-1",
             "mine": min(a for a, _ in hold_alphas.values()) * 100,
             "verdict": "confirmed" if all(a < 0 for a, _ in hold_alphas.values()) else "DISCREPANCY",
             "note": "; ".join(f"{k}:{100 * a:.2f}({t:.2f})" for k, (a, t) in hold_alphas.items())})
kmin = min(hold_alphas, key=lambda k: hold_alphas[k][0])
rows.append({"claim": "most negative holdout alpha is -10.79% (6-1)", "builder": -10.79, "mine": 100 * hold_alphas[kmin][0],
             "verdict": "confirmed" if kmin == "6-1" else "DISCREPANCY",
             "note": f"most negative alpha is {kmin} {100 * hold_alphas[kmin][0]:.2f}% (t={hold_alphas[kmin][1]:.2f}); 6-1 has the most negative t"})
# vintage claim: team file vs KF differ only in final month?
dif = (R - R_kf).abs().max(axis=1)
diff_months = dif[dif > 1e-6]
print(f"  months where team file and KF Aug-2026 vintage differ by > 1e-6: {len(diff_months)}; last 5: {list(diff_months.index[-5:].strftime('%Y-%m'))}; "
      f"max abs {dif.max():.5f}")
rows.append({"claim": "KF Aug-2026 vintage differs from team file only in the final month", "builder": "only 2026-07",
             "mine": len(diff_months), "verdict": "confirmed" if list(diff_months.index.strftime("%Y-%m")) == ["2026-07"] else "DISCREPANCY",
             "note": f"differing months (>1e-6): {len(diff_months)} from {diff_months.index[0]:%Y-%m}; max abs outside 2026-07 = "
                     f"{dif.drop(pd.Timestamp('2026-07-31')).max():.4f}; 2026-07 max abs {dif.loc['2026-07-31']:.4f} (minor wording issue)"})

# ================================================================== 3. carbon WACI and screens
covered = [c for c in R.columns if c in emis.index]; ci = emis.reindex(covered)
def waci(W, sign):
    w = (sign * W).clip(lower=0); wc = w[covered]
    return (wc * ci).sum(axis=1) / wc.sum(axis=1).replace(0, np.nan), wc.sum(axis=1) / w.sum(axis=1)
lw, lcov = waci(Wh, 1); sw, _ = waci(Wh, -1)
capf = cap.shift(0).reindex(Wh.index - pd.offsets.MonthEnd(1))[covered]; capf.index = Wh.index    # cap at formation month t
mkt_w = (capf * ci).sum(axis=1) / capf.sum(axis=1)
cw = tab("carbon_waci").set_index("period")
chk("long WACI X full", 0.179, lw.mean(), cw.loc["full_1970", "long_waci_X"]); chk("short WACI X full", 0.195, sw.mean(), cw.loc["full_1970", "short_waci_X"])
chk("market41 WACI full", 0.277, mkt_w.mean(), cw.loc["full_1970", "market41_waci"])
chk("share months long > market full (%)", 24.7, 100 * (lw > mkt_w).mean())
chk("long covered share full (%)", 84, 100 * lcov.mean(), tol=0.5)
chk("long WACI X post2010", 0.193, S(lw, "post2010").mean()); chk("market WACI post2010", 0.192, S(mkt_w, "post2010").mean())
chk("long/market holdout ratio", 1.08, S(lw, "holdout").mean() / S(mkt_w, "holdout").mean())
top8 = list(emis.sort_values(ascending=False).index[:8]); top5 = top8[:5]
print("  top5:", top5, " top8:", top8)
brown5 = ["Util", "Ships", "Aero", "Steel", "BldMt"]
chk("share months >=1 Brown-5 in long leg (%)", 60.5, 100 * (Wh[brown5] > 0).any(axis=1).mean())
screens = {"A8X": ([c for c in covered if c not in top8], None), "B8X": ([c for c in covered if c not in top8],) * 2,
           "A5X": ([c for c in covered if c not in top5], None), "A0X": (covered, None), "B0X": (covered, covered),
           "A8M": ([c for c in R.columns if c not in top8], None), "B8M": ([c for c in R.columns if c not in top8],) * 2}
cs = tab("carbon_screens").set_index("book"); scr_bt = {}
for k, (lu, su) in screens.items():
    b_, W_ = book(R, long_u=lu, short_u=su); scr_bt[k] = b_
    lw_s, _ = waci(W_, 1); d = boot_dsr(b_["net"], bt["net"])
    key = [i for i in cs.index if i.startswith(k + "_")][0]
    print(f"  screen {k}: Sharpe {ann(b_['net'])[2]:.3f} (csv {cs.loc[key, 'sharpe_full_1970']:.3f}); dSR {d[0]:+.3f} CI [{d[1]:+.3f},{d[2]:+.3f}] "
          f"p_boot(mine, seed 777) {d[3]:.3f} (csv {cs.loc[key, 'p_d_sharpe_boot']:.3f}); long WACI {lw_s.mean():.3f} ({100 * (lw_s.mean() / lw.mean() - 1):.0f}%); "
          f"post2010 Sharpe {ann(S(b_['net'], 'post2010'))[2]:.3f}")
    if k == "A8X":
        chk("A8X long WACI", 0.046, lw_s.mean()); chk("A8X Sharpe full", 0.456, ann(b_["net"])[2]); chk("A8X dSharpe", -0.017, d[0])
        chk("A8X p boot (own seed, ~)", 0.68, d[3], tol=0.03)
        rr = nw(b_["net"] - bt["net"], X6); chk("A8X alpha diff (%)", -0.15, 1200 * rr["b"]["const"]); chk("A8X alpha diff t", -0.20, rr["t"]["const"])
    if k == "B8X":
        chk("B8X Sharpe full", 0.481, ann(b_["net"])[2]); chk("B8X Sharpe post2010", 0.32, ann(S(b_["net"], "post2010"))[2])
        rr = nw(b_["net"], X6); chk("B8X alpha full (%)", 2.10, 1200 * rr["b"]["const"]); chk("B8X alpha t", 1.68, rr["t"]["const"])
    if k == "A5X":
        rows.append({"claim": "A5X long WACI cut (%)", "builder": "67-74% range (A5X/A8X)", "mine": 100 * (lw_s.mean() / lw.mean() - 1), "verdict": "info"})
print("  screens: all |dSharpe| (csv):", cs["d_sharpe_vs_primary"].abs().max(), " min p (csv):", cs["p_d_sharpe_boot"].min())
print("  post-2010 screen Sharpe minus primary (csv):", (cs["sharpe_post2010"] - cs.loc["primary", "sharpe_post2010"]).round(3).to_dict())

# ================================================================== 4. Q4 link to green-minus-brown
green, brown = C.legs_by_emissions(5)
assert green == ["Fun", "RlEst", "Drugs", "Telcm", "Fin"] and brown == brown5, (green, brown)
GB = (T["industries"][green].mean(axis=1) - T["industries"][brown].mean(axis=1)).rename("GB")
INDMOM = bt["gross"].rename("INDMOM")
F3i = F3[["Mkt-RF", "SMB", "HML"]].join(INDMOM).join(F5["UMD"])
y = S(GB, "full"); r = nw(y, F3i.loc[y.index, ["Mkt-RF", "SMB", "HML", "INDMOM"]])
chk("Q4 PRIMARY INDMOM loading", -0.062, r["b"]["INDMOM"]); chk("Q4 PRIMARY t", -1.94, r["t"]["INDMOM"]); chk("Q4 PRIMARY p", 0.053, r["p"]["INDMOM"])
r0 = nw(y, F3i.loc[y.index, ["Mkt-RF", "SMB", "HML"]])
chk("GB HML FF3 full", -0.233, r0["b"]["HML"]); chk("GB HML t FF3 full", -4.63, r0["t"]["HML"]); chk("GB HML FF3+INDMOM full", -0.253, r["b"]["HML"])
yp = S(GB, "post2010")
chk("GB HML FF3 post2010", -0.298, nw(yp, F3i.loc[yp.index, ["Mkt-RF", "SMB", "HML"]])["b"]["HML"])
chk("GB HML FF3+INDMOM post2010", -0.306, nw(yp, F3i.loc[yp.index, ["Mkt-RF", "SMB", "HML", "INDMOM"]])["b"]["HML"])
chk("GB HML FF3+UMD post2010", -0.256, nw(yp, F3i.loc[yp.index, ["Mkt-RF", "SMB", "HML", "UMD"]])["b"]["HML"])
chk("corr(GB, INDMOM) full", -0.068, pd.concat([y, INDMOM], axis=1).dropna().corr().iloc[0, 1])
gs = pd.concat([GB.rename("y"), (np.expm1(np.log1p(GB).rolling(11).sum().shift(1))).shift(1).rename("s")], axis=1).loc["1970-01-31":"2026-07-31"].dropna()
rt = nw(gs.y, gs[["s"]]); chk("GB tsmom slope", 0.0069, rt["b"]["s"]); chk("GB tsmom t", 0.60, rt["t"]["s"])
# team traded strategies from the orchestrator's independent replication
from team_pipeline import run_pipeline
tp = run_pipeline(bootstrap_reps=0, placebo_reps=0, macro_states=False, paired=False, extras=False)
ct = tp["comparison_table"].set_index("strategy") if "comparison_table" in tp else None
for h, (h0, t0, h1, t1, bi, ti, pct) in {3: (-0.051, -2.34, -0.040, -2.00, 0.038, 2.12, 22), 6: (-0.061, -2.36, -0.046, -2.12, 0.054, 2.59, 25)}.items():
    sname = f"Original | Short Brown hold {h}m"; s_ = tp["strategies"][sname]["net_return"]
    if h == 3:
        a, b_ = S(s_, "post2010"), s_.loc["2010-01-31":"2026-07-31"]
        print(f"  team replica check {sname}: ann ret {12 * a.mean():.6f} (team 0.000696), vol {np.sqrt(12) * a.std(ddof=1):.5f} (team 0.03255)")
    ys = S(s_, "post2010")
    ra = nw(ys, F3i.loc[ys.index, ["Mkt-RF", "SMB", "HML"]]); rb = nw(ys, F3i.loc[ys.index, ["Mkt-RF", "SMB", "HML", "INDMOM"]])
    chk(f"SB h{h} HML FF3", h0, ra["b"]["HML"]); chk(f"SB h{h} HML t FF3", t0, ra["t"]["HML"])
    chk(f"SB h{h} HML FF3+INDMOM", h1, rb["b"]["HML"]); chk(f"SB h{h} HML t +INDMOM", t1, rb["t"]["HML"])
    chk(f"SB h{h} INDMOM loading", bi, rb["b"]["INDMOM"]); chk(f"SB h{h} INDMOM t", ti, rb["t"]["INDMOM"])
    chk(f"SB h{h} % HML absorbed", pct, 100 * (1 - rb["b"]["HML"] / ra["b"]["HML"]), tol=1.0)
    chk(f"SB h{h} corr INDMOM post2010", 0.21 if h == 3 else 0.22, pd.concat([ys, INDMOM], axis=1).dropna().corr().iloc[0, 1], tol=0.01)
    hh = S(s_, "holdout"); print(f"  SB h{h} holdout corr with INDMOM {pd.concat([hh, INDMOM], axis=1).dropna().corr().iloc[0, 1]:.3f}; "
                                 f"post2010 zero-return months {int((ys == 0).sum())}/{len(ys)}")

# ================================================================== 5. realized IC
nxt = R.shift(-1); ics = []
for t in Wh.index - pd.offsets.MonthEnd(1):
    win = R.loc[:t].iloc[-12:-1]; s = (1 + win).prod(min_count=11) - 1; s[win.isna().any()] = np.nan
    m = s.notna() & nxt.loc[t].notna()
    ics.append(stats.spearmanr(s[m], nxt.loc[t][m])[0])
ics = pd.Series(ics, index=Wh.index)
chk("rank IC full", 0.054, ics.mean()); chk("rank IC t full", 4.85, nw(ics)["t"]["const"]); chk("rank IC holdout", 0.030, S(ics, "holdout").mean())
chk("rank IC last18", -0.005, S(ics, "last18").mean())

# ================================================================== 6. ledger and multiple testing
led = tab("tests_ledger"); mt = tab("multiple_testing")
print(f"  ledger rows {len(led)}; primaries {(led.primary_or_exploratory == 'primary').sum()}; duplicated ids {led.test_id.duplicated().sum()}; "
      f"NaN p {led.p_value_two_sided.isna().sum()}")
chk("ledger rows", 335, len(led), tol=0); chk("ledger primaries", 4, (led.primary_or_exploratory == "primary").sum(), tol=0)
def holm_own(p):
    o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for k, j in enumerate(o):
        run = max(run, (m - k) * p[j]); adj[j] = min(1, run)
    return adj
def bh_own(p):
    o = np.argsort(p); m = len(p); adj = np.empty(m); run = 1.0
    for k in range(m - 1, -1, -1):
        j = o[k]; run = min(run, p[j] * m / (k + 1)); adj[j] = run
    return adj
pri = mt[mt.primary_or_exploratory == "primary"]; exp_ = mt[mt.primary_or_exploratory == "exploratory"]
print("  primaries:\n", pri.to_string())
print("  max |Holm own - csv|:", np.abs(holm_own(pri.p_value_two_sided.values) - pri.p_holm_within_primary.values).max(),
      " max |BH own - csv|:", np.abs(bh_own(exp_.p_value_two_sided.values) - exp_.p_bh_within_exploratory.values).max())
chk("n exploratory BH < 0.05", 24, int((exp_.p_bh_within_exploratory < 0.05).sum()), tol=0)
optkey = "M5-Q3-optalpha-X_unc-full_1970"
chk("BH p of X_unc full alpha", 0.034, float(mt.set_index("test_id").loc[optkey, "p_bh_within_exploratory"]))
# p-values in the ledger vs my own recomputation for the 4 primaries
lp = led.set_index("test_id")
chk("ledger P1 p == own", round(r1["p"]["const"], 4), lp.loc["M5-P1", "p_value_two_sided"], tol=5e-4)
chk("ledger P2 p == own", round(r2["p"]["const"], 4), lp.loc["M5-P2", "p_value_two_sided"], tol=5e-4)
chk("ledger Q4 p == own", round(r["p"]["INDMOM"], 4), lp.loc["M5-Q4-PRIMARY", "p_value_two_sided"], tol=5e-4)
# ledger completeness: FINDINGS cites these t-stats; are they logged?
cited = {"gross FF5+UMD alpha (0 bp)": led.test_id.str.contains("cost0"), "DM bear-state beta BxM": led.note.str.contains("BxM") | led.statistic_name.str.contains("BxM$"),
         "Q3 optimizer X_unc alpha": led.test_id.eq("M5-Q3-optalpha-X_unc-full_1970"), "optimizer vs primary": led.test_id.eq("M5-Q3-opt-vs-primary-dIR")}
for k, msk in cited.items():
    print(f"  ledger contains [{k}]: {bool(msk.any())}")
rows.append({"claim": "ledger logs every inferential statistic cited in FINDINGS", "builder": "335 rows", "mine": np.nan,
             "verdict": "DISCREPANCY" if not all(bool(m.any()) for m in cited.values()) else "confirmed",
             "note": "; ".join(f"{k}: {'logged' if bool(m.any()) else 'NOT logged'}" for k, m in cited.items())})

# omissions / wording checks against the CSVs
opp = tab("optimizer_periods").set_index(["key", "period"]); mtx = mt.set_index("test_id")
r20 = opp.loc[("X_unc", "2020s_to_2026_07")]
rows.append({"claim": "optimizer X_unc alpha 'not significant in any decade'", "builder": "largest t=1.97", "mine": r20.p_alpha,
             "verdict": "DISCREPANCY" if r20.p_alpha < 0.05 else "confirmed",
             "note": f"2020-2026 t={r20.t_alpha:.3f}, nominal p={r20.p_alpha:.4f} (<0.05); BH p={mtx.loc['M5-Q3-optalpha-X_unc-2020s_to_2026_07', 'p_bh_within_exploratory']:.3f}"})
rp = opp.loc[("X_unc", "post2010")]
rows.append({"claim": "OMITTED: optimizer X_unc post-2010 FF5+UMD alpha", "builder": "not reported", "mine": 100 * rp.alpha_ff5umd,
             "verdict": "omission", "note": f"{100 * rp.alpha_ff5umd:.2f}%/yr t={rp.t_alpha:.2f} p={rp.p_alpha:.3f}; BH p={mtx.loc['M5-Q3-optalpha-X_unc-post2010', 'p_bh_within_exploratory']:.3f}; IR post-2010 {rp.ir:.3f}"})
alc = al_net.loc[("covid", "FF5+UMD")]
rows.append({"claim": "OMITTED from BH-survivor list: primary FF5+UMD alpha in COVID 2020-21", "builder": "not reported", "mine": 100 * alc.alpha_ann,
             "verdict": "omission", "note": f"{100 * alc.alpha_ann:.2f}%/yr t={alc.t_alpha:.2f} (n=24); BH p={mtx.loc['M5-Q1-alpha-FF5+UMD-covid', 'p_bh_within_exploratory']:.3f}; also 6-1 holdout t=-3.02 BH p={mtx.loc['M5-Q2-window_6-1-holdout', 'p_bh_within_exploratory']:.3f}"})
gr = tab("gb_regressions").set_index(["y", "period", "spec"])
for h in (3, 6):
    g1 = gr.loc[(f"short_brown_h{h}", "post2010", "FF3+UMD+INDMOM")]
    rows.append({"claim": f"SB h{h}: INDMOM loading robust to UMD?", "builder": "interpreted as momentum tilt", "mine": g1.t_INDMOM,
                 "verdict": "overreach-check",
                 "note": f"with UMD also in: INDMOM t={g1.t_INDMOM:.2f}; BH p of FF3+INDMOM loading={mtx.loc[f'M5-Q4-short_brown_h{h}-FF3+INDMOM-post2010', 'p_bh_within_exploratory']:.3f}"})
pd.DataFrame(rows).to_csv(OUT / "verify_core_results.csv", index=False)
print("\nDISCREPANCIES:"); print(pd.DataFrame(rows).query("verdict == 'DISCREPANCY'")[["claim", "builder", "mine", "note"]].to_string())
