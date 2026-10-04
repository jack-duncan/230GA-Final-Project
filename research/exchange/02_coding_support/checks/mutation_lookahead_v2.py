"""Round 2: power of ChatGPT's NEW check_no_lookahead against the same injected timing bugs as round 1 (M1-M6),
plus M7, run through the real v2 driver on ChatGPT's synthetic inputs (seed 0, TEST_WINDOW), exactly as its
__main__ calls the audit. Each mutant monkeypatches one function of chatgpt_code_v2 (unmodified on disk).

usage: uv run python mutation_lookahead_v2.py MUTANT      (MUTANT in none, M1..M7)
Writes out/r2_mutation_<MUTANT>.csv (audit rows) and out/r2_mutation_<MUTANT>_summary.csv.
"""
import sys
import time
from dataclasses import replace

sys.dont_write_bytecode = True
CHECKS = "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks"
sys.path.insert(0, CHECKS)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import chatgpt_code_v2 as g2  # noqa: E402

orig = {k: getattr(g2, k) for k in ("hold_positions", "run_trade", "attention_signal", "leg_pipeline")}


def _refit_tail(out, sd_window=36, vol_target=0.05):
    """Recompute e, sd, m from (possibly mutated) a, b with leg_pipeline's own formulas."""
    ks = g2.HEDGE_COLS
    fit_prev = out["a"].shift(1) + sum(out[f"b_{k}"].shift(1) * out[f"f_{k}"] for k in ks)
    out["e"] = out["RB"] - fit_prev
    out["sd"] = out["e"].rolling(sd_window, min_periods=sd_window).std(ddof=1)
    out["m"] = np.minimum(1.0, vol_target / (np.sqrt(12.0) * out["sd"]))
    return out


def m1(cross, index, cfg):
    """M1: publication lag dropped (position at end of t uses the signal of month t)."""
    return orig["hold_positions"](cross, index, replace(cfg, pub_lag=0))


def m2(rb, f, b, m, hold, cfg):
    """M2: month-t return hedged with b_t (estimated with R^B_t itself) instead of b_{t-1}."""
    out = orig["run_trade"](rb, f, b, m, hold, cfg)
    hf = list(cfg.hedge_factors)
    out["hedged"] = rb - (b.reindex(rb.index)[hf] * f.reindex(rb.index)[hf]).sum(axis=1, min_count=len(hf))
    out["gross"] = out["w_prev"] * out["hedged"]
    out["net"] = out["gross"] - out["cost"]
    return out


def m3(env, overall, **kw):
    """M3: signal month t uses the EMV of t+1."""
    return orig["attention_signal"](env.shift(-1), overall.shift(-1), **kw)


def m4(*a, **kw):
    """M4: size m_t uses sd_{t+1}."""
    out = orig["leg_pipeline"](*a, **kw)
    out["m"] = out["m"].shift(-1)
    return out


def m5(*a, **kw):
    """M5: hedge betas from a window centered on t (30 future months); residual and size rebuilt from them."""
    out = orig["leg_pipeline"](*a, **kw)
    for c in ["a"] + [f"b_{k}" for k in g2.HEDGE_COLS]:
        out[c] = out[c].shift(-30)
    return _refit_tail(out)


def m5b(*a, **kw):
    """M5b: as M5, but the last 30 months (no future data yet) keep the latest available centered beta, so the
    bug leaves no NaN at the sample end (M5 as written crashes any truncated run in timing_difference)."""
    out = orig["leg_pipeline"](*a, **kw)
    last = out["a"].last_valid_index()
    for c in ["a"] + [f"b_{k}" for k in g2.HEDGE_COLS]:
        sh = out[c].shift(-30)
        out[c] = sh.where(out.index < last - pd.offsets.MonthEnd(29), sh.ffill())
    return _refit_tail(out)


def m6(rb, f, b, m, hold, cfg):
    """M6: the position set at the end of t earns month t (not t+1)."""
    out = orig["run_trade"](rb, f, b, m, hold, cfg)
    out["gross"] = out["w"] * out["hedged"]
    out["net"] = out["gross"] - out["cost"]
    return out


def m7(rb, f, b, m, hold, cfg):
    """M7: the trade made at the end of t is charged in month t (not t+1)."""
    out = orig["run_trade"](rb, f, b, m, hold, cfg)
    out["cost"] = out["trade_cost"]
    out["net"] = out["gross"] - out["cost"]
    return out


MUTANTS = {"none": ("none (as delivered)", None, None),
           "M1": ("M1 publication lag dropped", "hold_positions", m1),
           "M2": ("M2 month-t return hedged with b_t", "run_trade", m2),
           "M3": ("M3 signal uses next month's EMV", "attention_signal", m3),
           "M4": ("M4 size m_t uses next month's sd", "leg_pipeline", m4),
           "M5": ("M5 hedge betas from a centered window", "leg_pipeline", m5),
           "M5b": ("M5b centered hedge betas, tail filled", "leg_pipeline", m5b),
           "M6": ("M6 position earns its own month", "run_trade", m6),
           "M7": ("M7 cost charged in the trade month", "run_trade", m7)}

if __name__ == "__main__":
    key = sys.argv[1]
    name, fn, repl = MUTANTS[key]
    if fn:
        setattr(g2, fn, repl)
    t0 = time.time()
    raw = g2.make_synthetic_inputs(seed=0)
    start, end = g2.TEST_WINDOW
    try:
        rep, ok = g2.check_no_lookahead(raw, lambda r: g2.run_panel(r, start, end)[0], start, end)
    except Exception as e:  # noqa: BLE001  (a mutant can make the audited pipeline itself raise)
        summ = {"mutant": name, "audit_rows": 0, "rows_flagged": 0, "detected": f"audit raised {type(e).__name__}: {e}",
                "flagged_by_test": "", "truncate_flags": 0, "synthetic_alpha": float("nan"), "seconds": round(time.time() - t0)}
        pd.DataFrame([summ]).to_csv(f"{CHECKS}/out/r2_mutation_{key}_summary.csv", index=False)
        print(summ)
        raise SystemExit(0)
    rep.to_csv(f"{CHECKS}/out/r2_mutation_{key}.csv", index=False)
    _, out = g2.run_panel(raw, start, end)
    flagged = rep.loc[~rep["passed"]].groupby("test").size().to_dict()
    summ = {"mutant": name, "audit_rows": len(rep), "rows_flagged": int((~rep["passed"]).sum()), "detected": not ok,
            "flagged_by_test": str(flagged), "truncate_flags": int(flagged.get("truncate", 0)),
            "synthetic_alpha": out["alpha"], "seconds": round(time.time() - t0)}
    pd.DataFrame([summ]).to_csv(f"{CHECKS}/out/r2_mutation_{key}_summary.csv", index=False)
    print(summ)
