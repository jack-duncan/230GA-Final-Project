"""Harmonization experiments: attribute each ChatGPT-vs-reference discrepancy to one cause.

These are NOT fixes to ChatGPT's code. Each switch replaces exactly one behaviour with the reference's
reading, via a wrapper or a copy of one function with a marked one- or two-line change:

  A  z burn-in: ChatGPT requires a full 60 calendar months of EMV history before any z (first z 1989-12);
     the reference (C5) counts months before 1985-01 as unavailable, so >= 48 nonzero months is the burn-in
     (first z 1989-01). Change: the two trailing-60 counts in attention_signal use min_periods=1 instead of 60.
  B  hedge/leg factor file: ChatGPT hedges with SMB/HML (and subtracts RF) from the `fac` it was given
     (Ken French FF5 2x3 file, current vintage); the reference (C10) uses the team FF3 file, as the team
     rule does. Change: leg_pipeline receives the team FF3 frame instead of `fac`. The attribution
     regressors still come from `fac` (FF5 + UMD), as in the reference.

usage: uv run python exchange/02_coding_support/checks/align.py {A|B|AB} [draws]
"""
import sys
import time
from dataclasses import replace

import numpy as np
import pandas as pd

from glue import g, real_inputs, save
from common import load_team

def attention_signal_A(emv_cat, emv_all, cfg):
    """Copy of chatgpt_code_v1.attention_signal (lines 249-295) with ONLY the two marked lines changed."""
    start = max(emv_cat.first_valid_index(), emv_all.first_valid_index())
    end = min(emv_cat.last_valid_index(), emv_all.last_valid_index())
    idx = g._month_range(start, end)
    s = emv_cat.reindex(idx) / emv_all.reindex(idx)
    missing = ~(s > 0)
    W = cfg.z_window
    max_missing = int(np.floor(cfg.max_zero_share * W + 1e-9))
    logs = np.log(s.where(~missing))
    n_miss = missing.astype(float).rolling(W, min_periods=1).sum()        # CHANGED (A): was min_periods=W
    n_nz = (~missing).astype(float).rolling(W, min_periods=1).sum()        # CHANGED (A): was W - n_miss
    mu = logs.rolling(W, min_periods=cfg.z_min_nonzero).mean()
    sd = logs.rolling(W, min_periods=cfg.z_min_nonzero).std(ddof=1)
    ok = (~missing) & (n_nz >= cfg.z_min_nonzero) & (n_miss <= max_missing) & (sd > 0)
    z = ((logs - mu) / sd).where(ok)
    zv = z.to_numpy(float)
    thr = np.full(len(zv), np.nan)
    hist = []
    for i, zi in enumerate(zv):
        if len(hist) >= cfg.min_pct_history:
            thr[i] = np.percentile(hist, cfg.pct)
        if np.isfinite(zi):
            hist.append(zi)
    defined = np.isfinite(zv) & np.isfinite(thr)
    extreme = np.where(defined, (np.nan_to_num(zv) > np.nan_to_num(thr)).astype(float), np.nan)
    return pd.DataFrame({"s": s, "missing": missing, "n_missing60": n_miss, "off": (~missing) & (n_miss > max_missing),
                         "z": z, "thr": thr, "extreme": extreme}, index=idx)


TEAM_FF3 = load_team()["ff3"][["Mkt-RF", "SMB", "HML", "RF"]]
_orig_leg_pipeline = g.leg_pipeline


def leg_pipeline_B(ff49, fac, industries, hold, index, cfg):
    """Wrapper: identical call, but the hedge factors and the leg's RF come from the team FF3 file."""
    return _orig_leg_pipeline(ff49, TEAM_FF3, industries, hold, index, cfg)


_orig_attention_signal = g.attention_signal


def apply(variant: str) -> None:
    """Install the harmonization switches named in `variant` ('', 'A', 'B', 'AB'); '' restores the originals."""
    g.attention_signal = attention_signal_A if "A" in variant else _orig_attention_signal
    g.leg_pipeline = leg_pipeline_B if "B" in variant else _orig_leg_pipeline


if __name__ == "__main__":
    variant = sys.argv[1]
    draws = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    apply(variant)
    inputs = real_inputs()
    t0 = time.time()
    tag = sys.argv[3] if len(sys.argv) > 3 else f"final_{variant}"
    cfg = replace(g.Config(), shuffle_draws=draws)
    if tag.startswith("seen"):
        cfg = replace(cfg, test_start="2010-01", test_end="2022-07")
    out = g.run_backtest(inputs, cfg)
    save(out, tag)
    print(f"\n[variant {variant}, draws {draws}, elapsed {time.time() - t0:.1f} s]")
