"""Build the report's compact tables from the verified module CSVs.

Run:  cd /home/hashim/projects/GA/project/research && uv run python report/make_tables.py

Writes tabular-only .tex files to report/tables/ so that report.tex owns every caption.
Every number is read from outputs/tables/*.csv; nothing is typed by hand except labels.
"""
from __future__ import annotations

import pathlib
import re

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
OUT = ROOT / "report" / "tables"
OUT.mkdir(parents=True, exist_ok=True)


def num(x: float, nd: int = 2, sign: bool = False) -> str:
    """Format a number for LaTeX with a true minus sign."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    s = f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"
    if s.startswith("-"):
        return "$-$" + s[1:]
    return s


def cell(alpha: float, t: float) -> str:
    """alpha in % a year with the NW t in parentheses."""
    return f"{num(100 * alpha)} ({num(t)})"


def write(name: str, body: str) -> None:
    (OUT / name).write_text(body)
    print("wrote", OUT / name)


# ---------------------------------------------------------------- Table: the same machinery, three signals (M1b)
def table_signals() -> None:
    g = pd.read_csv(TAB / "M1b_alt_signals_alpha_grid_realtime.csv")
    g = g[g.timing == "realtime"]
    rules = [("O3", "Original 3m"), ("P3", "Pure 3m"), ("O6", "Original 6m"), ("P6", "Pure 6m"),
             ("CR", "Continuous raw"), ("CP", "Continuous pure")]
    measures = [("EMV_env", "EMV tracker"), ("MCCC", "MCCC"), ("CPU", "CPU")]
    rows = []
    for code, label in rules:
        cells = []
        for m, _ in measures:
            for per in ("validation", "holdout"):
                r = g[(g.measure == m) & (g.strategy == code) & (g.period == per)]
                assert len(r) == 1, (m, code, per)
                cells.append(cell(float(r.alpha_ann.iloc[0]), float(r.t.iloc[0])))
        rows.append(label + " & " + " & ".join(cells) + r" \\")
    # count of validation alphas with t >= 1.96, and mean validation alpha (key_numbers)
    kn = pd.read_csv(TAB / "M1b_alt_signals_key_numbers.csv").set_index("name")["value"]
    counts, means, holdneg = [], [], []
    for m, _ in measures:
        v = g[(g.measure == m) & (g.period == "validation") & g.strategy.isin([c for c, _ in rules])]
        h = g[(g.measure == m) & (g.period == "holdout") & g.strategy.isin([c for c, _ in rules])]
        counts.append(int((v.t >= 1.96).sum()))
        holdneg.append(int((h.alpha_ann < 0).sum()))
        means.append(float(kn[f"{m}_validation_mean_alpha_6strats"]))
    # mean row: one value under each measure's validation column
    mean_cells = []
    for mu in means:
        mean_cells += [num(100 * mu), ""]
    summary = (r"\midrule" "\n"
               r"Count: $t\ge1.96$ / $\alpha<0$ & "
               + " & ".join(f"{c} of 6 & {h} of 6" for c, h in zip(counts, holdneg)) + r" \\" "\n"
               r"Mean validation alpha & " + " & ".join(mean_cells) + r" \\")
    head = (r"\begin{tabular}{@{}l*{6}{r}@{}}" "\n" r"\toprule" "\n"
            r" & \multicolumn{2}{c}{EMV tracker (team)} & \multicolumn{2}{c}{MCCC} & "
            r"\multicolumn{2}{c}{CPU} \\" "\n"
            r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}" "\n"
            r"Rule & Validation & Holdout & Validation & Holdout & Validation & Holdout \\" "\n" r"\midrule" "\n")
    write("tab_signals.tex", head + "\n".join(rows) + "\n" + summary + "\n" + r"\bottomrule" "\n" r"\end{tabular}" "\n")


# ---------------------------------------------------------------- Table: time patterns (M2 grid + M3 GB)
def table_time() -> None:
    g = pd.read_csv(TAB / "M2_christhian_tests_strategy_grid.csv")
    s = g[(g.legs == "L5") & (g.baseline == "corr") & (g.hedge == "FF3") & (g.costs == "team") & (g.eval_id == "E:FF3")]
    e = pd.read_csv(TAB / "M3_alpha_beta_exposures.csv")
    gb = e[(e.asset == "GB") & (e.model == "FF3")].set_index("period")
    strats = ["Original 3m", "Original 6m", "Continuous raw", "Always-short Brown"]
    periods = [("full_live", "full_1970", "Full sample$^{a}$"), ("post2010", "post2010", "Post-2010"),
               ("validation", "validation", "Validation"), ("holdout", "holdout", "Holdout"),
               ("covid", "covid", "COVID"), ("last18", "last18", "Last 18 months"),
               ("last12", "last12", "Last 12 months")]
    ym = lambda x: str(x)[:7]  # noqa: E731
    rows = []
    for i, (sp, gp, label) in enumerate(periods):
        nets, alphas = [], []
        n = None
        for st in strats:
            r = s[(s.strat == st) & (s.period == sp)]
            assert len(r) == 1, (st, sp)
            r = r.iloc[0]
            n = int(r.perf_n) if st == "Original 3m" else n
            nets.append(num(100 * r.perf_ann_net))
            alphas.append(cell(r.alpha_ann, r.t_alpha))
        rg = gb.loc[gp]
        nets.append(num(100 * rg.mean_ann))
        alphas.append(cell(rg.alpha_ann, rg.t_alpha))
        if i:
            rows.append(r"\addlinespace[1pt]")
        r0 = s[(s.strat == strats[0]) & (s.period == sp)].iloc[0]
        rows.append(f"{label}, $n={n}$ & Net & " + " & ".join(nets) + r" \\")
        rows.append(f"\\quad {ym(r0.window_start)} to {ym(r0.window_end)} & $\\alpha$ ($t$) & " + " & ".join(alphas) + r" \\")
    head = (r"\begin{tabular}{@{}llrrrrr@{}}" "\n" r"\toprule" "\n"
            r"Window & & Original 3m & Original 6m & Continuous raw & Always-short Brown & Raw GB spread$^{b}$ \\" "\n"
            r"\midrule" "\n")
    write("tab_time.tex", head + "\n".join(rows) + "\n" + r"\bottomrule" "\n" r"\end{tabular}" "\n")
    # team-timing recent rows for the table note (same grid, team baseline)
    t = g[(g.legs == "L5") & (g.baseline == "team") & (g.hedge == "FF3") & (g.costs == "team") & (g.eval_id == "E:FF3")
          & (g.strat == "Original 3m") & g.period.isin(["last18", "last12"])].set_index("period")
    note = {p: (100 * t.loc[p, "perf_ann_net"], 100 * t.loc[p, "alpha_ann"], t.loc[p, "t_alpha"]) for p in ["last18", "last12"]}
    print("team-timing Original 3m recent:", {k: tuple(round(x, 2) for x in v) for k, v in note.items()})
    starts = {st: s[(s.strat == st) & (s.period == "full_live")].window_start.iloc[0] for st in strats}
    print("full_live starts:", starts, "GB full n:", int(gb.loc["full_1970", "n"]))


# ---------------------------------------------------------------- Table: the frozen 1994-2009 test (M8)
def table_frozen() -> None:
    att = pd.read_csv(TAB / "M8_attribution.csv")
    summ = pd.read_csv(TAB / "M8_strategy_summary.csv").set_index("signal")
    drop = pd.read_csv(TAB / "M8_drop_one.csv")
    pb = pd.read_csv(TAB / "M8_passbar.csv")
    sigs = ["Frozen EMV-share rule (primary)", "Team EMV_env level, lagged 1m (secondary)"]
    a = {}
    for sgn in sigs:
        r = att[(att.signal == sgn) & (att.term == "const")].iloc[0]
        a[sgn] = (12 * float(r.coef), float(r.t_nw6), float(r["p_upper_nw6_t(n-k)"]))
    comp = lambda sgn, key: pb[(pb.signal == sgn) & pb.component.str.startswith(key)].iloc[0]  # noqa: E731

    def pf(sgn, key):
        return r"\textsc{pass}" if str(comp(sgn, key)["pass"]) == "True" else r"\textsc{fail}"

    def drops(sgn):
        d = drop[drop.signal == sgn].set_index("dropped")
        order = ["Util", "Ships", "Aero", "Steel", "BldMt"]
        return ", ".join(f"{k} {num(100 * d.loc[k, 'alpha_ann'], sign=True)}" for k in order), int((d.alpha_ann > 0).sum())

    fns = {
        "(i)": lambda s: f"{num(100 * a[s][0], sign=True)}\\% a year, $t={a[s][1]:.2f}$; one-sided $p={a[s][2]:.3f}$",
        "(ii)": lambda s: f"$p={float(comp(s, '(ii)').p_value):.3f}$ (5,000 draws)",
        "(iii)": lambda s: f"{comp(s, '(iii)').statistic} merged episodes",
        "(iv)": lambda s: f"{drops(s)[1]} of 5 positive",
    }
    labels = {"(i)": "(i) Timing alpha, NW(6)", "(ii)": "(ii) Calendar shuffle", "(iii)": "(iii) Episodes",
              "(iv)": "(iv) Drop one industry"}
    bars = {"(i)": r"$\alpha>0$, $t\ge2$", "(ii)": r"$p\le0.05$", "(iii)": r"$\ge8$", "(iv)": r"all five $>0$"}
    rows = []
    for key in ["(i)", "(ii)", "(iii)", "(iv)"]:
        rows.append(f"{labels[key]} & {bars[key]} & {fns[key](sigs[0])} & {pf(sigs[0], key)} & "
                    f"{fns[key](sigs[1])} & {pf(sigs[1], key)} " r"\\")
    n_pass = {s: int(sum(str(comp(s, k)["pass"]) == "True" for k in ["(i)", "(ii)", "(iii)", "(iv)"])) for s in sigs}
    rows.append(r"\midrule")
    rows.append(r"Verdict & all four & \textsc{fail}, " + f"{n_pass[sigs[0]]} of 4" + r" & & \textsc{fail}, "
                + f"{n_pass[sigs[1]]} of 4" + r" & \\")
    ctx = []
    for s in sigs:
        r = summ.loc[s]
        ctx.append(f"{int(r.months_in_position)} of {int(r.n_months)}; $\\pi={r.pi:.3f}$")
    head = (r"\begin{tabular}{@{}L{0.19\textwidth}L{0.11\textwidth}L{0.27\textwidth}lL{0.27\textwidth}l@{}}" "\n"
            r"\toprule" "\n"
            r"Component & Bar & Frozen EMV-share rule & & Team signal, lagged & \\" "\n"
            r"\midrule" "\n")
    write("tab_frozen.tex", head + "\n".join(rows) + "\n" + r"\bottomrule" "\n" r"\end{tabular}" "\n")
    r0 = summ.iloc[0]
    print("always-on net:", round(100 * r0.always_ann_net, 2), "t", round(r0.always_t_mean_nw6, 2),
          "| D mean", round(100 * r0.D_ann_mean, 2), "t", round(r0.D_t_mean_nw6, 2))


# ---------------------------------------------------------------- Appendix: M1 crossings vs volatility (p formatting fixed)
def table_m1_cross() -> None:
    d = pd.read_csv(TAB / "M1_signal_audit_crossings_vix_summary.csv")
    d = d[d.event == "crossing"]

    def p(x, bound="0.001"):
        return f"$<${bound}" if x < float(bound) else f"{x:.3f}"

    rows = []
    for _, r in d.iterrows():
        flag = "High VIX" if "VIX" in r.flag else "High overall EMV"
        win = {"all_threshold_sample": "All", "since_2010": "Since 2010", "pre2010": "Pre-2010",
               "validation": "Validation", "holdout": "Holdout"}[r.window]
        # a zero shift p means no rotation was as extreme; its resolution is 1/n_shifts, so print that bound
        bound = f"{np.ceil(1000 / int(r.n_shifts)) / 1000:.3f}"
        shift = f"$<${bound}" if r.p_circular_shift == 0 else f"{r.p_circular_shift:.3f}"
        rows.append(f"{flag} & {win} & {r.start} to {r.end} & {int(r.n_events)} & {r.frac_events_flag:.2f} & "
                    f"{r.frac_other_flag:.2f} & {p(r.fisher_p)} & {shift} & {int(r.n_shifts)} & {p(r.p_lpm_nw12)} " r"\\")
    head = (r"\begin{tabular}{@{}lllrrrrrrr@{}}" "\n" r"\toprule" "\n"
            r"Flag & Window & Months & Crossings & Share, crossings & Share, other & $p$ Fisher & $p$ shift & Rotations & $p$ LPM \\"
            "\n" r"\midrule" "\n")
    write("tab_m1_cross.tex", head + "\n".join(rows) + "\n" + r"\bottomrule" "\n" r"\end{tabular}" "\n")


# ---------------------------------------------------------------- Appendix E: ledger counts
def table_ledgers() -> None:
    names = [("M1", "M1_signal_audit"), ("M1b", "M1b_alt_signals"), ("M2", "M2_christhian_tests"), ("M3", "M3_alpha_beta"),
             ("M4", "M4_emissions"), ("M5", "M5_industry_momentum"), ("M6", "M6_factor_timing"), ("M8", "M8")]

    def counts(pre):
        d = pd.read_csv(TAB / f"{pre}_tests_ledger.csv")
        c = d["primary_or_exploratory"].value_counts()
        prim, rob, exp_ = int(c.get("primary", 0)), int(c.get("robustness", 0)), int(c.get("exploratory", 0))
        detail = ", ".join(f"{int(v)} {k}" for k, v in c.items() if k not in ("primary", "robustness", "exploratory"))
        return np.array([len(d), prim, rob, exp_, len(d) - prim - rob - exp_]), detail

    def row(label, v, detail=""):
        return (f"{label} & {v[0]:,} & {v[1]} & {v[2]:,} & {v[3]:,} & {v[4] if v[4] else ''}"
                + (f" ({detail})" if detail else "") + r" \\")

    rows, tot = [], np.zeros(5, int)
    for short, pre in names:
        v, detail = counts(pre)
        tot += v
        rows.append(row(short, v, detail))
    rows.append(r"\midrule")
    rows.append(row("Eight module ledgers", tot))
    v7, d7 = counts("M7_robustness")
    rows.append(row("M7 (project-wide checks)", v7, d7))
    rows.append(r"\midrule")
    rows.append(row("All ledgers", tot + v7))
    head = (r"\begin{tabular}{@{}lrrrrl@{}}" "\n" r"\toprule" "\n"
            r"Ledger & Rows & Primary & Robustness & Exploratory & Other \\" "\n" r"\midrule" "\n")
    write("tab_ledgers.tex", head + "\n".join(rows) + "\n" + r"\bottomrule" "\n" r"\end{tabular}" "\n")


# ---------------------------------------------------------------- Appendix E: M7 tables, body only (report.tex owns captions)
M7_BODIES = ["M7_census_family_by_module", "M7_multiple_testing_summary", "M7_grid_windows", "M7_search_summary",
             "M7_dsr", "M7_holdout_reading", "M7_frozen_pre1970", "M7_cost_stress", "M7_verdict_table"]
M7_TEXT = [  # plain-language replacements inside the builder's cells and notes
    ("spec check", "check"), ("X\\_unc", "unconstrained"), ("optimizer X b-", "optimizer, $b=-$"),
    ("Original | Short Brown hold 3m", "Original 3m"), ("Pure | Short Brown hold 3m", "Pure 3m"),
    ("Original | Short Brown hold 6m", "Original 6m"), ("Pure | Short Brown hold 6m", "Pure 6m"),
    ("Continuous | raw attention", "Continuous raw"), ("Continuous | pure attention", "Continuous pure"),
    ("full\\_1970", "full, 1970"), ("full\\_live", "full, live"), ("pre\\_covid", "pre-COVID"),
    ("inflation\\_rates", "rates, 2022--24"), ("last18", "last 18"), ("last12", "last 12"),
    ("labelled", "labeled"), ("'rejects'", "``rejects''"),
]


def m7_body(name: str) -> None:
    src = (TAB / f"{name}.tex").read_text()
    t0 = src.index(r"\begin{tabular}")
    t1 = src.rindex(r"\end{tabular}") + len(r"\end{tabular}")
    body = src[t0:t1]
    note = ""
    m = re.search(r"\\par\\smallskip\{\\scriptsize (.*)\}\s*\\end\{table\}", src, re.S)
    if m:
        note = m.group(1).strip()
    for a, b in M7_TEXT:
        body = body.replace(a, b)
        note = note.replace(a, b)
    if name == "M7_verdict_table":  # ragged-right text columns (avoids underfull boxes)
        spec_end = body.index("\n")
        body = body[:spec_end].replace("p{", r">{\raggedright\arraybackslash}p{") + body[spec_end:]
    out = ("% Written by report/make_tables.py from outputs/tables/" + name + ".tex (tabular and note only).\n"
           "\\begin{adjustbox}{max width=\\linewidth}\n" + body + "\n\\end{adjustbox}\n"
           + ("\\par\\smallskip{\\scriptsize " + note + "}\n" if note else ""))
    write(f"body_{name}.tex", out)


def m7_bodies() -> None:
    for n in M7_BODIES:
        m7_body(n)


# ---------------------------------------------------------------- Appendix C: builder tables re-wrapped to fit the page
APPENDIX_TABLES = [
    "M1_signal_audit_zero_counts", "M1_signal_audit_decomposition_team_signal", "M1_signal_audit_predictive_ic_summary",
    "M1_signal_audit_zero_counterfactual_summary",
    "M1b_alt_signals_primary", "M1b_alt_signals_placebo_covid", "M1b_alt_signals_covid_attribution", "M1b_alt_signals_recent",
    "M2_christhian_tests_q1_table1_corr", "M2_christhian_tests_q2_spread_controls", "M2_christhian_tests_q3_hml_contributions",
    "M2_christhian_tests_q4_costs_corr", "M2_christhian_tests_summary_best_case",
    "M4_emissions_key_industries", "M4_emissions_aero_ships_calibration", "M4_emissions_post2010_family",
    "M4_emissions_primary_sensitivity", "M4_emissions_team_rule_rerun",
    "M6_factor_timing_oos_primary", "M6_factor_timing_cv_design", "M6_factor_timing_team_target_check",
    "M8_attribution", "M8_decomposition", "M8_drop_one", "M8_crossings", "M8_bond_check",
]


REWRAP_TEXT = {  # code identifiers in builder tables, replaced by plain labels (content unchanged)
    "M4_emissions_post2010_family": [("(family = these 9 specifications).",
                                      r"(family = these 9 specifications). Alphas are annual decimals (0.047 is 4.7\% a year).")],
    "M4_emissions_primary_sensitivity": [("not pre-specified.",
                                          r"not pre-specified. Returns and alphas are annual decimals (0.047 is 4.7\% a year).")],
    "M8_attribution": [("k = 15.", r"k = 15. The alpha is an annual decimal ($-0.0018$ is $-0.18$\% a year).")],
    "M8_drop_one": [("1994-03 to 2009-12.", r"1994-03 to 2009-12. Alphas are annual decimals ($-0.0061$ is $-0.61$\% a year).")],
    "M8_decomposition": [("1994-03 to 2009-12.", r"1994-03 to 2009-12, in annual decimals (0.0089 is 0.89\% a year).")],
    "M8_bond_check": [("duration and convexity).",
                       r"duration and convexity). Returns, yields and volatilities are decimals ($-0.0746$ is $-7.46$\%); "
                       r"durations are in years.")],
    "M1_signal_audit_predictive_ic_summary": [
        ("outcome & signal & full\\_start & ic\\_full\\_overlap & t\\_nw\\_full\\_overlap & ic\\_validation & "
         "t\\_nw\\_validation & ic\\_holdout & t\\_nw\\_holdout",
         "Outcome & Signal & Start & IC, full & $t$ & IC, validation & $t$ & IC, holdout & $t$"),
        ("brown\\_resid\\_FF3 = Brown-leg residual", "Brown resid. = Brown-leg residual"),
        ("brown\\_resid\\_FF3 &", "Brown resid. &"),
        ("z\\_EMV\\_env\\_share", "$z$ EMV share"), ("z\\_EMV\\_env", "$z$ EMV env."),
        ("z\\_EMV\\_overall", "$z$ EMV overall"), ("z\\_VIX", "$z$ VIX"),
        ("z\\_MCCC\\_transition", "$z$ MCCC transition"), ("z\\_MCCC", "$z$ MCCC"), ("z\\_CPU", "$z$ CPU"),
        ("shock\\_EMV\\_env\\_share", "shock EMV share"), ("shock\\_EMV\\_env", "shock EMV env."),
        ("shock\\_EMV\\_overall", "shock EMV overall"), ("shock\\_VIX", "shock VIX"),
        ("shock\\_MCCC\\_transition", "shock MCCC transition"), ("shock\\_MCCC", "shock MCCC"),
        ("shock\\_CPU", "shock CPU"),
    ],
    "M4_emissions_team_rule_rerun": [("reproduces the team's numbers exactly.",
                                      r"reproduces the team's numbers exactly, under same-month timing. Returns and alphas "
                                      r"are annual decimals; active months is the team's count, which includes exit-cost "
                                      r"months (Appendix~\ref{app:replication}, item 6).")],
    "M1b_alt_signals_recent": [(" All six strategies in M1b\\_alt\\_signals\\_recent.csv.", "")],
    "M1_signal_audit_zero_counts": [
        ("Exact zeros in EMV\\_env (FRED EMVENRGYENVREG)", "Exact zeros in the team series (FRED EMVENRGYENVREG)"),
        ("period & start & end & n\\_months & n\\_zero & zero\\_share",
         "Period & Start & End & Months & Zero months & Zero share"),
        ("full\\_1985 &", "Full sample &"), ("pre\\_2021-10 &", "Before 2021-10 &"), ("post\\_2021-10 &", "From 2021-10 &"),
        ("post2010 &", "Post-2010 &"), ("validation &", "Validation &"), ("holdout &", "Holdout &"),
        ("pre\\_covid &", "Pre-COVID &"), ("covid &", "COVID &"), ("inflation\\_rates &", "Rates, 2022--24 &"),
        ("last18 &", "Last 18 months &"), ("last12 &", "Last 12 months &"),
    ],
    "M1_signal_audit_decomposition_team_signal": [
        ("$z_t=$ rolling\\_z(log1p(EMV\\_env)) is explained by rolling z-scores of log1p(VIX) and log1p(overall EMV)",
         "$z_t$, the rolling 60-month z-score of $\\log(1+\\text{EMV env.})$, is explained by rolling z-scores of "
         "$\\log(1+\\text{VIX})$ and $\\log(1+\\text{overall EMV})$"),
        ("sample & start & end & n & regressors & R2 & slope 1 & t 1 & slope 2 & t 2",
         "Sample & Start & End & $n$ & Regressors & $R^2$ & Slope 1 & $t$ 1 & Slope 2 & $t$ 2"),
        ("full &", "Full sample &"), ("pre\\_2021-10 &", "Before 2021-10 &"), ("post\\_2021-10 &", "From 2021-10 &"),
        ("validation &", "Validation &"), ("holdout &", "Holdout &"),
        ("z\\_EMV\\_overall", "$z$ overall EMV"), ("z\\_VIX", "$z$ VIX"),
    ],
    "M1_signal_audit_zero_counterfactual_summary": [
        ("; the CSV adds the full validation window)", ")"),
        ("60m\\_calendar", "60 calendar months"), ("last60\\_nonzero", "last 60 nonzero months"),
    ],
    "M4_emissions_key_industries": [  # team ranks are integers; headers keep their width so the page holds C.21 and C.22
        ("ff49 & team\\_intensity & team\\_rank\\_from\\_top\\_of41 & epa\\_sc\\_mean & epa\\_rank\\_from\\_top\\_of49 & "
         "epa\\_median\\_rank\\_from\\_top\\_of49 & useeio\\_direct\\_mean & direct\\_ghg\\_rank\\_from\\_top\\_of49 & n\\_naics",
         "Industry & Team intensity & Team rank (of 41) & EPA supply-chain mean & EPA rank, mean (of 49) & "
         "EPA rank, median (of 49) & USEEIO direct mean & USEEIO direct rank (of 49) & Number of NAICS codes"),
        (".000 & ", " & "),
    ],
    "M4_emissions_aero_ships_calibration": [
        ("team\\_over\\_predicted = team value / predicted value. holm\\_p\\_12: Holm-adjusted over these 12 tests.",
         r"Team/predicted is the team value over the predicted value, and Holm $p$ is adjusted over these 12 tests."),
        ("measure & industry & mapping & measure\\_value & team\\_value & predicted\\_team\\_value & "
         "team\\_over\\_predicted & t\\_prediction & p\\_two\\_sided & holm\\_p\\_12",
         r"Measure & Industry & Codes & Measure value & Team value & Predicted team value & Team/predicted & "
         r"$t$ & $p$ & Holm $p$"),
        ("useeio\\_direct\\_co2\\_mean &", r"USEEIO direct CO$_2$ &"),
        ("useeio\\_direct\\_mean &", "USEEIO direct &"),
        ("epa\\_sc\\_mean &", "EPA supply chain &"),
        ("& mfg &", "& manufacturing &"),
    ],
}
# the zero-count caption names M1's Fisher test; its result is read from the M1 ledger
_FZ = pd.read_csv(TAB / "M1_signal_audit_tests_ledger.csv").set_index("test_id").loc["Q3_fisher_zero_pre_post"]
_FZ_M, _FZ_E = f"{_FZ['p_value_two_sided']:.1e}".split("e")
REWRAP_TEXT["M1_signal_audit_zero_counts"].append(
    ("versus 1985-01 to 2021-09.",
     f"versus 1985-01 to 2021-09: odds ratio {_FZ['statistic']:.1f}, $p={_FZ_M}\\times10^{{{int(_FZ_E)}}}$."))


def _braced(s: str, start: int) -> tuple[str, int]:
    """Return the content of the balanced {...} group that starts at s[start] == '{', and the index after it."""
    assert s[start] == "{", s[start:start + 20]
    depth, i = 0, start
    while True:
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i + 1
        i += 1


def rewrap(name: str) -> None:
    src = (TAB / f"{name}.tex").read_text()
    cap_at = src.index(r"\caption")
    caption, _ = _braced(src, src.index("{", cap_at))
    label = ""
    if r"\label{" in src:
        label, _ = _braced(src, src.index("{", src.index(r"\label{")))
    t0 = src.index(r"\begin{tabular}")
    t1 = src.rindex(r"\end{tabular}") + len(r"\end{tabular}")
    body = src[t0:t1]
    after = src[t1:src.rindex(r"\end{table}")].strip() if r"\end{table}" in src else ""
    for a_, b_ in REWRAP_TEXT.get(name, []):
        assert a_ in caption or a_ in body, (name, a_)
        caption, body = caption.replace(a_, b_), body.replace(a_, b_)
    # window, rule and model codes read as in the Appendix E tables (M7_TEXT), plus codes only these tables use
    for a_, b_ in M7_TEXT + [("full\\_1985", "full, 1985"), ("post2010", "post-2010"), ("hold3", "3-month"),
                             ("hold6", "6-month"), ("log1p(", "log(1 + "), ("; the CSV adds the full validation window", ""),
                             ("histmean", "historical mean"), ("ridgecv", "ridge-CV"), ("TEAMTGT\\_", "team target, "),
                             ("covid", "COVID")]:
        caption, body = caption.replace(a_, b_), body.replace(a_, b_)
    # remaining code identifiers (snake_case labels) read as plain words; numbers are untouched
    caption, body = caption.replace("\\_", " "), body.replace("\\_", " ")
    size = r"\small"
    for cmd in (r"\scriptsize", r"\footnotesize", r"\small"):
        if cmd in src[:t0]:
            size = cmd
            break
    m = re.search(r"\\setlength\{\\tabcolsep\}\{[^}]*\}", src[:t0])
    sep = m.group(0) if m else ""
    out = ("% Re-wrapped by report/make_tables.py from outputs/tables/" + name + ".tex (content unchanged).\n"
           "\\begin{table}[H]\n\\centering" + size + (sep and "\n" + sep) + "\n\\caption{" + caption + "}\n"
           + (f"\\label{{{label}}}\n" if label else "")
           + "\\begin{adjustbox}{max width=\\linewidth}\n" + body + "\n\\end{adjustbox}\n"
           + (after + "\n" if after else "") + "\\end{table}\n")
    write(f"app_{name}.tex", out)


def appendix_tables() -> None:
    for n in APPENDIX_TABLES:
        rewrap(n)


if __name__ == "__main__":
    table_signals()
    table_time()
    table_frozen()
    table_m1_cross()
    table_ledgers()
    m7_bodies()
    appendix_tables()
