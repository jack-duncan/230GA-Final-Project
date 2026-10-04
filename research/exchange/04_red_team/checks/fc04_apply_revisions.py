"""Exchange 04: the report edits from revisions.md as exact (old, new) pairs, applied to a COPY of report.tex.

Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/04_red_team/checks/fc04_apply_revisions.py <copy/report.tex>
It refuses to touch research/report/report.tex itself; the orchestrator applies the edits to the real file.
Each pair must match exactly once. Numbers tagged [fc04] in revisions.md come from fc04_checks.py.
"""
from __future__ import annotations

import pathlib
import sys

EDITS: list[tuple[str, str, str]] = []

# E1: executive summary (ChatGPT claims 1, 3, 4, 5; its edit 2 in corrected form)
EDITS.append(("E1 executive summary",
r"""The study uses Fama--French industry and factor returns, FRED news and macro series, two climate-concern indices (MCCC and CPU) and EPA supply-chain emission factors; every inference uses real-time inputs and small-sample p-values, each module fixes a primary test, and an independent verifier rebuilt each module's headline numbers. The recommendation is \textbf{Do not implement}, for four reasons. First, the ``attention'' series is FRED's equity-volatility news tracker for energy and environmental regulation (identical in 500 of 500 months), its z-score is uncorrelated with media climate concern ($r=-0.0004$), and the same machinery fed genuine climate measures earns 0 of 12 validation alphas with $t\ge1.96$. Second, the rule frozen before its test window earns $-0.18$\% a year over 1994--2009 ($t=-0.27$, shuffle $p=0.48$). Third, the COVID gain belongs to the position: an untimed short of the same leg earns 71\% of it, and the rule's edge over that short is $+1.84$\% a year ($t=0.87$). Fourth, every timed rule has a negative 2022--2026 holdout alpha in all 900 net-of-cost configurations, all 28 zero-cost runs are negative too, and rates do not explain the loss. Carbon-aware industry momentum and shrinkage-based timing on the same data fare no better. In short:""",
r"""The study uses Fama--French industry and factor returns, FRED news and macro series, two climate-concern indices (MCCC and CPU) and EPA supply-chain emission factors. Every threshold, percentile and hedge uses only past data (macro series are final vintages and emissions a static snapshot), p-values come from small-sample $t$ distributions, each module names a primary test (only the frozen test's is timestamped), and an independent verifier rebuilt each module's headline numbers. The recommendation is \textbf{Do not implement}, for four reasons. First, the ``attention'' series is FRED's equity-volatility news tracker for energy and environmental regulation (identical in 500 of 500 months); its z-score is uncorrelated with media climate concern ($r=-0.0004$), its weak link to climate policy uncertainty ($r=0.123$, Holm $p=0.074$) runs through overall volatility news, and the same machinery fed either climate measure earns 0 of 12 validation alphas with $t\ge1.96$. Second, the rule frozen before its test window earns $-0.18$\% a year over 1994--2009 ($t=-0.27$, shuffle $p=0.48$); that window detects only an edge of about 1.9\% a year with 80\% power, so the fail excludes a large edge, not a small one. Third, most of the COVID gain came from the position, not the timing: the rule's edge over an untimed short of the same leg is $+1.84$\% a year ($t=0.87$; 95\% interval $-2.6$\% to $+6.2$\%). Fourth, every one of our team's timed rules lost over the 2022--2026 holdout, before costs as well as after (Pure 6m: FF3 alpha $-1.97$\% a year, $t=-1.30$, six entries), the untimed short lost too ($-1.72$\%, $t=-1.09$), and rates do not explain the loss; the 900 net-of-cost variants of the six rules share that one 48-month window, so their common sign is one result, not 900. Carbon-aware industry momentum (FF5+UMD alpha 1.74\%, $t=1.09$) and shrinkage timing (out-of-sample $R^2$ of 0.000\%) add nothing. In short:"""))

# E2: Section 2.3, holdout paragraph (claim 1; alternative 2)
EDITS.append(("E2 section 2.3 holdout",
r"""\textbf{The holdout loss is residual Brown performance plus costs, not rates.} None of the 900 net-of-cost holdout alphas of the six timed rules is positive; adding BOND and UMD makes every one more negative (smallest Holm $p=0.155$), and rates moved holdout returns by at most about half a point a year. For Pure 6m, net $-1.84$\% = leakage $-0.24$\% + residual $-1.14$\% $-$ cost 0.46\%: the FF3-hedged Brown leg beat its hedge (alpha $+2.82$\%, $t=0.95$).""",
r"""\textbf{The holdout loss is residual Brown performance plus costs, not rates, and it is one result, not 900.} Corrected Pure 6m has an FF3 alpha of $-1.97$\% a year ($t=-1.30$; 95\% interval $-5.0$\% to $+1.1$\%) from six entries and 32 months in position, and one principal component carries 90\% of the corrected rules' holdout variance, so the common sign of the 900 variants is robustness of sign, not replication. Adding BOND and UMD makes every alpha more negative (smallest Holm $p=0.155$). For Pure 6m, net $-1.84$\% = leakage $-0.24$\% + residual $-1.14$\% $-$ cost 0.46\%, and Steel alone carries the gross loss ($-1.37$ of $-1.38$ points)."""))

# E3: Section 2.5, power of the frozen test (claim 2; corrects my "+0.9%")
EDITS.append(("E3 section 2.5 power",
r"""Power was limited (a pass needed about $+0.9$\% a year), but no alternative reading comes near $t=2$, and ChatGPT's independent implementation agrees ($-0.19$\%, $t=-0.25$). A pass would have been weak evidence; a fail is not weakened.""",
r"""Power was limited: the $t$ bar needed about $+1.4$\% a year and the shuffle $+0.9$\%, and only an edge near 1.9\% passes with 80\% probability, so the fail excludes a large edge, not a small one. It contradicts no in-sample edge either: on the seen 2010--2022 window the rule's timing alpha was already $-0.12$\% ($t=-0.19$)."""))

# E4: Section 2.4, COVID interval, with a cut
EDITS.append(("E4 section 2.4 COVID",
r"""the rule's paired edge is $+1.84$\% a year ($t=0.87$), or $+0.42$\% without March and April 2020. Pure 6m held the always-short position in 24 of 24 months, and its gain came through leakage of the lagged FF3 hedge (market 1.97 and size 2.14 of 6.87 points), not momentum. The window cannot separate a climate trigger from being short the Brown residual: under real-time timing overall EMV reproduces the gain in 4 of 6 rules, exactly the pre-specified boundary, while for Original 3m the placebos fall short and CPU matches it.""",
r"""the rule's paired edge is $+1.84$\% a year ($t=0.87$; 95\% interval $-2.6$\% to $+6.2$\%), or $+0.42$\% without March and April 2020, and Pure 6m held the always-short position in all 24 months (Figure~\ref{fig:attribution}). The window cannot separate a climate trigger from being short the Brown residual: overall EMV reproduces the gain in 4 of 6 rules, and for Original 3m CPU matches it."""))

# E5: Section 2.1 and Appendix M1, the non-volatility part of the signal and the same-month test (claim 4; alternative 1)
EDITS.append(("E5a section 2.1 topic share",
r"""a link that runs through overall volatility news (partial correlation 0.05).""",
r"""a link that runs through overall volatility news (partial correlation 0.05); its topic share, the part that is not volatility news, correlates 0.03 with CPU."""))
EDITS.append(("E5b appendix M1 same-month slopes",
r"""it is overall volatility news plus a topic share, and it is unrelated to climate concern.""",
r"""it is overall volatility news plus a topic share, and it is unrelated to climate concern. Same-month slopes of GB on MCCC and CPU shocks have the wrong sign ($t=-0.49$ and $-1.23$), so a faster trade would not have caught a \citet{pst2022} repricing on these legs."""))

# E6: Section 2.9, verdict scope and the strongest case against it (section 3 of the reply)
EDITS.append(("E6 section 2.9 verdict",
r"""and the one clean test failed. \textbf{Do not implement.} The playbook""",
r"""and the one clean test failed. \textbf{Do not implement}, timed or untimed. The strongest case against it, our team's signal lagged, has a timing alpha of $+0.36$\% ($t=0.70$) over the two windows it was not designed on. The playbook"""))

# E7: Section 2.8, one sentence on exchange 04 (the 03 half of the placeholder stays open)
EDITS.append(("E7 section 2.8 exchange 04",
r"""that is a result about these prompts, not the tool. %% EXCHANGE-03/04-PENDING:""",
r"""that is a result about these prompts, not the tool. Exchange 04, a red team of this draft, rewrote five sentences of the summary, but the result it said would reverse the verdict is noise ($+1.07$\%, $t=0.79$). %% EXCHANGE-03-PENDING (04 done):"""))

# E8: Table 3, the exchange 04 row (03 stays pending)
EDITS.append(("E8 table 3 row",
r"""03, 04 & \pending{robustness design; red team of this draft} & & & \\""",
r"""03 Robustness design & \pending{exchange 03} & & & \\
04 Red team & Break ``Do not implement'': five weak claims, four alternatives, three edits (782 words) & A 1,340-word review (cap 1,200) with replacement text & A holdout fix for a rule that never traded; a 2.4-SE claim on the wrong comparator; a sign-only reversal test & Five summary rewordings; the holdout interval; the frozen test's power \\"""))

# E9: Appendix M1b, COVID figure caption
EDITS.append(("E9 appendix M1b caption",
r"""and the rule's edge over it ($+1.84$\% a year, $t=0.87$) is within noise.}""",
r"""and the rule's edge over it ($+1.84$\% a year, $t=0.87$, 95\% interval $-2.6$\% to $+6.2$\%) is within noise.}"""))

# E10: Section 2.7, limitations: swap the holdout-power clause (now in E2) for the pre-2010 caveat (claim 2)
EDITS.append(("E10 section 2.7 limitations",
r"""A 48-month holdout has an expected $t$ of about twice the Sharpe ratio, so it cannot confirm a small edge, and COVID and recent-window inference rests on 12 to 24 observations.""",
r"""COVID and recent-window inference rests on 12 to 24 observations, and 1994--2009 predates the concern shocks that \citet{pst2022} use to explain 2012--2020 green returns."""))


def main(path: str) -> None:
    p = pathlib.Path(path).resolve()
    if p == pathlib.Path("/home/hashim/projects/GA/project/research/report/report.tex"):
        sys.exit("refusing to edit the real report; pass a copy")
    s = p.read_text()
    for name, old, new in EDITS:
        k = s.count(old)
        if k != 1:
            sys.exit(f"{name}: old text found {k} times")
        s = s.replace(old, new)
        print(f"{name}: applied ({len(old.split())} -> {len(new.split())} words)")
    p.write_text(s)


if __name__ == "__main__":
    main(sys.argv[1])
