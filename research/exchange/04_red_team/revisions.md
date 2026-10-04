# Revisions to the report after exchange 04 (red team)

These are the edits to `report/report.tex` that survived my check of Claude's red team (`evaluation.md`). Each one is stored as an exact (old, new) pair in `checks/fc04_apply_revisions.py`, which applies E1 to E10 to a copy of the file and refuses to touch the real one. Applied to a copy, the report compiles with tectonic with no errors and no overfull boxes, the executive summary still fits on page 1, Section 1 grows by the Table 3 row to about 4.8 pages, and Section 2 still runs about 3.9 pages (bottom of page 6 to three-quarters down page 10), inside its four-page limit. The one layout cost: the Section 2 heading now sits at the foot of page 6 with one sentence under it.

Source tags: **[M#]** a number already in a verified module table; **[derived]** arithmetic on verified numbers; **[fc04]** a new number from `checks/fc04_checks.py` (key in `checks/out/fc04_results.json`). Section 1.3 admits a number only after independent code produced it too, so every [fc04] number needs a verifier re-run before submission (list at the end).

## Edits, in order of effect on the grade

**E1. Executive summary: data sentence and the four reasons** (Claude claims 1, 3, 4 and 5; its edit 2 in corrected form). Replaces the text from "The study uses Fama--French industry..." through "...fare no better. In short:". The verdict stays unqualified; the untimed short now carries its own number, so "Do not implement" covers the position as well as the timing.

```latex
The study uses Fama--French industry and factor returns, FRED news and macro series, two climate-concern indices (MCCC and CPU) and EPA supply-chain emission factors. Every threshold, percentile and hedge uses only past data (macro series are final vintages and emissions a static snapshot), p-values come from small-sample $t$ distributions, each module names a primary test (only the frozen test's is timestamped), and an independent verifier rebuilt each module's headline numbers. The recommendation is \textbf{Do not implement}, for four reasons. First, the ``attention'' series is FRED's equity-volatility news tracker for energy and environmental regulation (identical in 500 of 500 months); its z-score is uncorrelated with media climate concern ($r=-0.0004$), its weak link to climate policy uncertainty ($r=0.123$, Holm $p=0.074$) runs through overall volatility news, and the same machinery fed either climate measure earns 0 of 12 validation alphas with $t\ge1.96$. Second, the rule frozen before its test window earns $-0.18$\% a year over 1994--2009 ($t=-0.27$, shuffle $p=0.48$); that window detects only an edge of about 1.9\% a year with 80\% power, so the fail excludes a large edge, not a small one. Third, most of the COVID gain came from the position, not the timing: the rule's edge over an untimed short of the same leg is $+1.84$\% a year ($t=0.87$; 95\% interval $-2.6$\% to $+6.2$\%). Fourth, every one of our team's timed rules lost over the 2022--2026 holdout, before costs as well as after (Pure 6m: FF3 alpha $-1.97$\% a year, $t=-1.30$, six entries), the untimed short lost too ($-1.72$\%, $t=-1.09$), and rates do not explain the loss; the 900 net-of-cost variants of the six rules share that one 48-month window, so their common sign is one result, not 900. Carbon-aware industry momentum (FF5+UMD alpha 1.74\%, $t=1.09$) and shrinkage timing (out-of-sample $R^2$ of 0.000\%) add nothing. In short:
```

Sources: CPU [M1]; 1.9% [derived: M8 alpha −0.1818%, t −0.2661, so s.e. 0.683% and (2 + 0.84) × 0.683]; COVID interval [derived: M1b edge 1.841%, t 0.871, t(20)]; −1.97% and −1.72% [M3, Table 5]; six entries [fc04]; 1.74% [M5]; 0.000% [M6].

**E2. Section 2.3, the holdout paragraph** (claim 1; alternative 2). Replaces the paragraph that opens "The holdout loss is residual Brown performance plus costs, not rates." The count of 900 becomes a statement about one window, and the lead rule gets its interval.

```latex
\textbf{The holdout loss is residual Brown performance plus costs, not rates, and it is one result, not 900.} Corrected Pure 6m has an FF3 alpha of $-1.97$\% a year ($t=-1.30$; 95\% interval $-5.0$\% to $+1.1$\%) from six entries and 32 months in position, and one principal component carries 90\% of the corrected rules' holdout variance, so the common sign of the 900 variants is robustness of sign, not replication. Adding BOND and UMD makes every alpha more negative (smallest Holm $p=0.155$). For Pure 6m, net $-1.84$\% = leakage $-0.24$\% + residual $-1.14$\% $-$ cost 0.46\%, and Steel alone carries the gross loss ($-1.37$ of $-1.38$ points).
```

Sources: interval [derived: M3 s.e. 1.51%, t(44)]; 32 months, 90%, Steel [fc04]. Dropped to make room: "rates moved holdout returns by at most about half a point a year" and the hedged leg's +2.82% (both remain in `modules/M3_alpha_beta/FINDINGS.md`).

**E3. Section 2.5, power of the frozen test** (claim 2). Fixes my own error: "+0.9%" was the shuffle's bar, not the pass bar. Replaces "Power was limited (a pass needed about $+0.9$\% a year) ... a fail is not weakened."

```latex
Power was limited: the $t$ bar needed about $+1.4$\% a year and the shuffle $+0.9$\%, and only an edge near 1.9\% passes with 80\% probability, so the fail excludes a large edge, not a small one. It contradicts no in-sample edge either: on the seen 2010--2022 window the rule's timing alpha was already $-0.12$\% ($t=-0.19$).
```

Sources: +1.4% and 1.9% [derived, as E1]; +0.9% and −0.12% [M8, dry run]. Claude's independent implementation (−0.19%, t −0.25) leaves this paragraph; it stays in Table 3 and Section 2.8.

**E4. Section 2.4, COVID** (claim 3). Adds the edge's interval and pays for E2 and E3 by shortening two sentences; the leakage split stays in the Figure C.7 caption.

```latex
the rule's paired edge is $+1.84$\% a year ($t=0.87$; 95\% interval $-2.6$\% to $+6.2$\%), or $+0.42$\% without March and April 2020, and Pure 6m held the always-short position in all 24 months (Figure~\ref{fig:attribution}). The window cannot separate a climate trigger from being short the Brown residual: overall EMV reproduces the gain in 4 of 6 rules, and for Original 3m CPU matches it.
```

The 71% stays in the body as description. Its block-bootstrap 90% interval is −36% to 233% [fc04], too wide to carry a headline, so it leaves the summary.

**E5. Section 2.1 and Appendix C.1, what is not volatility in the signal** (claim 4; alternative 1). Answers Claude's best conceptual point, that the 83% of the signal's variance that is not volatility could be transition-policy news.

In Section 2.1, after "(partial correlation 0.05)":
```latex
; its topic share, the part that is not volatility news, correlates 0.03 with CPU.
```
In Appendix C.1, after "...and it is unrelated to climate concern.":
```latex
Same-month slopes of GB on MCCC and CPU shocks have the wrong sign ($t=-0.49$ and $-1.23$), so a faster trade would not have caught a \citet{pst2022} repricing on these legs.
```
Sources: 0.03 [M1, share against z_CPU, p 0.62]; slopes [M1, Q6a].

**E6. Section 2.9, verdict scope and the case against** (Section 3 of the reply, in corrected form). Replaces "\textbf{Do not implement.}" with:

```latex
\textbf{Do not implement}, timed or untimed. The strongest case against it, our team's signal lagged, has a timing alpha of $+0.36$\% ($t=0.70$) over the two windows it was not designed on.
```
Source: +0.36% [fc04]; its 1994–2009 part (+0.69%, t 1.00) is already in Table 6.

**E7. Section 2.8, one sentence on exchange 04.** Replaces the 04 half of the `EXCHANGE-03/04-PENDING` comment; the 03 half stays open.

```latex
Exchange 04, a red team of this draft, rewrote five sentences of the summary, but the result it said would reverse the verdict is noise ($+1.07$\%, $t=0.79$).
```
Source: +1.07% [fc04].

**E8. Table 3, the exchange 04 row.** Splits the pending "03, 04" row; 03 stays pending.

```latex
03 Robustness design & \pending{exchange 03} & & & \\
04 Red team & Break ``Do not implement'': five weak claims, four alternatives, three edits (782 words) & A 1,340-word review (cap 1,200) with replacement text & A holdout fix for a rule that never traded; a 2.4-SE claim on the wrong comparator; a sign-only reversal test & Five summary rewordings; the holdout interval; the frozen test's power \\
```

**E9. Appendix C.2, Figure C.3 caption.** After "$t=0.87$" add ", 95\% interval $-2.6$\% to $+6.2$\%".

**E10. Section 2.7, Limitations** (claim 2, the valid half). E2 now shows the holdout's interval, so the holdout-power clause gives way to the pre-2010 caveat. Replaces "A 48-month holdout has an expected $t$ ... 12 to 24 observations." with:

```latex
COVID and recent-window inference rests on 12 to 24 observations, and 1994--2009 predates the concern shocks that \citet{pst2022} use to explain 2012--2020 green returns.
```

**E11. Appendix A.** Add a `BOXES["04"]` entry to `report/build_transcripts.py` and rerun it; the four-line box reads:
- Asked: a red team of the draft summary and its claims: five weakest claims ranked by effect on the verdict, at most four alternative explanations with separating predictions, the strongest case against "Do not implement" and the one result that would reverse it, three replacement edits, and its two least certain assumptions.
- Came back: a 1,340-word review (cap 1,200) with five ranked claims, four alternatives, a narrowed-verdict argument whose reversal test was a positive holdout alpha for the untimed EPA-ranked short, and three replacement texts.
- Verified: every criticism checked against the module outputs, and the missing tests run (`checks/fc04_checks.py`): holdout paths and intervals, frozen-test power, a COVID bootstrap, trigger overlap, oil and breakeven controls, the frozen rule on the EPA leg, the untimed EPA short, and our team's signal on both unseen windows.
- Kept: five rewordings of the executive summary, the holdout interval and path count, and a corrected power statement for the frozen test; not its holdout fix, its 2.4-standard-error comparison or its sign-only reversal test.

## Not adopted

1. **"Do not implement the timed rule" (its edit 1).** Too narrow: the untimed short lost in the holdout too (−1.72%, t −1.09). Its wording also calls the EPA spread "an EPA-ranked Brown leg"; the 4.7% belongs to the Green-minus-Brown spread, whose holdout alpha comes from the Green leg (+3.29%, t 1.36, against −0.62% for Brown) [M4].
2. **"About [2.4] standard errors below its validation alpha" and "the frozen specification's 2022–2026 alpha" (its edit 2).** The first compares the frozen rule's timing alpha with a mean strategy alpha of another signal; the second does not exist, because the frozen rule is off from 2022-04 and holds a position in 0 of 48 holdout months [fc04].
3. **"The 1994–2009 test is informative and the holdout only weakly so" (its edit 3).** The lead holdout alphas have t of −1.30 to −1.90, and the frozen test cannot contradict an in-sample edge the rule never had. Its "one result, not 900" point is adopted as the E2 claim head instead.
4. **Oil or breakevens in the hedge (alternative 3).** Checked, not added: oil in the evaluation trims Pure 6m's holdout alpha from −1.97% to −1.50% (t −0.88), breakevens add nothing once oil is in (t 0.54), and M2's commodity hedge already left every holdout alpha negative [fc04; M2].
5. **The EPA leg as the missing piece (alternative 4) and its reversal test.** The frozen rule on the EPA leg earns −0.01% over 1994–2009 (t −0.01) and +0.35% over 2010–2022 (t 0.45); the untimed EPA short earns +1.07% in the holdout (t 0.79) after −1.57% over 1994–2009 (t −0.74) [fc04]. A positive sign on 48 months reverses nothing.
6. **Judging the EPA spread against "a family of 23,923 tests".** The report corrects within pre-specified families; M4's primary is a single test with p = 0.129, which does not need the ledger to fail.

## [fc04] numbers to verify before submission

| Number | Used in | Key in `out/fc04_results.json` |
|---|---|---|
| six entries, 32 months in position | E1, E2 | `holdout_lead_rules.corrected_6m` |
| 90% first principal component (Original = Pure in the corrected holdout is already in M3) | E2 | `holdout_paths.corrected` |
| Steel −1.37 of −1.38 gross points | E2 | `holdout6_split` |
| +0.36% (t 0.70) on the two unseen windows | E6 | `team_lagged6_timing.unseen_pooled` |
| +1.07% (t 0.79) untimed EPA short, holdout | E7, not adopted 5 | `always_short_EPA_brown.holdout` |
| −36% to 233% bootstrap interval on the 71% | not in the report | `covid` |
| 0 of 48 holdout months in position for the frozen rule | not adopted 2 | `frozen_rule_holdout` |

The script reproduces M8's frozen alpha (−0.1818%, t −0.2661), M3's corrected holdout alphas and Table 5's COVID and always-short alphas exactly, so the engine is the verified one; only the new cuts of it need a second pair of eyes.
