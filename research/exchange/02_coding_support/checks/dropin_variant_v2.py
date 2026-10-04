"""Round 2, issue N1: the silent consequence of applying ChatGPT's new attention_signal without an output adapter.
A literal drop-in raises KeyError 'off' in diagnostics_summary. If only that crash is patched (add `off`, keep
everything else as the new function returns it), the boolean `extreme` (False where undefined) reaches the
unchanged test_window and crossings. This variant monkeypatches g2._driver_signal to do exactly that, then runs the
real test window with the same audit-free settings as the main run (5000 draws, leave-one-out).
Writes out/r2_dropin_<tag>_*.csv via run_v2_real.save.

usage: uv run python dropin_variant_v2.py {test|seen}
"""
import sys

sys.dont_write_bytecode = True
CHECKS = "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks"
sys.path.insert(0, CHECKS)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import chatgpt_code_v2 as g2  # noqa: E402
from run_v2_real import PATHS, real_fac, real_hedge_fac, save  # noqa: E402


def driver_signal_min_patch(sig, cfg):
    """Only what is needed to stop the KeyError: add `off`; s, extreme stay as the new function returns them."""
    out = sig.copy()
    out["off"] = sig["s"].notna() & (sig["n_zero"] > int(np.floor(cfg.max_zero_share * cfg.z_window + 1e-9)))
    return out


g2._driver_signal = driver_signal_min_patch
mode = sys.argv[1]
start, end = g2.TEST_WINDOW if mode == "test" else g2.SEEN_WINDOW
raw = g2.read_raw(PATHS, real_fac(), real_hedge_fac())
if mode == "seen":
    raw = g2.truncate_raw(raw, end)
panel, out = g2.run_panel(raw, start, end, n_shuffle=5000, loo=True, verbose=True)
save(out, f"r2_dropin_{mode}")
