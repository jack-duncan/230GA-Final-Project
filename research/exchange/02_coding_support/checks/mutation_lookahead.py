"""Power of ChatGPT's check_no_lookahead: inject known timing bugs (mutants) and see which ones it flags.

Each mutant is installed by monkeypatching one function of chatgpt_code_v1 (unmodified on disk), then
check_no_lookahead runs on the synthetic inputs exactly as ChatGPT's synthetic mode calls it.
Writes out/mutation_lookahead.csv.
"""
from dataclasses import replace

import numpy as np
import pandas as pd

from glue import OUT, g

syn = g.make_synthetic_inputs(seed=0)
cfg = g.Config()
orig = {k: getattr(g, k) for k in ("hold_positions", "run_trade", "attention_signal", "hedge_residual_and_size", "rolling_hedge")}


def m_no_pub_lag(cross, index, cfg_):
    """M1: position at end of t uses the signal of month t (publication lag dropped)."""
    return orig["hold_positions"](cross, index, replace(cfg_, pub_lag=0))


def m_same_month_hedge(rb, f, b, m, hold, cfg_):
    """M2: month-t return hedged with b_t (estimated with R^B_t itself) instead of b_{t-1}."""
    out = orig["run_trade"](rb, f, b, m, hold, cfg_)
    hf = list(cfg_.hedge_factors)
    out["hedged"] = rb - (b.reindex(rb.index)[hf] * f.reindex(rb.index)[hf]).sum(axis=1, min_count=len(hf))
    out["gross"] = out["w_prev"] * out["hedged"]
    out["net"] = out["gross"] - out["cost"]
    return out


def m_future_emv(emv_cat, emv_all, cfg_):
    """M3: signal month tau uses EMV of tau+1."""
    return orig["attention_signal"](emv_cat.shift(-1), emv_all.shift(-1), cfg_)


def m_future_vol(rb, f, a, b, cfg_):
    """M4: size m_t uses sd_{t+1}."""
    e, sd, m = orig["hedge_residual_and_size"](rb, f, a, b, cfg_)
    return e, sd, m.shift(-1)


def m_centered_hedge(rb, f, window=60):
    """M5: hedge betas from a window centered on t (uses 30 future months)."""
    a, b = orig["rolling_hedge"](rb, f, window)
    return a.shift(-30), b.shift(-30)


def m_same_month_return(rb, f, b, m, hold, cfg_):
    """M6: the position set at the end of t earns month t (not t+1)."""
    out = orig["run_trade"](rb, f, b, m, hold, cfg_)
    out["gross"] = out["w"] * out["hedged"]
    out["net"] = out["gross"] - out["cost"]
    return out


mutants = [("none (as delivered)", None, None),
           ("M1 publication lag dropped", "hold_positions", m_no_pub_lag),
           ("M2 month-t return hedged with b_t", "run_trade", m_same_month_hedge),
           ("M3 signal uses next month's EMV", "attention_signal", m_future_emv),
           ("M4 size m_t uses next month's sd", "hedge_residual_and_size", m_future_vol),
           ("M5 hedge betas from a centered window", "rolling_hedge", m_centered_hedge),
           ("M6 position earns its own month", "run_trade", m_same_month_return)]
rows = []
for name, fn, repl in mutants:
    for k, v in orig.items():
        setattr(g, k, v)
    if fn:
        setattr(g, fn, repl)
    la = g.check_no_lookahead(syn, cfg)
    # does the mutant change the backtest at all? (alpha on the synthetic run, 50 shuffle draws is enough for this)
    out = g.run_backtest(syn, replace(cfg, shuffle_draws=50), verbose=False)
    rows.append({"mutant": name, "cuts": len(la), "cuts_flagged": int((~la["ok"]).sum()), "detected": bool((~la["ok"]).any()),
                 "synthetic_alpha": float(out["attribution"].loc["alpha", "coef"]) if "attribution" in out else np.nan})
    print(rows[-1], flush=True)
for k, v in orig.items():
    setattr(g, k, v)
res = pd.DataFrame(rows)
res.to_csv(OUT / "mutation_lookahead.csv", index=False)
print(res.to_string(index=False))
