"""V7: team macro-state 'High rates' slope difference, with a BOND(t+1) control, and with corrected (lagged) signals.
Uses team_pipeline.state_slopes / team_states (allowed); the control regression is coded here."""
import numpy as np
import pandas as pd
from scipy import stats
from vlib import build_bond_independent, load_team, nw, OUT, END, HOLD
from team_pipeline import run_pipeline, team_controls, team_states, state_slopes

T = load_team(); rf = T["ff3"]["RF"]
bond = build_bond_independent(rf)["BOND"]
team = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=True)
mac = T["macro"].copy(); mac["cpi"] = mac["cpi"].interpolate(limit_area="inside")
corr = run_pipeline(macro=mac, attention=mac["attention"].shift(1), controls=team_controls(mac).shift(1),
                    bootstrap_reps=0, extras=False, paired=False, macro_states=True)
mt = team["macro_state_table"]
print(mt[(mt.state == "High rates")].round(4).to_string())
start = team["macro_state_start"]
eps = team["models"]["Brown leg"]["epsilon"]


def ctrl_diff(sig, S, fwd, c, a, e):
    zs = lambda s: (s - s.mean()) / s.std(ddof=1)  # noqa: E731
    d = pd.concat([sig.rename("A"), S.rename("S"), fwd.rename("y"), c.rename("c")], axis=1, sort=True).loc[a:e].dropna()
    A, s = zs(d["A"]), d["S"]
    X = pd.DataFrame({"S": s, "Aoff": A * (1 - s), "Aon": A * s, "c": zs(d["c"])})
    f = nw(zs(d["y"]), X)
    w = np.array([0, 0, -1, 1, 0]); est = w @ f["b"].to_numpy(); se = np.sqrt(w @ f["V"].to_numpy() @ w)
    return est, est / se, len(d)


st_team = team_states(T["macro"])["High rates"]
r = state_slopes(team["signals"]["raw"], st_team, eps.shift(-1), start, END)
print(f"team raw High rates: off {r['slope_off']:.3f} on {r['slope_on']:.3f} (t {r['t_on']:.2f}) diff {r['diff']:.3f} (t {r['t_diff']:.2f}), "
      f"p t(n-4) {2*stats.t.sf(abs(r['t_diff']), r['n']-4):.3f}, p normal {2*stats.norm.sf(abs(r['t_diff'])):.3f}, n {r['n']}")
est, t, n = ctrl_diff(team["signals"]["raw"], st_team, eps.shift(-1), bond.shift(-1), start, END)
print(f"  + BOND(t+1) control: diff {est:.3f} (t {t:.2f})")
st_c = team_states(mac)["High rates"]
eps_c = corr["models"]["Brown leg"]["epsilon"]
for nm in ("raw", "pure"):
    r = state_slopes(corr["signals"][nm], st_c, eps_c.shift(-1), start, END)
    print(f"corrected {nm} High rates: diff {r['diff']:.3f} (t {r['t_diff']:.2f}), p t(n-4) {2*stats.t.sf(abs(r['t_diff']), r['n']-4):.3f}")
hs = st_team.loc[HOLD[0]:END]
fw = eps.shift(-1).loc[HOLD[0]:END].dropna()
print("holdout months with a forward residual:", len(fw), "; of which High rates:", int(hs.reindex(fw.index).sum()))
