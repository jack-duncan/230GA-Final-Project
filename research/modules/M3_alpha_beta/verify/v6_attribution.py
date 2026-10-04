"""V6: COVID and holdout attribution of Pure 6m / Continuous pure; position overlap with Always-short Brown;
in-period factor contributions (which factors carried the COVID gain?)."""
import numpy as np
import pandas as pd
from vlib import (build_bond_independent, factor_panel, pipelines, load_team, nw, OUT, END, HOLD, COVID, POST10, STRATS, BENCH, SH,
                  FF3UB, FF5UB)
from team_pipeline import TEAM_BROWN

T = load_team(); rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
team, corr = pipelines()
brown = T["industries"][TEAM_BROWN].mean(axis=1) - rf

# ---- position overlap with Always-short Brown, COVID
for bl, res in (("team", team), ("corrected", corr)):
    ao = res["strategies"][BENCH]["position"].shift(1).loc[COVID[0]:COVID[1]]
    for s in ("Pure | Short Brown hold 6m", "Original | Short Brown hold 6m", "Pure | Short Brown hold 3m", "Continuous | pure attention"):
        h = res["strategies"][s]["position"].shift(1).loc[COVID[0]:COVID[1]]
        print(f"{bl:9s} {SH[s]:9s} COVID months equal to Always-short: {int(np.isclose(h, ao).sum())}/24; in position {int((h != 0).sum())}; "
              f"net {12*res['strategies'][s]['net_return'].loc[COVID[0]:COVID[1]].mean():.4f} vs benchmark "
              f"{12*res['strategies'][BENCH]['net_return'].loc[COVID[0]:COVID[1]].mean():.4f}")

# ---- structural centered-window attribution (own implementation)
def centered(y, Fm, w):
    d = pd.concat([y.rename("y"), Fm], axis=1, sort=True).dropna()
    n = len(d); B = pd.DataFrame(np.nan, index=d.index, columns=Fm.columns)
    for t in range(n):
        lo = min(max(t - w // 2 + 1, 0), n - w)
        seg = d.iloc[lo:lo + w]
        B.iloc[t] = np.linalg.lstsq(np.column_stack([np.ones(w), seg[Fm.columns].to_numpy()]), seg["y"].to_numpy(), rcond=None)[0][1:]
    return B


rows = []
for w in (36, 24):
    bc = centered(brown, F[FF3UB], w)
    for bl, res in (("team", team), ("corrected", corr)):
        hedge = res["models"]["Brown leg"]["betas"].shift(1)
        for s in ("Pure | Short Brown hold 6m", "Continuous | pure attention"):
            st = res["strategies"][s]; h = st["position"].shift(1)
            idx = st.index.intersection(bc.index)
            comp = pd.DataFrame(index=idx)
            for c in FF3UB:
                hb = hedge[c].reindex(idx) if c in ("Mkt-RF", "SMB", "HML") else 0.0
                comp[c] = h.reindex(idx) * (bc[c].reindex(idx) - hb) * F[c].reindex(idx)
            comp["leak"] = comp[FF3UB].sum(axis=1)
            comp["resid"] = st["gross_return"].reindex(idx) - comp["leak"]
            comp["cost"] = -st["cost"].reindex(idx); comp["net"] = st["net_return"].reindex(idx)
            # identity check: net = leak + resid + cost
            assert float((comp["net"] - comp["leak"] - comp["resid"] - comp["cost"]).abs().max()) < 1e-12
            for per, (a, e) in (("covid", COVID), ("holdout", HOLD)):
                c_ = comp.loc[a:e]
                fr, fl = nw(c_["resid"]), nw(c_["leak"])
                rows.append({"w": w, "baseline": bl, "s": SH[s], "period": per, "net": 12 * c_["net"].mean(), "leak": 12 * c_["leak"].mean(),
                             "p_leak": fl["p"]["const"], "resid": 12 * c_["resid"].mean(), "t_resid": fr["t"]["const"],
                             "p_resid": fr["p"]["const"], "cost": 12 * c_["cost"].mean(),
                             **{f"L_{c}": 12 * c_[c].mean() for c in FF3UB}})
R = pd.DataFrame(rows)
pd.set_option("display.width", 260)
print(R.round(4).to_string())

# ---- in-period regressions, COVID, corrected Pure 6m: loadings and per-factor contribution b_k x mean(f_k)
y = corr["strategies"]["Pure | Short Brown hold 6m"]["net_return"].loc[COVID[0]:COVID[1]]
for nm, cols in (("FF3+UMD+BOND", FF3UB), ("FF5+UMD+BOND", FF5UB)):
    f = nw(y, F[cols]); fm = F[cols].loc[COVID[0]:COVID[1]].mean()
    contrib = {c: round(1200 * f["b"][c] * fm[c], 2) for c in cols}
    print(f"COVID corrected Pure 6m {nm}: alpha {12*f['b']['const']:.4f} (t {f['t']['const']:.2f}); loadings",
          {c: (round(f['b'][c], 2), round(f['t'][c], 2)) for c in cols}, "; contributions %/yr", contrib,
          "; sum", round(sum(contrib.values()), 2))
print("COVID factor means %/yr:", (1200 * F[FF3UB].loc[COVID[0]:COVID[1]].mean()).round(2).to_dict())
R.to_csv(OUT / "v6_attribution.csv", index=False)
