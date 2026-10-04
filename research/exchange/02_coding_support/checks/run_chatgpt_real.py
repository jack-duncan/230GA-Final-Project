"""Run ChatGPT's code (unmodified) on the real data. Glue only (see glue.py).

usage: uv run python exchange/02_coding_support/checks/run_chatgpt_real.py {final|seen|seen0722|lookahead_seen}
  final         Config() as delivered: 1993-01..2009-12 (window start moved by the code itself)
  seen          ChatGPT's own "seen" mode: 2010-01..2022-12
  seen0722      2010-01..2022-07 = the reference dry-run window (team validation end)
  lookahead_seen  ChatGPT's own look-ahead test on the seen data (cuts >= 2010-01)
"""
import sys
import time
from dataclasses import replace

from glue import g, real_inputs, save

mode = sys.argv[1]
inputs = real_inputs()
t0 = time.time()
if mode == "final":
    out = g.run_backtest(inputs, g.Config())
    save(out, "final_asis")
elif mode == "seen":
    out = g.run_backtest(inputs, replace(g.Config(), test_start="2010-01", test_end="2022-12"))
    save(out, "seen_asis")
elif mode == "seen0722":
    out = g.run_backtest(inputs, replace(g.Config(), test_start="2010-01", test_end="2022-07"))
    save(out, "seen0722_asis")
elif mode == "lookahead_seen":
    cfg = replace(g.Config(), test_start="2010-01", test_end="2022-12")
    la = g.check_no_lookahead(inputs, cfg, cut_from="2010-01")
    g._show("LOOK-AHEAD TEST (seen data only)", la)
    la.to_csv(g.__dict__.get("OUT", None) or "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks/out/lookahead_seen_asis.csv")
    print("all ok:", bool(la["ok"].all()), "rows:", len(la))
else:
    raise SystemExit(mode)
print(f"\n[elapsed {time.time() - t0:.1f} s]")
