"""Round 2 component comparison: chatgpt_code_v2.py runs (run_v2_real.py outputs) against the reference
(modules/M8_frozen_pre2010/run.py, rebuilt in memory and first checked against the published tables).

  r2_test_nonzero      vs the primary reference (1993-01..2009-12 -> 1994-03..2009-12)
  r2_test_calendar     vs the primary reference, and vs round-1 final_B (v1 + switch B) which it should equal
  r2_seen_nonzero      vs the reference dry run (2010-01..2022-07, dryrun/M8dry_*)
Writes out/r2_compare_components.csv, out/r2_compare_attribution.csv, out/r2_compare_summary.json.
"""
import json
import sys

sys.dont_write_bytecode = True
CHECKS = "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks"
RESEARCH = "/home/hashim/projects/GA/project/research"
sys.path.insert(0, CHECKS)
sys.path.insert(0, f"{RESEARCH}/lib")
sys.path.insert(0, f"{RESEARCH}/modules/M8_frozen_pre2010")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import chatgpt_code_v2 as g2  # noqa: E402
import run as ref  # noqa: E402  (import only; main() is never called)
from run_v2_real import PATHS  # noqa: E402
from team_pipeline import TEAM_BROWN, _magnitude, resolve_costs  # noqa: E402

OUT = f"{CHECKS}/out"
TAB = f"{RESEARCH}/outputs/tables"
DRY = f"{RESEARCH}/modules/M8_frozen_pre2010/dryrun"
res = {}

# ------------------------------------------------------------------ reference, rebuilt and checked against the published tables
T, ff5, env, overall, vix, wti, gs10 = ref.load_inputs()
ff3 = T["ff3"]
rates = resolve_costs(ref.HEDGE_COLS)
bf = ref.build_bond(gs10, ff5["RF"])
rfac = ff5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].copy()
rfac["BOND"], rfac["WTI"], rfac["dVIX"], rfac["dlogEMV"] = bf["BOND"], np.log(wti).diff(), vix.diff(), np.log(overall).diff()
rsig = ref.share_signal(env, overall)
rmodel = ref.brown_model(TEAM_BROWN, T["industries"], ff3)
grid = pd.date_range(rmodel["epsilon"].index.min(), max(rmodel["epsilon"].index.max(), rsig.index.max() + pd.offsets.MonthEnd(1)), freq="ME")
_, rhold = ref.decision_hold(rsig["cross"], grid)
rT = ref.run_strategy(rhold, rmodel, ff3, rates)
rA = ref.run_strategy(pd.Series(True, index=rmodel["epsilon"].index), rmodel, ff3, rates)
_, rmag = _magnitude(rmodel["epsilon"], ref.VOL_TGT, ref.VOL_WIN, ref.CAP)


def ref_bundle(kind):
    if kind == "primary":
        win, pre = ("1994-03-31", "2009-12-31"), f"{TAB}/M8_"
    else:
        win, pre = ("2010-01-31", "2022-07-31"), f"{DRY}/M8dry_"
    att = ref.attribution(rT["net_return"], rA["net_return"], rT["position"], rA["position"], rfac, win)
    panel = pd.read_csv(pre + "monthly_panel.csv", index_col=0, parse_dates=True)
    pub_att = pd.read_csv(pre + "attribution.csv")
    pub_att = pub_att[pub_att.signal.str.startswith("Frozen")].set_index("term")
    w = pd.date_range(*win, freq="ME")
    selfcheck = {
        "net_primary": float((rT["net_return"].reindex(w) - panel["net_primary"].reindex(w)).abs().max()),
        "net_always": float((rA["net_return"].reindex(w) - panel["net_always"].reindex(w)).abs().max()),
        "D_primary": float((att["D"] - panel["D_primary"].reindex(w)).abs().max()),
        "coef": float((att["table"]["coef"] - pub_att["coef"]).abs().max()),
        "t_nw6": float((att["table"]["t_nw6"] - pub_att["t_nw6"]).abs().max()),
    }
    assert max(selfcheck.values()) < 1e-12, (kind, selfcheck)
    pb = pd.read_csv(pre + "passbar.csv")
    pb = pb[pb.signal.str.startswith("Frozen")].set_index("component")
    drop = pd.read_csv(pre + "drop_one.csv")
    drop = drop[drop.signal.str.startswith("Frozen")].set_index("dropped")
    eps = pd.read_csv(pre + "episodes.csv")
    eps = eps[eps.signal.str.startswith("Frozen")]
    terms = pd.read_csv(pre + "decomposition_terms.csv")
    terms = terms[terms.signal.str.startswith("Frozen")].set_index("term")["ann_contribution"] / 12
    shuf = pd.read_csv(pre + "shuffle_draws.csv")["primary_alpha_ann"].to_numpy() / 12
    pf = {"(i)": bool(att["alpha_m"] > 0 and att["t6"] >= 2),
          "(ii)": bool(pb.loc["(ii) calendar shuffle", "pass"]),
          "(iii)": bool(pb.loc["(iii) independent episodes", "pass"]),
          "(iv)": bool(pb.loc["(iv) drop-one Brown industry", "pass"])}
    pf["overall"] = all(pf.values())
    return dict(win=win, att=att, selfcheck=selfcheck, shuffle_p=float(pb.loc["(ii) calendar shuffle", "p_value"]),
                drop=drop, eps=eps, terms=terms, shuf=shuf, pf=pf)


REF = {"primary": ref_bundle("primary"), "dry": ref_bundle("dry")}
res["reference_rebuild_vs_published_maxdiff"] = {k: v["selfcheck"] for k, v in REF.items()}

cfg = g2.Config()
env1 = g2.load_fred_monthly(PATHS["EMVENRGYENVREG"], "EMVENRGYENVREG")
all1 = g2.load_fred_monthly(PATHS["EMVOVERALLEMV"], "EMVOVERALLEMV")
rows, att_rows = [], []
rcross = set(rsig.index[rsig["cross"]])
name = {"alpha": "const", "I*Mkt-RF": "I x Mkt-RF", "I*HML": "I x HML", "I*BOND": "I x BOND", "I*dVIX": "I x dVIX"}


def num(x):
    return isinstance(x, (int, float, np.floating, np.integer)) and not isinstance(x, bool)


for tag, zb, kind in [("r2_test_nonzero", "nonzero", "primary"), ("r2_test_calendar", "calendar", "primary"),
                      ("r2_seen_nonzero", "nonzero", "dry")]:
    R = REF[kind]
    ratt = R["att"]

    def add(comp, cg, rv, note=""):
        rows.append({"run": tag, "component": comp, "chatgpt_v2": cg, "reference": rv,
                     "diff": (cg - rv) if num(cg) and num(rv) else "", "note": note})

    sig = g2._driver_signal(g2.attention_signal(env1, all1, z_burn_in=zb), cfg)
    cr = g2.crossings(sig["extreme"], cfg)
    hold = pd.read_csv(f"{OUT}/{tag}_hold.csv", index_col=0, parse_dates=True)["hold"].astype(bool)
    books = pd.read_csv(f"{OUT}/{tag}_books.csv", index_col=0, parse_dates=True)
    meta = pd.read_csv(f"{OUT}/{tag}_attribution_meta.csv", index_col=0)["value"]
    coef = pd.read_csv(f"{OUT}/{tag}_attribution.csv", index_col=0)
    shuf = pd.read_csv(f"{OUT}/{tag}_shuffle.csv", index_col=0)["value"]
    loo = pd.read_csv(f"{OUT}/{tag}_leave_one_out.csv", index_col=0).set_index("dropped")
    eps = pd.read_csv(f"{OUT}/{tag}_episodes.csv", index_col=0)
    D = pd.read_csv(f"{OUT}/{tag}_D.csv", index_col=0, parse_dates=True)["D"]
    null = pd.read_csv(f"{OUT}/{tag}_null_alphas.csv")["null_alphas"].to_numpy()
    X = pd.read_csv(f"{OUT}/{tag}_X.csv", index_col=0, parse_dates=True)
    pf = pd.read_csv(f"{OUT}/{tag}_pass_fail.csv", index_col=0)
    dec = pd.read_csv(f"{OUT}/{tag}_decomposition.csv", index_col=0)["value"]
    wv = D.index
    wref = pd.date_range(*R["win"], freq="ME")

    # signal
    add("first data month with z", sig["z"].first_valid_index().strftime("%Y-%m"), rsig["z"].first_valid_index().strftime("%Y-%m"))
    zc = sig["z"].dropna().index.intersection(rsig["z"].dropna().index)
    add("max |z diff|, common months", float((sig["z"] - rsig["z"]).loc[zc].abs().max()), 0.0, f"{len(zc)} common months")
    add("first data month with threshold", sig["thr"].first_valid_index().strftime("%Y-%m"), rsig["threshold"].first_valid_index().strftime("%Y-%m"))
    tc = sig["thr"].dropna().index.intersection(rsig["threshold"].dropna().index)
    add("max |threshold diff|, common months 1985-2026", float((sig["thr"] - rsig["threshold"]).loc[tc].abs().max()), 0.0)
    ccg = set(cr.index[cr.to_numpy(bool)])
    only_g, only_r = sorted(ccg - rcross), sorted(rcross - ccg)
    add("crossings over 1985-01..2026-08 (count)", len(ccg), len(rcross),
        f"only v2: {[t.strftime('%Y-%m') for t in only_g]}; only reference: {[t.strftime('%Y-%m') for t in only_r]}")
    dec_m = pd.date_range(pd.Timestamp(R["win"][0]) - pd.offsets.MonthEnd(1), pd.Timestamp(R["win"][1]) - pd.offsets.MonthEnd(1), freq="ME")
    hdiff = hold.reindex(dec_m).astype(bool) != rhold.reindex(dec_m).astype(bool)
    add("hold months differing, decision months of the window", int(hdiff.sum()), 0,
        ", ".join(t.strftime("%Y-%m") for t in dec_m[hdiff.to_numpy()][:12]))
    # window and leg
    add("window", f"{meta['window start']} to {meta['window end']}", f"{wref[0]:%Y-%m} to {wref[-1]:%Y-%m}")
    add("n", int(meta["n"]), int(ratt["n"]))
    bcols = [f"b_{k}" for k in cfg.hedge_factors]
    add("max |b_t diff| (hedge betas), window", float(np.abs(books[bcols].reindex(wref).to_numpy() - rmodel["betas"].reindex(wref).to_numpy()).max()), 0.0)
    add("max |m_t diff| (vol-target size), window", float((books["m"].reindex(wref) - rmag.reindex(wref)).abs().max()), 0.0)
    add("max |net R^T diff|, window", float((books["net_T"].reindex(wv) - rT["net_return"].reindex(wv)).abs().max()), 0.0)
    add("max |net R^AO diff|, window", float((books["net_AO"].reindex(wv) - rA["net_return"].reindex(wv)).abs().max()), 0.0)
    add("pi", float(meta["pi"]), float(ratt["pi"]))
    add("max |D diff|, window", float((D - ratt["D"].reindex(wv)).abs().max()), 0.0)
    add("months in position (I=1)", int(X["I*Mkt-RF"].ne(0).sum()), int(ratt["I"].sum()))
    common = X.index.intersection(ratt["X"].index)
    add("max |regressor diff| (10 unconditional factors)",
        float(max((X.loc[common, c] - ratt["X"].loc[common, c]).abs().max() for c in ref.UNCOND)), 0.0)
    add("k", int(meta["k"]), int(ratt["k"]))
    # inference
    t6 = float(coef.loc["alpha", "t NW(6)"])
    p2 = float(coef.loc["alpha", "p NW(6)"])
    add("alpha, %/yr", 1200 * float(coef.loc["alpha", "coef"]), 1200 * float(ratt["alpha_m"]))
    add("alpha NW(6) t", t6, float(ratt["t6"]))
    add("alpha NW(12) t", float(coef.loc["alpha", "t NW(12)"]), float(ratt["t12"]))
    add("alpha two-sided p, t(n-k)", p2, float(ratt["p6"]))
    add("alpha one-sided upper p", p2 / 2 if t6 > 0 else 1 - p2 / 2, float(ratt["p6_upper"]))
    add("shuffle one-sided p", float(shuf["p (one-sided)"]), R["shuffle_p"])
    add("shuffle null median, %/yr", 1200 * float(np.median(null)), 1200 * float(np.median(R["shuf"])))
    if len(null) == len(R["shuf"]):
        add("max |null alpha diff| draw by draw (same seed)", float(np.abs(null - R["shuf"]).max()), 0.0)
    add("episodes", len(eps), len(R["eps"]), f"v2 lengths {list(eps['months'])}; reference {list(R['eps']['months'])}")
    for ind in TEAM_BROWN:
        add(f"drop {ind}: alpha %/yr", 1200 * float(loo.loc[ind, "alpha"]), 100 * float(R["drop"].loc[ind, "alpha_ann"]))
        add(f"drop {ind}: t", float(loo.loc[ind, "t NW(6)"]), float(R["drop"].loc[ind, "t_nw6"]))
    add("decomposition identity gap", float(dec["identity gap"]), float(ratt["resid_mean"]))
    for comp in ["(i)", "(ii)", "(iii)", "(iv)", "overall"]:
        add(f"pass/fail row {comp}", str(pf.loc[comp, "result"]), "PASS" if R["pf"][comp] else "FAIL",
            f"v2 value {pf.loc[comp, 'value']}; {pf.loc[comp, 'detail']}"[:200])
    for term in coef.index:
        rt = name.get(term, term)
        dkey = "alpha" if term == "alpha" else (f"gamma*mean({term})" if term.startswith("I*") else f"beta*mean({term})")
        att_rows.append({"run": tag, "term": term, "coef_v2": coef.loc[term, "coef"], "coef_ref": ratt["table"].loc[rt, "coef"],
                         "t6_v2": coef.loc[term, "t NW(6)"], "t6_ref": ratt["table"].loc[rt, "t_nw6"],
                         "t12_v2": coef.loc[term, "t NW(12)"], "t12_ref": ratt["table"].loc[rt, "t_nw12"],
                         "p6_v2": coef.loc[term, "p NW(6)"], "p6_ref": ratt["table"].loc[rt, "p_nw6_t(n-k)"],
                         "contrib_v2": dec[dkey], "contrib_ref": R["terms"]["alpha" if term == "alpha" else rt]})

# ------------------------------------------------------------------ calendar run vs round-1 v1 + switch B (should be identical)
cal = {}
for k in ["D", "X", "null_alphas"]:
    a = pd.read_csv(f"{OUT}/r2_test_calendar_{k}.csv", index_col=None if k == "null_alphas" else 0)
    b = pd.read_csv(f"{OUT}/final_B_{k}.csv", index_col=None if k == "null_alphas" else 0)
    cal[k] = float(np.abs(a.to_numpy(float) - b.to_numpy(float)).max()) if a.shape == b.shape else f"shape {a.shape} vs {b.shape}"
a = pd.read_csv(f"{OUT}/r2_test_calendar_attribution.csv", index_col=0)
b = pd.read_csv(f"{OUT}/final_B_attribution.csv", index_col=0)
cal["attribution"] = float((a - b).abs().max().max())
a = pd.read_csv(f"{OUT}/r2_test_calendar_leave_one_out.csv", index_col=0)
b = pd.read_csv(f"{OUT}/final_B_leave_one_out.csv", index_col=0)
cal["leave_one_out_alpha"] = float((a["alpha"] - b["alpha"]).abs().max())
res["calendar_run_vs_round1_final_B_maxdiff"] = cal

comp = pd.DataFrame(rows)
comp.to_csv(f"{OUT}/r2_compare_components.csv", index=False)
att = pd.DataFrame(att_rows)
for c in ("coef", "t6", "t12", "p6", "contrib"):
    att[f"{c}_absdiff"] = (att[f"{c}_v2"] - att[f"{c}_ref"]).abs()
att.to_csv(f"{OUT}/r2_compare_attribution.csv", index=False)
res["attribution_max_absdiff_by_run"] = att.groupby("run")[[c for c in att.columns if c.endswith("absdiff")]].max().to_dict("index")
num_rows = comp[comp["diff"] != ""].copy()
num_rows["absdiff"] = num_rows["diff"].astype(float).abs()
res["component_max_absdiff_by_run"] = num_rows.groupby("run")["absdiff"].max().to_dict()
open(f"{OUT}/r2_compare_summary.json", "w").write(json.dumps(res, indent=1, default=str))
pd.set_option("display.width", 250, "display.max_colwidth", 110, "display.max_rows", 400)
print(json.dumps(res, indent=1, default=str))
for tag in comp.run.unique():
    print(f"\n==== {tag}")
    print(comp[comp.run == tag].drop(columns="run").to_string(index=False))
