"""Component-by-component comparison: ChatGPT code (as delivered and under harmonization switches A, B, AB)
against the verified reference implementation (modules/M8_frozen_pre2010/run.py and its published tables).

Reads out/final_{asis,A,B,AB}_*.csv (written by run_chatgpt_real.py and align.py); recomputes intermediate
series (signal, hedge, sizing, books) by calling ChatGPT's own functions. The reference is rebuilt in memory
from run.py's functions (no file is written by run.py; bytecode writing is disabled) and checked against the
published outputs/tables/M8_*.csv first.

Writes out/compare_components.csv, out/compare_attribution.csv, out/compare_crossings.csv, out/compare_summary.json.
"""
import json
import sys

import numpy as np
import pandas as pd

import align
from glue import OUT, RESEARCH, g, real_inputs

sys.path.insert(0, str(RESEARCH / "modules" / "M8_frozen_pre2010"))
import run as ref  # noqa: E402  (import only; main() is never called)
from common import load_fred  # noqa: E402
from team_pipeline import TEAM_BROWN, resolve_costs, _magnitude  # noqa: E402

TAB = RESEARCH / "outputs" / "tables"
WIN = ("1994-03-31", "2009-12-31")
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
ratt = ref.attribution(rT["net_return"], rA["net_return"], rT["position"], rA["position"], rfac, WIN)
_, rmag = _magnitude(rmodel["epsilon"], ref.VOL_TGT, ref.VOL_WIN, ref.CAP)

panel = pd.read_csv(TAB / "M8_monthly_panel.csv", index_col=0, parse_dates=True)
pub_att = pd.read_csv(TAB / "M8_attribution.csv")
pub_att = pub_att[pub_att.signal.str.startswith("Frozen")].set_index("term")
w = pd.date_range(*WIN, freq="ME")
selfcheck = {
    "net_primary": float((rT["net_return"].reindex(w) - panel["net_primary"].reindex(w)).abs().max()),
    "net_always": float((rA["net_return"].reindex(w) - panel["net_always"].reindex(w)).abs().max()),
    "D_primary": float((ratt["D"] - panel["D_primary"].reindex(w)).abs().max()),
    "share_z": float((rsig["z"] - panel["share_z"].reindex(rsig.index)).abs().max()),
    "coef": float((ratt["table"]["coef"] - pub_att["coef"]).abs().max()),
    "t_nw6": float((ratt["table"]["t_nw6"] - pub_att["t_nw6"]).abs().max()),
}
res["reference_rebuild_vs_published_maxdiff"] = selfcheck
assert max(selfcheck.values()) < 1e-12, selfcheck

# ------------------------------------------------------------------ ChatGPT intermediate series under each variant
inputs = real_inputs()
ff49 = g.load_ff49(inputs["ff49"])
fac = g.load_factors(inputs["fac"])
emv_cat = g.load_fred_monthly(inputs["emv_cat"], "EMVENRGYENVREG")
emv_all = g.load_fred_monthly(inputs["emv_all"], "EMVOVERALLEMV")
index = g._month_range(fac.index.min(), min(fac.index.max(), ff49.index.max()))
cfg = g.Config()

pub = {  # published reference values (outputs/tables), used for every "reference" cell below
    "window": "1994-03 to 2009-12", "n": 190, "pi": ratt["pi"], "alpha_m": ratt["alpha_m"], "t6": ratt["t6"], "t12": ratt["t12"],
    "p6": ratt["p6"], "p6_upper": ratt["p6_upper"],
    "shuffle_p": 0.47790441911617676, "episodes": 10, "hold_months_in_window": int(ratt["I"].sum()),
}
pub_drop = pd.read_csv(TAB / "M8_drop_one.csv")
pub_drop = pub_drop[pub_drop.signal.str.startswith("Frozen")].set_index("dropped")
pub_shuf = pd.read_csv(TAB / "M8_shuffle_draws.csv")["primary_alpha_ann"].to_numpy() / 12
pub_eps = pd.read_csv(TAB / "M8_episodes.csv", parse_dates=["first_decision_month", "last_decision_month"])
pub_eps = pub_eps[pub_eps.signal.str.startswith("Frozen")]
pub_terms = pd.read_csv(TAB / "M8_decomposition_terms.csv")
pub_terms = pub_terms[pub_terms.signal.str.startswith("Frozen")].set_index("term")["ann_contribution"] / 12

rows, att_rows, cross_rows = [], [], []
rcross = set(rsig.index[rsig["cross"]])
for v in ["asis", "A", "B", "AB"]:
    align.apply("" if v == "asis" else v)
    tag = f"final_{v}"
    sig = g.attention_signal(emv_cat, emv_all, cfg)
    cr = g.crossings(sig["extreme"], cfg)
    hold = g.hold_positions(cr, index, cfg)
    leg = g.leg_pipeline(ff49, fac, cfg.brown, hold, index, cfg)
    meta = pd.read_csv(OUT / f"{tag}_attribution_meta.csv", index_col=0)["value"]
    coef = pd.read_csv(OUT / f"{tag}_attribution.csv", index_col=0)
    shuf = pd.read_csv(OUT / f"{tag}_shuffle.csv", index_col=0)["value"]
    loo = pd.read_csv(OUT / f"{tag}_leave_one_out.csv", index_col=0).set_index("dropped")
    eps = pd.read_csv(OUT / f"{tag}_episodes.csv", index_col=0, parse_dates=["position_from", "position_to"])
    D = pd.read_csv(OUT / f"{tag}_D.csv", index_col=0, parse_dates=True)["D"]
    null = pd.read_csv(OUT / f"{tag}_null_alphas.csv")["null_alphas"].to_numpy()
    X = pd.read_csv(OUT / f"{tag}_X.csv", index_col=0, parse_dates=True)
    wv = D.index

    def add(comp, cg, rv, note=""):
        rows.append({"variant": v, "component": comp, "chatgpt": cg, "reference": rv,
                     "diff": (cg - rv) if isinstance(cg, (int, float, np.floating, np.integer)) and isinstance(rv, (int, float, np.floating, np.integer)) else "", "note": note})

    # signal
    z_common = sig["z"].dropna().index.intersection(rsig["z"].dropna().index)
    add("first data month with z", sig["z"].first_valid_index().strftime("%Y-%m"), rsig["z"].first_valid_index().strftime("%Y-%m"))
    add("max |z diff|, common months", float((sig["z"] - rsig["z"]).loc[z_common].abs().max()), 0.0, f"{len(z_common)} common months")
    add("first data month with threshold", pd.Series(sig["thr"], index=sig.index).first_valid_index().strftime("%Y-%m"),
        rsig["threshold"].first_valid_index().strftime("%Y-%m"))
    thr_common = sig["thr"].dropna().index.intersection(rsig["threshold"].dropna().index)
    thr_common = thr_common[thr_common <= "2009-12-31"]
    add("max |threshold diff|, common months to 2009-12", float((sig["thr"] - rsig["threshold"]).loc[thr_common].abs().max()), 0.0)
    ccg = set(cr.index[cr.to_numpy(bool)])
    lo, hi = pd.Timestamp("1993-01-31"), pd.Timestamp("2009-10-31")
    only_g = sorted(t for t in ccg - rcross if lo <= t <= hi)
    only_r = sorted(t for t in rcross - ccg if lo <= t <= hi)
    add("crossings 1993-01..2009-10 (data months)", len([t for t in ccg if lo <= t <= hi]), len([t for t in rcross if lo <= t <= hi]),
        f"only ChatGPT: {[t.strftime('%Y-%m') for t in only_g]}; only reference: {[t.strftime('%Y-%m') for t in only_r]}")
    for t in only_g + only_r:
        cross_rows.append({"variant": v, "data_month": t.strftime("%Y-%m"), "in": "ChatGPT only" if t in ccg else "reference only",
                           "z_chatgpt": sig["z"].get(t), "thr_chatgpt": sig["thr"].get(t), "z_ref": rsig["z"].get(t), "thr_ref": rsig["threshold"].get(t)})
    dec_months = pd.date_range("1994-02-28", "2009-11-30", freq="ME")
    hdiff = (hold.reindex(dec_months).astype(bool) != rhold.reindex(dec_months).astype(bool))
    add("hold months differing, decision months 1994-02..2009-11", int(hdiff.sum()), 0,
        ", ".join(t.strftime("%Y-%m") for t in dec_months[hdiff.to_numpy()][:12]))
    # window and leg
    add("window", f"{meta['window start']} to {meta['window end']}", pub["window"])
    add("n", int(meta["n"]), pub["n"])
    wref = pd.date_range(*WIN, freq="ME")
    b_cg = leg["b"].reindex(wref)
    b_rf = rmodel["betas"].reindex(wref)
    add("max |b_t diff| (hedge betas), 1994-03..2009-12", float((b_cg - b_rf).abs().max().max()), 0.0)
    add("max |m_t diff| (vol-target size)", float((leg["m"].reindex(wref) - rmag.reindex(wref)).abs().max()), 0.0)
    add("max |net R^T diff|, common window months", float((leg["tr_T"]["net"].reindex(wv) - rT["net_return"].reindex(wv)).abs().max()), 0.0)
    add("max |net R^AO diff|, common window months", float((leg["tr_AO"]["net"].reindex(wv) - rA["net_return"].reindex(wv)).abs().max()), 0.0)
    add("pi", float(meta["pi"]), pub["pi"])
    add("max |D diff|, common window months", float((D - ratt["D"].reindex(wv)).abs().max()), 0.0)
    add("months in position (I=1)", int(X["I*Mkt-RF"].ne(0).sum()), pub["hold_months_in_window"])
    # regressors
    common = X.index.intersection(ratt["X"].index)
    fx = {"Mkt-RF": "Mkt-RF", "SMB": "SMB", "HML": "HML", "RMW": "RMW", "CMA": "CMA", "UMD": "UMD", "BOND": "BOND", "WTI": "WTI", "dVIX": "dVIX", "dlogEMV": "dlogEMV"}
    add("max |regressor diff| (10 unconditional factors), common months",
        float(max((X.loc[common, a] - ratt["X"].loc[common, b]).abs().max() for a, b in fx.items())), 0.0)
    # inference
    add("alpha, %/yr", 1200 * float(coef.loc["alpha", "coef"]), 1200 * pub["alpha_m"])
    add("alpha NW(6) t", float(coef.loc["alpha", "t NW(6)"]), pub["t6"])
    add("alpha NW(12) t", float(coef.loc["alpha", "t NW(12)"]), pub["t12"])
    add("alpha two-sided p, t(n-k)", float(coef.loc["alpha", "p NW(6)"]), pub["p6"])
    t6 = float(coef.loc["alpha", "t NW(6)"]); p2 = float(coef.loc["alpha", "p NW(6)"])
    add("alpha one-sided upper p", p2 / 2 if t6 > 0 else 1 - p2 / 2, pub["p6_upper"])
    add("R-squared", float(meta["R-squared"]), float("nan"), "reference does not report R2")
    add("shuffle one-sided p", float(shuf["p (one-sided)"]), pub["shuffle_p"])
    add("shuffle null median, %/yr", 1200 * float(np.median(null)), 1200 * float(np.median(pub_shuf)))
    if len(null) == len(pub_shuf):
        add("max |null alpha diff| draw by draw (same seed)", float(np.abs(null - pub_shuf).max()), 0.0)
    add("episodes", len(eps), pub["episodes"], "lengths " + str(list(eps["months"])))
    for ind in TEAM_BROWN:
        add(f"drop {ind}: alpha %/yr", 1200 * float(loo.loc[ind, "alpha"]), 100 * float(pub_drop.loc[ind, "alpha_ann"]))
        add(f"drop {ind}: t", float(loo.loc[ind, "t NW(6)"]), float(pub_drop.loc[ind, "t_nw6"]))
    add("(iv) same-sign count", int(loo["same_sign"].sum()), int((np.sign(pub_drop["alpha_ann"]) == np.sign(pub["alpha_m"])).sum()))
    # attribution table and decomposition, all terms
    dec = pd.read_csv(OUT / f"{tag}_decomposition.csv", index_col=0)["value"]
    add("decomposition identity gap", float(dec["identity gap"]), float(ratt["resid_mean"]))
    name = {"alpha": "const", "I*Mkt-RF": "I x Mkt-RF", "I*HML": "I x HML", "I*BOND": "I x BOND", "I*dVIX": "I x dVIX"}
    for term in coef.index:
        rt = name.get(term, term)
        dkey = "alpha" if term == "alpha" else (f"gamma*mean({term})" if term.startswith("I*") else f"beta*mean({term})")
        att_rows.append({"variant": v, "term": term, "coef_chatgpt": coef.loc[term, "coef"], "coef_ref": ratt["table"].loc[rt, "coef"],
                         "t6_chatgpt": coef.loc[term, "t NW(6)"], "t6_ref": ratt["table"].loc[rt, "t_nw6"],
                         "t12_chatgpt": coef.loc[term, "t NW(12)"], "t12_ref": ratt["table"].loc[rt, "t_nw12"],
                         "p6_chatgpt": coef.loc[term, "p NW(6)"], "p6_ref": ratt["table"].loc[rt, "p_nw6_t(n-k)"],
                         "contrib_ann_chatgpt": 12 * dec[dkey], "contrib_ann_ref": 12 * pub_terms["alpha" if term == "alpha" else rt]})
    res[f"{v}_first_signal"] = str(sig["extreme"].first_valid_index().date())

align.apply("")
comp = pd.DataFrame(rows)
comp.to_csv(OUT / "compare_components.csv", index=False)
att = pd.DataFrame(att_rows)
for c in ("coef", "t6", "t12", "p6", "contrib_ann"):
    att[f"{c}_absdiff"] = (att[f"{c}_chatgpt"] - att[f"{c}_ref"]).abs()
att.to_csv(OUT / "compare_attribution.csv", index=False)
pd.DataFrame(cross_rows).to_csv(OUT / "compare_crossings.csv", index=False)
res["attribution_max_absdiff_by_variant"] = att.groupby("variant")[[c for c in att.columns if c.endswith("absdiff")]].max().to_dict("index")
(OUT / "compare_summary.json").write_text(json.dumps(res, indent=1, default=str))
pd.set_option("display.width", 250, "display.max_colwidth", 120, "display.max_rows", 400)
print(json.dumps(res, indent=1, default=str))
for v in ["asis", "A", "B", "AB"]:
    print(f"\n==== variant {v}")
    print(comp[comp.variant == v].drop(columns="variant").to_string(index=False))
