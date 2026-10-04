# Writing style guide: Hashim Almodamagha

Source: Hashim's solo industry report, *Count Each Idea Once: Building Robust Composites from Correlated Alpha Signals* (Berkeley MFE industry project for Ultramarin, July 2026, 28 pages). This is the only authentic sample. I read all 28 pages. The counts below come from the prose on pages 1 to 25 (about 10,500 words, with tables, axis labels and references stripped). Every quotation was string-matched against the PDF text. The PDF uses curly quotes, en dashes in ranges and in two-name terms (Newey–West), and `∼` for "approximately", and the quotes keep them.

---

## 0. The voice in brief

A skeptical practitioner writing up his own research. Each paragraph states a claim, backs it with a number in parentheses, gives the mechanism in plain words, and ends on a short verdict or an operating rule. Methods act as characters that win, fail or get retired. Negative results come first and without apology, and they are treated as the product. Hedging is done with measured quantities and fixed labels ("nominally", "suggestive, not certified", "within noise"), never with modal verbs. There are no contractions and no em dashes. Asides sit between commas or inside parentheses. Colons and "X, not Y" contrasts are used heavily.

---

## 1. Voice and stance

### Person
- **"I" is for actions he took** (21 uses): *I built*, *I ran*, *I also checked*, *I attacked*, *I therefore re-ran*, *I correct the whole family*, *I re-learned it*.
- **"We" is for conventions, positions and the shared reader-sponsor frame** (18 uses, plus 18 of "our"): *We refer to it as the benchmark*, *What we add is*, *here we follow the standard institutional playbook*, *We import it as*, *What we want instead is*, *we fixed it at 0.7*, *We were asked whether*, *We consider the negative results the most valuable deliverable*.
- **Most sentences have an inanimate subject**: "the study" (35 uses), "this report", "the benchmark", "the estimator", "the test", "Class 1". Of about 400 sentences, 105 start with "The".
- **"You" appears once**, in a practitioner aside: "That is the conservative failure mode you want in production."
- **No contractions.** None in the whole report.
- For a team report, use "we" for team decisions and analyses. Keep "I" for a step Hashim personally ran, and only in sections he owns. Do not switch between "I" and "we" inside one paragraph.

### Tense
- **Present tense for claims, results and what the document does**: "This report asks", "Every class has a hard IC ceiling", "The benchmark is last on 17 of 20 class-4 subsets".
- **Past tense for the research process and for events on the hold-out**: "I built a single fixed evaluation framework", "The hold-out arrived after the in-sample study was complete", "Its linear composites lost two-thirds of their IC", "Two caveats were recorded at the time, and both mattered later."
- He tells the process as a sequence on purpose: "This section reports the in-sample study in the order it was actually run, because each step's result determined the next."

### Hedging level
- **Modal hedges almost never appear**: *may* 1, *might* 0, *perhaps* 0, *seems* 0, *possibly* 0, *arguably* 0, *potentially* 0, *likely* 1.
- **Uncertainty is carried by numbers and fixed labels instead**: "roughly" (11), "about", "approximately", "∼", "within noise", "a hair wide", "nominally significant", "not itself significant", "suggestive, not certified", "noise-level", "To our knowledge", "at least in principle".
- He is sure of what the data showed and states its scope in the same sentence: "The focus on ranks is a scope decision, not a claim of universality".

### Negative results
- **State them first and flatly, as findings**: "No method in the study, including this one, delivers more raw predictive accuracy than the benchmark." His own method is included in the negative.
- **Give the mechanism**: "fails on this cluster for a reason the regularization path makes visible: ..."
- **Scope the failure precisely**: "This is a negative result about this cluster, not the method."
- **Turn the failure into a rule or lesson**: "The gap between the best cell in a sensitivity table and what tuning actually delivers is this study's recurring look-ahead lesson." / "The operational moral for any frozen composite is to monitor the level, not just the structure".
- **Value negative results openly**: "We consider the negative results the most valuable deliverable: each one retired an upgrade before it could cost money."
- **Give failed methods short labels**: *the casualty*, *retired*, *the unsupervised straw man*, *craters*, *collapses*, *a documented failure*, *whipsaw*.

### Limitations
- A separate subsection titled "Limitations". It opens "Several limitations should be kept in mind." and then lists one concrete limit per sentence with no apology and no generic "future research" filler.
- He discloses process contamination himself: "The hold-out, though blind at delivery, was consulted repeatedly during the final review phase; every such use is labeled in the notebook".
- He also puts limits in the body next to the claim they limit: "Four anonymized classes cannot certify a universal rule; that is a sample of four."

### How conclusions are stated
- Answer the question directly, often with a "not": "The disciplined answer is: not on raw IC."
- Then say what does hold, with its strength labelled: "(+0.0019 per day pooled, t = 1.7, suggestive rather than certified, at 35–40% lower turnover where turnover matters)".
- Compress the recommendation into one sentence and label it as such: "In one sentence: count each idea once, weight ideas equally, learn feature shapes only where the evidence is strong, and freeze everything."
- End with the practical value to the reader (desk, sponsor, production), not with a broad statement.

### Stance
- Skeptical of added complexity. Each addition "must justify itself against the simpler alternatives". Sophistication has a "false promise ... that sophistication is free".
- Writes for a practitioner: *desk*, *book*, *production*, *costs money*, *bankable number*, *trades more cheaply*.
- States the reporting stance once, early: "From the outset, the project favored transparent reporting over good-looking results, and that mandate shaped it more than any single method did."

---

## 2. Paragraph architecture

**Default shape: claim, then evidence, then mechanism, then implication.** Most prose paragraphs run about 80 to 180 words.

1. **Opening sentence**: a topic claim, often short and declarative, or a framing condition.
   - "The cost is measurable."
   - "The mechanism behind the puzzle has a name and a remedy."
   - "Before any averaging is meaningful, all variants in a cluster must point the same way relative to the target."
   - "The test that ended up anchoring my confidence came from perturbing the feature set itself."
2. **Evidence**: numbers in parentheses or after a colon, plus a pointer (Section X, Figure Y). Several numbers are packed into one sentence rather than spread across several.
3. **Mechanism**: one sentence of plain-language "why", often joined with "so", "because" or "that is,".
4. **Landing**: a short verdict sentence, an imperative rule, or a bridge to the next test. The landing is usually the shortest sentence in the paragraph.
   - "The bias–variance ledger favors the simpler method."
   - "Pool everything."
   - "Nothing re-weightable was lost."
   - "...and that is the route the next section takes."

**Annotated example 1 (Section 6.1), a negative result.**

> [Claim + mechanism behind a colon] "The uniqueness regression, the literal implementation of the project's objective, fails on this cluster for a reason the regularization path makes visible: out-of-fold IC improves as λ grows, that is, as the method stops trusting the off-diagonal of the estimated correlation matrix." [Why] "Class 1 is nearly one-dimensional, so no variant is meaningfully more unique than another, and the matrix-inverse correction amplifies estimation noise in exactly the small-eigenvalue directions where noise lives." [Verdict] "The bias–variance ledger favors the simpler method." [Scope] "This is a negative result about this cluster, not the method." [Bridge] "The real test is class 4, flagged in the exploratory analysis as having several sub-themes."

**Annotated example 2 (Section 7.2), a hold-out failure.** The paragraph opens with a bold run-in claim, "Class 1 is the alpha-decay lesson."

> [Number, then a "yet" turn] "Its linear composites lost two-thirds of their IC (0.031 → 0.0119, t ≈ 1.9), yet the drift diagnostic shows the redundancy structure barely moved." [Stacked evidence] "The correlation matrix's Frobenius drift is 0.22, in line with the other classes, not one of 16 variants flips IC sign, and all shrink uniformly 50–70%." [Two-clause verdict] "The correlation matrix is stable; the signal level decayed." [Figure as evidence] "Figure 10 shows how: ..." [Short verdict] "Nothing re-weightable was lost." [Counter-test] "A rolling re-estimation arm (quarterly refits on an expanding window) recovers exactly nothing on class 1, because there is nothing stale to refresh." [Rule] "The operational moral for any frozen composite is to monitor the level, not just the structure, because alpha decay cannot be recovered by re-estimation."

**Variations he uses:**
- **Pre-emptive self-audit**: "Because the one significant win sits only just past the 2σ line, I also checked its sensitivity ..." A check he ran against his own best result.
- **Reframe paragraph**: "This re-frames the study. No positive paired comparison here, including our own headline win, should be quoted as significant on its own. The defensible claim shifts to where the stress tests had already placed it, the floor rather than the mean, which multiplicity correction does not touch."
- **Roadmap paragraph** at the start of a long section, one sentence per subsection, ending on "The summary to keep in mind throughout: ..."

---

## 3. Sentence-level habits

### Length and rhythm
- Mean sentence length is about 26 words (median 23). About 16% of sentences are 10 words or fewer, and about 30% run past 30 words.
- **Rhythm: long, number-dense sentences, then a short verdict.** The short sentences almost always follow evidence. Real short sentences from the report: "The cost is measurable." / "The pattern generalizes cleanly." / "This re-frames the study." / "The detection is estimator-robust." / "Everything else is noise-level." / "Pool everything." / "The protocol is strict freeze."

### Signature constructions (with approximate frequency)
1. **"X, not Y" contrast** (about 30 uses, one per 350 words): "it weights definitions, not ideas", "a scope decision, not a claim of universality", "suggestive, not certified", "a property of the class, not of the exact feature list", "Level decay says retire or de-weight, not refit."
2. **Colon reveal**: a claim, a colon, then the specification or the number (149 colons; about one sentence in three has one). "it has one structural flaw: it weights definitions, not ideas." / "The disciplined answer is: not on raw IC."
3. **Comma appositive where others use a dash.** This is how he avoids em dashes. "Dedup with equal weights, cluster then count each idea once, is the only method ..." / "the lesson, keep the detector and drop the tilt, became the final method's form." / "The defensible claim shifts to where the stress tests had already placed it, the floor rather than the mean, which ..."
4. **"What X is Y" cleft** (8 uses): "What we add is the deduplication observation." / "What makes the number credible is its consistency." / "What can be beaten is the benchmark's fragility".
5. **"The one ..." for singling something out** (16 uses): "the one property of the target that matters", "the one idea that survives every test", "the one data-driven decision", "the one failure that actually occurred".
6. **Count announcer before a list**: "Three findings define the story." / "Two further exploratory facts constrain what follows." / "Three headlines order the results." / "Two labels belong on this number."
7. **Methods as agents**: "The tuner picks k = 1 in all five folds", "tuning was offered a wide grid twice and could not beat it", "the tree that taught it the shapes", "Every rival craters somewhere", "the estimator chose full pooling in 19 of 20 class-folds".
8. **Two-clause verdicts** with a semicolon or a light comma: "The correlation matrix is stable; the signal level decayed." / "The detector stays and the tilt goes." / "Detection is robust, monetization fails, and the method keeps τ2 as a diagnostic flag".
9. **Deliberate comma splice for emphasis** (about 4 uses): "is not just weaker, it points the wrong way." / "The idea was not wrong, it was already embedded in the method."
10. **Plain-language gloss after jargon**: "that is, as the method stops trusting the off-diagonal", "which is to say at zero", "(1 bp = 0.0001)", "a slowly-changing state".
11. **Borrowed-field analogy stated plainly**: clinical meta-analysis, pharmacokinetics. "Econometrics knows the same phenomenon as the forecast-combination puzzle, and medicine got there first with a closed form."
12. **Imperatives for rules** in method steps and playbooks: "Group the duplicates." / "Pool everything." / "walk away." / "Treat it as a research flag, not a production decision".

### Transitions he actually uses
- Sentence-initial: *First, / Second, / Third,*; *Finally,*; *But* (sentence-initial, e.g. "But on class 3 the tuner froze k = 6"); *Because ...,*; *Having [done X], I ...*; *Before ...,*; *Whatever ...,*; *For example,*; *In short,*; *In effect*; *In one sentence:*; *Equally important is*; *Out of sample as in sample,*.
- Mid-sentence: *therefore* ("The objective is therefore", "I therefore re-ran"); *that is,*; *so* (clause linker, about 25 uses); *because* (about 12); *yet*; *while*; *rather than*; *meanwhile*; *instead*.
- Counts of transitions **he never uses**: *however* 0, *moreover* 0, *furthermore* 0, *additionally* 0, *thus* 0, *whereas* 0, *indeed* 0, *notably* 0, *importantly* 0, *crucially* 0, *interestingly* 0.

### Words and phrases he favors
- Precision and scope words: *exactly* (22), *precisely* (6), *only* (41), *every* (44), *nothing* (17), *never* (12), *real* (18), *actually* (8), *truly* (4), *literal/literally*.
- Process words: *frozen/freeze* (34), *blind* (11), *leak-free*, *out of fold*, *scored exactly once*, *pre-specified*, *post hoc*, *retired*.
- Verdict words: *survive(s)*, *collapse(s)* (15), *casualty*, *craters*, *certified*, *suggestive*, *nominally*, *defensible*, *noise-level*, *within noise*, *a hair wide*.
- Cost and trade words: *tax*, *earns*, *buys nothing*, *pays for itself*, *costs money*, *desk*, *book*, *bankable*.
- Plain qualifiers: *sensible*, *plain*, *textbook*, *simplest*, *cheap*, *mechanical*.
- Framing nouns: *lesson*, *moral*, *ledger*, *story*, *map*, *playbook*, *verdict*, *headline*, *census*.

### Words he avoids (zero or near-zero in 10,500 words)
*delve, leverage, crucial, key (as adjective), landscape, nuanced, comprehensive, robustly, substantially, genuinely, honest/honestly, highlight, underscore, reveal, indicate, suggests, interestingly, surprisingly, remarkably, striking, basically, it's worth noting, we find.*
He writes "shows" (6), "delivers", "confirms", "establishes" instead. He uses "robust" only in its technical sense (robust composite, robust to fat-tailed returns, estimator-robust). He says "transparent reporting", never "honest".

### Punctuation
- **No em dashes** (0 in the report). En dashes only in number ranges (0.7–0.95, classes 2–4) and paired names (Newey–West, Benjamini–Hochberg).
- Parentheses are heavy (about 190 in the prose, roughly one pair per 55 words). They hold numbers, section pointers and short glosses, not whole sidebar thoughts.
- Semicolons are moderate (36). They join two parallel verdicts or separate items in a list that already has commas.
- Almost no questions. The one real one is explanatory: "The statistic Q asks one question: is the spread of the block ICs larger than their own standard errors would generate if every block carried identical information?"
- Curly quotes mark a coined or borrowed term, e.g. the "forecast combination puzzle", or a sarcastic usage ("the "obvious" improvements").

---

## 4. Numbers, tables, figures and captions

### Number conventions in prose
- ICs to four decimals (0.0309), t-stats to two (t = 2.26), signed deltas with an explicit + or − (+0.0028, −0.0031).
- Pairs use "vs.": "(0.047 vs. 0.031)", "(0.0127 vs. 0.0080)".
- Counts use "k of N": "on 17 of 20 class-4 subsets", "five folds of five", "19 of 20".
- Relative changes as percentages, with the underlying levels beside them: "a 59% relative improvement (0.0127 vs. 0.0080)".
- Units defined once, where first used: "35 to 117 basis points of daily IC (1 bp = 0.0001)", "approximately 21 trading days (one month)".
- **Placement: the number goes after the claim, in parentheses or after a colon.** It is rarely the subject of the sentence. For example: "XGBoost's apparent in-sample IC edge (0.047 vs. 0.031) evaporates the moment it is scored out of fold (Section 6.1)."
- Paired values are put side by side with a slash: "(+0.0033/+0.0036) with lower significance (t = 1.82/1.63)".

### Referring to figures and tables
- Figures usually appear as a parenthetical pointer after the claim they support: "(Figure 4)", "(Figure 5, first panel)". There are 33 figure references and 41 section references in the prose.
- When a figure is the subject, the sentence says what it is for: "Figure 9 is the scorecard and Figure 8 the study in one figure, and the full numeric table is Appendix A." / "Figure 2 shows each class's correlation matrix three ways: raw, grouped by sign convention, and grouped by redundancy after sign alignment." / "Figure 10 shows how: ..."
- Tables are introduced with what they summarize: "Table 1 summarizes the panels after preprocessing to complete cases, that is, dropping rows with a missing target or any missing variant."
- Small comparison tables are placed inline in the prose, with the sentence right after them explaining what they show.

### Caption anatomy
Each caption has three parts: (1) a short title fragment that names or characterizes the figure, (2) how to read it (encodings, lines, colors), and (3) **the takeaway as a full declarative sentence**. Short titles he used: "The returns being modeled.", "The recipe's merge trees.", "The study in one figure.", "The selected composite.", "The feature-subset stress test: ...". Multi-panel figures get a color-convention sentence ("Throughout, gray marks the benchmark, blue the selected composite ...") and a takeaway for each lettered panel.

Four real captions:

> **Figure 1:** The returns being modeled. The target's autocorrelation traces the overlap triangle of a ∼21-day cumulative forward return sampled daily; this one property sets the purge window and the HAC lag count for the entire study.

> **Figure 4:** Purged 5-fold CV mean IC for every method on every class. Shading is scaled within each class column (darker = higher IC on that class) and the bold entry marks the class best. The benchmark is the robust anchor everywhere, supervision helps only where the cluster is diffuse (class 4), and trees collapse on the three smaller or tighter classes.

> **Figure 12:** Every paired method-versus-benchmark t-statistic in the study (the in-sample purged-CV family), one dot per method and class, blue for positive and red for negative. The inner dashed lines mark nominal |t| = 2, which flags seven comparisons; the outer dashed lines mark the dependence-aware Westfall–Young 95% max-T bar (±3.75), which flags none. The two survivors at the looser BH-10% rate are both negative results.

> **Table 2:** The weekly level-plus-decay criterion, pooled across classes, paired against the benchmark on the hold-out. Each row is one four-class package: which composite serves each class. The retired references calibrate the scale: the criterion can flag a bad package at t = −3, so the selected package's +1.72 is competing against a real zero, not against a test with no power.

Table captions go above the table and explain column meanings and their caveats in the caption itself (Table 1 defines "PC1 var. share"). A caption can also carry a methodological caveat: "This test is pre-freeze by construction, since re-running method selection on the hold-out would contaminate it."

---

## 5. Section and report architecture

### Title
A slogan in imperative or aphorism form, a colon, then a plain descriptive subtitle: *Count Each Idea Once: Building Robust Composites from Correlated Alpha Signals*. The slogan comes back as the recommendation in the abstract and conclusion.

### Abstract (one paragraph, about 250 words), in order
1. The practical problem in general terms: "A quantitative research team rarely holds one definition of a factor. It holds a cluster of correlated variants of the same idea, and those variants must somehow become one signal."
2. The question, with the benchmark named: "This report asks how ... and whether anything beats the benchmark of ranking each variant and averaging."
3. Data with sizes, then the list of methods, then the evaluation framework, then the blind hold-out.
4. The recommendation as an imperative chain: "Count each idea once: cluster ..., average ..., weight ..., add ... only where ..., and freeze every parameter."
5. The negative stated flatly, including his own method: "No method in the study, including this one, delivers more raw predictive accuracy than the benchmark."
6. What does improve, with numbers: "What the selected composite improves is everything around the accuracy: ..."
7. Closing with "In short, ...".

For the 230GA Executive Summary (one paragraph, must say "Do not implement" if there is no alpha), use the same order: problem, strategy tested, data and test design, verdict, then what the evidence does and does not show.

### Introduction
- Opens with a general observation about the domain, stated as fact: "Feature definitions in finance are arbitrary in a specific, well-known way."
- Defines the benchmark precisely (with an equation) and names its structural flaw, then gives a concrete example ("For example, if eight of ten variants are ...").
- Rules out the textbook answer and measures what it costs: "The textbook dimensionality-reduction answer, PCA, is unfortunately not the answer here." ... "The cost is measurable."
- Describes the approach in first person: "To answer the question systematically, I built a single fixed evaluation framework (...) and pushed a sequence of composition methods of increasing complexity through it".
- States the reporting stance, then announces the findings: "Three findings define the story."
- **Numbered findings**: each starts with a bold full-sentence claim, followed by two or three sentences of evidence with numbers and a section pointer. Findings claim things; they are not topics:
  1. "Each cluster is worth what it is worth, and no weighting scheme extracts more."
  2. "Deduplication is the one idea that survives every test."
  3. "The selected composite's edge is signal quality, not the level of its IC."

### Related work
Organized by idea, not paper by paper. Each paragraph ties a literature strand to his own result: "Our study effectively replays this literature inside a single alpha signal, and reaches the same resolution the literature does: shrink toward equal weights, and deviate only on strong evidence. What we add is the deduplication observation." Novelty is claimed carefully: "To our knowledge the explicit mapping (...) is not standard in the signal-combination literature".

### Body sections, in order
- **Data and exploratory analysis**: facts that constrain what follows ("Two further exploratory facts constrain what follows.").
- **Evaluation framework**: "defined before any comparison was run". A metric / definition / "reads as" table. Three guard procedures with run-in heads ("HAC significance.", "Purged cross-validation.", "Paired tests, out of fold.").
- **Methods**: "organized from simplest to most complex, and each addition must justify itself against the simpler alternatives". Bulleted, with bold labels and one-line purposes ("The unsupervised straw man, retained precisely so its failure is measured, not assumed.").
- **In-sample results**: in run order, with a roadmap paragraph and a "summary to keep in mind throughout".
- **Stress tests / robustness**: "I attacked the dedup composite from every direction I was able to think of".
- **Blind hold-out**: "Protocol" (strict freeze, what was locked) and then "Results" ("Three headlines order the results." plus bold run-in claim paragraphs).
- **Statistical checks**: multiplicity, estimator robustness, stability.
- **The selected methodology**: numbered imperative steps, each with the evidence that justifies it; then "In one sentence: ..."; then "Equally important is what the composite deliberately leaves out", with each exclusion paired with its documented failure.
- **Discussion**: a playbook (numbered diagnostics, each mapped to an action), *What we would explore with [sponsor]'s resources*, and "Limitations".
- **Conclusion**: restates the question in past tense ("We were asked whether ..."), gives a one-word answer, says what can be beaten, and closes on why the negative results are valuable.
- **Appendices**: the full scorecard table and a reproducibility note (seeded randomness, Restart-and-Run-All, date of the last clean run, which script makes each figure).

### Heading phrasing
- Top-level sections use plain nouns in sentence case: "Introduction", "Related work", "Data and exploratory analysis", "Evaluation framework", "Methods", "In-sample results", "The blind hold-out", "Statistical checks", "Discussion", "Conclusion".
- Subsections are noun phrases that name the object or the finding: "The accuracy ceiling", "Variance dimension versus predictive dimension", "The heterogeneity estimator as a detector", "What the trees contribute", "A tuning-free adaptive weight, borrowed from medicine", "PCA and PLS out of sample", "A playbook for a new feature class".
- **Bold run-in paragraph heads are full claim sentences**: "Class 1 is the alpha-decay lesson." / "The shaped composite is the class-1 method that survives." / "The adaptive tilt is the casualty."
- No question headings and no clever puns. The title slogan is the only flourish.

### Mapping onto the 230GA template
- *Executive Summary*: the abstract pattern above, in one paragraph, with the verdict sentence stated flatly.
- *What did you try*: framework first (fixed before testing), then methods from simplest to most complex, then risk model, turnover and costs. ChatGPT prompts are reported like any other method: what it was asked, what it returned, and how that was tested.
- *What did you learn*: run-in claim heads for each finding (factor exposures, full sample / post-2010 / recent 12 to 18 months), multiplicity handled as in Section 6 of this guide, then Limitations.
- *Critical ChatGPT evaluation*: judge its output the way he judges a tuner, by what survived out of sample, with specific failures named and scoped the way he scopes methods (a negative result about this prompt, not about the tool).

---

## 6. How he handles statistics in prose

- **Say what kind of t-stat it is and why**: "Every t-statistic in this report is Newey–West with 25 lags, wide enough to absorb the overlap established in Section 3.2." Report t next to the effect, in the same sentence or the same parentheses: "it gains +0.0028 daily IC over the benchmark with Newey–West t = 2.26", "(class 2: −0.0180, t = −2.97)".
- **A fixed ladder of labels, each used literally**:
  - *not significant* / *not itself significant*: "The shaped-minus-linear IC gap (+0.0035, t = 1.3) is not itself significant."
  - *within noise* / *indistinguishable inside fold noise* / *noise-level*
  - *nominally significant*: past |t| = 2 before correction.
  - *suggestive, not certified*: 1.5 < t < 2, or post hoc.
  - *survives Holm / BH*: the only thing he calls certified.
  "Significant" is only ever used in the statistical sense.
- **Separate point estimates from significance**: "Supervised rivals post slightly larger point gains there (+0.0033/+0.0036) with lower significance (t = 1.82/1.63): estimated weights add point-estimate gains and variance in roughly equal measure."
- **Multiple testing**: state the size of the family and how it was built ("The study ran 56 paired "does X beat the benchmark?" comparisons, all on the purged-CV out-of-fold record (12 methods × 4 classes, plus the retired PCA and PLS; ...)"). Then the nominal count ("Seven clear |t| > 2 nominally: six negative and one positive"). Then survivors under each correction ("Zero tests survive Holm at 5%, Benjamini–Hochberg at 5%, or the dependence-aware Westfall–Young max-T"). Then the adjusted p for his own headline (≈ 0.66). Then a reframe: "This re-frames the study."
- **Show the test had power before calling a null a null**: "The test has power, since it flags the known pathologies at BH 10%, so the null results elsewhere reflect an absence of effect rather than an absence of power."
- **Hold-outs**: *blind*, *frozen*, *strict freeze*, *scored exactly once*. List everything that was frozen. "Nothing is fit, tuned, or selected on the hold-out." Mark which tests are pre-freeze by construction. Disclose any later use of the hold-out and label post hoc combinations ("a post hoc combination of pre-specified components").
- **Sensitivity checks aimed at his own best result**: "Because the one significant win sits only just past the 2σ line, I also checked its sensitivity ..." Then say precisely what the check does and does not establish: "What the check establishes is that ..., not that ...".
- **Consistency as evidence when t is weak**: "What makes the number credible is its consistency. The same ordering holds on every class where anything differs, on 20 of 20 class-1 feature subsets, and under every aggregation tried."
- **In-sample versus achievable**: "not ex-ante selectable: leak-free tuning delivered 0.0208, not 0.0226."

---

## 7. Exemplar sentences (verbatim)

1. "It is harder to beat than it looks, but it has one structural flaw: it weights definitions, not ideas."
   *Shows: colon reveal plus "X, not Y". Concedes the benchmark's strength, then names its one flaw.*
2. "The cost is measurable. On the one class in our data with several distinct sub-themes, a frozen first-principal-component composite keeps about a third of the benchmark's out-of-sample IC."
   *Shows: four-word claim, then a quantified consequence.*
3. "From the outset, the project favored transparent reporting over good-looking results, and that mandate shaped it more than any single method did."
   *Shows: the stance statement, made once and early.*
4. "No method in the study, including this one, delivers more raw predictive accuracy than the benchmark."
   *Shows: the negative result stated flatly, including his own method.*
5. "A purely unsupervised composite of this cluster is not just weaker, it points the wrong way."
   *Shows: comma splice used for emphasis; escalation from weak to wrong.*
6. "A method never gets credit for its in-sample fit."
   *Shows: a methodological rule stated as a short maxim.*
7. "This discipline pays for itself early. XGBoost's apparent in-sample IC edge (0.047 vs. 0.031) evaporates the moment it is scored out of fold (Section 6.1)."
   *Shows: claim, evidence in parentheses, section pointer.*
8. "This is a negative result about this cluster, not the method."
   *Shows: precise scoping of a failure.*
9. "Choosing between them by validation search mostly measures luck."
   *Shows: skepticism of tuning in one short, plain sentence.*
10. "Econometrics knows the same phenomenon as the forecast-combination puzzle, and medicine got there first with a closed form."
    *Shows: cross-field analogy with dry wit.*
11. "Because the one significant win sits only just past the 2σ line, I also checked its sensitivity to the concordance measure within the rank family"
    *Shows: first-person self-audit of his own best result.*
12. "Two caveats were recorded at the time, and both mattered later."
    *Shows: count announcer, past tense, and transparency about the process.*
13. "In effect the data redrew the ruler each variant is measured with, and the ruler it drew ignores mid-pack shuffling and counts only depth into the tail: the composite says the same thing it always said, it just stops changing its mind over noise."
    *Shows: explaining a technical mechanism with a plain metaphor.*
14. "The gap between the best cell in a sensitivity table and what tuning actually delivers is this study's recurring look-ahead lesson."
    *Shows: turning a failure into a named lesson.*
15. "The correlation matrix is stable; the signal level decayed."
    *Shows: two-clause verdict with a semicolon.*
16. "The detector stays and the tilt goes."
    *Shows: a short decision sentence with methods as agents.*
17. "Supervision that wins the inner split does not survive the freeze."
    *Shows: a general rule drawn from a hold-out failure.*
18. "This re-frames the study. No positive paired comparison here, including our own headline win, should be quoted as significant on its own."
    *Shows: how he handles multiple testing and downgrades his own headline.*
19. "The test has power, since it flags the known pathologies at BH 10%, so the null results elsewhere reflect an absence of effect rather than an absence of power."
    *Shows: defending a null result with a power argument.*
20. "Two labels belong on this number. The t of 1.72 is suggestive, not certified, and the package combination is post hoc, although its components were pre-specified."
    *Shows: labelling a result's strength and its post hoc status.*
21. "Four anonymized classes cannot certify a universal rule; that is a sample of four."
    *Shows: stating a limitation bluntly, with no apology.*
22. "We were asked whether a cluster of correlated feature variants can be combined into something better than the rank-and-average benchmark. The disciplined answer is: not on raw IC."
    *Shows: the conclusion opening. The question is restated and answered in one word.*
23. "We consider the negative results the most valuable deliverable: each one retired an upgrade before it could cost money."
    *Shows: valuing negative results in practitioner terms.*

---

## 8. Do and don't checklist

**Do**
- Write in first person: "I" for steps you ran, "we" for conventions, positions and team decisions. Use "the study" or "this report" as the default subject.
- Build each paragraph as **claim, then evidence, then implication**. Put the number in parentheses after the claim, add the mechanism in one plain sentence, and end on the verdict or rule.
- State negative results first and flatly, scope them precisely, and name the lesson.
- Report every effect with its t-stat and say what kind of t it is (Newey–West, lags).
- Use the label ladder literally: not significant, within noise, nominally significant, suggestive not certified, survives Holm.
- Give the size of the test family and say what survives correction, including for your own headline result.
- Say what was frozen and what the hold-out was, and disclose any later use of the hold-out.
- Give each caption a title fragment, how to read it, and a takeaway sentence.
- Write findings and run-in heads as claims, not topics.
- Use plain qualifiers (sensible, plain, textbook) and practitioner words (desk, book, costs money).
- Define a unit or abbreviation once, where it first appears.
- Keep asides between commas or inside parentheses.

**Don't**
- **No em dashes.** Use commas, colons, semicolons or parentheses. En dashes only in ranges (2010–2022) and paired names (Fama–French).
- **No filler**: no "It is worth noting", "Importantly,", "Interestingly,", "In conclusion,", "Overall,", "This highlights", "This underscores", "plays a crucial role", "a comprehensive analysis".
- No *however, moreover, furthermore, additionally, thus, indeed, notably, crucially*. Use *But*, *so*, *because*, *therefore* (mid-sentence), *First/Second/Third*, *Finally*.
- No modal hedging ("may potentially", "could suggest", "seems to indicate"). Put a number or a label on the uncertainty instead.
- No contractions.
- No rhetorical questions in headings or body text, except a question used to explain how a test works.
- Do not call anything "significant" unless you mean the statistical sense and it passed.
- Do not say "honest" or "honestly". Say "transparent", or show it by what you disclose.
- Do not end a paragraph on a broad sweeping statement. End on a number-backed verdict, a rule, or a pointer to the next test.
- Do not copy the few generic lines in his own report. These are its weakest sentences and read as filler: "The resulting findings led to a robust methodology supported by evidence.", "To ensure the integrity and soundness of our results, ...", "due to their unpromising results".

---

## 9. Habits that read as AI-generated if overused

The report uses several constructions that are also common in machine-written text. They sound like Hashim when they are rationed and backed by evidence. Stacked together, they sound like a model imitating him.

| Habit | Rate in the report | Keep it natural by |
|---|---|---|
| "X, not Y" contrast | about 1 per 350 words | At most one per paragraph, never in two consecutive sentences, and only when Y is something a reader would actually believe. |
| Colon reveal ("The answer is simple: ...") | about 1 in 3 sentences | Use colons to introduce a specification, list or number. Never use a colon for suspense. If three sentences in a row have colons, rewrite one. |
| Short punchy verdict sentence | about 16% of sentences | Only right after a number-dense sentence. Never open a section with one, and never put two in a row. |
| Count announcer ("Three findings define the story.") | about 8 in the report | Two or three per document at most, and the count must match what follows. |
| "exactly" / "precisely" | 28 in 10,500 words | At most one per 500 words, and only when a quantity or an equality really is exact. |
| *the one X that ...* | 16 uses | Use it when there really is only one, and not twice on a page. |
| Methods as agents ("The tuner picks", "craters") | frequent | Keep the verbs literal (picks, loses, collapses, survives). Avoid cute ones (dances, whispers, shines). |
| Lists of three | common but not automatic | Vary the count. He writes twos, fours and fives as often as threes. |
| Comma-splice emphasis | about 4 uses | At most one per document section. |
| Aphoristic closers ("Pool everything.") | a handful | Only where it states a rule the paragraph has just earned. |

Other tells to avoid: perfectly parallel bullet lists, every paragraph the same length, a summary sentence that repeats the paragraph's first sentence, "Not only ... but also", and opening sentences like "In the world of ...".

---

## 10. Illustrative contrast (for calibration only)

*Generic register (avoid):* "Importantly, our analysis reveals that the climate attention strategy's performance appears to be largely driven by the COVID period, which may suggest that the signal is not robust."

*Hashim's register (numbers in brackets are placeholders; check each against the team outputs before use):* "The strategy's gains are a COVID story, not a climate one. Remove [dates] and the Short-Brown leg earns [x]% a year (t = [x]); on the frozen hold-out it loses 2–4% a year, and the IC changes sign. Only 2 of 32 strategy-period cells survive Holm. Do not implement."
