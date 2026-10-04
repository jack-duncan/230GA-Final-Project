"""V5b: Monte Carlo stability of the Ferson-Schadt bootstrap p-values (5 seeds x 999 reps, and one 4,999-rep run)."""
import numpy as np
import pandas as pd
from v5_ferson_schadt import fs, corr, POST10, SH, STRATS, OUT

rows = []
for s in ["Pure | Short Brown hold 3m", "Pure | Short Brown hold 6m", "Continuous | raw attention", "Continuous | pure attention"]:
    y = corr["strategies"][s]["net_return"]
    for seed in (1, 2, 3, 4, 5):
        o = fs(y, *POST10, reps=999, seed=seed)
        rows.append({"s": SH[s], "seed": seed, "reps": 999, "p_fixed": o["p_boot_fixed"], "q95_fixed": o["q95_fixed"],
                     "p_wild": o["p_boot_wild"], "q95_wild": o["q95_wild"]})
    o = fs(y, *POST10, reps=4999, seed=99)
    rows.append({"s": SH[s], "seed": 99, "reps": 4999, "p_fixed": o["p_boot_fixed"], "q95_fixed": o["q95_fixed"],
                 "p_wild": o["p_boot_wild"], "q95_wild": o["q95_wild"]})
R = pd.DataFrame(rows)
print(R.round(3).to_string())
print(R.groupby("s")[["p_fixed", "p_wild"]].agg(["min", "max"]).round(3))
R.to_csv(OUT / "v5b_fs_seeds.csv", index=False)
