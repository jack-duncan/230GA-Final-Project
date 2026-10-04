"""Round 2: ChatGPT's checks (b)9 (null seeds) and (b)10 (positive control) on the v2 generator and driver.

usage: uv run python pc_null_v2.py pc                 -> out/r2_positive_control.csv (seeds 0-2, plant 3%, and seed 0 at 0%)
       uv run python pc_null_v2.py null s1 s2 ...     -> out/r2_null_seeds_<s1>.csv (500 draws, as round 1)
"""
import sys
import time

sys.dont_write_bytecode = True
CHECKS = "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks"
sys.path.insert(0, CHECKS)
import pandas as pd  # noqa: E402

import chatgpt_code_v2 as g2  # noqa: E402

import os  # noqa: E402
DRAWS = int(os.environ.get("R2_DRAWS", "500"))
start, end = g2.TEST_WINDOW
rows = []
if sys.argv[1] == "pc":
    for seed, plant in [(0, 0.03), (1, 0.03), (2, 0.03), (0, 0.0)]:
        t0 = time.time()
        raw0 = g2.make_synthetic_inputs(seed)
        p0, o0 = g2.run_panel(raw0, start, end, n_shuffle=DRAWS)
        w0 = p0.loc[start:end]
        held = w0.index[(w0["I"] == 1).to_numpy()]
        raw1 = g2.make_synthetic_inputs(seed, plant=plant, plant_months=held) if plant else raw0
        p1, o1 = g2.run_panel(raw1, start, end, n_shuffle=DRAWS)
        shift = o1["D"].mean() - o0["D"].mean()
        pc = g2.positive_control(seed, plant=plant) if plant else {}
        top = o1["attribution"]["t NW(6)"].drop("alpha").abs().idxmax()
        rows.append({"seed": seed, "plant": plant, "n_held": len(held), "alpha_base": o0["alpha"], "alpha_planted": o1["alpha"],
                     "t_planted": o1["alpha_t"], "shuffle_p_planted": o1["shuffle"].at["p (one-sided)", "value"],
                     "mean_D_shift": shift, "share_in_alpha": (o1["alpha"] - o0["alpha"]) / shift if shift else float("nan"),
                     "largest_|t|_regressor": top, "its_t": o1["attribution"].loc[top, "t NW(6)"],
                     "positive_control_fn_share": pc.get("share"), "positive_control_fn_t": pc.get("t"),
                     "verdict": o1["verdict"], "seconds": round(time.time() - t0)})
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(f"{CHECKS}/out/r2_positive_control.csv", index=False)
else:
    for sd in map(int, sys.argv[2:]):
        try:
            _, o = g2.run_panel(g2.make_synthetic_inputs(sd), start, end, n_shuffle=DRAWS)
            rows.append({"seed": sd, "alpha": o["alpha"], "t6": o["alpha_t"],
                         "shuffle_p": o["shuffle"].at["p (one-sided)", "value"], "episodes": len(o["episodes"]),
                         "verdict": o["verdict"], "error": ""})
        except Exception as e:  # noqa: BLE001
            rows.append({"seed": sd, "error": repr(e)[:300]})
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(f"{CHECKS}/out/r2_null_seeds_{sys.argv[2]}_d{DRAWS}.csv", index=False)
