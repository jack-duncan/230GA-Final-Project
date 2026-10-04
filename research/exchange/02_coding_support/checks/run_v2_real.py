"""Round 2: run chatgpt_code_v2.py exactly as its __main__ does, with glue only (no function of v2 is edited).

Glue, same as round 1 plus the new input ChatGPT asked for:
  G1  fac       = common.load_ff5_mom()[FF5 + RF + UMD] (Ken French 2x3 + momentum, decimals, month-end).
  G2  PATHS     = absolute paths of the team FF49 file and research/data/raw/fred_<id>.csv (bare names in __main__).
  G3  MODE      = chosen on the command line instead of editing the constant in __main__; each mode runs the
                  same statements as __main__ (read_raw, cut for "seen", check_no_lookahead, final run_panel).
  G5  hedge_fac = the team FF3 file (common.load_team()["ff3"][Mkt-RF, SMB, HML, RF]); __main__ leaves it None.

usage: uv run python run_v2_real.py MODE [z_burn_in] [--no-audit] [--draws N]
  MODE in {synthetic, seen, test}; z_burn_in in {nonzero (default), calendar}
Writes out/r2_<mode>_<z>_*.csv and, unless --no-audit, out/r2_lookahead_<mode>_<z>.csv.
"""
import argparse
import sys
import time

sys.dont_write_bytecode = True
CHECKS = "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks"
sys.path.insert(0, CHECKS)
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import chatgpt_code_v2 as g2  # noqa: E402
from common import load_ff5_mom, load_team  # noqa: E402

OUT = f"{CHECKS}/out"
RAWDIR = "/home/hashim/projects/GA/project/research/data/raw"
PATHS = {"ff49": "/home/hashim/projects/GA/project/230GA-Final-Project/data/ff49_industry_monthly.csv",
         **{sid: f"{RAWDIR}/fred_{sid}.csv" for sid in g2.FRED_IDS}}


def real_fac():
    return load_ff5_mom()[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF", "UMD"]].copy()


def real_hedge_fac():
    return load_team()["ff3"][["Mkt-RF", "SMB", "HML", "RF"]].copy()


def save(out: dict, tag: str) -> None:
    for k, v in out.items():
        if isinstance(v, (pd.DataFrame, pd.Series)):
            v.to_csv(f"{OUT}/{tag}_{k}.csv")
        elif isinstance(v, np.ndarray):
            pd.Series(v, name=k).to_csv(f"{OUT}/{tag}_{k}.csv", index=False)
    leg = out.get("leg")
    if leg is not None:
        books = pd.DataFrame({"RB": leg["rb"], "m": leg["m"], "net_T": leg["tr_T"]["net"], "net_AO": leg["tr_AO"]["net"],
                              "w_T": leg["tr_T"]["w"], "w_AO": leg["tr_AO"]["w"]})
        books = books.join(leg["b"].add_prefix("b_"))
        books.to_csv(f"{OUT}/{tag}_books.csv")
    scal = {k: out[k] for k in ("alpha", "alpha_t", "verdict") if k in out}
    pd.Series(scal, name="value").to_csv(f"{OUT}/{tag}_scalars.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["synthetic", "seen", "test"])
    ap.add_argument("z_burn_in", nargs="?", default="nonzero", choices=["nonzero", "calendar"])
    ap.add_argument("--no-audit", action="store_true")
    ap.add_argument("--draws", type=int, default=5000)
    a = ap.parse_args()
    MODE, Z_BURN_IN = a.mode, a.z_burn_in
    t0 = time.time()

    # ---- statements of chatgpt_code_v2.__main__, with G1-G5 substituted ----
    WINDOWS = {"synthetic": g2.TEST_WINDOW, "seen": g2.SEEN_WINDOW, "test": g2.TEST_WINDOW}
    start, end = WINDOWS[MODE]
    if MODE == "synthetic":
        raw = g2.make_synthetic_inputs(seed=0)          # run_unit_tests() is run separately (run_v2_tests.py)
    else:
        raw = g2.read_raw(PATHS, real_fac(), real_hedge_fac())

    cut_to = end if MODE == "seen" else None
    if cut_to is not None:
        raw = g2.truncate_raw(raw, cut_to)

    tag = f"r2_{MODE}_{Z_BURN_IN}"
    if not a.no_audit:
        rep, ok = g2.check_no_lookahead(raw, lambda r: g2.run_panel(r, start, end, z_burn_in=Z_BURN_IN)[0],
                                        start, end, cut_to=cut_to)
        rep.to_csv(f"{OUT}/r2_lookahead_{MODE}_{Z_BURN_IN}.csv", index=False)
        print(rep.groupby("test")["passed"].agg(["size", "sum"]).to_string())
        print(f"audit ok: {ok}; max pre_diff {rep['pre_diff'].max():.3g}; max ret_err {rep['ret_err'].max():.3g}; "
              f"[{time.time() - t0:.0f} s]", flush=True)
        if not ok:
            print(rep.loc[~rep["passed"]].to_string())
            sys.exit("STOP: look-ahead audit failed.")

    panel, out = g2.run_panel(raw, start, end, z_burn_in=Z_BURN_IN, n_shuffle=a.draws, loo=True, verbose=True)
    save(out, tag)
    print(f"\n[{tag}: elapsed {time.time() - t0:.1f} s]")
