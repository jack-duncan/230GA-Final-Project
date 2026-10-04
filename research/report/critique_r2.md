# Critique of the draft report "Read the Label" (build of 26 Sep 2026, 10:58)

Reviewed: `report/report.tex` (742 lines), `report/appendix_transcripts.tex`, and the compiled `report/report.pdf` (112 pages: title and executive summary p. 1, Section 1 pp. 2 to 6, Section 2 pp. 7 to 10, references pp. 11 to 12, Appendix A pp. 13 to 68, B pp. 69 to 70, C pp. 71 to 96, D pp. 97 to 103, E pp. 104 to 112). I read it against the course brief (`MFE230GA_Final_Project_2025.pdf`), `logs/style_guide.md`, the authentic Ultramarin report, the module `FINDINGS.md` files and the exchange folders wherever a number or claim looked off. This critique replaces the earlier one at this path, which reviewed a 93-page draft.

## Verdict in brief

The draft is much closer than the last one. Every template section is present, there are no placeholders or red notes in the PDF, four ChatGPT exchanges are documented, realized risk and dated recent windows are in the main body, and the prose has no em dashes, no banned transitions and no contractions. Three things still stand between this draft and submission.

1. **The ChatGPT requirement is met only by proxy.** Section 1.5 and the Appendix A provenance note say the replies came from "a language model instructed to answer as ChatGPT, not from a live ChatGPT session". The disclosure is transparent, but a grader reading the brief ("Use at least three substantial ChatGPT interactions") can score the requirement as unmet, and Section 2.8 then evaluates "ChatGPT" while its last sentence says it evaluated a stand-in. This is the largest grading risk in the report.
2. **The AI-use statement is unfinished.** Section 1.3 says an AI coding agent wrote each module's code and that "'I' in this report covers that work", and the source still carries `%% HASHIM-CONFIRM: add one clause on what you checked or decided yourself`. Only Hashim can write that clause.
3. **About a dozen internal contradictions a careful grader can find** (Section 1.4 below), none of which changes the verdict: "the one pre-registered test failed" when there are two pre-registered tests, "every input enters only after its publication date" against the Limitations, five holdout entries on p. 3 against six on p. 7, a style-exposure head that claims a profitability tilt that is not significant, and others.

Both body sections sit at their page caps (Section 1 has about 1 line free, Section 2 about 1.7 lines), so every addition below comes with a cut (Section 4).

---

## 1. Brief compliance

### 1.1 Template checklist

| Brief item | Where | Status | Fix |
|---|---|---|---|
| Executive summary, one paragraph, strategy stated | p. 1 | Present, one paragraph, about 430 words and about 39 numbers | Trim to about 330 words and lead with the thesis (rewrite in 3.1) |
| Explicit "Do not implement" with justification | p. 1 (bold), 2.9 (bold) | Present, four reasons | None |
| What did you try, 2 to 5 pages | pp. 2 to 6 | 5.0 pages, at the cap | Any addition needs a cut (Section 4) |
| a. Ideas, origin | 1.1 | Present (HW1, Pastor et al., team thesis, three conditions) | None |
| b. Data, sources | 1.2, Table 1 | Present (Ken French, FRED, EPA, USEEIO on BEA input-output accounts, MCCC, CPU) | Fix the overclaim in 1.2 (item 1.4.2) |
| c. Risk modeling | 1.4 | Present: rolling 60-month FF3 model named as the risk model, realized volatility, IR and drawdown, COMEQ, BOND, Ferson-Schadt, Lewellen-Nagel | Second paragraph opens with an unsupported claim (item 1.4.9) |
| c. Turnover and costs | 1.4 | Present (2.4 to 5.8 turns, drag at most 0.63%, break-even 40 to 100 bp, 28 cost-free runs defined) | None |
| c. At least 3 high-quality ChatGPT prompts | 1.5, Table 3, App. A | Four exchanges with key prompt lines, word counts, full prompts in App. A | Blocking: live provenance (1.3 below) |
| 3a. Style and risk exposures | 2.2 | Raw spread (FF3, FF5, COMEQ) and the rules' residual HML | Add GB's BOND loading and the COVID UMD and BOND exposures of the traded short; fix the head (item 1.4.5) |
| 3b. Full sample, post-2010, recent 12 to 18 months | 2.3, Table 4 | Present with dates (1993-02 or 1970-01 to 2026-07; 2010-01; 2025-02; 2025-08) | Table 4 caption has no takeaway (3.2) |
| 3c. Robustness and limits | 2.7 | Present: family size, nominal count, survivors, equivalence reading, a concrete Limitations list | Small wording fixes (items 1.4.11, 1.4.12) |
| 3d. ChatGPT evaluation: usefulness, flaws, **adaptations** | 2.8 | Usefulness and flaws present; **adaptations are not stated** anywhere in the main body | Add one sentence on how the prompts changed after each failure (text in 1.3 below) |
| Reflect on strengths and limits as a research assistant | 2.8, last paragraph | Present ("a referee and a second implementation, never a verifier") | Keep; reconcile with provenance |
| Document each interaction: prompt, summarized output, critical evaluation | Table 3, App. A.1 to A.4 | Present for all four | Stale module codes in the exchange 01 evaluation (item 1.4.14) |
| Appendix: transcripts, tables and plots, code | App. A, C, D | Present | Appendix table labels and units (3.2) |

### 1.2 Page limits (measured from the PDF text blocks)

- Executive summary: page 1, one paragraph, text ends 5.6 lines above the bottom margin.
- Section 1: starts at the top of p. 2 and fills p. 6 to within about 1 line of the margin: **5.0 pages (limit 5)**. The `\clearpage` before Section 2 means any overflow pushes Section 2 to p. 8.
- Section 2: pp. 7 to 10, ending about 1.7 lines above the margin: **about 3.95 pages (limit 4)**.
- The fixes below add about 12 lines of text. Section 4 lists cuts that pay for them. Recompile after the edits and confirm that Section 1 ends on p. 6 and Section 2 on p. 10.

### 1.3 The ChatGPT requirement (blocking)

**Problem.** The four exchanges are well designed and well evaluated, but the replies were generated by another model told to answer as ChatGPT (1.5: "The replies came from a language model instructed to answer as ChatGPT, not from a live ChatGPT session"; App. A provenance note; 2.8: "These replies came from a model in ChatGPT's role ... so the verdict describes that role"). The brief's requirement is to use ChatGPT. The appendix even says "Rerunning the prompts in ChatGPT and rebuilding this appendix with report/build_transcripts.py would replace these replies without other changes", which invites the question of why that was not done. The Section 2.8 head ("ChatGPT was a sharp referee...") and the Appendix A evaluations ("ChatGPT wrote a correct backtest...") then attribute to ChatGPT what a stand-in did.

**Fix, preferred.** Paste the prompts in `exchange/0x_*/prompt.md` (and the two follow-ups) into a live ChatGPT session, save the replies over `chatgpt_response.md` and `chatgpt_followup_response.md`, rerun the fact-check scripts where they exist, and rebuild Appendix A with `report/build_transcripts.py`. Then re-derive every ChatGPT-derived number: Table 3 (6 of 52, 8 of 72, 1,772, 1,716 and 1,340 words, the 985-line script, 3.3e-13, the "What was wrong" cells), 2.8 (4 of 6 and 7 of 8 injected bugs, +1.07%), and the four evaluations. Keep the sentence that the 1994 to 2009 rule and the 1931 to 1969 run took their designs from the earlier replies and cannot be re-drawn, because both windows are spent. Delete the last sentence of 2.8 and the "Rerunning the prompts..." sentence in App. A.

**Fix, fallback (if a live rerun is impossible).** Keep the disclosure, but stop attributing the stand-in's behavior to ChatGPT: change the 2.8 head to "The replies were a sharp referee on the numbers they were given...", replace "ChatGPT" with "the reply" or "the model" in the four evaluations, and add to 1.5 one sentence saying why no live session was used. Be aware that this still leaves the requirement unmet in the strict reading.

**Adaptations (brief item 3d), text ready to use.** Put this in 1.5, where Section 1 has room after the cut in 4.1, and point to it from 2.8:

```latex
The prompts changed after each failure. After exchange 01 accepted an unsourced label, exchanges 02 and 03 named each input's FRED series; after its generic ideas, exchange 03 said ``Do not propose new signals'' and accepted ``no candidate can reach implement'' as an answer; and exchange 04 asked it to attack overreach toward my own verdict.
```

Every clause is checked against the prompt files: `EMVENRGYENVREG` appears in the 02 and 03 prompts, the two quotations are in `03_robustness_design/prompt.md` line 28, and `04_red_team/prompt.md` line 19 reads "Overreach toward "Do not implement" counts".

### 1.4 Factual and internal-consistency problems a grader can find

1. **"The one pre-registered test failed" (2.9) is false as written.** The report has two pre-registered, hashed tests, and the 1931 to 1969 momentum run passed (1.3, 2.6, App. E.7). Change to "the pre-registered test of the climate rule failed".
2. **"Every input enters only after its publication date" (1.2, first sentence)** contradicts the Limitations (a static, undated or 2022-vintage emissions snapshot applied back to 1970; final-vintage FRED, EMV and MCCC data; an assumed EMV lag). Replace with: "The study uses only public data (Table~\ref{tab:data}). Returns and macro controls enter only after publication and the EMV trackers are lagged one month; the emissions snapshots are the exception (Section~\ref{sec:robust})."
3. **Five holdout entries (1.2, p. 3) against six entries (2.3, p. 7).** Both are right: M1's five entries (2023-04, 2024-06, 2025-02, 2025-09, 2025-11) are under the team's same-month timing, and the corrected rules add a 2022-08 entry from the July 2022 crossing that the one-month lag moves into the holdout (`exchange/04_red_team/checks/out/fc04_results.json`). In 1.2 write "under our team's timing, with the z-score's scaling frozen at 2021-09 or with zeros treated as missing, the rule enters in the same five holdout months". In 2.3 write "from six entries (the five holdout crossings plus a July 2022 crossing that the lag moves into the holdout)".
4. **"Two input errors" (1.3, first sentence).** The same paragraph says the EMV timing is something "I could not verify", so it is an assumption, not a demonstrated error. Write "two input problems". Also say why the October 2025 CPI is missing: "The October 2025 CPI print, never published because of the federal government shutdown, silenced..." (`logs/replication.md` item 2 gives the cause).
5. **The 2.2 head claims more than the evidence.** "The raw spread is short value, profitability and investment" is followed by "only CMA significant". Change the head to "The raw spread is a short-value bet, and the value tilt lives in the Brown leg." In the same paragraph: "adding COMEQ gives a loading of -0.18" reads as an HML loading; M2's FINDINGS (line 183) show it is the COMEQ loading, so write "and GB loads $-0.18$ on COMEQ ($t=-8.70$)". "GB is long financials" understates the Green leg (entertainment, real estate, drugs, telecom, finance); write "long services and financials". The Brown contribution of -0.437 exceeds the total of -0.298 in magnitude, so add "and the Green side $+0.14$".
6. **The EPA alpha mechanism is misstated (2.6 and App. C.5).** "Its full-sample alpha (4.5%, t = 2.58) comes from short CMA and UMD loadings" reads as if loadings produce alpha. M4's FINDINGS (line 154): the raw mean is 2.5% (t 1.40) and the FF5+UMD alpha is larger only because the spread is short CMA and UMD, which earned positive premia. Write "Its full-sample FF5+UMD alpha (4.5\%, $t=2.58$) exceeds its raw return (2.5\%, $t=1.40$) only because the spread is short CMA and UMD, which earned positive premia, on a 2022 sort applied back to 1970".
7. **"Pre-registered" is used for an untimestamped test.** 2.6 says "Under pre-registered cross-validation the ... ridge", and App. C.7 repeats it, while 1.3 says only the two frozen tests have timestamped pre-registrations. Use "pre-specified" for M6 in both places, and keep "pre-registered" for the two hashed tests only.
8. **"32 of 32 Table 1 cells" (Table 2, Replication row; App. B.1 step 4)** points at this report's Table 1, which is the data table. Write "all 32 cells of the team write-up's Table 1".
9. **1.4, second paragraph, opens with a claim it does not support.** "Wider risk models do not rescue the strategy." is followed only by definitions. Either add the evidence ("with the FF5+UMD+COMEQ hedge every cost-free holdout alpha is still negative, the highest $-0.39$\%") or change the opening to "The wider risk models add three exposures and two decompositions." Also gloss the carbon bound: "a bound $b$ on the book's carbon exposure $c'h$ ($h$ the active weights)".
10. **"900 variants" is never defined** (exec summary, 2.3 twice). M2's FINDINGS (line 15): 900 net-of-cost holdout regressions of the six rules. Write once in 2.3: "the 900 net-of-cost holdout alphas of the six rules in \CR's robustness grid (every combination of legs, hedges, baselines, cost levels and evaluation models)".
11. **"High overall-EMV months" is never defined (2.1).** M1 flags a month as high when overall EMV is above its past-only expanding median. Write "Crossings fall in months when overall EMV is above its past-only median 88\% of the time, against 64.5\% of other months (Fisher $p=0.0006$)." In the first sentence of that paragraph, "On the z-scores of VIX and overall EMV it has $R^2=0.169$" should be "Regressed on the z-scores of VIX and overall EMV, it has $R^2=0.169$".
12. **2.7: authors used as agents, and BH used before it is named.** "Benjamini and Yekutieli (2001) keep none and Benjamini and Hochberg (1995) keep one" reads as if the authors did the keeping, and "(BH 0.72)" appears a sentence earlier. Write "the Benjamini--Hochberg (BH) correction \citep{bh1995} keeps one and the Benjamini--Yekutieli correction \citep{by2001} none", and move the BH definition up. Also say whether the corrected-baseline rules reject too, since "as our team ran them" invites the question of whether the version that rejects most easily was picked. A rough check from Table 4 says they do (Original 6m: FF3 alpha $-1.97$\%, standard error about 1.5\%, so a 90\% upper bound near $+0.6$\% against a margin near 1.1\%), but M7 should confirm it on FF5+UMD before the sentence changes.
13. **Two totals for one census.** 1.3 says "24,404 rows in nine ledgers, 156 of them primary" and 2.7 says "all 23,923 module tests". Both are right (Table E.1: 23,923 module rows plus 481 from M7; 155 plus 1 primaries), but the grader sees two numbers. In 1.3 use "23,923 tests in eight module ledgers, 155 of them primary".
14. **The exchange 01 evaluation uses stale module codes** (App. A.1, "Where each piece went"). It lists the climate-index work under "M1" (the report calls it M1b) and the frozen 1993 to 2009 rule under "M7" (the report calls it M8; M7 is the ledger). Edit `exchange/01_idea_generation/evaluation.md` lines 14 and 17 to M1b and M8, then rebuild with `build_transcripts.py`.
15. **81 or 73 primary alpha tests.** The exchange 03 evaluation says "one-sided Holm and BH on the 81 primary alpha tests"; 2.7 and Table 2 say 73. Add "(73 after removing exact duplicates)" in `exchange/03_robustness_design/evaluation.md`.
16. **The verdict's "two windows" are unnamed (2.9).** Write "on the two windows it was not designed on, 1994--2009 and the 2022--2026 holdout, pooled".

---

## 2. Voice

### 2.1 Measured against the authentic sample

Main-body prose (executive summary through 2.9, excluding tables, captions and math): about 4,100 words in 173 sentences.

| Measure | Draft | Ultramarin report | Reading |
|---|---|---|---|
| Mean / median sentence length | 23.7 / 23 words | about 26 / 23 | Matches |
| Sentences over 40 words | 12 (7%); two over 50, both in the executive summary (60 and 57 words) | uncommon | Split the two long ones (2.5 below) |
| Semicolons per 1,000 words | about 3.7 | about 3.4 | Matches |
| Parentheses per 1,000 words | about 27 | about 18 | Too dense; mostly statistics |
| "X, not Y" per 1,000 words | about 2.4 | about 2.9 | Matches overall, but two in one executive-summary paragraph |
| Colons | about 1 sentence in 5 | about 1 in 3 | Fine |
| Em dashes, contractions, however/moreover/thus/notably, honest/leverage/crucial/reveal/genuine | 0 | 0 | Clean |
| "our team" | 16 in the main body | not applicable | Heavy; use "the team" after the first mention in a paragraph |
| British spelling | "labelled" (report.tex line 639; App. A provenance note), "labelling" (exchange 01 evaluation) | American ("labeled" in his sample) | Fix all three |

Sentence length and connective habits now match him. The remaining gap is density. His paragraphs go claim, two or three numbers, a plain "why", then a short verdict. Several draft paragraphs carry 10 to 14 statistics: 2.1's first paragraph has 12 in about 100 words, 2.4's paragraph has 15, and the executive summary about 39. Cap a sentence at about three numbers and let the table carry the rest.

### 2.2 Passages that read as machine-written or unlike him

| Where | Draft text | Why it reads wrong | Replacement |
|---|---|---|---|
| Exec. summary | "that window detects an edge of about 1.9\% a year with 80\% power, so the fail excludes a large edge, not a small one" | "the fail" as a noun is not his register; this is the red-team model's wording (E1 in `04_red_team/revisions.md`); second "X, not Y" in the paragraph | "The test had 80\% power only against an edge of about 1.9\% a year, but its estimate is negative." |
| 1.3 | "hashed a pre-registration of 32 implementation choices five minutes before its code existed" | Minute-level timing reads as an agent log and draws attention to the pipeline | "Its pre-registration of 32 implementation choices was hashed before its code was written" |
| 1.3 | "one of them, M2's commodity-hedge test, was printed during a code check four minutes before the test was written down" | Forensic detail in the body | Move to App. D; in 1.3 keep "the other modules fixed their primary tests in code without a timestamp" |
| 1.3 | "so ``I'' in this report covers that work" | Defensive, and it contradicts his rule that "I" is for actions he took | Replace with Hashim's own clause on what he decided and checked (blocking fix 2) |
| 2.4 | "By the pre-specified placebo rule the climate reading fails on its boundary" | "fails on its boundary" is private shorthand | "The pre-specified placebo test rejects the climate reading, but only at its threshold: a volatility placebo counts as reproducing the gain if its COVID alpha is positive and at least half the rule's, the reading fails if that happens in 4 of the 6 rules, and overall EMV does it in exactly 4. For Original 3m, where the volatility placebos fall short, CPU matches it." (M1b FINDINGS lines 37 to 38 and 163) |
| 2.4 | "the raw edge is larger (5.4\% a year, $t=2.35$) but falls to 3.0\% once in-window factors enter" | "raw edge", "in-window factors" | "the edge over the exposure-matched benchmark is 5.4\% a year ($t=2.35$) but falls to 3.0\% ($t=1.67$, $p=0.11$) once factors estimated inside the COVID window enter" |
| 2.8 | "aligned on two open readings, its 985-line script reproduced..." | Opaque | "once two choices my prompt had left open were set the same way, its 985-line script reproduced..." |
| 2.8 | "These replies came from a model in ChatGPT's role (Appendix A), so the verdict describes that role." | Undercuts the section's own head | Delete after a live rerun; otherwise see the fallback in 1.3 |
| 2.9 | "Each is an afternoon's check before a desk funds a climate-timing idea." | Aphoristic closer the paragraph has not earned: a frozen out-of-sample test is not an afternoon's work | Cut it, or "None of the three needs new data, and together they would have stopped this trade before it reached a desk." |
| App. C.8 | "birth and modify times 4 ms apart", "confirmed on compiled bytecode", "on-disk birth time now reads 06:05:07" | Reads as a file-system audit, not a research report | One sentence: the specification was hashed (SHA-256 below) before the code was written, the rule ran once, and every rerun reproduces the first-run key; point to `corrections/pre_correction_0341/manifest.json` for the full timeline |
| App. A | "Evaluation (typeset from \texttt{evaluation.md})"; Table A.1 "Counted by this script from the claims table in factcheck.md"; the "Layout and character map" paragraph | Workflow language | "My evaluation"; "Counted from the fact-check's claims table"; cut the character map to one sentence ("Non-ASCII characters are mapped to ASCII so that no glyph is lost."). The strings are in `build_transcripts.py` lines 215, 368 and 405 |
| App. C intro | "Tables whose captions are not written for this report are the module's own output tables, included unchanged apart from plain column labels" | Awkward, and not accurate: the labels are not plain (3.2) | "Tables without a takeaway sentence are the modules' own output tables." |

The voice is otherwise his: claim-first bold heads written as findings, "X, not Y" scoping ("a null about our emissions-sorted industry legs, not a refutation of Pastor et al."), negative results stated flatly, the slogan returning at the end. Keep "In plain terms, the rule shorts value-tilted utility and industrial stocks after stock-market volatility makes the news."; it is the clearest sentence on page 1 ("In effect," is closer to his usual transition).

### 2.3 Jargon and coined labels a grader must decode

| Term | Where | Fix |
|---|---|---|
| "Team z" | Table 2, M1 row | "Team signal's z-score" |
| "shock-purged mean" | 1.1 | "mean return after removing concern shocks" |
| "the last unused window" | exec. summary, 2.9 | "a window it was not designed on" (1994 to 2009 is not unused: the team's macro-state notebook used 192 of its months, as 1.3 discloses) |
| "the fail" | exec. summary | "the failure" |
| "robustness of sign, not replication" | 2.3 | Acceptable, but only once; the exec. summary sentence on the 900 variants can go (3.1) |
| "null-seed counts", "null-seed size check" | 1.3, Table 3 | "a size check on 100 simulated null datasets" |
| "Families by decision" | Table 3 | "test families defined by the decision each test can change" |
| "reaching my verdict" | Table 3, row 02 | "that, run on my data, gave my verdict" |
| "the verdict map" | 2.6 | "the decision rule fixed before the run" |
| "deflated appraisal ratio" | exec. summary, 2.6 | Gloss once in 2.6: "(the appraisal ratio discounted for the number of strategies tried)" |
| "flips the raw spread" | 2.6 head | "reverses the sign of the raw spread after 2010" |
| "Fun" | 1.2 | "Fun (entertainment)" |

### 2.4 Module codes

The codes are defined, in one 43-word sentence in 1.1, with Table 2 as the key. They still reach the grader 35 times in ten pages, the numbering runs out of order (M1, M1b, M2, M3, M4, M8, then M5, M6 and "M7, run last"), and 1.3 uses four of them in one parenthesis ("M2, M3, M8, and M1b on windows under 60 months"). Keep the codes in Table 2 and the appendix headings, and use plain names in the prose:

- 1.3: "In the strategy tests (M2, M3, M8, and M1b on windows under 60 months)" becomes "In every test of a traded rule (for the climate-index rules, on windows under 60 months)".
- 1.3: "(for example, 128 of 128 numbers match for M8)" becomes "for the frozen test".
- 1.3: "(M8 and M7's 1931--1969 run)" becomes "(the 1994--2009 rule and the 1931--1969 momentum run)".
- 2.7: "M7 assigned all 23,923 module tests" becomes "The project-wide ledger assigned all 23,923 module tests".
- Table 3 "What I adopted" column: "(M8)", "(M4)", "(M7)" can stay; the table is a key.

Add one clause to 1.1 so the out-of-order numbering does not look like an error: "(the codes follow the order the modules were planned, and Table~\ref{tab:program} lists them in the order they are reported)".

### 2.5 Sentences to split

- Exec. summary, 60 words: "Second, a cleaner version frozen before its test ... not a small one." Covered by the rewrite in 3.1.
- Exec. summary, 57 words: "Fourth, every one of our team's timed rules lost ... one result." Covered by the rewrite in 3.1.
- 1.5, 46 words: "Following the HW2 workflow, each prompt put our numbers and constraints first and fixed the number of items. It asked for falsifiable pass bars and for the assumptions it was least sure of, capped the length, and said ``label any number you have not computed as a guess''."
- 1.1, 43 words: the module roadmap sentence. Split after "M1b feeds the same rules climate-concern indices and volatility placebos."

The other eight sentences over 40 words are lists and can stay.

---

## 3. Clarity for a grader

### 3.1 Is the thesis clear on page 1?

The verdict is: "Do not implement" is bold, early, and backed by four numbered reasons. The thesis of the extension is less visible. The clearest statement of it is in 1.1, not on page 1: "For our team's result to be climate alpha, three things had to hold: the signal measures climate concern, the gain comes from timing rather than exposure, and the rule survives a window it was not designed on." The four reasons map onto those three conditions, but the summary never says so, and the reader meets 39 numbers before the slogan. Suggested replacement (about 330 words, every number taken from the current draft):

```latex
Our team's halfway project proposed a state-dependent climate trade, and this report is my solo extension of it. The strategy shorts a factor-hedged Brown leg of five high-emission industries (utilities, shipbuilding and railroad equipment, aircraft, steel, construction materials) for three or six months after ``climate-transition attention'' crosses its past-only 80th percentile, sized to 5\% residual volatility. For that to be climate alpha, three things had to hold: the signal measures climate concern, the gain comes from timing rather than from being short, and the rule works on data it was not designed on. I tested each on Fama--French industry and factor returns, FRED news and macro series, two climate-concern indices and EPA supply-chain emission factors, with only past data in every threshold and hedge. None survives testing, and the recommendation is \textbf{Do not implement}. First, the ``attention'' series is FRED's equity-volatility news tracker for energy and environmental regulation (identical in 500 of 500 months). It is uncorrelated with media climate change concern (MCCC, $r=-0.0004$), and the same rules fed MCCC or climate policy uncertainty (CPU) earn 0 of 12 validation alphas with $t\ge1.96$. In effect, the rule shorts value-tilted utility and industrial stocks after stock-market volatility makes the news. Second, most of the COVID gain came from being short: the rule's alpha over the always-short position, an untimed short of the same leg, is $+1.84$\% a year ($t=0.87$). Third, a cleaner version frozen before its test (the regulation share of volatility news, lagged one month) has a timing alpha of $-0.18$\% a year over 1994--2009 ($t=-0.27$); the test had 80\% power only against an edge of about 1.9\% a year, but its estimate is negative. Fourth, every timed rule lost over the 2022--2026 holdout before and after costs (6-month rule: FF3 alpha $-1.97$\% a year, $t=-1.30$), and so did the always-short position ($-1.72$\%, $t=-1.09$). Of the alternatives, shrinkage timing collapses to the historical mean, and an optimized industry-momentum book that passed a pre-registered 1931--1969 test (alpha 1.95\% a year, $t=2.45$) fails the deflated appraisal ratio and lost in the holdout, which earns it a paper-trading pilot, not capital. In short: read the label of every input, benchmark every timing claim against the always-short position, and test one frozen rule, once, on a window it was not designed on.
```

What it changes: the thesis moves to sentence 3; COVID becomes reason two so the reasons follow the three conditions; the 900-variant and rates clauses leave (they stay in 2.3); "untimed short" and "always-short position" are tied together once; "the last unused window" becomes accurate. Also consider a credit line under the author name, for example "Solo extension of the Group 4 halfway project (A. Aryan, J. Duncan, C. Ruiz Cardozo, C. Takkallapalli)", after confirming the group number (4 or 5, flagged in `logs/hw_context.md` line 238).

### 3.2 Figures and tables

**Main body.** Every exhibit is cited in the text.

| Exhibit | Takeaway in caption? | Fix |
|---|---|---|
| Table 1 (data) | Not needed | "(= problem set 1 course file)" becomes "(the problem set 1 course file)" |
| Figure 1 (signal vs MCCC and CPU) | Yes | The legend and plot title use code labels ("EMV\_env (team attention)", "log1p"); relabel to "Team ``attention'' (EMVENRGYENVREG)" and drop the in-figure title, which repeats the caption |
| Table 2 (program) | Yes | "Team z" and "Table 1 cells" (items above) |
| Table 3 (ChatGPT) | Yes | Jargon cells (2.3); numbers change after a live rerun |
| **Table 4 (time patterns)** | **No** | Add: "Every rule loses in the holdout and over the last 18 months, the only positive $t$ above 2 outside COVID is Original 6m in validation, and the always-short position earns at least two-thirds of the best rule's net return in every window where the rules gain." (checked against the table: 0.73 of 1.08, 1.05 of 1.19, 1.71 of 2.16, 6.87 of 8.04). Move note b (same-month alphas) to Table C.10 to pay for it |
| Figure 2 (COVID paths) | Left panel only | Add: "In the right panel the always-short position ends well above every Continuous raw version, which holds smaller positions." |
| Table 5 (frozen test) | Yes | None |

**Appendix.** Most module tables (C.1, C.2, C.4, C.5, C.7 to C.15, C.18, C.20 to C.28, C.30 to C.37) have no takeaway sentence, and none of the C-subsection introductions cites its own tables by number. Several print code identifiers and mix units: Table C.25 ("team brown", "epa41 brown", "hold3", "ann net", "alpha ff3 t hac6", "b HML", returns as decimals), Tables C.34 and C.35 (decimals, "t nw6", "p tnk"), Table C.2 ("$z_t$ = rolling z(log1p(EMV env))", "slope 1", "t 1"), Table C.1 ("full 1985", "last18"), Table C.5 ("the CSV adds"). The main text reports percent a year throughout. Table C.15's caption also uses the internal code "Q2 primary". Fix in `report/make_tables.py`: percent units, plain labels, and one takeaway sentence per module table, starting with the tables that carry a module's headline (C.2, C.4, C.10, C.15, C.23, C.30, C.33). The appendix exhibits the main text cites (Table C.6, Figures C.6 and C.7) already have takeaways. If time is short, fix the appendix intro sentence (2.2) so it does not promise plain labels.

### 3.3 Redundant

- The provenance and verification paragraph of 1.3 (about 11 lines) repeats App. D ("How the work was done and verified"). Keep three sentences in 1.3 (text in 4.1) and move the rest to App. D.
- 2.8's first paragraph repeats Table 3's caption (6 of 52, 8 of 72). Keep the duration example only: "Its errors were mostly about our data, not the method (Table~\ref{tab:chatgpt}): in exchange 01 it blamed the holdout loss on duration (rate beta $t=0.05$)."
- "Original 6m" and "Pure 6m" name the same holdout series (2.3: "Corrected Pure 6m (the table's Original 6m, since the two coincide in the holdout)"). Use "Original 6m" in the text so it matches Table 4, and say once that Pure is identical there.
- Three names for one benchmark: "always-short Brown position", "always-short position", "untimed short". Define "the always-short position, an untimed short of the same leg" once (exec. summary and 1.3) and use "always-short position" afterward, including in the Figure 2 caption and 2.8.

### 3.4 Missing

- **Style exposures beyond HML (brief 3a).** GB's duration tilt is in Table 2 (BOND loading 0.132) but never in the text, and the traded short's COVID momentum and duration exposure is only in M3's FINDINGS. Add to 2.2: "GB is also modestly long duration over 1970--2026 (BOND loading 0.132, $t=2.60$, Holm $p=0.019$, about one year of duration per unit of GB) but not since 2010 (0.088, $t=0.60$), and in COVID the traded short (Pure 6m, in position all 24 months) carried momentum and duration that the FF3 hedge left open (UMD 0.31, $t=4.49$; BOND 0.76, $t=2.29$)." (M3 FINDINGS lines 100 to 106 and 250.)
- **Why the frozen rule was this rule.** 2.5 concedes it "had no in-sample edge to confirm", so a grader will ask why the last clean-ish window went to it. Add to 1.3: "because it removes the zero problem and, unlike MCCC (from 2003) and CPU (no signal before 1995), can trade before 2010" (App. A.1 evaluation gives this reason).
- **Adaptations of the prompts** (1.3 above).
- **Hashim's own role** in the provenance statement (blocking fix 2).

---

## 4. Where the space comes from

### 4.1 Section 1 (needs about 5 lines; has about 1)

Replace the last paragraph of 1.3 (about 11 lines) with this (about 5 lines), and move the single-computed numbers list and the four-minute note to App. D:

```latex
Each module's headline numbers were produced twice, by the module's code and by a second implementation that shares none of it (128 of 128 match for the frozen test), and every inferential statistic is logged: 23,923 tests in eight module ledgers, 155 of them primary. Only the two frozen tests have timestamped pre-registrations; the other modules fixed their primary tests in code without a timestamp (Appendix~\ref{app:code}). An AI coding agent (Anthropic's Claude) wrote each module's code under my direction, and a second agent wrote the re-implementation; <Hashim's clause on what he decided and checked>.
```

That frees about 6 lines, which pays for the adaptation sentence in 1.5 (about 3.5 lines), the frozen-rule reason in 1.3 (about 1.3 lines) and the small wording fixes in 1.2 and 1.3.

### 4.2 Section 2 (needs about 8 lines; has about 1.7)

Additions: BOND and COVID-exposure sentence in 2.2 (about 2.3 lines), 900 definition and six-entries clause in 2.3 (about 1.8), placebo rewrite in 2.4 (about +1), Table 4 takeaway (about 1.7), "high" and "Regressed on" in 2.1 (about 0.3), named windows in 2.9 (about 0.4), adaptation pointer in 2.8 (about 0.7).

Cuts:
- 2.8: replace the first paragraph's statistics with the shorter sentence in 3.3 (about 0.8 lines); delete the provenance sentence after a live rerun (about 1).
- 2.9: cut "Each is an afternoon's check..." (about 0.8).
- 2.6: drop "and $b=-1$ cuts it 60\% for an IR change of $-0.005$ whose interval allows a loss of 0.1" (about 1.2; it is in App. C.6).
- 2.7: drop "among them 1,624 alphas (783 positive, 841 negative)" (about 0.8).
- 2.3: shorten the leakage sentence to "Of Original 6m's net $-1.84$\%, the residual Brown return is $-1.14$\%, cost 0.46\% and hedge leakage $-0.24$\% (centered ex post betas), and Steel alone carries the gross loss." (about 0.4).
- 2.1: drop "(slope 0.43, $t=5.07$)" (about 0.3).
- Table 4: move note b to Table C.10 (about 1.4).

Net: about 6.7 lines cut plus 1.7 free against about 8.2 added. Recompile and check p. 10; if it overflows, reduce Figure 2 from 0.7 to 0.64 of the text width.

---

## 5. Required fixes in priority order

1. Rerun the four exchanges in a live ChatGPT session, rebuild Appendix A, and re-derive every ChatGPT-derived number (1.3). Fallback wording if impossible (1.3).
2. Hashim writes the clause on what he decided and checked himself, replacing "so ``I'' in this report covers that work", and removes the `HASHIM-CONFIRM` comment. Make App. D's "the prompts were written and the replies fact-checked with code" name who did each.
3. Add the prompt-adaptation sentence to 1.5 and a pointer in 2.8 (brief item 3d).
4. Fix the sixteen consistency items in 1.4, above all items 1 (two pre-registered tests), 2 (publication-date overclaim), 3 (five vs six entries), 5 (2.2 head and COMEQ loading) and 6 (EPA alpha mechanism).
5. Add GB's duration tilt and the COVID UMD and BOND exposures to 2.2 (3.4).
6. Replace the executive summary with the thesis-first version in 3.1, or at least split its two longest sentences and fix "the fail" and "the last unused window".
7. Add a takeaway to the Table 4 caption and the right-panel sentence to the Figure 2 caption (3.2).
8. Replace module codes with plain names in the 1.3 and 2.7 prose (2.4) and the jargon in 2.3.
9. Condense App. C.8's timeline and the App. A workflow labels (2.2); fix "labelled" and "labelling".
10. Make the space cuts in Section 4 and recompile; confirm Section 1 ends on p. 6 and Section 2 on p. 10.
11. Confirm the teammate spelling ("Cristhian" in the `\CR` macro and HW1, "Christhian" in the verbatim exchange 01 prompt and the WhatsApp log) and the group number, and consider the title-page credit line.
12. Lower priority: appendix table units, labels and takeaways in `make_tables.py` (3.2), and the final page, which holds one line ("Merton, 1981).") of the nominal-positives list at the end of Appendix E; tighten the list or its spacing so the PDF ends on p. 111.
