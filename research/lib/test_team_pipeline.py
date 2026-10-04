"""Reproduction and API tests for team_pipeline.

Run:  cd /home/hashim/projects/GA/project/research && uv run pytest -q lib/test_team_pipeline.py
 or:  uv run python lib/test_team_pipeline.py
"""
from __future__ import annotations

import functools
import pathlib
import pickle
import sys
import time
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from common import load_team, load_ff5_mom, load_fred, load_cpu  # noqa: E402
from team_pipeline import (  # noqa: E402
    run_pipeline, team_legs, team_controls, rolling_factor_model, holm_bonferroni, TEAM_GREEN, TEAM_BROWN,
)

TEAM = pathlib.Path("/home/hashim/projects/GA/project/230GA-Final-Project")
COMMITTED = TEAM / "outputs" / "tables"
TEAM_REF_PKL = pathlib.Path("/home/hashim/projects/GA/project/research/scratch/team_reference.pkl")
TOL = 1e-9
DISCRETE = ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m", "Original | Short Brown hold 6m", "Pure | Short Brown hold 6m"]
CHEAP = dict(bootstrap_reps=0, extras=False, paired=False, macro_states=False)

# writeup.pdf Table 1: (net %, Sharpe, FF3 alpha %, t(alpha))
WRITEUP_TABLE1 = {
    "Validation 2010-Jul2022": {
        "Original | Short Brown hold 3m": (1.31, 0.41, 1.33, 1.47),
        "Pure | Short Brown hold 3m": (1.41, 0.44, 1.44, 1.50),
        "Original | Short Brown hold 6m": (2.45, 0.59, 2.25, 2.23),
        "Pure | Short Brown hold 6m": (2.59, 0.60, 2.51, 2.46),
    },
    "Holdout Aug2022-Jul2026": {
        "Original | Short Brown hold 3m": (-3.82, -1.15, -4.03, -2.19),
        "Pure | Short Brown hold 3m": (-2.17, -0.93, -2.21, -1.93),
        "Original | Short Brown hold 6m": (-2.14, -0.49, -2.28, -1.66),
        "Pure | Short Brown hold 6m": (-3.04, -0.74, -2.71, -1.94),
    },
}


@functools.lru_cache(maxsize=None)
def default_run():
    return run_pipeline()


@functools.lru_cache(maxsize=None)
def cheap_run():
    return run_pipeline(**CHEAP)


def _rounds_to(x, target, dp=2):
    return abs(x - target) <= 0.5 * 10 ** -dp + 1e-12


# ------------------------------------------------------------------ reproduction of committed outputs
def test_comparison_table_matches_committed():
    ref = pd.read_csv(COMMITTED / "comparison_table.csv")
    new = default_run()["comparison_table"]
    assert list(ref.columns) == list(new.columns)
    assert list(ref["strategy"]) == list(new["strategy"])
    for col in ref.columns:
        if col == "strategy":
            continue
        if col == "significant_after_multiple_testing":
            assert (ref[col].astype(bool).to_numpy() == new[col].astype(bool).to_numpy()).all(), col
            continue
        a, b = ref[col].to_numpy(float), new[col].to_numpy(float)
        assert np.array_equal(np.isnan(a), np.isnan(b)), col
        diff = np.nanmax(np.abs(a - b))
        assert diff <= TOL, f"{col}: max abs diff {diff}"


def test_writeup_table1():
    pt = default_run()["period_table"].set_index(["period", "strategy"])
    for period, rows in WRITEUP_TABLE1.items():
        for strat, (net, sharpe, alpha, t) in rows.items():
            r = pt.loc[(period, strat)]
            got = (100 * r["ann_net"], r["sharpe_net"], 100 * r["alpha_ann"], r["alpha_t_hac6"])
            for g, w, nm in zip(got, (net, sharpe, alpha, t), ("net", "sharpe", "alpha", "t")):
                assert _rounds_to(g, w), f"{period} {strat} {nm}: got {g:.4f}, writeup {w}"


def test_writeup_text_claims():
    res = default_run()
    pt = res["period_table"].set_index(["period", "strategy"])
    covid3 = pt.loc[("COVID 2020-2021", "Original | Short Brown hold 3m")]
    covid6 = pt.loc[("COVID 2020-2021", "Original | Short Brown hold 6m")]
    assert _rounds_to(100 * covid3.ann_net, 5.94) and _rounds_to(100 * covid3.alpha_ann, 6.03) and _rounds_to(covid3.alpha_t_hac6, 3.21)
    assert _rounds_to(100 * covid6.ann_net, 7.41) and _rounds_to(100 * covid6.alpha_ann, 5.23) and _rounds_to(covid6.alpha_t_hac6, 2.07)
    ct = res["claims_table"]
    assert len(ct) == 32 and int(ct.reject_at_5pct.sum()) == 2
    assert set(ct[ct.reject_at_5pct].period) == {"COVID 2020-2021"}
    d = res["diagnostics"]["macro_r_squared"]
    assert _rounds_to(100 * d["Raw attention"], 6.24) and _rounds_to(100 * d["Purified attention (investable)"], 0.83)
    unc = res["unconditional"]
    assert _rounds_to(unc.loc["Full 1970-Jul2022", "HML"], -0.24) and _rounds_to(unc.loc["Post-2010", "HML"], -0.35)


def test_macro_state_tables_match_committed():
    res = default_run()
    ref = pd.read_csv(COMMITTED / "macro_state_slopes.csv")
    new = res["macro_state_table"]
    assert list(ref.columns) == list(new.columns)
    assert (ref[["signal", "state"]].to_numpy() == new[["signal", "state"]].to_numpy()).all()
    num = [c for c in ref.columns if c not in ("signal", "state")]
    assert np.nanmax(np.abs(ref[num].to_numpy(float) - new[num].to_numpy(float))) <= TOL
    refp = pd.read_csv(COMMITTED / "macro_state_slopes_by_period.csv", header=[0, 1], index_col=[0, 1])
    newp = res["macro_state_by_period"]
    a, b = refp.to_numpy(float), newp.to_numpy(float)
    assert a.shape == b.shape and np.array_equal(np.isnan(a), np.isnan(b))
    assert np.nanmax(np.abs(a - b)) <= TOL


def test_against_team_script_objects():
    """Compare every intermediate object pickled from a run of the team script (scratch/capture_team_globals.py)."""
    if not TEAM_REF_PKL.exists():
        warnings.warn("team_reference.pkl missing; run scratch/capture_team_globals.py to enable this test")
        return
    R = pickle.load(open(TEAM_REF_PKL, "rb"))
    res = run_pipeline(placebo_reps=300)
    for name, df in R["all_models"].items():
        for col in df.columns:
            a, b = df[col].align(res["strategies"][name][col])
            assert a.isna().equals(b.isna()) and float((a - b).abs().max()) <= 1e-12, (name, col)
    for key, mine in [("attention", "raw"), ("pure_attention", "pure"), ("w_original", "w_raw"), ("w_pure", "w_pure")]:
        a, b = R[key].align(res["signals"][mine])
        assert float((a - b).abs().max()) <= 1e-12, key
    ic = pd.concat([R["ic_table"], pd.DataFrame(R["ic_rows_cont"])]).merge(res["ic_table"], on=["signal", "period"])
    assert len(ic) == 12 and float((ic.IC_x - ic.IC_y).abs().max()) <= TOL
    pt = pd.concat([R["baseline_table"], R["improved_table"]]).merge(res["period_table"], on=["strategy", "period"])
    assert len(pt) == 48 and float((pt.alpha_t_hac6_x - pt.alpha_t_hac6_y).abs().max()) <= TOL
    assert float((R["paired_table"].p_two_sided - res["paired_table"].p_two_sided).abs().max()) == 0
    assert np.array_equal(R["draws"], res["placebo"]["draws"]) and res["placebo"]["p_ge_real"] == 0.12


# ------------------------------------------------------------------ API behaviour
def test_explicit_inputs_equal_defaults():
    T = load_team()
    a = cheap_run()["comparison_table"]
    b = run_pipeline(industries=T["industries"], factors=T["ff3"], macro=T["macro"], green=TEAM_GREEN, brown=TEAM_BROWN,
                     attention=T["macro"]["attention"], costs={"asset": 10e-4, "Mkt-RF": 5e-4, "other_factor": 25e-4},
                     **CHEAP)["comparison_table"]
    num = a.select_dtypes("number").columns
    assert float((a[num] - b[num]).abs().max().max()) == 0.0


def test_team_legs_default_and_tie_warning():
    assert team_legs(5) == (TEAM_GREEN, TEAM_BROWN)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        g8, b8 = team_legs(8)
    assert len(g8) == 8 and len(b8) == 8 and any("tie" in str(x.message) for x in w)


def test_extra_factors_and_legs():
    fac = load_ff5_mom().join(load_fred("PALLFNFINDEXM").pct_change().rename("COM"), how="left")
    cols = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "COM")
    g8, b8 = team_legs(8)
    res = run_pipeline(factors=fac, factor_cols=cols, green=g8, brown=b8, **CHEAP)
    assert list(res["models"]["Brown leg"]["betas"].columns) == list(cols)
    assert set(res["cost_rates"]) == {"asset", *cols}
    assert "UMD_beta" in res["period_table"].columns and "COM_t" in res["period_table"].columns
    assert res["comparison_table"]["ann_return_full"].notna().all()


def test_uniform_costs():
    base = cheap_run()
    zero = run_pipeline(cost_bps_uniform=0, **CHEAP)
    for n in base["baseline_names"]:
        s0, sb = zero["strategies"][n], base["strategies"][n]
        pd.testing.assert_series_equal(s0["gross_return"], sb["gross_return"])      # costs never touch gross
        assert float((s0["net_return"] - s0["gross_return"]).abs().max()) == 0.0
    prev = None
    for bp in (5, 10, 25):
        r = run_pipeline(cost_bps_uniform=bp, **CHEAP)
        assert set(r["cost_rates"].values()) == {bp * 1e-4}
        full = r["comparison_table"].set_index("strategy").loc[DISCRETE, "ann_return_full"]
        if prev is not None:
            assert (full < prev).all()                                               # more cost, less net
        prev = full
        s = r["strategies"]["Pure | Short Brown hold 6m"]
        expected = bp * 1e-4 * s["turnover"]                                          # uniform rate x total turnover
        assert np.allclose(s["cost_incurred"], expected, atol=1e-15)


def test_replacement_attention():
    T = load_team()
    shifted = run_pipeline(attention=T["macro"]["attention"].shift(1), controls=team_controls(T["macro"]).shift(1), **CHEAP)
    base = cheap_run()
    # shifting every signal input by one month shifts every signal by exactly one month
    a, b = base["signals"]["pure"].shift(1).align(shifted["signals"]["pure"])
    assert float((a - b).abs().max()) < 1e-12
    cpu = run_pipeline(attention=load_cpu(), **CHEAP)
    assert cpu["signals"]["raw"].first_valid_index() == pd.Timestamp("1990-03-31")
    assert cpu["comparison_table"]["ann_return_full"].notna().all()


def test_cheap_mode_speed():
    t = time.perf_counter()
    run_pipeline(bootstrap_reps=200, cost_bps_uniform=10)
    assert time.perf_counter() - t < 15


def test_no_lookahead():
    """Randomize every input after D; nothing in the monthly signals or strategy series up to D may change."""
    T = load_team()
    D = "2016-12-31"
    rng = np.random.default_rng(0)
    ind, ff3, mac = T["industries"].copy(), T["ff3"].copy(), T["macro"].copy()
    m = ind.index > D; ind.loc[m] = rng.normal(0, .08, size=ind.loc[m].shape)
    m = ff3.index > D; ff3.loc[m, ["Mkt-RF", "SMB", "HML"]] = rng.normal(0, .04, size=(m.sum(), 3))
    m = mac.index > D
    for c in ["attention", "rate10y", "wti", "cpi", "activity", "supply_chain"]:
        mac.loc[m, c] = np.abs(rng.normal(mac[c].mean(), mac[c].std(), size=m.sum()))
    r2, base = run_pipeline(industries=ind, factors=ff3, macro=mac, **CHEAP), cheap_run()
    for n, df in base["strategies"].items():
        for c in df.columns:
            assert float((df[c].loc[:D] - r2["strategies"][n][c].loc[:D]).abs().max()) == 0.0, (n, c)
    for k in ["raw", "pure", "w_raw", "w_pure", "threshold_raw", "threshold_pure"]:
        assert float((base["signals"][k].loc[:D] - r2["signals"][k].loc[:D]).abs().max()) == 0.0, k


def test_rolling_factor_model_timing():
    idx = pd.date_range("2000-01-31", periods=100, freq="ME")
    rng = np.random.default_rng(1)
    x = pd.DataFrame({"f": rng.normal(size=100)}, index=idx)
    y = pd.Series(0.5 * x["f"] + rng.normal(scale=.1, size=100), index=idx)
    betas, hedged, eps, alpha = rolling_factor_model(y, x, window=60)
    assert betas["f"].first_valid_index() == idx[59] and hedged.first_valid_index() == idx[60]
    X = np.column_stack([np.ones(60), x["f"].iloc[:60]])
    coef = np.linalg.lstsq(X, y.iloc[:60], rcond=None)[0]
    assert np.isclose(hedged.iloc[60], y.iloc[60] - coef[1] * x["f"].iloc[60])


def test_holm():
    adj, rej = holm_bonferroni([0.01, 0.04, 0.03, 0.005])
    assert np.allclose(adj, [0.03, 0.06, 0.06, 0.02]) and rej.tolist() == [True, False, False, True]


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            t = time.perf_counter()
            try:
                fn()
                print(f"PASS {name} ({time.perf_counter() - t:.1f}s)")
            except AssertionError as e:
                fails += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if fails else 0)
