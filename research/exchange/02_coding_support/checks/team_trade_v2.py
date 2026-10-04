"""Round 2: ChatGPT check (b)2 on v2. The v2 books (ChatGPT's leg_pipeline on hedge_fac = team FF3, unchanged
run_trade via _leg_books) fed the team's 6-month hold must reproduce run_pipeline's 'Original | Short Brown hold 6m'
and 'Benchmark | Always-short Brown' net returns on 2010-01..2022-07 to 1e-8 (stop rule). Writes out/r2_team_trade.csv.
"""
import sys

sys.dont_write_bytecode = True
CHECKS = "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks"
sys.path.insert(0, CHECKS)
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import pandas as pd  # noqa: E402

import chatgpt_code_v2 as g2  # noqa: E402
from run_v2_real import PATHS, real_fac, real_hedge_fac  # noqa: E402
from team_pipeline import run_pipeline  # noqa: E402

cfg = g2.Config()
ff49 = g2.load_ff49(PATHS["ff49"])
fac = g2.load_factors(real_fac())
index = g2._month_range(fac.index.min(), min(fac.index.max(), ff49.index.max()))
team = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
t_ao = team["strategies"]["Benchmark | Always-short Brown"]["net_return"]
t_o6 = team["strategies"]["Original | Short Brown hold 6m"]["net_return"]
h6 = team["signals"]["hold_raw"][6].reindex(index, fill_value=False).astype(bool)
seen = pd.date_range("2010-01-31", "2022-07-31", freq="ME")
leg = g2._leg_books(ff49, real_hedge_fac(), cfg.brown, h6, index, cfg)
d_ao = float((leg["tr_AO"]["net"].reindex(seen) - t_ao.reindex(seen)).abs().max())
d_o6 = float((leg["tr_T"]["net"].reindex(seen) - t_o6.reindex(seen)).abs().max())
row = {"check": "(b)2 team trade 2010-01..2022-07, v2 books on hedge_fac = team FF3", "max_abs_diff_always_short": d_ao,
       "max_abs_diff_original_6m": d_o6, "status": "pass" if max(d_ao, d_o6) <= 1e-8 else "STOP"}
pd.DataFrame([row]).to_csv(f"{CHECKS}/out/r2_team_trade.csv", index=False)
print(row)
