# Critique of the draft report "Read the Label"

Reviewed: `report/report.tex` (656 lines), `report/appendix_transcripts.tex`, and the compiled `report/report.pdf` (93 pages: title and executive summary p. 1, Section 1 pp. 2 to 6, Section 2 pp. 6 to 10, references pp. 11 to 12, appendices pp. 13 to 93). I read it against the course brief (`MFE230GA_Final_Project_2025.pdf`), `logs/style_guide.md`, the authentic Ultramarin report, and the module `FINDINGS.md` files where a number looked off.

## Verdict in brief

The analysis is strong and the structure maps cleanly onto the template. The draft is **not submittable yet**, for three reasons:

1. **The ChatGPT requirement is not met.** The two exchanges came from a model told to answer as ChatGPT, not from a live ChatGPT session. The draft's own red notes say so, yet Appendix A still labels each one "Tool: ChatGPT" and "Reply (verbatim)". Only two of the three required interactions exist, since exchange 03 (robustness design) is still pending.
2. **Placeholders and a few factual inconsistencies are still in the PDF.** There are two red draft notes and five `[Pending]` markers. There is also a "no positive holdout alpha" claim that Table 4 contradicts, a "four nominal positives" pointer to a list of six, and a carbon IR number that does not match between Table 2 and Section 2.6.
3. **The page budget is nearly used up.** Section 1 runs about 4.8 of its 5 pages and Section 2 about 3.9 of its 4. Filling the pending rows and adding exchange 03 will push Section 2 over the limit unless cuts are planned now (Section 4 below lists them).

On voice, sentence length matches Hashim's sample well. The prose is still denser than his: more semicolons, more parentheses and more "X, not Y" turns, too many count announcers, and several sentences lifted almost word for word from the Ultramarin report. On clarity, the thesis is visible on page 1, but internal codes (M1b, Q2, Original 3m, Pure 6m, "leakage", "builder", "verifier") reach the grader before they are defined.

---

## 1. Brief compliance

### 1.1 Template checklist

| Brief item | Where in draft | Status | Fix |
|---|---|---|---|
| Executive summary, 1 paragraph, strategy stated | p. 1 | Present, about 320 words, one paragraph | Say it is a solo extension. Define MCCC and CPU. Drop "module" and "verifier" (see 3.1). |
| Explicit "Do not implement" with justification | p. 1 (bold), 2.9 (bold) | Present, four numbered reasons | None |
| What did you try, 2 to 5 pages | pp. 2 to 6 | About 4.8 pages | Keep under 5 after the pending rows are filled (see Section 4) |
| a. Ideas, origin | 1.1 | Present (HW1, Pastor et al., team thesis) | None |
| b. Data, sources | 1.2, Table 1 | Present (Ken French, FRED, EPA, MCCC, CPU) | Optional: note that USEEIO is built on the BEA input-output accounts, one of the brief's suggested sources |
| c. Risk modeling | 1.4 | Partly present. It covers the hedge, COMEQ, BOND and conditional betas, but "risk model" is never named, and realized risk (volatility against the 5% target, IR, drawdown) never appears in the main body | Add one sentence naming the rolling 60-month FF3 time-series model as the risk model, plus realized volatility and IR per window (Table 5 or text) |
| c. Turnover and costs | 1.4, third paragraph | Present (1.8 to 5.8 turns a year, drag at most 0.63%, break-even 40 to 100 bp, zero-cost runs) | Explain "28 zero-cost runs" and "900 configurations" (what varies) |
| c. At least 3 high-quality ChatGPT prompts | 1.6, Table 3, App. A | **Not met.** Two exchanges (01, 02), each with a follow-up, and both simulated. Exchange 03 is pending. No prompt text is quoted in the main body. | Blocking fixes 1 and 2. Quote 2 to 4 key prompt lines per exchange in Table 3, since prompt design is graded under originality. |
| 3a. Style and risk exposures | 2.2 | Present for the raw spread (FF3, FF5, COMEQ, BOND) and the residual HML of the rules | Optional: one line on the traded rules' FF5+UMD loadings (the appendix has them) |
| 3b. Full sample, post-2010, recent 12 to 18 months | 2.3, Table 5 | Present, but the table never gives the calendar dates of the last 18 and last 12 months | Add "Last 18 months (2025-02 to 2026-07)", "Last 12 months (2025-08 to 2026-07)" and the full-sample and post-2010 spans to Table 5's row labels |
| 3c. Robustness and limits | 2.7, Limitations | Present | Fix the inconsistencies in 1.3 below |
| 3d. ChatGPT evaluation | 2.8 | Present for 01 and 02 only | Add exchange 03. Make strengths and limits explicit (see 2.4). |
| Reflect on strengths and limits as an investment research assistant | 2.8, last paragraph | Implicit, and undercut by "that is a result about these prompts, not the tool" | Replace with an explicit strengths/limits pair (rewrite in 2.4) |
| Appendix: transcripts | App. A | Present, but with false provenance labels | Rebuild after live runs |
| Appendix: tables and plots | App. C | Present | Caption fixes (see 3.3) |
| Appendix: code snippets | App. D | Present, read from the files that ran | None |

### 1.2 Page limits (measured from the PDF text blocks)

- Section 1 starts at the top of p. 2 and ends 72% of the way down p. 6: **about 4.8 pages (limit 5)**.
- Section 2 starts 73% of the way down p. 6 and ends two-thirds of the way down p. 10: **about 3.9 pages (limit 4)**.
- Still to add: the M7 row of Table 2, the 03 and 04 rows of Table 3, one or two sentences on exchange 03 in 2.8, and project-wide multiplicity counts in 2.7. Without cuts, Section 2 will go over 4 pages. Section 4 of this critique frees about 10 lines in Section 2 and 6 to 10 in Section 1.
- The running header on p. 6 reads "2 What Did I Learn?" although most of the page is Section 1. This is cosmetic, because the preamble uses `\leftmark`, which takes the last mark on the page. It is optional to fix.

### 1.3 Factual and internal-consistency problems a grader can find

1. **"No positive holdout alpha" is false as written.** Table 2 (M1b row) and the Appendix C.2 introduction both say the climate measures give "no positive holdout alpha". Table 4 shows two positive CPU holdout alphas: Original 3m +0.36 (t = 0.37) and Pure 6m +0.20 (t = 0.20). M1b's FINDINGS words it correctly as "no significant positive holdout alpha". Change both places to "no significant positive holdout alpha (largest t = 0.37)".
2. **"The four nominal positives are retired in Appendix E"** (2.7), but E.5 lists six bullets. Change to "six".
3. **The carbon IR change disagrees.** Table 2 (M5) gives "+0.010" and 2.6 gives "-0.005". Both are right, but for different bounds: b = 0 is the primary, which cut long-book WACI by only 11.6%, and b = -1 cut it by 60%. Name the bound in both places, and say in 2.6 that the primary bound was a weak test.
4. **"I tested each in eight modules, M1 to M8"** (1.1). There are nine labels (M1, M1b, M2 to M8), M7 is a ledger and not a test, and M5 and M6 are alternatives, not tests of the three conditions. Rewrite the count or drop it.
5. **Two HML numbers for the same thing.** 2.2 gives GB's post-2010 FF3 HML loading as -0.298. Step 4 of Appendix B.1 and the exchange 01 prompt say the team's -0.35 was reproduced, and M2's FINDINGS gets -0.35 only with 8-and-8 legs. Add one clause saying which window or legs produce each number.
6. **1993 or 1994?** Table 3 says "one frozen 1993-2009 rule". 2.5, Table 6 and the headings say 1994-03 to 2009-12. State once that the proposed window was 1993 to 2009 and the first usable month after burn-in is 1994-03.
7. **"Every t-statistic is Newey-West with 6 lags"** (1.3) is too strong. Table C.3 uses NW(12), the note to Table 5 quotes classical OLS t, and the frozen test also uses shuffle p. Write "Unless stated otherwise, every t-statistic ...".
8. **The frozen window was not fully clean.** M8's own FINDINGS (caveat 1) discloses that the team's macro-state notebook used 192 pre-2010 months of forward Brown residuals. The report leaves this out and calls 1994 to 2009 "the one clean test" (Section 2 intro, 2.9). Add the disclosure to 2.5, and say "the one pre-registered test" instead of "the one clean test".
9. **The power sentence in 2.5 is wrong.** "A pass would have been weak evidence; a fail is not weakened." With limited power (a pass needed about +0.9% a year), a fail is weak evidence against a small edge. The defensible claim is about the point estimate. Suggested text: "Power was limited, since a pass needed about +0.9% a year, so the test could not have confirmed a small edge; but the estimate is negative and sits at the median of its own shuffle distribution, so it offers the rule no support."
10. **"A null about our low-emission industry legs"** (2.1) should be "our emissions-sorted industry legs". The traded leg is the high-emission Brown leg.
11. **2.7's opening claim mixes two denominators.** "Across 23,923 logged tests no positive alpha survives its pre-specified family" is loose, because only 155 rows sit in primary families. The draft also never gives the nominal count, which the style guide's multiplicity pattern asks for. M2's grid of 8,091 has 368 positive and 531 negative alphas at p < 0.05 (M2 FINDINGS, "Whole grid"). Give the family size, the nominal count, then the survivors.
12. **Sign confusion in 2.3.** "The FF3-hedged Brown leg beat its hedge (alpha +2.82%, t = 0.95)" sits right after a negative residual of -1.14% for the short. Say "the Brown leg itself had a positive alpha of +2.82% (t = 0.95), which a short position loses".
13. **Pure 6m appears in the text but not in Table 5.** 2.3 and 2.4 use Pure 6m. Add one clause saying that in the corrected holdout Original and Pure are identical (M2 FINDINGS: "Original = Pure in the corrected holdout"), which also explains the identical columns in Table 4, and that in COVID Pure 6m was in position all 24 months, so it equals the always-short position.

---

## 2. Voice

### 2.1 Measured against the authentic sample

Main-body prose (executive summary through 2.9, excluding tables, captions and math) is about 3,440 words in 144 sentences.

| Measure | Draft | Ultramarin report | Reading |
|---|---|---|---|
| Mean / median sentence length | 23.9 / 21 words | about 26 / 23 | Matches |
| Sentences over 45 words | 10 (longest 77) | uncommon | Split them (list in 2.3) |
| Semicolons per 1,000 words | about 9 | about 3.4 | Too many, about 2.7 times his rate |
| Parentheses per 1,000 words | about 26 | about 18 | Dense |
| "X, not Y" turns per 1,000 words | about 4.6 (16 uses) | about 2.9 | Too many, twice inside a single sentence |
| Count announcers | 9 | about 8 in 28 pages; the guide caps it at 2 to 3 per document | Far too many for 10 pages |
| Bold run-in claim heads | 27 in 10 pages | used in results sections only | Every paragraph has the same shape |
| Em dashes | 0 in his prose (the ChatGPT listings' em dashes are mapped to "--") | 0 | Clean |
| Banned transitions (however, moreover, thus, notably, ...) | 0 | 0 | Clean |
| "honest", "leverage", "crucial", "highlight", "reveal" | 0 | 0 | Clean |
| "genuine" | 3 | avoided ("genuinely" is on his avoid list) | Replace |
| British spellings | "favoured" (1.1), "centre" (2.5) | American ("favored") | Fix |

The biggest difference from his sample is not sentence length but what a paragraph does. His paragraphs go claim, evidence, mechanism in plain words, short verdict. Many draft paragraphs are a claim followed by a run of statistics, with no plain "why". Example: the first paragraph of 2.1 packs 13 statistics (R-squared, two p-values, a slope, two t-statistics, two correlations, Holm p, a partial correlation, two shares, Fisher p) into about 85 words and never says why a volatility-news count would trigger a short of Brown industries. Cap each sentence at about three numbers. Move the rest to the table the paragraph cites, and add one plain mechanism sentence per finding.

### 2.2 Passages lifted from the Ultramarin report

Stacked together, these read as a model imitating him (style guide, Section 9). A grader who has seen his earlier report would notice them.

| Draft | Ultramarin original | Suggested replacement |
|---|---|---|
| "From the outset the study favoured transparent reporting over good-looking results, and that mandate shaped the design more than any single method: ..." (1.1) | "From the outset, the project favored transparent reporting over good-looking results, and that mandate shaped it more than any single method did." | "Three rules shaped the design more than any single method: a primary test fixed in code before each run, real-time inputs, and an untimed benchmark for every timing claim." |
| "The summary to keep in mind throughout: ..." (1.5) | same words | Delete. The sentence repeats Table 2's caption and 2.7's head. |
| "Four findings define the story: ..." (Section 2 intro) | "Three findings define the story." | "Section 2 reports four findings in turn: the signal is volatility news, the trade is a Brown-leg value exposure, COVID rewarded the position rather than the trigger, and the pre-registered test fails." |
| "The negative results are the most useful part of this study: each one retired an idea before it could cost money." (2.9) | "We consider the negative results the most valuable deliverable: each one retired an upgrade before it could cost money." | Make it specific to this study, for example: "Each negative result here is a check a desk can run in an afternoon before it funds a climate-timing idea." |
| "that is a result about these prompts, not the tool" (2.8) | "This is a negative result about this cluster, not the method." | Replace with the strengths/limits pair in 2.4. As written, the sentence also contradicts the one before it, which generalizes about the tool. |
| "Several limitations should be kept in mind." (2.7) | same words | Delete. The bold "Limitations." head already announces the list, and cutting it saves a line. |

### 2.3 Specific passages to rewrite

- **Count announcers (9).** "I asked three questions" and "for four reasons" (executive summary), "three things had to hold" (1.1), "Two facts about the data" (1.2), "Two input errors" and "Three disclosures" (1.3), "three ways" (1.4), "Four findings define the story" (Section 2), "three rules" (2.9). Keep "for four reasons" and "three rules", and rephrase the rest.
- **"X, not Y" in back-to-back use.** "This is a null about our ... legs, not a refutation of Pastor et al. (2022): the validation alpha belongs to the EMV family, not to climate." Two in one sentence. There is also a third in the same subsection heading ("volatility news, not climate concern"). Keep at most one per paragraph, and never in two consecutive sentences.
- **"genuine" (executive summary, 1.5, 2.1 head).** Replace with "climate-concern indices" or "measures built to track climate concern".
- **Dangling participle in the 2.1 head.** "Fed genuine climate concern, the same machinery reproduces neither the in-sample nor the out-of-sample result." This is also inaccurate, because MCCC does reproduce the holdout loss (6 of 6 negative). Suggested head: "Climate-concern indices fed through the same rules earn no validation alpha and no significant holdout alpha."
- **Internal jargon from the agent workflow.** In 1.3: "M2's Q2 primary was printed in a smoke test four minutes before its docstring". Suggested: "one primary result, the commodity-hedge test, was printed during a code check four minutes before the test was written down". In 1.3 and Appendix C: "a verifier who imported none of the builder's code". See blocking fix 3 on disclosure.
- **"Its best-specified form, which I froze before testing it"** (executive summary). "Best-specified" is a coined phrase with no support. Suggested: "A cleaner version, frozen before its test (the regulation share of volatility news, lagged one month), is scored once on 1994 to 2009."
- **The last sentence of 2.4 is unparseable on a first read.** "... under real-time timing overall EMV reproduces the gain in 4 of 6 rules, exactly the pre-specified boundary, while for Original 3m the placebos fall short and CPU matches it." Suggested: "By the pre-specified placebo rule the climate reading fails, on its boundary: overall volatility news, which carries no climate content, reproduces the COVID gain in 4 of 6 rules. Only for Original 3m do the volatility placebos fall short, and there CPU matches it." Hashim should confirm the rule's threshold wording against M1b's pre-specification.
- **Sentences over 45 words (10).** Split: the data sentence in the executive summary (47 words), the rule sentence (48) and validation sentence (52) in 1.1, the EPA-rank sentence in 1.2 (68), the lag sentence in 1.3 (48), the COMEQ sentence (47) and the turnover sentence (48) in 1.4, the 1.5 roadmap (77), the prompt-design sentence in 1.6 (46), and the EMV-tracker sentence in 2.1 (55).
- **Paragraph shape.** Twenty-seven bold claim heads in ten pages, each followed by a number-dense sentence, gives every paragraph the same silhouette. Keep bold heads for the findings in Section 2. In 1.3, 1.4 and 1.6, fold the claim into an ordinary first sentence.

### 2.4 Suggested strengths/limits close for 2.8

Re-derive the numbers after the live rerun. Every number below comes from the simulated exchanges.

> "As a research assistant it has two strengths and three limits. It referees stated numbers quickly and proposes the right benchmark, and where the specification is exact its code is exact (its script matched mine to 3.3 x 10^-13 once two open readings were aligned). But it never questions the inputs it is handed, it adopts a confident user's framing, and its own checks miss what they were not told to look for: its look-ahead test caught 4 of the 6 timing bugs I injected, and the revised version 7 of 8. Use it as a referee and a second implementation, never as a verifier or a source of facts about the data."

The injected-bug (mutation) test is the most original part of the ChatGPT work, and today it is visible only as a cell in Table 3 ("missed 2 of 6 bugs"). The brief gives bonus credit for well-structured ChatGPT use, so the main text should state it.

---

## 3. Clarity for a grader

### 3.1 Is the thesis clear on page 1?

Mostly. The title and subtitle carry it, and "Do not implement" is bold with four reasons. Five things slow a first read:

- It never says this is **a solo extension of a team project**, so the switch between "our team" and "I" is unexplained. Add half a sentence, and consider a credit line on the title page naming the teammates and the group number. `logs/hw_context.md` flags that the group number is inconsistent (4 or 5), so confirm it first.
- **MCCC and CPU** appear without definition, and **Util, Ships, Aero, Steel, BldMt** are Fama-French short codes. Spell out the industries once (utilities, shipbuilding and railroad equipment, aircraft, steel, construction materials).
- The 47-word process sentence ("... each module fixes a primary test, and an independent verifier rebuilt each module's headline numbers") uses internal terms that mean nothing on page 1. Cut it to "every test uses real-time inputs and small-sample p-values".
- **No plain mechanism sentence.** Add something like "In plain terms, the rule shorts value-tilted utility and industrial stocks after stock-market volatility makes the news." This follows from the report's own evidence: 88% of crossings fall in high overall-EMV months, and the Brown side carries an HML loading of -0.437.
- "all 900 net-of-cost configurations" needs a gloss of what varies: legs, hedges, costs, baselines and evaluation models, per M2's grid.

### 3.2 Terms used before they are defined

| Term | First use | Where to define |
|---|---|---|
| Module codes M1 to M8, M1b | executive summary ("module"), Table 1 ("M4"), 1.3 ("M8", "M1b and M3", "M2's Q2") | Move the 1.5 roadmap into 1.1 so the codes are defined before first use. In prose, use plain names ("the signal audit", "the frozen test") and keep codes in parentheses and in Table 2. |
| Original 3m/6m, Pure 3m/6m, Continuous raw/pure | 1.3 ("Original 3m's ...") | 1.1: "the six rules are Original and Pure (raw and macro-purified signal) with 3- and 6-month holds, plus Continuous raw and Continuous pure" |
| Always-on position / untimed short / signal-free always-short Brown / always-short Brown | executive summary, 1.3, 2.2, Table 5, 2.4 | Four names for one benchmark. Pick "always-short Brown", define it in 1.3, and use it everywhere. |
| Real-time timing, team timing, same-month timing, corrected baseline | 1.3, Table 4, Table 5 note | One sentence in 1.3 that fixes both labels |
| "Leakage" | 2.3, 2.4 | "the return from factor exposure that the lagged hedge failed to remove" |
| IC | Table 2 ("8 predictive ICs"), Table 3 ("IC flip") | "information coefficient (IC)" at first use |
| Shuffle p | executive summary | "a calendar-shuffle placebo that moves the rule's holding blocks to random dates" |
| 28 zero-cost runs | executive summary, 1.4 | "cost-free runs of the six rules with the FF3 and FF5+UMD+COMEQ hedges" |
| PS1 | Table 1 | "problem set 1 course file" |

### 3.3 Figures and tables

- **Main body:** Figures 1 and 2 and Tables 1 to 6 are all cited in the text. Captions carry a takeaway except Table 1, where none is needed, and **Table 3**, which needs one. Suggested: "ChatGPT changed the plan three times and was wrong on 6 of 52 checkable claims; its code matched mine once the specification was exact."
- **Table 5:** add the calendar dates to the recent-window labels. Consider adding a realized volatility or IR row so the risk-model box is ticked where the grader looks. Drop the caption's repeated sentence "Outside COVID, the only positive t above 2 is in validation", since the 2.3 head says the same.
- **Table 2:** it duplicates its own introduction ("Table 2 is the study in one table" in 1.5 next to the caption "The study in one table"). The "no module finds a positive alpha that survives its own family" line appears three times (Table 2 caption, end of 1.5, 2.7 head). Keep it once.
- **Figure C.3 (COVID paths)** carries the evidence for finding 3 but sits in the appendix. If a quarter page frees up, promote it. Otherwise the pointer is fine.
- **Appendix captions:**
  - Several figures have no takeaway or label: M1 VIX, M1b heatmap, M2 HML and cost figures, M4 cumulative GB, M6 shrinkage path, M8 signal.
  - Some captions name source files or internal steps. Table C.3 opens "formatting of `M1_signal_audit_crossings_vix_summary.csv` fixed", and Table C.9 ends "All six strategies in M1b_alt_signals_recent.csv".
  - Some builder tables print code identifiers as column and row labels: Table C.4 has `ic_full_overlap`, `z_EMV_env`, `brown_resid_FF3`, and Table C.28 has `dIR` and `Conv. X/M`.
  - The phrase "tables with a builder caption" in the Appendix C introduction is workflow jargon.
- **Appendix C intros** open with verification-round counts ("104, 257 and 34 independent checks match"). A grader cannot use these. Replace them with one sentence in Appendix D on how verification worked.
- **Appendix A** is 44 pages. Exchange 02 alone takes 34, most of it the 7,110-word reply (the script) and the 4,745-word follow-up. That is acceptable under "include transcripts". Optionally set the script in `\tiny` or move it after the evaluation, so the four-line summary box and the evaluation come first.

### 3.4 Redundancy that can be cut

- r = -0.0004 appears four times (executive summary, Figure 1 caption, 2.1, Table 2). Keep it in the executive summary, 2.1 and the table.
- The 1.2 data findings and 2.1 overlap. That is acceptable, because 1.2 explains why the data section carries findings. Trim the 2.1 restatement.
- The 2.9 verdict's first sentence restates the question from 1.1. The slogan repeating from the executive summary is intended (his title-slogan habit).

### 3.5 Missing

- Exchange 03 (required) and, optionally, exchange 04.
- The M7 project-wide correction, or the removal of every reference to it.
- Realized risk of the traded rules: volatility against the 5% target, IR, drawdown. For an Active Asset Management grader, IR is the headline metric, and the main body never reports one for the strategy.
- An AI-use and provenance statement (blocking fix 3).
- Quoted prompt lines in the main body (prompt design is graded).

---

## 4. Where to find the space

**Section 2 (needs about 10 to 12 lines):**
- 2.1: drop the partial-correlation clause and the VIX t, since Table 2 carries them (about 2 lines).
- 2.3: fold "The last 18 months are losses..." into one sentence, and cut the Table 5 caption sentence it repeats (about 3 lines). Shorten note b of Table 5 (about 1 line).
- 2.4: use the shorter last sentence from 2.3 of this critique (about 1 line).
- 2.7: delete "Several limitations should be kept in mind." (1 line).
- 2.9: cut the first sentence, which restates 1.1 (1 line).
- 2.6: replace "(95% interval -0.110 to +0.096)" with "(the interval allows a loss of about 0.1)" (about 1 line).

**Section 1 (needs about 6 to 10 lines):**
- Merge 1.5 into the last paragraph of 1.1, keeping only what defines the modules and the alternatives (saves the heading and about 5 lines).
- 1.4: move the BOND validation detail ("-15.0% in 2022 against Damodaran's -17.8%; annual correlation 0.991") to Appendix C.4 (1 line).
- 1.6: shorten the prose paragraph by the amount the quoted prompt lines add to Table 3.

---

## 5. Blocking fixes in priority order

1. **Run the prompts in a live ChatGPT session and rebuild Appendix A.** This means 01, 02 and the new 03, rebuilt with `report/build_transcripts.py`. Then re-derive every ChatGPT-derived number in Table 3, 1.6, 2.5 ("ChatGPT's independent implementation agrees (-0.19%, t = -0.25)") and 2.8 (the 52-claim tally, 3.21 to 5.32, the 985-line script, 5,000 shuffle draws, 4 of 6 and 7 of 8 bugs). Do not submit Appendix A with the "Tool: ChatGPT" and "Reply (verbatim)" labels on replies that did not come from ChatGPT. Whatever the rerun shows, state in 2.5 and Appendix A that the frozen rule was adopted from the earlier, simulated exchange-01 follow-up, because the 1994 to 2009 window cannot be spent twice. If the live session can execute code, recheck the Appendix A sentence "It cannot run code".
2. **Complete exchange 03 (robustness design).** Fill the Table 3 row and A.3, and add one sentence to 2.8. Exchange 04 is optional. If it is dropped, remove its row and A.4.
3. **Add a short provenance paragraph** to 1.3 or Appendix D. It should name the AI tools that wrote and independently re-implemented the module code (M2's FINDINGS cites a "builder transcript (workflow ..., agent ...)"), what Hashim decided and checked himself, and the role of ChatGPT. Then make every first-person "I" claim match it, including the Appendix A labels "Evaluation (my own text, typeset)" and "Fact-check". Without it, "an independent verifier", "I ported" and the timeline in Appendix C.8 (code first written at 03:35:43, dry run 52 seconds later) will read to a grader as undisclosed automation.
4. **Remove every placeholder.** That is both `\draftnote` blocks (p. 6 and Appendix A), `\pending` in Table 2 (M7), Table 3 (03, 04), A.3, A.4 and E.4. Either deliver M7 or delete its row and E.4 and reword 2.7 so it does not rely on M7.
5. **Fix the thirteen consistency items in 1.3** of this critique.
6. **Confirm the teammate spelling.** The `\CR` macro prints "Cristhian", which matches the HW1 author list, while the WhatsApp log and the module folder use "Christhian". Confirm it, and confirm the group number.
