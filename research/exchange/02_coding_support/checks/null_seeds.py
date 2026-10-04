"""ChatGPT check (b)9, last bullet: across 20 synthetic seeds with no planted effect, the shuffle p <= 0.05 should occur
about 5% of the time; stop if more than 4 of 20. Runs the UNMODIFIED v1 code (and v2 for comparison) with 500 draws,
as ChatGPT's synthetic mode does.

usage: uv run python null_seeds.py {v1|v2} seed0 seed1 ...
"""
import importlib
import sys
from dataclasses import replace

import pandas as pd

sys.dont_write_bytecode = True
sys.path.insert(0, "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks")
mod = importlib.import_module("chatgpt_code_" + sys.argv[1])
rows = []
for sd in map(int, sys.argv[2:]):
    cfg = replace(mod.Config(), shuffle_draws=500)
    out = mod.run_backtest(mod.make_synthetic_inputs(seed=sd), cfg, verbose=False)
    if "attribution" not in out:
        rows.append({"seed": sd, "note": "no episodes"})
        continue
    a = out["attribution"].loc["alpha"]
    rows.append({"seed": sd, "alpha": a["coef"], "t6": a["t NW(6)"], "p2": a["p NW(6)"],
                 "shuffle_p": out["shuffle"].at["p (one-sided)", "value"], "episodes": len(out["episodes"]),
                 "verdict": out["verdict"]})
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(f"/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks/out/null_seeds_{sys.argv[1]}_{sys.argv[2]}.csv", index=False)
