"""Exchange 04, round 2: the report edits from revisions.md as exact (old, new) pairs, applied to a COPY of report.tex.

Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/04_red_team/checks/fc04b_apply_revisions.py <copy/report.tex>
It refuses to touch research/report/report.tex itself; the orchestrator applies the edits to the real file.
Each old string must match exactly once. Numbers tagged [fc04b] in revisions.md come from fc04b_checks.py
(out/fc04b_results.json); [fc04] numbers come from round 1's fc04_checks.py.
"""
from __future__ import annotations

import pathlib
import sys

EDITS: list[tuple[str, str, str]] = []

# ---------------------------------------------------------------- executive summary (page 1, about 80 words of room)
EDITS.append(("S1 summary: legs (weak claim 5)",
r"""five high-emission industries (utilities, shipbuilding and railroad equipment, aircraft, steel, construction materials)""",
r"""five industries our team ranked high-emission (utilities, shipbuilding and railroad equipment, aircraft, steel, construction materials; two rank mid-table on EPA factors)"""))

EDITS.append(("S2 summary: verdict sentence, label versus returns (weak claim 3)",
r"""The recommendation is \textbf{Do not implement}, for four reasons.""",
r"""The recommendation is \textbf{Do not implement}: the label is wrong, and under any label the returns do not pay."""))

EDITS.append(("S3 summary: in plain terms (weak claim 3; not its edit 3)",
r"""In plain terms, the rule shorts value-tilted utility and industrial stocks after stock-market volatility makes the news.""",
r"""In plain terms, the rule shorts hedged utility and industrial stocks after stock-market volatility makes the news."""))

EDITS.append(("S4 summary: reason 2 (weak claim 1; the idea of its edit 1, without the cost comparison)",
r"""Second, a cleaner version frozen before its test (the regulation share of volatility news, lagged one month) has a timing alpha of $-0.18$\% a year over 1994--2009 ($t=-0.27$; $p=0.48$ against random re-datings of its holding periods); that window detects an edge of about 1.9\% a year with 80\% power, so the fail excludes a large edge, not a small one.""",
r"""Second, timing earns nothing detectable on windows no rule was designed on: a cleaner version frozen before its test (the regulation share of volatility news) has a timing alpha of $-0.18$\% a year over 1994--2009 ($t=-0.27$; $p=0.48$ against random re-datings, whose median is $-0.22$\%), and our team's signal, lagged, earns $+0.69$\% there ($t=1.00$) and $-1.11$\% in the holdout ($t=-1.13$). Pooled, these windows detect only edges above about 1.5\% a year with 80\% power."""))

EDITS.append(("S5 summary: reason 3, COVID (weak claim 4)",
r"""Third, most of the COVID gain came from the position: the rule's alpha over an untimed short of the same leg is $+1.84$\% a year ($t=0.87$; 95\% interval $-2.6$\% to $+6.2$\%).""",
r"""Third, COVID cannot certify the timing: an untimed short of the same leg had an alpha of 4.54\% a year ($t=1.96$), and the rule's edge over it is $+1.84$\% ($t=0.87$), or 3.0\% over an exposure-matched short ($t=1.67$)."""))

EDITS.append(("S6 summary: reason 4, holdout (weak claim 2; not its edit 2)",
r"""Fourth, every one of our team's timed rules lost over the 2022--2026 holdout, before costs as well as after (6-month rule: FF3 alpha $-1.97$\% a year, $t=-1.30$), the untimed short lost too ($-1.72$\%, $t=-1.09$), and rates do not explain the loss; the 900 net-of-cost variants share that one 48-month window, so their common sign is one result.""",
r"""Fourth, every one of our team's timed rules lost over the 2022--2026 holdout, before costs as well as after (6-month rule: FF3 alpha $-1.97$\% a year, $t=-1.30$); the untimed short lost too ($-1.72$\%, $t=-1.09$), and the timing lost a further 1.0\% to 1.7\% a year against an exposure-matched short ($t=-0.99$ to $-1.72$). Rate factors and dropping any one industry leave the alphas negative, and the 900 net-of-cost variants share one 48-month window, so their sign is one result."""))

EDITS.append(("S7 summary: alternatives (alternative 1, tested)",
r"""Of the alternatives, shrinkage timing collapses to the historical mean,""",
r"""Of the alternatives, climate indices on EPA-ranked legs add no timing edge, shrinkage timing collapses to the historical mean,"""))

EDITS.append(("S8 summary: which window is left (weak claim 1; section 3 of the reply)",
r"""benchmark timing against the always-short position, and spend the last unused window on one frozen rule.""",
r"""benchmark timing against the always-short position, and spend the only window left, the live record, on one frozen rule."""))

# ---------------------------------------------------------------- Section 1 (Table 3 row; pages 2 to 6, full)
EDITS.append(("T1 Table 3: exchange 04 row, both rounds",
r"""04 Red team & ``Break the conclusion before a grader does. No summary, no praise'' (795 words) & 1,340 words (cap 1,200) with replacement text & A fix for a rule that never traded in the holdout; a 2.4-SE claim on the wrong comparator; a sign-only reversal test & Five summary rewordings; the holdout interval; the frozen test's power \\""",
r"""04 Red team, two rounds & ``Break the conclusion before a grader does'' (795 words); round 2 added the best evidence against me (798) & 1,340 and 1,091 words (caps 1,200 and 1,000) with replacement text & A fix for a rule that never traded; a 2.4-SE claim on the wrong comparator; a pooled edge read as positive twice; costs deducted twice & Thirteen summary rewordings; the holdout interval and timing loss; three alternatives tested and retired \\"""))

# ---------------------------------------------------------------- Section 2 (pages 7 to 10, under two lines of room)
EDITS.append(("B1 section 2.1: EPA legs with genuine climate measures (alternative 1, tested; details in Appendix M4)",
r"""This is a null about our emissions-sorted industry legs, not a refutation of \citet{pst2022}.""",
r"""The same holds on EPA-ranked legs (Appendix~\ref{app:m4}), so this is a null about industry legs, not a refutation of \citet{pst2022}."""))

EDITS.append(("B2a section 2.3: shorter gloss (pays for B2c)",
r"""Corrected Pure 6m (the table's Original 6m, since the two coincide in the holdout) has""",
r"""Corrected Pure 6m (identical to the table's Original 6m in the holdout) has"""))

EDITS.append(("B2b section 2.3: the claim head already says one result (pays for B2c)",
r"""One principal component carries 90\% of the corrected rules' holdout variance, so the common sign of the 900 variants is robustness of sign, not replication.""",
r"""One principal component carries 90\% of the corrected rules' holdout variance."""))

EDITS.append(("B2c section 2.3: Steel split versus rebuilt legs, and the holdout timing loss (weak claim 2)",
r"""residual $-1.14$\% and cost 0.46\%, and Steel alone carries the gross loss ($-1.37$ of $-1.38$ points).""",
r"""residual $-1.14$\% and cost 0.46\%. Steel carries the gross loss in that split ($-1.37$ of $-1.38$ points), yet the rule rebuilt without any one industry still loses, and timing lost 1.0\% to 1.7\% a year against an exposure-matched short ($t=-0.99$ to $-1.72$; Appendix~\ref{app:m3})."""))

EDITS.append(("B2d section 2.3: tighter recent-window sentences (pays for B2c)",
r"""Over the last 18 months every timed rule lost money and the raw spread lost 14.7\% a year as Brown beat Green. Twelve months are too few to split a loss into alpha and beta (Original 3m nets $-5.21$\% with an alpha of $+1.20$\%, $t=0.30$).""",
r"""Over the last 18 months every timed rule lost and the raw spread lost 14.7\% a year; twelve months are too few to split a loss into alpha and beta (Original 3m nets $-5.21$\%, alpha $+1.20$\%, $t=0.30$)."""))

EDITS.append(("B3a section 2.4 heading (weak claim 4)",
r"""\subsection{COVID rewarded the position, not the timing}""",
r"""\subsection{COVID cannot separate the position from the timing}"""))

EDITS.append(("B3b section 2.4 claim paragraph: both benchmarks (weak claim 4)",
r"""\textbf{The always-short position earns most of the COVID gain} (Figure~\ref{fig:covid}; Table~\ref{tab:time}). Original 3m's COVID alpha is 6.38\% ($t=3.62$) and the always-short position's 4.54\% ($t=1.96$), 71\% of it. Its paired alpha over that position is $+1.84$\% a year ($t=0.87$; 95\% interval $-2.6$\% to $+6.2$\%), or $+0.42$\% without March and April 2020. Against the $\pi$-scaled benchmark the raw edge is larger (5.4\% a year, $t=2.35$) but falls to 3.0\% once in-window factors enter ($t=1.67$, $p=0.11$), and Pure 6m held the always-short position in all 24 months, earning mostly hedge leakage (Figure~\ref{fig:attribution}). The window cannot separate a climate trigger from being short the Brown residual.""",
r"""\textbf{An untimed short earns 71\% of the COVID alpha} (Figure~\ref{fig:covid}; Table~\ref{tab:time}). Original 3m's COVID alpha is 6.38\% ($t=3.62$) and the always-short position's 4.54\% ($t=1.96$). The rule's paired alpha over that position is $+1.84$\% a year ($t=0.87$; 95\% interval $-2.6$\% to $+6.2$\%), or $+0.42$\% without March and April 2020. Against the $\pi$-scaled, exposure-matched short the raw edge is larger (5.4\% a year, $t=2.35$) but falls to 3.0\% once in-window factors enter ($t=1.67$, $p=0.11$). With in-window factors neither edge is significant, and Pure 6m held the always-short position in all 24 months (Figure~\ref{fig:attribution})."""))

EDITS.append(("B4 section 2.8: exchange 04, both rounds",
r"""The exchange 04 red team rewrote five summary sentences well, but the result it said would reverse the verdict, a positive holdout alpha for the untimed EPA short, is noise ($+1.07$\%, $t=0.79$).""",
r"""The exchange 04 red team, run twice, prompted thirteen summary rewordings, but its cases against the verdict rested on misread numbers, such as a pooled $+0.36$\% read as positive in both windows."""))

EDITS.append(("B5 section 2.9: the strongest case against, split by window (case against, first bullet)",
r"""has a timing alpha of $+0.36$\% ($t=0.70$) on the two windows it was not designed on.""",
r"""has a timing alpha of $+0.69$\% over 1994--2009 ($t=1.00$) but $-1.11$\% over the holdout ($t=-1.13$)."""))

# ---------------------------------------------------------------- appendices (no page limit)
EDITS.append(("A1 Appendix M3: drop-one holdout (weak claim 2; case against, fourth bullet)",
r"""the gap coming from GS10's monthly averaging.""",
r"""the gap coming from GS10's monthly averaging. Steel carries the corrected 6-month rule's gross holdout loss in the five-industry split ($-1.37$ of $-1.38$ points), but that split is accounting, not a counterfactual: rebuilt without any one Brown industry (leg, hedge and volatility scaling re-estimated), the rule's holdout FF3 alpha is $-1.45$\% to $-2.61$\% for 6-month holds and $-1.26$\% to $-2.43$\% for 3-month holds, 10 of 10 negative. Without Steel the untimed short loses more ($-2.67$\%, $t=-1.66$), and only the timing alpha from M8's attribution regression turns positive ($+0.39$\%, $t=0.38$, against $-1.11$\% with Steel). Against the $\pi$-scaled short with in-window FF3, UMD and BOND, the four corrected discrete rules' holdout timing alphas are $-1.03$\% to $-1.71$\% ($t=-0.99$ to $-1.72$), so the holdout indicts the timing as well as the position (exploratory; \texttt{exchange/\allowbreak 04\_red\_team/\allowbreak checks/\allowbreak fc04b\_checks.py})."""))

EDITS.append(("A2 Appendix M4: genuine climate measures on EPA-ranked legs (alternative 1)",
r"""comes from short CMA and UMD loadings on a 2022 sort applied back to 1970.

\begin{figure}[H]""",
r"""comes from short CMA and UMD loadings on a 2022 sort applied back to 1970.

Exchange 04 asked whether the climate reading fails only because of the legs, so I fed MCCC and CPU through our team's rules on the EPA-ranked legs (exploratory; \texttt{exchange/\allowbreak 04\_red\_team/\allowbreak checks/\allowbreak fc04b\_checks.py}). The same-month GB slopes on real-time concern shocks become more wrong-signed, not less: $-0.51$\% and $-0.29$\% a month per standard deviation ($t=-2.95$ and $-2.17$; with FF3 controls $t=-2.50$ and $-2.05$), against $-0.09$\% and $-0.16$\% on the team legs. All six CPU-timed rules have positive holdout alphas to 2025-10 (0.49\% to 1.97\%, largest $t=1.79$), but the untimed EPA short earns 1.41\% over the same 39 months ($t=1.05$), the timing edge over an exposure-matched short ($\pi$ and FF3 fitted in each window) is $+0.05$\% to $+1.22$\% there (largest $t=1.43$), and over 1994--2009, a window this combination never saw, it is negative in 5 of 6 rules ($-2.59$\% to $+0.15$\%). MCCC timing on the same legs does no better (holdout edges $-1.29$\% to $+0.61$\%). The holdout gain belongs to the EPA position, not the climate timing.

\begin{figure}[H]"""))

def apply(s: str) -> str:
    for name, old, new in EDITS:
        k = s.count(old)
        if k != 1:
            sys.exit(f"{name}: old text found {k} times")
        s = s.replace(old, new)
        print(f"{name}: applied ({len(old.split())} -> {len(new.split())} words)")
    return s


def main(path: str) -> None:
    p = pathlib.Path(path).resolve()
    if p == pathlib.Path("/home/hashim/projects/GA/project/research/report/report.tex"):
        sys.exit("refusing to edit the real report; pass a copy")
    p.write_text(apply(p.read_text()))


if __name__ == "__main__":
    main(sys.argv[1])
