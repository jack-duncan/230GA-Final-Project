"""M1b_alt_signals: feed the team's exact trading machinery alternative attention measures.

Run:  cd /home/hashim/projects/GA/project/research && uv run python modules/M1b_alt_signals/run.py

PRE-SPECIFICATION (written before any alternative measure was run; only the EMV_env team and corrected
baselines were known from the replication log)
-------------------------------------------------------------------------------------------------------
Machinery: lib/team_pipeline.run_pipeline, unchanged (5+5 legs, rolling 60m FF3 hedge, Brown-leg residual,
rolling_z(transform(attention)), expanding past-only p80 crossing, 3m/6m holds, walk-forward ridge
purification, continuous weight). Only the attention series (and its timing) changes.
Transform: log1p for every measure (all are nonnegative); robustness: level ('none') for MCCC and CPU.
Timing: primary = corrected baseline ('realtime': attention and purification controls lagged one month,
Oct-2025 CPI gap interpolated). Comparison = team timing ('same_month', CPI interpolated). Team baseline
(run_pipeline() defaults) kept as a reference row for EMV_env.
Windows: validation 2010-01..2022-07; holdout 2022-08..end_m, end_m = last month whose return is driven by
the measure under both timings (last data month + 1): MCCC 2025-07, CPU 2025-10, others 2026-07.
p-values: t(n-k) when n < 60, else normal; NW(6) t-stats throughout.

Q1 PRIMARY (family of 40 tests, Holm and BH within the family): for m in {MCCC aggregate, CPU}, realtime
timing: FF3 alpha t of the 6 team strategies (Original 3m, Pure 3m, Original 6m, Pure 6m, Continuous raw,
Continuous pure) in validation and holdout (24 tests), and the IC of the 4 signals (raw z, purified,
continuous weight raw, continuous weight pure) in validation and holdout (16 tests). IC is the NW slope of
z(eps_{t+1}) on z(signal_t); for a Short-Brown rule a NEGATIVE IC is favorable.
Decision rule: the result "changes" (towards implementation) only if some MCCC or CPU strategy has a
positive holdout FF3 alpha with Holm-adjusted p < 0.05. Descriptively, compare the sign pattern with
EMV_env (validation alpha > 0 with t >= 1.96, holdout alpha < 0).

Q2 PLACEBO (pre-specified, separate family): for p in {VIX monthly mean, EMV overall}, realtime timing:
the same validation/holdout/IC statistics, plus the COVID window (2020-01..2021-12, n = 24) FF3 alpha of
the 6 strategies and a paired test (FF3 alpha of r_EMVenv - r_placebo, NW(6), t(20) p-value).
A placebo "reproduces" the COVID gain for a strategy if its COVID alpha is > 0 and >= 50% of the EMV_env
COVID alpha for the same strategy. The climate interpretation of the COVID result fails if either
placebo reproduces the gain in >= 4 of the 6 strategies.

Everything else (team timing, EMV_env_share, MCCC transition composite, level transform, matched holdout
windows, live-window validation, other periods, crossing overlap) is robustness or exploratory.
"""
# Revision after independent verification (VERIFY.md); the pre-specification above is unchanged:
#  - crossings: chance overlap uses the exact share of window months within +/-1 month of a team crossing, plus a
#    circular-shift permutation; the ledger stores two-sided p-values (one-sided in the note);
#  - full_mode_comparison.csv: pipeline columns significant_after_multiple_testing and active_months_full dropped
#    (invalid here, audit items 3, 6, 8); months_held_full added;
#  - ledger: pipeline full-mode per-strategy and paired bootstrap tests added; paired COVID tests against the
#    signal-free always-short position added; bootstrap p = 0 stored as the 2/5000 resolution bound;
#  - covid_paths figure compounds 2020-01..2021-12 only (it previously included the Dec-2019 return);
#  - new tables: recent (.csv/.tex), covid_attribution (.tex); more key numbers.
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from helpers import (MODULE, MEASURES, STRATS, STRAT_LABEL, STRAT_SIGNAL, STRAT_LIVE_KEY, SIGNAL_LABEL, SAMPLE_END,  # noqa: E402
                     macro_fixed, build_measures, native_range, eval_end, run_measure, window_stats, ic_return_aligned,
                     ic_team_convention, paired_alpha, live_start, crossings, within, p_from_t, CHEAP)
from common import load_team, TABLES, holm, bh  # noqa: E402
from team_pipeline import run_pipeline, circular_block_bootstrap  # noqa: E402
import plotstyle as ps  # noqa: E402
from scipy.stats import binom, binomtest  # noqa: E402
from plotstyle import plt, savefig  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
T0 = time.perf_counter()
ME = pd.offsets.MonthEnd(1)
VAL = (pd.Timestamp("2010-01-31"), pd.Timestamp("2022-07-31"))
HOLD_START = pd.Timestamp("2022-08-31")
COVID = (pd.Timestamp("2020-01-31"), pd.Timestamp("2021-12-31"))
TIMINGS = ("realtime", "same_month")
PRIMARY, PLACEBO = ("MCCC", "CPU"), ("VIX", "EMV_overall")
COLORS = {"EMV_env": ps.ORANGE, "EMV_env_share": ps.MAGENTA, "EMV_overall": ps.RED, "VIX": ps.MUTED,
          "MCCC": ps.AQUA, "MCCC_transition": ps.YELLOW, "CPU": ps.VIOLET}
ORDER = ["EMV_env", "MCCC", "CPU", "VIX", "EMV_overall", "EMV_env_share", "MCCC_transition"]
ORDER_COVID = ORDER
SHORT = {"EMV_env": "EMV env.", "EMV_env_share": "EMV env. share", "EMV_overall": "EMV overall", "VIX": "VIX",
         "MCCC": "MCCC", "MCCC_transition": "MCCC transition", "CPU": "CPU"}


def out(name):
    return TABLES / f"{MODULE}_{name}"


def to_tex(df: pd.DataFrame, name: str, caption: str, label: str, col_fmt: str | None = None, escape=True):
    """booktabs table; df already formatted as strings where needed."""
    body = df.to_latex(index=False, escape=escape, column_format=col_fmt or ("l" * 2 + "r" * (df.shape[1] - 2)))
    tex = ("\\begin{table}[htbp]\n\\centering\n\\footnotesize\n\\caption{" + caption + "}\n\\label{" + label + "}\n"
           + body + "\\end{table}\n")
    (TABLES / f"{MODULE}_{name}.tex").write_text(tex)


def f2(x, d=2):
    return "" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"


def pct(x, d=2):
    return "" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.{d}f}"


# ============================================================================ 1. data and runs
print("building measures ...")
MEAS = build_measures()
MEAS.to_csv(out("measures_monthly.csv"), index_label="date")
MAC = macro_fixed()
FF3F = load_team()["ff3"]
END = {m: eval_end(MEAS[m]) for m in MEASURES}

runs = {}
for m, meta in MEASURES.items():
    for timing in TIMINGS:
        runs[(m, timing, "log1p")] = run_measure(MEAS[m], MAC, timing, meta["transform"])
for m in PRIMARY:  # robustness: level transform
    runs[(m, "realtime", "none")] = run_measure(MEAS[m], MAC, "realtime", "none")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    runs[("EMV_env", "team_baseline", "log1p")] = run_pipeline(**CHEAP)
print(f"  {len(runs)} cheap runs done in {time.perf_counter() - T0:.1f}s")
EPS = runs[("EMV_env", "realtime", "log1p")]["models"]["Brown leg"]["epsilon"]  # identical in every run (legs/factors fixed)
for k, r in runs.items():
    assert float((r["models"]["Brown leg"]["epsilon"] - EPS).abs().max()) == 0.0


def role_of(m, timing, transform):
    role = MEASURES[m]["role"]
    if timing == "team_baseline":
        return "reference"
    if transform != "log1p" or timing == "same_month" or role == "robustness":
        return "robustness"
    return {"team": "reference", "primary": "primary", "placebo": "placebo"}[role]


# ============================================================================ 2. signal availability
avail_rows = []
ez_same = runs[("EMV_env", "same_month", "log1p")]["signals"]["raw"]
for m in MEASURES:
    s = MEAS[m].dropna()
    st, en = native_range(s)
    for timing in TIMINGS:
        sig = runs[(m, timing, "log1p")]["signals"]
        row = {"measure": m, "label": MEASURES[m]["label"], "role": MEASURES[m]["role"], "timing": timing,
               "data_start": st.date(), "data_end": en.date(), "eval_end": END[m].date(),
               "first_z": sig["raw"].first_valid_index().date()}
        for key, nm in [("threshold_raw", "live_original"), ("threshold_pure", "live_pure"), ("w_raw", "live_cont_raw"),
                        ("w_pure", "live_cont_pure")]:
            ls = live_start(sig, key)
            row[nm] = ls.date()
            row[f"{nm}_months_in_validation"] = int(((sig[key].notna()) & (sig[key].index >= VAL[0] - ME) & (sig[key].index <= VAL[1] - ME)).sum())
        row["zero_share_validation"] = float((s.loc[VAL[0]:VAL[1]] == 0).mean())
        row["zero_share_holdout"] = float((s.loc[HOLD_START:min(en, SAMPLE_END)] == 0).mean())
        z = sig["raw"]
        zz = pd.concat([z, runs[("EMV_env", timing, "log1p")]["signals"]["raw"]], axis=1).loc["2010-01-31":en].dropna()
        row["corr_z_with_EMV_env_post2010"] = float(zz.corr().iloc[0, 1])
        avail_rows.append(row)
AVAIL = pd.DataFrame(avail_rows)
AVAIL.to_csv(out("signal_availability.csv"), index=False)
a = AVAIL[AVAIL.timing == "realtime"]
to_tex(pd.DataFrame({"Measure": a.label, "Data": a.data_start.astype(str).str[:7] + " to " + a.data_end.astype(str).str[:7],
                     "Eval. end": a.eval_end.astype(str).str[:7], "Original live": a.live_original.astype(str).str[:7],
                     "Pure live": a.live_pure.astype(str).str[:7], "Zeros val.": a.zero_share_validation.map(lambda x: f"{100*x:.0f}\\%"),
                     "Zeros hold.": a.zero_share_holdout.map(lambda x: f"{100*x:.0f}\\%"),
                     "Corr. z with EMV env.": a["corr_z_with_EMV_env_post2010"].map(lambda x: f"{x:.2f}")}),
       "signal_availability", "Attention measures and when the team machinery can trade them (real-time timing: first return month "
       "with a defined signal). Zeros: share of months with a value of exactly 0. Correlation of the rolling z-scores with EMV env., "
       "2010 onward.", "tab:m1b_availability", "lllllrrr", escape=False)

# ============================================================================ 3. long results table
LONG = []
IC_ROWS = []


def periods_for(m, sig, code):
    e = END[m]
    ls = live_start(sig, STRAT_LIVE_KEY[code])
    P = {"post2010": (VAL[0], e), "validation": VAL, "holdout": (HOLD_START, e),
         "holdout_to_2025-07": (HOLD_START, pd.Timestamp("2025-07-31")),
         "holdout_to_2025-10": (HOLD_START, pd.Timestamp("2025-10-31")),
         "pre_covid": (VAL[0], pd.Timestamp("2019-12-31")), "covid": COVID,
         "inflation_rates": (pd.Timestamp("2022-01-31"), pd.Timestamp("2024-12-31")),
         "last18": (pd.Timestamp("2025-02-28"), SAMPLE_END), "last12": (pd.Timestamp("2025-08-31"), SAMPLE_END),
         "full_live": (ls, e)}
    if ls > VAL[0]:
        P["validation_live"] = (ls, VAL[1])
    return P


IC_PERIODS = ("validation", "holdout", "covid", "post2010", "holdout_to_2025-07", "holdout_to_2025-10", "full_live")
for (m, timing, tr), res in runs.items():
    sig = res["signals"]
    for code, sname in STRATS.items():
        df = res["strategies"][sname]
        for per, (a_, b_) in periods_for(m, sig, code).items():
            available = b_ <= END[m]
            row = {"measure": m, "timing": timing, "transform": tr, "role": role_of(m, timing, tr), "strategy": code,
                   "strategy_name": sname, "period": per, "start": a_.date(), "end": b_.date(), "available": available}
            if available:
                st = window_stats(df, a_, b_, FF3F)
                row.update(st or {})
                if per in IC_PERIODS:
                    ic, t, n, p = ic_return_aligned(sig[STRAT_SIGNAL[code]], EPS, a_, b_)
                    row.update({"ic_signal": STRAT_SIGNAL[code], "ic": ic, "ic_t": t, "ic_n": n, "ic_p": p})
            LONG.append(row)
    # IC table (each signal once)
    for key in ("raw", "pure", "w_raw", "w_pure"):
        for per in ("validation", "holdout", "covid", "post2010", "holdout_to_2025-07", "holdout_to_2025-10"):
            a_, b_ = periods_for(m, sig, "O3")[per]
            if b_ > END[m]:
                continue
            ic, t, n, p = ic_return_aligned(sig[key], EPS, a_, b_)
            ic2, t2, n2 = ic_team_convention(sig[key], EPS, a_, b_)
            IC_ROWS.append({"measure": m, "timing": timing, "transform": tr, "role": role_of(m, timing, tr), "signal": key,
                            "signal_label": SIGNAL_LABEL[key], "period": per, "start": a_.date(), "end": b_.date(),
                            "ic": ic, "ic_t": t, "ic_n": n, "ic_p": p, "ic_team_convention": ic2, "ic_t_team_convention": t2,
                            "ic_n_team_convention": n2})
LONG = pd.DataFrame(LONG)
ICT = pd.DataFrame(IC_ROWS)
# benchmark (signal-free) for context
bench = runs[("EMV_env", "realtime", "log1p")]["strategies"]["Benchmark | Always-short Brown"]
brow = []
for per, (a_, b_) in {"post2010": (VAL[0], SAMPLE_END), "validation": VAL, "holdout": (HOLD_START, SAMPLE_END),
                      "holdout_to_2025-07": (HOLD_START, pd.Timestamp("2025-07-31")),
                      "holdout_to_2025-10": (HOLD_START, pd.Timestamp("2025-10-31")), "covid": COVID,
                      "last18": (pd.Timestamp("2025-02-28"), SAMPLE_END), "last12": (pd.Timestamp("2025-08-31"), SAMPLE_END)}.items():
    brow.append({"measure": "none", "timing": "-", "transform": "-", "role": "reference", "strategy": "AS",
                 "strategy_name": "Benchmark | Always-short Brown", "period": per, "start": a_.date(), "end": b_.date(),
                 "available": True, **window_stats(bench, a_, b_, FF3F)})
LONG = pd.concat([LONG, pd.DataFrame(brow)], ignore_index=True)
LONG.to_csv(out("results_long.csv"), index=False)
ICT.to_csv(out("ic.csv"), index=False)
print(f"  long table {LONG.shape}, IC table {ICT.shape}")


def get(m, timing, code, per, tr="log1p"):
    x = LONG[(LONG.measure == m) & (LONG.timing == timing) & (LONG.strategy == code) & (LONG.period == per) & (LONG['transform'] == tr)]
    return x.iloc[0] if len(x) else None


def get_ic(m, timing, key, per, tr="log1p"):
    x = ICT[(ICT.measure == m) & (ICT.timing == timing) & (ICT.signal == key) & (ICT.period == per) & (ICT['transform'] == tr)]
    return x.iloc[0] if len(x) else None


def get_bench(per):
    return LONG[(LONG.measure == "none") & (LONG.period == per)].iloc[0]


# ============================================================================ 4. primary family (Q1)
prim = []
for m in PRIMARY:
    for code in STRATS:
        for per in ("validation", "holdout"):
            r = get(m, "realtime", code, per)
            prim.append({"test_id": f"Q1_{m}_realtime_{code}_{per}_alpha", "measure": m, "kind": "FF3 alpha", "strategy": code,
                         "signal": STRAT_SIGNAL[code], "period": per, "start": r.start, "end": r.end, "n": int(r.n_months),
                         "estimate": r.alpha_ann, "t": r.alpha_t_hac6, "p": r.p_alpha, "ann_net": r.ann_net, "sharpe": r.sharpe_net})
    for key in ("raw", "pure", "w_raw", "w_pure"):
        for per in ("validation", "holdout"):
            r = get_ic(m, "realtime", key, per)
            prim.append({"test_id": f"Q1_{m}_realtime_{key}_{per}_IC", "measure": m, "kind": "IC", "strategy": "",
                         "signal": key, "period": per, "start": r.start, "end": r.end, "n": int(r.ic_n),
                         "estimate": r.ic, "t": r.ic_t, "p": r.ic_p})
PRIM = pd.DataFrame(prim)
PRIM["holm_p"] = holm(PRIM["p"]).values
PRIM["bh_p"] = bh(PRIM["p"]).values
# EMV_env reference rows (same statistics, corrected baseline) for side-by-side comparison
ref = []
for code in STRATS:
    for per in ("validation", "holdout", "holdout_to_2025-07", "holdout_to_2025-10"):
        r = get("EMV_env", "realtime", code, per)
        ref.append({"test_id": f"REF_EMV_env_realtime_{code}_{per}_alpha", "measure": "EMV_env", "kind": "FF3 alpha", "strategy": code,
                    "signal": STRAT_SIGNAL[code], "period": per, "start": r.start, "end": r.end, "n": int(r.n_months),
                    "estimate": r.alpha_ann, "t": r.alpha_t_hac6, "p": r.p_alpha, "ann_net": r.ann_net, "sharpe": r.sharpe_net})
for key in ("raw", "pure", "w_raw", "w_pure"):
    for per in ("validation", "holdout", "holdout_to_2025-07", "holdout_to_2025-10"):
        r = get_ic("EMV_env", "realtime", key, per)
        ref.append({"test_id": f"REF_EMV_env_realtime_{key}_{per}_IC", "measure": "EMV_env", "kind": "IC", "strategy": "", "signal": key,
                    "period": per, "start": r.start, "end": r.end, "n": int(r.ic_n), "estimate": r.ic, "t": r.ic_t, "p": r.ic_p})
PRIM_ALL = pd.concat([PRIM.assign(family="primary"), pd.DataFrame(ref).assign(family="reference")], ignore_index=True)
PRIM_ALL.to_csv(out("primary.csv"), index=False)

changes = PRIM[(PRIM.kind == "FF3 alpha") & (PRIM.period == "holdout") & (PRIM.estimate > 0) & (PRIM.holm_p < 0.05)]
DECISION_Q1 = "changes" if len(changes) else "unchanged"
print(f"Q1 decision: result {DECISION_Q1}; min Holm p in family = {PRIM.holm_p.min():.3f}")

# primary tex: strategies x measures, validation and holdout alpha (t)
rows = []
for code in STRATS:
    row = {"Strategy": STRAT_LABEL[code]}
    for m in ("EMV_env", "MCCC", "CPU"):
        for per, lab in (("validation", "Val."), ("holdout", "Hold.")):
            r = get(m, "realtime", code, per)
            row[f"{SHORT[m]} {lab}"] = f"{pct(r.alpha_ann)} ({f2(r.alpha_t_hac6)})"
    rows.append(row)
for key in ("raw", "pure", "w_raw", "w_pure"):
    row = {"Strategy": f"IC: {SIGNAL_LABEL[key].lower()}"}
    for m in ("EMV_env", "MCCC", "CPU"):
        for per, lab in (("validation", "Val."), ("holdout", "Hold.")):
            r = get_ic(m, "realtime", key, per)
            row[f"{SHORT[m]} {lab}"] = f"{f2(r.ic)} ({f2(r.ic_t)})"
    rows.append(row)
hold_note = (f"Holdout ends {END['MCCC']:%Y-%m} for MCCC ({int(get('MCCC','realtime','O3','holdout').n_months)} months) and "
             f"{END['CPU']:%Y-%m} for CPU ({int(get('CPU','realtime','O3','holdout').n_months)} months); 2026-07 for EMV env. (48 months).")
to_tex(pd.DataFrame(rows), "primary", "Primary test: team machinery fed a climate-concern measure, corrected-baseline timing "
       "(inputs lagged one month, CPI gap interpolated). FF3 alpha in \\% per year with NW(6) t in parentheses; IC is the slope of "
       "$z(\\varepsilon_{t+1})$ on $z(\\text{signal}_t)$ (negative favors Short-Brown). " + hold_note +
       f" Smallest Holm-adjusted p across the 40 primary tests: {PRIM.holm_p.min():.2f}.", "tab:m1b_primary",
       "l" + "r" * 6, escape=False)

# ============================================================================ 5. placebo family (Q2) and COVID comparison
plc, plc_tests = [], []
for timing in TIMINGS:
    for code, sname in STRATS.items():
        e = get("EMV_env", timing, code, "covid")
        for m in ("EMV_env", "VIX", "EMV_overall", "MCCC", "CPU", "EMV_env_share", "MCCC_transition"):
            r = get(m, timing, code, "covid")
            row = {"timing": timing, "strategy": code, "measure": m, "n": int(r.n_months), "ann_net": r.ann_net,
                   "sharpe": r.sharpe_net, "alpha_ann": r.alpha_ann, "t": r.alpha_t_hac6, "p": r.p_alpha,
                   "months_held": r.months_held, "ratio_to_EMV_env": r.alpha_ann / e.alpha_ann if e.alpha_ann else np.nan}
            if m != "EMV_env":
                d = paired_alpha(runs[("EMV_env", timing, "log1p")]["strategies"][sname]["net_return"],
                                 runs[(m, timing, "log1p")]["strategies"][sname]["net_return"], *COVID, FF3F)
                row.update({f"emv_minus_{k}" if not k.startswith("diff") else k.replace("diff", "emv_minus_measure"): v
                            for k, v in d.items() if k != "n"})
                row["reproduces"] = bool(r.alpha_ann > 0 and r.alpha_ann >= 0.5 * e.alpha_ann) if e.alpha_ann > 0 else np.nan
            plc.append(row)
PLC = pd.DataFrame(plc)
# supporting: Holm within the 12 real-time paired tests (EMV_env minus each volatility placebo, 6 strategies)
fam = (PLC.timing == "realtime") & PLC.measure.isin(PLACEBO)
PLC["holm_p_paired_placebo_family"] = np.nan
PLC.loc[fam, "holm_p_paired_placebo_family"] = holm(PLC.loc[fam, "emv_minus_measure_p"]).values
PLC.to_csv(out("placebo_covid.csv"), index=False)
rep = (PLC[(PLC.timing == "realtime") & PLC.measure.isin(PLACEBO)].groupby("measure")["reproduces"].sum().astype(int))
rep_same = (PLC[(PLC.timing == "same_month") & PLC.measure.isin(PLACEBO)].groupby("measure")["reproduces"].sum().astype(int))
DECISION_Q2 = "fails" if (rep >= 4).any() else "survives"
print(f"Q2: placebo reproduces COVID gain in (realtime) {rep.to_dict()} of 6 strategies; same-month {rep_same.to_dict()}; "
      f"climate interpretation {DECISION_Q2}")

# placebo tex
rows = []
for timing, tlab in (("realtime", "Real-time timing (primary)"), ("same_month", "Team timing (same month)")):
    rows.append({"Strategy": f"\\textit{{{tlab}}}", **{c: "" for c in ["EMV env.", "VIX", "EMV overall", "MCCC", "CPU",
                                                                          "EMV env. $-$ VIX", "EMV env. $-$ EMV overall"]}})
    for code in STRATS:
        g = lambda m: PLC[(PLC.timing == timing) & (PLC.strategy == code) & (PLC.measure == m)].iloc[0]  # noqa: E731
        row = {"Strategy": STRAT_LABEL[code]}
        for m in ("EMV_env", "VIX", "EMV_overall", "MCCC", "CPU"):
            x = g(m)
            row[SHORT[m]] = f"{pct(x.alpha_ann)} ({f2(x.t)})"
        for m in PLACEBO:
            x = g(m)
            row[f"EMV env. $-$ {SHORT[m]}"] = f"{pct(x.emv_minus_measure_alpha_ann)} ({f2(x.emv_minus_measure_t)})"
        rows.append(row)
to_tex(pd.DataFrame(rows), "placebo_covid", "COVID window (2020-01 to 2021-12, 24 months): FF3 alpha in \\% per year (NW(6) t) of "
       "the team strategies fed each measure; the last two columns are the FF3 alpha of the return difference between the EMV env. "
       "strategy and the volatility placebo. With 24 observations, $|t| > 2.09$ is needed for p < 0.05 under t(20). "
       f"Pre-specified rule: a placebo reproduces the gain when its alpha is positive and at least half the EMV env. alpha; "
       f"real-time timing: VIX {rep.get('VIX', 0)} of 6, EMV overall {rep.get('EMV_overall', 0)} of 6; team timing: VIX "
       f"{rep_same.get('VIX', 0)} of 6, EMV overall {rep_same.get('EMV_overall', 0)} of 6. For reference, the signal-free "
       f"always-short-Brown benchmark earns {pct(get_bench('covid').alpha_ann)}\\% (t = {f2(get_bench('covid').alpha_t_hac6)}) "
       "in the same window.", "tab:m1b_placebo_covid", "l" + "r" * 7, escape=False)

# ---- exploratory: how much of each COVID gain is the March-April 2020 Brown-residual crash?
CRASH = pd.to_datetime(["2020-03-31", "2020-04-30"])
dec = []
eps_c = EPS.loc[COVID[0]:COVID[1]]
for timing in TIMINGS:
    for m in ORDER_COVID:
        for code, sname in STRATS.items():
            df = runs[(m, timing, "log1p")]["strategies"][sname]
            net = df["net_return"].loc[COVID[0]:COVID[1]]
            ex = df.drop(CRASH)
            st = window_stats(ex, *COVID, FF3F)
            held_c = df["position"].shift(1).loc[CRASH] != 0
            # paired FF3 alpha of (strategy - signal-free always-short Brown), full COVID window and excluding Mar-Apr 2020
            pb = paired_alpha(df["net_return"], bench["net_return"], *COVID, FF3F)
            pbx = paired_alpha(df["net_return"].drop(CRASH), bench["net_return"].drop(CRASH), *COVID, FF3F)
            dec.append({"timing": timing, "measure": m, "strategy": code, "covid_sum_net": float(net.sum()),
                        "mar_apr_2020_net": float(net.loc[CRASH].sum()), "share_mar_apr": float(net.loc[CRASH].sum() / net.sum()) if net.sum() else np.nan,
                        "months_held_mar_apr": int(held_c.sum()),
                        "held_mar_apr": ", ".join(d.strftime("%Y-%m") for d in CRASH[held_c.to_numpy()]),
                        "alpha_ex_mar_apr": st["alpha_ann"], "t_ex_mar_apr": st["alpha_t_hac6"], "p_ex_mar_apr": st["p_alpha"],
                        "n_ex": st["n_months"],
                        "minus_bench_alpha_covid": pb["diff_alpha_ann"], "minus_bench_t_covid": pb["diff_t"],
                        "minus_bench_p_covid": pb["diff_p"],
                        "minus_bench_alpha_ex_mar_apr": pbx["diff_alpha_ann"], "minus_bench_t_ex_mar_apr": pbx["diff_t"],
                        "minus_bench_p_ex_mar_apr": pbx["diff_p"]})
    bdf = bench.drop(CRASH)
    st = window_stats(bdf, *COVID, FF3F)
    bn = bench["net_return"].loc[COVID[0]:COVID[1]]
    dec.append({"timing": timing, "measure": "none (always-short Brown)", "strategy": "AS", "covid_sum_net": float(bn.sum()),
                "mar_apr_2020_net": float(bn.loc[CRASH].sum()), "share_mar_apr": float(bn.loc[CRASH].sum() / bn.sum()),
                "months_held_mar_apr": 2, "held_mar_apr": "2020-03, 2020-04",
                "alpha_ex_mar_apr": st["alpha_ann"], "t_ex_mar_apr": st["alpha_t_hac6"],
                "p_ex_mar_apr": st["p_alpha"], "n_ex": st["n_months"]})
DEC = pd.DataFrame(dec)
DEC.to_csv(out("covid_decomposition.csv"), index=False)
BROWN_EPS_CRASH = {d.strftime("%Y-%m"): float(eps_c.loc[d]) for d in CRASH}
# report table: Original 3m COVID attribution under both timings (exploratory)
rows = []
for timing, tlab in (("realtime", "Real-time timing (primary)"), ("same_month", "Team timing (same month)")):
    rows.append({"Measure": f"\\textit{{{tlab}}}", **{c: "" for c in ["COVID $\\alpha$ ($t$)", "Ratio to EMV env.",
                                                                     "Mar-Apr 2020 held", "Mar-Apr share of net",
                                                                     "$\\alpha$ ex Mar-Apr ($t$)"]}})
    for m in ("EMV_env", "CPU", "MCCC", "VIX", "EMV_overall", "none (always-short Brown)"):
        x = DEC[(DEC.timing == timing) & (DEC.measure == m)].iloc[0] if m.startswith("none") else \
            DEC[(DEC.timing == timing) & (DEC.measure == m) & (DEC.strategy == "O3")].iloc[0]
        if m.startswith("none"):
            b_ = get_bench("covid")
            a_c, t_c, ratio = b_.alpha_ann, b_.alpha_t_hac6, b_.alpha_ann / get("EMV_env", timing, "O3", "covid").alpha_ann
        else:
            p_ = PLC[(PLC.timing == timing) & (PLC.measure == m) & (PLC.strategy == "O3")].iloc[0]
            a_c, t_c, ratio = p_.alpha_ann, p_.t, p_.ratio_to_EMV_env
        rows.append({"Measure": SHORT.get(m, "Always-short Brown (no signal)"), "COVID $\\alpha$ ($t$)": f"{pct(a_c)} ({f2(t_c)})",
                     "Ratio to EMV env.": f2(ratio), "Mar-Apr 2020 held": x.held_mar_apr.replace("2020-", "").replace("03", "Mar").replace("04", "Apr") or "none",
                     "Mar-Apr share of net": f"{100 * x.share_mar_apr:.0f}\\%",
                     "$\\alpha$ ex Mar-Apr ($t$)": f"{pct(x.alpha_ex_mar_apr)} ({f2(x.t_ex_mar_apr)})"})
to_tex(pd.DataFrame(rows), "covid_attribution", "Exploratory: Original 3m in the COVID window (2020-01 to 2021-12). FF3 alpha in \\% "
       "per year (NW(6) $t$; $|t| > 2.09$ for p < 0.05 under t(20)); ratio of the alpha to the EMV env. alpha under the same "
       "timing; which of March and April 2020 the rule was short in; their share of the summed COVID net return; FF3 alpha "
       "re-estimated without those two months (22 observations). The always-short row holds the position in every month.",
       "tab:m1b_covid_attribution", "lrrlrr", escape=False)

# ============================================================================ 6. alpha grid and compact comparison
for timing in TIMINGS:
    rows, csv_rows = [], []
    for per, plab in (("validation", "Validation 2010-01 to 2022-07"), ("holdout", "Holdout 2022-08 onward (as available)"),
                      ("covid", "COVID 2020-01 to 2021-12")):
        rows.append({"Measure": f"\\textit{{{plab}}}", **{STRAT_LABEL[c]: "" for c in STRATS}})
        for m in ORDER:
            row = {"Measure": MEASURES[m]["label"] + (f" (to {END[m]:%Y-%m})" if per == "holdout" and END[m] < SAMPLE_END else "")}
            for c in STRATS:
                r = get(m, timing, c, per)
                row[STRAT_LABEL[c]] = f"{pct(r.alpha_ann)} ({f2(r.alpha_t_hac6)})"
                csv_rows.append({"timing": timing, "period": per, "measure": m, "strategy": c, "n": r.n_months,
                                 "alpha_ann": r.alpha_ann, "t": r.alpha_t_hac6, "p": r.p_alpha})
            rows.append(row)
    pd.DataFrame(csv_rows).to_csv(out(f"alpha_grid_{timing}.csv"), index=False)
    tl = "corrected-baseline timing (inputs lagged one month)" if timing == "realtime" else "team timing (same-month attention)"
    to_tex(pd.DataFrame(rows), f"alpha_grid_{timing}", f"FF3 alpha in \\% per year (NW(6) t) of the six team strategies by attention "
           f"measure, {tl}, CPI gap interpolated.", f"tab:m1b_alpha_grid_{timing}", "l" + "r" * 6, escape=False)

comp = []
for m in ORDER:
    for code in STRATS:
        for per in ("validation", "holdout", "covid", "post2010", "last18", "last12"):
            r = get(m, "realtime", code, per)
            comp.append({"measure": m, "strategy": code, "period": per, "start": r.start, "end": r.end, "available": r.available,
                         "n": r.get("n_months"), "ann_net": r.get("ann_net"), "sharpe": r.get("sharpe_net"),
                         "alpha_ann": r.get("alpha_ann"), "t": r.get("alpha_t_hac6"), "p": r.get("p_alpha"),
                         "annual_turnover": r.get("annual_turnover"), "ann_cost_drag": r.get("ann_cost_drag"),
                         "ic_signal": STRAT_SIGNAL[code], "ic": r.get("ic"), "ic_t": r.get("ic_t")})
COMP = pd.DataFrame(comp)
COMP.to_csv(out("compact.csv"), index=False)
rows = []
for m in ORDER:
    for per, plab in (("validation", "Val."), ("holdout", "Hold."), ("covid", "COVID")):
        row = {"Measure": SHORT[m] if per == "validation" else "", "Period": plab + (f" to {END[m]:%y-%m}" if per == "holdout" and END[m] < SAMPLE_END else "")}
        for code in ("O3", "CR"):
            x = COMP[(COMP.measure == m) & (COMP.strategy == code) & (COMP.period == per)].iloc[0]
            lab = "O3" if code == "O3" else "CR"
            row[f"{lab} net"] = pct(x.ann_net)
            row[f"{lab} SR"] = f2(x.sharpe)
            row[f"{lab} $\\alpha$"] = pct(x.alpha_ann)
            row[f"{lab} $t$"] = f2(x.t)
            row[f"{lab} IC"] = f2(x.ic)
        rows.append(row)
to_tex(pd.DataFrame(rows), "compact", "Compact comparison, corrected-baseline timing: Original 3m (O3) and Continuous raw (CR), the "
       "team's two COVID Holm survivors. Net return and FF3 alpha in \\% per year, Sharpe net, NW(6) $t$ of alpha, IC of the matching "
       "signal (raw z for O3, continuous weight for CR; negative favors Short-Brown). All six strategies and more windows in "
       "M1b\\_alt\\_signals\\_compact.csv.", "tab:m1b_compact", "ll" + "r" * 10, escape=False)

# ---- recent windows (brief: last 12 and 18 months), real-time timing; only measures that drive returns through 2026-07
REC_WIN = {"last18": "Last 18 months (2025-02 to 2026-07)", "last12": "Last 12 months (2025-08 to 2026-07)"}
REC_MEAS = [m for m in ORDER if END[m] >= SAMPLE_END]
rec = []
for per in REC_WIN:
    for m in REC_MEAS:
        for code in STRATS:
            r = get(m, "realtime", code, per)
            rec.append({"measure": m, "strategy": code, "period": per, "start": r.start, "end": r.end, "n": int(r.n_months),
                        "ann_net": r.ann_net, "sharpe": r.sharpe_net, "alpha_ann": r.alpha_ann, "t": r.alpha_t_hac6, "p": r.p_alpha,
                        "months_held": r.months_held, "annual_turnover": r.annual_turnover, "ann_cost_drag": r.ann_cost_drag})
    b_ = get_bench(per)
    rec.append({"measure": "none (always-short Brown)", "strategy": "AS", "period": per, "start": b_.start, "end": b_.end,
                "n": int(b_.n_months), "ann_net": b_.ann_net, "sharpe": b_.sharpe_net, "alpha_ann": b_.alpha_ann, "t": b_.alpha_t_hac6,
                "p": b_.p_alpha, "months_held": b_.months_held, "annual_turnover": b_.annual_turnover, "ann_cost_drag": b_.ann_cost_drag})
REC = pd.DataFrame(rec)
REC.to_csv(out("recent.csv"), index=False)
rows = []
for per, plab in REC_WIN.items():
    rows.append({"Measure": f"\\textit{{{plab}}}", **{c: "" for c in ["O3 net", "O3 $\\alpha$ ($t$)", "O6 net", "O6 $\\alpha$ ($t$)",
                                                                       "CR net", "CR $\\alpha$ ($t$)"]}})
    for m in REC_MEAS + ["none (always-short Brown)"]:
        row = {"Measure": SHORT.get(m, "Always-short Brown (no signal)")}
        for code in ("O3", "O6", "CR"):
            x = REC[(REC.measure == m) & (REC.period == per) & (REC.strategy == (code if m in REC_MEAS else "AS"))].iloc[0]
            row[f"{code} net"] = pct(x.ann_net)
            row[f"{code} $\\alpha$ ($t$)"] = f"{pct(x.alpha_ann)} ({f2(x.t)})"
        rows.append(row)
to_tex(pd.DataFrame(rows), "recent", "Recent windows, corrected-baseline timing: annualized net return and FF3 alpha in \\% "
       "(NW(6) $t$) for Original 3m (O3), Original 6m (O6) and Continuous raw (CR). The always-short row repeats the same "
       "signal-free position in every column. p < 0.05 under t(n-4) needs $|t| > 2.14$ with 18 observations and $|t| > 2.31$ "
       "with 12. MCCC and "
       "CPU end before these windows. All six strategies in M1b\\_alt\\_signals\\_recent.csv.", "tab:m1b_recent", "l" + "r" * 6,
       escape=False)

# ============================================================================ 7. crossings and overlap
ev, cs = [], []
team_x = crossings(runs[("EMV_env", "same_month", "log1p")]["signals"], "cross_raw", "2010-01-31")
team_xp = crossings(runs[("EMV_env", "same_month", "log1p")]["signals"], "cross_pure", "2010-01-31")
team_hold = runs[("EMV_env", "same_month", "log1p")]["signals"]["hold_raw"][3]
for m in ORDER:
    sig = runs[(m, "same_month", "log1p")]["signals"]
    dend = native_range(MEAS[m])[1]
    dend = min(dend, SAMPLE_END)
    for key, tref in (("cross_raw", team_x), ("cross_pure", team_xp)):
        x = crossings(sig, key, "2010-01-31", dend)
        tr_ = tref[tref <= dend]
        ex = np.isin(x, tr_)
        pm1 = within(x, tr_, 1)
        for d, a1, a2 in zip(x, ex, pm1):
            ev.append({"measure": m, "signal": key.replace("cross_", ""), "data_month": d.date(),
                       "trade_month_same_month": d.date(), "trade_month_realtime": (d + ME).date(),
                       "same_month_as_EMV_env": bool(a1), "within_1m_of_EMV_env": bool(a2)})
        if key == "cross_raw":
            grid = pd.date_range("2010-01-31", dend, freq="ME")
            months = len(grid)
            # exact chance coverage: share of window months that lie within +/-1 month of a team crossing (team crossings are
            # never adjacent and the window has edges, so the approximation 1-(1-p)^3 understates it)
            cover = within(grid, tr_, 1)
            share = float(cover.mean())
            k_obs, n_x = int(pm1.sum()), len(x)
            # circular-shift permutation: rotate this measure's crossing months around the window, keep the team's fixed
            xi = np.searchsorted(grid, x)
            cov_i = cover.astype(bool)
            perm = np.array([cov_i[(xi + s) % months].sum() for s in range(1, months)])
            hm = sig["hold_raw"][3].loc["2010-01-31":dend]
            th = team_hold.loc["2010-01-31":dend]
            jac = float((hm & th).sum() / max((hm | th).sum(), 1))
            val_n = int(((x >= VAL[0]) & (x <= VAL[1])).sum())
            cs.append({"measure": m, "window": f"2010-01 to {dend:%Y-%m}", "months": months, "n_cross_raw": n_x,
                       "n_cross_validation": val_n, "n_cross_holdout": int((x >= HOLD_START).sum()),
                       "n_cross_covid": int(((x >= COVID[0]) & (x <= COVID[1])).sum()),
                       "n_cross_pure": len(crossings(sig, "cross_pure", "2010-01-31", dend)),
                       "n_team_cross_same_window": len(tr_), "overlap_exact": int(ex.sum()), "overlap_pm1": k_obs,
                       "share_overlap_pm1": float(pm1.mean()) if n_x else np.nan,
                       "coverage_share_pm1": share,
                       "expected_overlap_pm1_if_independent": n_x * share,
                       "p_one_sided_binomial": float(binom.sf(k_obs - 1, n_x, share)),
                       "p_two_sided_binomial": float(binomtest(k_obs, n_x, share).pvalue),
                       "expected_overlap_pm1_circular_shift": float(perm.mean()),
                       "p_one_sided_circular_shift": float((perm >= k_obs).mean()),
                       "p_two_sided_circular_shift": float(min(1.0, 2 * min((perm >= k_obs).mean(), (perm <= k_obs).mean()))),
                       "jaccard_hold3_months": jac,
                       "covid_crossings": ", ".join(d.strftime("%Y-%m") for d in x if COVID[0] - 2 * ME <= d <= COVID[1])})
EV = pd.DataFrame(ev)
CS = pd.DataFrame(cs)
EV.to_csv(out("crossings_events.csv"), index=False)
CS.to_csv(out("crossings.csv"), index=False)
to_tex(pd.DataFrame({"Measure": CS.measure.map(lambda m: MEASURES[m]["label"]), "Window": CS.window, "Crossings": CS.n_cross_raw,
                     "Val.": CS.n_cross_validation, "Hold.": CS.n_cross_holdout, "COVID": CS.n_cross_covid,
                     "Exact": CS.overlap_exact, "$\\pm$1m": CS.overlap_pm1,
                     "Chance $\\pm$1m": CS.expected_overlap_pm1_if_independent.map(lambda x: f"{x:.1f}"),
                     "p": [("" if m == "EMV_env" else f"{v:.2f}") for m, v in zip(CS.measure, CS.p_one_sided_binomial)],
                     "Jaccard": CS.jaccard_hold3_months.map(lambda x: f"{x:.2f}"),
                     "Crossings 2019-11 to 2021-12": CS.covid_crossings}),
       "crossings", "Extreme-attention crossings (raw z above its expanding past-only 80th percentile after being below it), dated by "
       "the data month; under real-time timing each trade happens one month later. Exact and $\\pm$1m: crossings in the same month as, "
       "or within one month of, a team EMV env. crossing in the same window. Chance: expected $\\pm$1m matches if the measure's "
       "crossings fell on random months, using the exact share of window months within one month of a team crossing "
       f"({CS.coverage_share_pm1.min():.3f} to {CS.coverage_share_pm1.max():.3f}); "
       "p: one-sided binomial p of at least the observed overlap. Jaccard: overlap of the 3-month hold months with the team's. MCCC can "
       "first cross in 2011 (signal undefined before).", "tab:m1b_crossings", "ll" + "r" * 9 + "p{3.2cm}", escape=False)

# ============================================================================ 8. full-mode primary rows and bootstrap
full_rows, paired_rows, boot_rows = [], [], []
for m in ("EMV_env",) + PRIMARY + PLACEBO:
    res = run_measure(MEAS[m], MAC, "realtime", "log1p", mode="full", full_end=END[m])
    ct = res["comparison_table"].copy()
    # The pipeline's 'significant_after_multiple_testing' is a normal-p Holm over 24-month COVID NW(6) t-stats placed in a
    # full-sample row (audit items 3 and 8), and 'active_months_full' counts exit-cost months as active (audit item 6).
    # Neither is valid here: drop both and report the months with a position actually held.
    ct = ct.drop(columns=["significant_after_multiple_testing", "active_months_full"])
    def _held_months(s):
        d = res["strategies"][s]
        if "position" not in d:  # buy-and-hold Green-Brown: invested every month with a return
            return int(d["net_return"].loc[VAL[0]:END[m]].notna().sum())
        return int((d["position"].shift(1).loc[VAL[0]:END[m]].fillna(0) != 0).sum())
    ct.insert(1, "months_held_full", [_held_months(s) for s in ct.strategy])
    ct.insert(0, "measure", m)
    ct.insert(1, "window", f"2010-01 to {END[m]:%Y-%m}")
    full_rows.append(ct)
    pt_ = res["paired_table"].copy()
    pt_.insert(0, "measure", m)
    pt_.insert(1, "window", f"{HOLD_START:%Y-%m} to {END[m]:%Y-%m}")
    paired_rows.append(pt_)
    for code, sname in STRATS.items():
        for per, (a_, b_) in (("validation", VAL), ("holdout", (HOLD_START, END[m]))):
            bt = circular_block_bootstrap(res["strategies"][sname]["net_return"].loc[a_:b_], block=12, reps=5000, seed=230)
            boot_rows.append({"measure": m, "strategy": code, "period": per, "start": a_.date(), "end": b_.date(),
                              "n": int(res["strategies"][sname]["net_return"].loc[a_:b_].notna().sum()), **bt.to_dict()})
    # consistency: full-mode strategies identical to cheap-mode ones
    for sname in STRATS.values():
        assert float((res["strategies"][sname]["net_return"] - runs[(m, "realtime", "log1p")]["strategies"][sname]["net_return"]).abs().max()) == 0.0
FULLCMP = pd.concat(full_rows, ignore_index=True)
FULLPAIR = pd.concat(paired_rows, ignore_index=True)
FULLCMP.to_csv(out("full_mode_comparison.csv"), index=False)
FULLPAIR.to_csv(out("full_mode_paired.csv"), index=False)
BOOT = pd.DataFrame(boot_rows)
BOOT.to_csv(out("bootstrap.csv"), index=False)
print(f"  full-mode runs done at {time.perf_counter() - T0:.1f}s")

# ============================================================================ 9. tests ledger
L = []


def add(test_id, question, stat_name, stat, p, n, kind, note):
    L.append({"test_id": test_id, "module": MODULE, "question": question, "statistic_name": stat_name, "statistic": stat,
              "p_value_two_sided": p, "n_obs": n, "primary_or_exploratory": kind, "note": note})


Q1 = "Q1: does a climate-concern measure change the team result?"
Q2 = "Q2: does a volatility placebo reproduce the COVID gain?"
for _, r in PRIM.iterrows():
    add(r.test_id, Q1, f"{r.kind} {'NW(6) t' if r.kind == 'FF3 alpha' else 'IC NW(6) t'} ({r.strategy or r.signal}, {r.period})",
        r.t, r.p, r.n, "primary", f"estimate={r.estimate:.5f}; window {r.start} to {r.end}; Holm p={r.holm_p:.4f}; BH p={r.bh_p:.4f}")
for _, r in LONG[LONG.available & LONG.alpha_t_hac6.notna()].iterrows():
    if r.measure == "none":
        kind = "reference"
    elif r.role == "primary" and r.period in ("validation", "holdout"):
        continue  # already in the primary family
    elif r.role == "placebo" and r.period in ("validation", "holdout", "covid"):
        kind = "placebo"
    elif r.role == "reference" and r.period in ("validation", "holdout", "covid"):
        kind = "reference"
    elif r.role == "robustness" or r.period in ("holdout_to_2025-07", "holdout_to_2025-10", "validation_live"):
        kind = "robustness"
    else:
        kind = "exploratory"
    q = Q2 if r.period == "covid" else Q1
    add(f"{r.measure}_{r.timing}_{r['transform']}_{r.strategy}_{r.period}_alpha", q, f"FF3 alpha NW(6) t ({r.strategy}, {r.period})",
        r.alpha_t_hac6, r.p_alpha, int(r.n_months), kind, f"alpha_ann={r.alpha_ann:.5f}; window {r.start} to {r.end}")
for _, r in ICT.iterrows():
    if r.role == "primary" and r['transform'] == "log1p" and r.timing == "realtime" and r.period in ("validation", "holdout"):
        continue
    if r.role == "placebo" and r.period in ("validation", "holdout"):
        kind = "placebo"
    elif r.role == "reference" and r.period in ("validation", "holdout"):
        kind = "reference"
    elif r.role == "robustness" or r.period.startswith("holdout_to"):
        kind = "robustness"
    else:
        kind = "exploratory"
    add(f"{r.measure}_{r.timing}_{r['transform']}_{r.signal}_{r.period}_IC", Q1, f"IC NW(6) t ({r.signal}, {r.period})", r.ic_t, r.ic_p,
        int(r.ic_n), kind, f"IC={r.ic:.4f}; return months {r.start} to {r.end}")
for _, r in PLC[PLC.measure != "EMV_env"].iterrows():
    kind = "placebo" if (r.measure in PLACEBO and r.timing == "realtime") else ("robustness" if r.measure in PLACEBO else "exploratory")
    add(f"Q2_{r.timing}_{r.strategy}_EMV_env_minus_{r.measure}_covid_alpha", Q2,
        f"FF3 alpha NW(6) t of r(EMV_env) - r({r.measure}), COVID", r.emv_minus_measure_t, r.emv_minus_measure_p, 24, kind,
        f"diff alpha_ann={r.emv_minus_measure_alpha_ann:.5f}; placebo alpha/EMV_env alpha={r.ratio_to_EMV_env:.3f}; reproduces={r.reproduces}"
        + (f"; Holm p within 12 real-time paired placebo tests={r.holm_p_paired_placebo_family:.4f}" if np.isfinite(r.holm_p_paired_placebo_family) else ""))
for _, r in CS[CS.measure != "EMV_env"].iterrows():
    add(f"CROSS_{r.measure}_overlap_pm1", Q1, "crossings within 1 month of an EMV_env crossing (exact binomial test, two-sided)",
        r.overlap_pm1, r.p_two_sided_binomial, int(r.n_cross_raw), "exploratory",
        f"expected if independent={r.expected_overlap_pm1_if_independent:.2f} (exact coverage share {r.coverage_share_pm1:.3f}); "
        f"one-sided upper p={r.p_one_sided_binomial:.4f}; window {r.window}")
    add(f"CROSSPERM_{r.measure}_overlap_pm1", Q1, "crossings within 1 month of an EMV_env crossing (circular-shift permutation, two-sided)",
        r.overlap_pm1, r.p_two_sided_circular_shift, int(r.n_cross_raw), "exploratory",
        f"mean overlap under {int(r.months) - 1} circular shifts={r.expected_overlap_pm1_circular_shift:.2f}; "
        f"one-sided upper p={r.p_one_sided_circular_shift:.4f}; window {r.window}")
for _, r in DEC.iterrows():
    add(f"COVIDX_{r.timing}_{r.measure.split(' ')[0]}_{r.strategy}_alpha_ex_mar_apr_2020", Q2,
        f"FF3 alpha NW(6) t, COVID window excluding 2020-03 and 2020-04 ({r.strategy})", r.t_ex_mar_apr, r.p_ex_mar_apr,
        int(r.n_ex), "exploratory", f"alpha_ann={r.alpha_ex_mar_apr:.5f}; Mar-Apr 2020 share of COVID net={r.share_mar_apr:.3f}")
    if r.strategy != "AS":  # paired: strategy minus the signal-free always-short Brown position (does the timing add anything?)
        for suff, lab, n_ in (("covid", "COVID window", 24), ("ex_mar_apr", "COVID window excluding 2020-03 and 2020-04", 22)):
            t_, p_, nt = r[f"minus_bench_t_{suff}"], r[f"minus_bench_p_{suff}"], ""
            if not np.isfinite(t_) and abs(r[f"minus_bench_alpha_{suff}"]) < 1e-12:  # held in every month: identical series
                t_, p_, nt = 0.0, 1.0, "; degenerate: the rule is short in every month of the window, so the difference is identically 0"
            add(f"COVIDB_{r.timing}_{r.measure}_{r.strategy}_minus_always_short_{suff}", Q2,
                f"FF3 alpha NW(6) t of r({r.measure} {r.strategy}) - r(always-short Brown), {lab}", t_, p_, n_, "exploratory",
                f"diff alpha_ann={r[f'minus_bench_alpha_{suff}']:.5f}" + nt)
for m in PRIMARY:  # exploratory: paired difference vs EMV_env in validation and holdout
    for code, sname in STRATS.items():
        for per, (a_, b_) in (("validation", VAL), ("holdout", (HOLD_START, END[m]))):
            d = paired_alpha(runs[(m, "realtime", "log1p")]["strategies"][sname]["net_return"],
                             runs[("EMV_env", "realtime", "log1p")]["strategies"][sname]["net_return"], a_, b_, FF3F)
            add(f"Q1_{m}_minus_EMV_env_realtime_{code}_{per}_alpha", Q1, f"FF3 alpha NW(6) t of r({m}) - r(EMV_env) ({code}, {per})",
                d["diff_t"], d["diff_p"], d["n"], "exploratory", f"diff alpha_ann={d['diff_alpha_ann']:.5f}; window {a_.date()} to {b_.date()}")
BOOT_RES = 2 / 5000  # smallest nonzero p of 2*min(P(draw>0), P(draw<0)) with 5000 draws
INV_STRATS = {v: k for k, v in STRATS.items()} | {"Benchmark | Always-short Brown": "AS", "Benchmark | Buy-and-hold Green-Brown": "BH"}


def boot_p(p):
    return (max(float(p), BOOT_RES), " (pipeline p = 0: no draw crossed zero; ledger stores the resolution bound 2/5000)"
            if float(p) == 0 else "")


for _, r in BOOT.iterrows():
    kind = "primary_support" if r.measure in PRIMARY else ("placebo" if r.measure in PLACEBO else "reference")
    p, pnote = boot_p(r.p_two_sided)
    add(f"BOOT_{r.measure}_realtime_{r.strategy}_{r.period}", Q1, "circular block bootstrap (block 12, 5000 reps) of mean net return",
        r.mean_ann, p, int(r.n), kind if kind != "primary_support" else "robustness",
        f"CI [{r.ci_low:.4f}, {r.ci_high:.4f}]; window {r.start} to {r.end}" + pnote)
for _, r in FULLCMP.iterrows():  # pipeline full-mode per-strategy bootstrap of the mean net return, 2010-01 to end_m
    code = INV_STRATS[r.strategy]
    p, pnote = boot_p(r.bootstrap_p)
    signal_free = code in ("AS", "BH")
    n_f = int(runs[(r.measure, "realtime", "log1p")]["strategies"][r.strategy]["net_return"].loc[VAL[0]:END[r.measure]].notna().sum())
    add(f"FULLBOOT_{r.measure}_realtime_{code}_full", Q1, "pipeline circular block bootstrap (block 12, 5000 reps) of mean net return, full window",
        r.ann_return_full, p, n_f, "reference" if signal_free else "robustness",
        f"CI [{r.bootstrap_ci_low:.4f}, {r.bootstrap_ci_high:.4f}]; window {r.window}; months held={int(r.months_held_full)}"
        + ("; signal-free benchmark, identical across measures that share the window" if signal_free else "") + pnote)
for _, r in FULLPAIR.iterrows():  # pipeline paired bootstrap, continuous minus discrete, holdout
    p, pnote = boot_p(r.p_two_sided)
    n_h = int(runs[(r.measure, "realtime", "log1p")]["strategies"][r.new]["net_return"].loc[HOLD_START:END[r.measure]].notna().sum())
    add(f"FULLPAIR_{r.measure}_realtime_{INV_STRATS[r.new]}_minus_{INV_STRATS[r.benchmark]}_holdout", Q1,
        "pipeline paired circular block bootstrap (block 12, 5000 reps) of mean net return difference, holdout",
        r.mean_ann, p, n_h, "robustness",
        f"{r.new} minus {r.benchmark}; CI [{r.ci_low:.4f}, {r.ci_high:.4f}]; window {r.window}; pipeline Holm p within the "
        f"measure's 4 pairs={r.holm_p:.4f}; continuous weights are de-leveraged (audit item 4)" + pnote)
LED = pd.DataFrame(L)
assert LED.test_id.is_unique, LED.test_id[LED.test_id.duplicated()].tolist()
LED.to_csv(out("tests_ledger.csv"), index=False)
print(f"  ledger: {len(LED)} tests; {LED.primary_or_exploratory.value_counts().to_dict()}")

# ============================================================================ 10. key numbers
K = []


def key(name, value, source):
    K.append({"name": name, "value": value, "source": source})


key("q1_decision", DECISION_Q1, "primary.csv (holdout alpha > 0 and Holm p < 0.05)")
key("q1_min_holm_p", PRIM.holm_p.min(), "primary.csv")
key("q1_min_raw_p", PRIM.p.min(), "primary.csv")
key("q1_min_raw_p_test", PRIM.loc[PRIM.p.idxmin(), "test_id"], "primary.csv")
for m in ("EMV_env",) + PRIMARY + PLACEBO:
    for per in ("validation", "holdout"):
        sub_ = LONG[(LONG.measure == m) & (LONG.timing == "realtime") & (LONG['transform'] == "log1p") & (LONG.period == per)]
        key(f"{m}_{per}_n_pos_alpha_t_ge_1.96", int(((sub_.alpha_ann > 0) & (sub_.alpha_t_hac6 >= 1.96)).sum()), "results_long.csv")
        key(f"{m}_{per}_n_neg_alpha", int((sub_.alpha_ann < 0).sum()), "results_long.csv")
        key(f"{m}_{per}_mean_alpha_6strats", float(sub_.alpha_ann.mean()), "results_long.csv")
key("q2_decision", DECISION_Q2, "placebo_covid.csv")
for m in PLACEBO:
    key(f"q2_{m}_reproduces_realtime", int(rep.get(m, 0)), "placebo_covid.csv")
    key(f"q2_{m}_reproduces_same_month", int(rep_same.get(m, 0)), "placebo_covid.csv")
for m in ORDER:
    c = CS[CS.measure == m].iloc[0]
    key(f"{m}_crossings", int(c.n_cross_raw), "crossings.csv")
    key(f"{m}_overlap_pm1", int(c.overlap_pm1), "crossings.csv")
for mth, v in BROWN_EPS_CRASH.items():
    key(f"brown_residual_{mth}", v, "run.py EPS (Brown-leg FF3 residual)")
key("bench_covid_alpha", float(get_bench("covid").alpha_ann), "results_long.csv (measure none)")
key("bench_covid_t", float(get_bench("covid").alpha_t_hac6), "results_long.csv (measure none)")
for timing in TIMINGS:
    for m in ("EMV_env", "CPU", "VIX", "EMV_overall", "MCCC"):
        x = DEC[(DEC.timing == timing) & (DEC.measure == m) & (DEC.strategy == "O3")].iloc[0]
        key(f"{m}_O3_covid_share_mar_apr_{timing}", float(x.share_mar_apr), "covid_decomposition.csv")
        key(f"{m}_O3_covid_months_held_mar_apr_{timing}", x.held_mar_apr, "covid_decomposition.csv")
        key(f"{m}_O3_covid_alpha_ex_mar_apr_{timing}", float(x.alpha_ex_mar_apr), "covid_decomposition.csv")
        key(f"{m}_O3_covid_t_ex_mar_apr_{timing}", float(x.t_ex_mar_apr), "covid_decomposition.csv")
    for m in ("EMV_env", "CPU"):
        x = DEC[(DEC.timing == timing) & (DEC.measure == m) & (DEC.strategy == "O3")].iloc[0]
        for suff in ("covid", "ex_mar_apr"):
            key(f"{m}_O3_minus_always_short_alpha_{suff}_{timing}", float(x[f"minus_bench_alpha_{suff}"]), "covid_decomposition.csv")
            key(f"{m}_O3_minus_always_short_t_{suff}_{timing}", float(x[f"minus_bench_t_{suff}"]), "covid_decomposition.csv")
    xb = DEC[(DEC.timing == timing) & (DEC.strategy == "AS")].iloc[0]
    key(f"bench_covid_alpha_ex_mar_apr_{timing}", float(xb.alpha_ex_mar_apr), "covid_decomposition.csv (signal-free, same in both timings)")
    key(f"bench_covid_t_ex_mar_apr_{timing}", float(xb.t_ex_mar_apr), "covid_decomposition.csv")
    for m in PLACEBO + ("CPU",):
        for code in ("O3", "P3"):
            x = PLC[(PLC.timing == timing) & (PLC.measure == m) & (PLC.strategy == code)].iloc[0]
            key(f"{m}_{code}_covid_ratio_to_EMV_env_{timing}", float(x.ratio_to_EMV_env), "placebo_covid.csv")
# which strategies drive the Q2 rule outcome, by timing
for timing, rr in (("realtime", rep), ("same_month", rep_same)):
    for m in PLACEBO:
        sub_ = PLC[(PLC.timing == timing) & (PLC.measure == m) & (PLC.reproduces == True)]  # noqa: E712
        key(f"q2_{m}_reproduced_strategies_{timing}", ", ".join(sub_.strategy), "placebo_covid.csv")
# EMV_env Original 3m position months around the COVID onset (real-time timing): hold months and the crossing that drives each
_s = runs[("EMV_env", "realtime", "log1p")]
_held = _s["strategies"][STRATS["O3"]]["position"].shift(1).loc["2019-10-31":"2020-06-30"]
key("EMV_env_O3_realtime_return_months_held_2019-10_to_2020-06",
    ", ".join(d.strftime("%Y-%m") for d in _held.index[_held.fillna(0) != 0]), "run.py (position lagged one month)")
_xr = _s["signals"]["cross_raw"].loc["2019-06-30":"2020-06-30"]
key("EMV_env_realtime_cross_signal_months_2019-06_to_2020-06", ", ".join(d.strftime("%Y-%m") for d in _xr.index[_xr.astype(bool)]),
    "run.py (signal date = data month + 1 under real-time timing)")
# cumulative COVID-window net return (compounded 2020-01..2021-12), as plotted in the covid_paths figure
for m in ("EMV_env", "VIX", "EMV_overall", "MCCC", "CPU"):
    for code in ("O3", "CR"):
        r = runs[(m, "realtime", "log1p")]["strategies"][STRATS[code]]["net_return"].loc[COVID[0]:COVID[1]].fillna(0)
        key(f"{m}_{code}_covid_cum_net_realtime", float((1 + r).prod() - 1), "covid_paths figure (compounded 2020-01 to 2021-12)")
key("bench_covid_cum_net", float((1 + bench["net_return"].loc[COVID[0]:COVID[1]].fillna(0)).prod() - 1), "covid_paths figure")
# recent windows, Original 3m, real-time timing
for per in REC_WIN:
    for m in REC_MEAS:
        x = REC[(REC.measure == m) & (REC.period == per) & (REC.strategy == "O3")].iloc[0]
        for k_ in ("alpha_ann", "t", "p", "ann_net", "n"):
            key(f"{m}_O3_{per}_{k_}", float(x[k_]), "recent.csv")
pd.DataFrame(K).to_csv(out("key_numbers.csv"), index=False)

# ============================================================================ 11. figures
# (a) crossings raster
fig, ax = plt.subplots(figsize=(7.2, 3.6))
x0, x1 = pd.Timestamp("2009-10-31"), pd.Timestamp("2026-09-30")
ax.axvspan(COVID[0] - pd.offsets.MonthBegin(1), COVID[1], color=ps.GRID, alpha=0.7, lw=0, label="COVID 2020-21")
ax.axvspan(HOLD_START - pd.offsets.MonthBegin(1), SAMPLE_END, color=ps.NEUTRAL_MID, alpha=1.0, lw=0, label="Holdout")
for d in team_x:
    ax.axvline(d, color=ps.ORANGE, lw=0.5, alpha=0.35, zorder=1)
ylab = []
for i, m in enumerate(ORDER):
    y = len(ORDER) - 1 - i
    ylab.append((y, MEASURES[m]["label"]))
    e = EV[(EV.measure == m) & (EV.signal == "raw")]
    d = pd.to_datetime(e.data_month)
    hit = e.within_1m_of_EMV_env.to_numpy()
    ax.scatter(d[hit], np.full(hit.sum(), y), s=26, color=COLORS[m], edgecolor=COLORS[m], zorder=3)
    ax.scatter(d[~hit], np.full((~hit).sum(), y), s=26, facecolor="white", edgecolor=COLORS[m], lw=1.2, zorder=3)
    dend = native_range(MEAS[m])[1]
    if dend < SAMPLE_END:
        ax.fill_between([dend + ME, x1], y - 0.3, y + 0.3, facecolor="none", edgecolor=ps.MUTED, hatch="////", lw=0, zorder=2)
    lo = live_start(runs[(m, "same_month", "log1p")]["signals"], "threshold_raw") - ME
    if lo > x0:
        ax.fill_between([x0, lo], y - 0.3, y + 0.3, facecolor="none", edgecolor=ps.MUTED, hatch="////", lw=0, zorder=2)
ax.set_yticks([p for p, _ in ylab]); ax.set_yticklabels([l for _, l in ylab])
ax.set_ylim(-0.7, len(ORDER) - 0.3); ax.set_xlim(x0, x1)
ax.grid(axis="y", visible=False)
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
handles = [Line2D([], [], marker="o", ls="", color=ps.INK2, label="within 1 month of an EMV env. crossing"),
           Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor=ps.INK2, label="no EMV env. crossing within 1 month"),
           Line2D([], [], color=ps.ORANGE, lw=0.8, alpha=0.5, label="EMV env. crossing month"),
           Patch(facecolor=ps.GRID, label="COVID 2020-21"), Patch(facecolor=ps.NEUTRAL_MID, label="Holdout"),
           Patch(facecolor="white", edgecolor=ps.MUTED, hatch="////", label="signal not defined")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=7)
ax.set_title("Extreme-attention crossings by measure (data month)")
savefig(fig, f"{MODULE}_crossings")

# (b) alpha t-stat heatmap, real-time timing
fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.1), sharey=True)
for ax, (per, plab) in zip(axes, (("validation", "Validation"), ("holdout", "Holdout (as available)"), ("covid", "COVID 2020-21"))):
    M_ = np.array([[get(m, "realtime", c, per).alpha_t_hac6 for c in STRATS] for m in ORDER])
    im = ax.imshow(M_, cmap=ps.DIVERGING, vmin=-4, vmax=4, aspect="auto")
    ax.set_xticks(range(len(STRATS))); ax.set_xticklabels([STRAT_LABEL[c] for c in STRATS], rotation=60, ha="right")
    ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([SHORT[m] for m in ORDER])
    ax.grid(False); ax.set_title(plab)
    for sp in ax.spines.values():
        sp.set_visible(False)
cb = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02)
cb.set_label("FF3 alpha NW(6) t")
savefig(fig, f"{MODULE}_alpha_t_heatmap")

# (c) COVID paths
def covid_path(ret: pd.Series) -> pd.Series:
    """Cumulative net return over the COVID window only: compound 2020-01..2021-12 and prepend 0 at 2019-12-31."""
    r = ret.loc[COVID[0]:COVID[1]].fillna(0)
    w = (1 + r).cumprod() - 1
    return pd.concat([pd.Series([0.0], index=[COVID[0] - ME]), w])


PATH_END = {}
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), sharey=True)
for ax, code in zip(axes, ("O3", "CR")):
    for m in ("EMV_env", "VIX", "EMV_overall", "MCCC", "CPU"):
        w = covid_path(runs[(m, "realtime", "log1p")]["strategies"][STRATS[code]]["net_return"])
        PATH_END[(m, code)] = float(w.iloc[-1])
        ax.plot(w.index, 100 * w, color=COLORS[m], label=SHORT[m], lw=1.5 if m == "EMV_env" else 1.2)
    wb = covid_path(bench["net_return"])
    PATH_END[("none", code)] = float(wb.iloc[-1])
    ax.plot(wb.index, 100 * wb, color=ps.INK2, ls="--", lw=1.0, label="Always-short Brown (no signal)")
    ax.axvspan(pd.Timestamp("2020-02-29"), pd.Timestamp("2020-04-30"), color=ps.GRID, alpha=0.6, lw=0)
    ax.axhline(0, color=ps.MUTED, lw=0.6)
    ax.set_title(STRAT_LABEL[code] + ", real-time timing")
    ax.set_ylabel("cumulative net return (%)" if code == "O3" else "")
h, l = axes[0].get_legend_handles_labels()
h.append(Patch(facecolor=ps.GRID, alpha=0.6, label=f"Mar-Apr 2020 (Brown residual {100 * BROWN_EPS_CRASH['2020-03']:.1f}%, {100 * BROWN_EPS_CRASH['2020-04']:.1f}%)"))
fig.legend(handles=h, loc="outside lower center", ncol=4, fontsize=7)
fig.autofmt_xdate()
savefig(fig, f"{MODULE}_covid_paths")

print(f"done in {time.perf_counter() - T0:.1f}s")
print("\nPrimary family:")
print(PRIM[["test_id", "n", "estimate", "t", "p", "holm_p"]].round(4).to_string())
print("\nCOVID placebo (realtime):")
print(PLC[PLC.timing == "realtime"][["strategy", "measure", "alpha_ann", "t", "ratio_to_EMV_env", "reproduces"]].round(3).to_string())
print(CS.drop(columns=["covid_crossings"]).round(2).to_string())
print(CS[["measure", "covid_crossings"]].to_string())
