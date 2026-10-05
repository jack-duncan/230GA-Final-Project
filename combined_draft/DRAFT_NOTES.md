# Draft notes (for the team; not part of the submission)

Prepared 2026-10-04 as a mock-up of a combined final report in which each of the five members runs one facet of the project in their own conversation with Claude. It merges the Climate work (team repo `main`, Hashim's audit on `hashim/research-extension`) with Charishma's analyst-revision strategy (`charisma` branch), restructured to the brief's template: one-paragraph Executive Summary; What Did You Try (pages 1-5); What Did You Learn (pages 5-8); appendices.

## What is real and what is drafted

| Part | Prompts | Claude replies | Evaluation |
|---|---|---|---|
| D.1 Jack, design review | **Re-voiced** from Hashim's exchange 01 (`research/exchange/01_idea_generation/`) in a repo-owner voice; content unchanged so the reply still fits. The EMV discovery in the follow-up is attributed to Hashim. | Real (exchange 01 replies, unchanged) | Adapted from Hashim's fact-check, written as Jack |
| D.2 Hashim, frozen test code | **Verbatim** (exchange 02) | Real | Hashim's own, lightly trimmed |
| D.3 Cristhian, multiple testing | **Re-voiced** from exchange 03 in a formal numbered-question voice; "my own four tests" refers to the tests Cristhian actually proposed at the halfway point | Real (exchange 03 reply) | Adapted from Hashim's fact-check, written as Cristhian |
| D.4 Aditya, red team | **Re-voiced** from exchange 04 (both rounds) in a blunt skeptic voice; the pasted draft summaries are quoted as "Hashim's draft", unchanged | Real (both rounds) | Adapted from Hashim's fact-checks, written as Aditya |
| D.5 Charishma, Claude Code | **Verbatim** from her `ai_log/ai_interactions.md` | Summarized from the log (Claude Code sessions have no saved transcript) | Written for this draft from the log, code history and reruns, as in the earlier combined report |

Dates in D.1, D.3 and D.4 are placeholders (the original exchanges all ran on 2026-09-26). Aditya's role is invented: there is no record of what he worked on. Before anyone signs: Jack, Cristhian and Aditya replace the drafted prompts with what they actually sent, or send these prompts themselves and swap in the replies; then delete the yellow box at the top of Appendix D.

## Other changes from `final_submission_organized`

- Restructured to the brief's template; the five-paragraph summary became one paragraph.
- The public GitHub link to the revision repo (which holds WRDS-derived data) is gone; D.5 says the repository was made private, which Charishma still has to do.
- "Charisma" in section titles became "Revision strategy"; folder names on disk (`data/charisma`, `supporting/code/charisma`, notebook 02) are unchanged so the notebooks and the claim audit still run.
- The 6-month rule's 2.45% / t = 2.23 and the 2.1-3.8% holdout losses are now labelled "as first built" where they appear next to corrected-baseline numbers.
- "-0.0%" became "0.0%" in the text and in `tables/T5_attribution.tex`.
- Added `supporting/transcripts/` (Claude replies per member, prompts as Markdown) and `supporting/code/md_prompts_to_tex.py`, which generates `prompts/*.tex` from them.

## Build

```
python supporting/code/md_prompts_to_tex.py
tectonic -X compile MFE230GA_Final_Project.tex
python supporting/claim_audit/claim_audit.py     # 121 values; "not quoted" rows are fine
```
