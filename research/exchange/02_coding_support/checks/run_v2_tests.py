"""Round 2: run ChatGPT's unit tests (run_unit_tests order) on chatgpt_code_v2.py, one at a time, recording each
result instead of stopping at the first failure. Writes out/v2_unit_tests.csv.

usage: uv run python run_v2_tests.py [test_name ...]
"""
import sys
import time
import traceback

sys.dont_write_bytecode = True
sys.path.insert(0, "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks")
import pandas as pd  # noqa: E402

import chatgpt_code_v2 as g2  # noqa: E402

names = sys.argv[1:] or ["test_attention_signal", "test_pass_fail_table", "test_seen_cut", "test_leg_pipeline",
                         "test_check_no_lookahead", "test_make_synthetic_inputs"]
rows = []
for n in names:
    t0 = time.time()
    try:
        getattr(g2, n)()
        res, msg = "ok", ""
    except Exception as e:  # noqa: BLE001
        res = type(e).__name__
        msg = (repr(e)[:3000] + "\n" + traceback.format_exc(limit=6)[-3000:])
    rows.append({"test": n, "result": res, "seconds": round(time.time() - t0, 1), "message": msg})
    print(f"{n}: {res} ({rows[-1]['seconds']} s)\n{msg}", flush=True)
tag = "_".join(sys.argv[1:]) if sys.argv[1:] else "all"
pd.DataFrame(rows).to_csv(f"/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks/out/v2_unit_tests_{tag}.csv", index=False)
