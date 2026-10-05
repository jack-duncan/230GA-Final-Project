# MFE 230GA Final Project — Group 4

Hashim Almodamagha, Aditya Aryan, Jack Duncan, Charishma Takkallapalli, Cristhian Ruiz Cardozo

## Main deliverable
**`MFE230GA_Final_Project.pdf`** (source: `MFE230GA_Final_Project.tex` and `appendix_D_claude_interactions.tex`)

## The story
We investigated a climate-attention timing strategy on high-emission industries, rejected it after it failed its holdout, a frozen pre-2010 test and a signal audit, and pivoted to analyst EPS revisions versus industry momentum. Both conclude **do not implement**: the Climate signal is a volatility-news index and its gain is Brown-leg exposure; the revision blend's alpha disappears once momentum (UMD) is controlled for. Each member ran one facet of the project in conversation with Claude (Appendix D).

## Notebooks (executed, outputs saved)
1. `notebooks/01_Green_Climate_Strategy.ipynb`: the Climate strategy, corrected baseline, benchmarks, imported audit results
2. `notebooks/02_Charisma_Final_Strategy.ipynb`: the revision strategy (IC, risk, backtest, attribution, robustness)

## Folders
| Folder | Contents |
|---|---|
| `data/green/` | Climate inputs (FF49, FF3, emissions, macro), FRED EMVENRGYENVREG, team results, verified audit results |
| `data/charisma/` | Revision strategy: processed signal panels, Ken French raw files, validated results |
| `figures/`, `tables/` | Exhibits used by the report, written by the notebooks |
| `prompts/` | LaTeX fragments of the prompts in Appendix D (generated) |
| `supporting/code/` | Revision pipeline (`charisma/src`, 68 tests), Climate library (`green/`), prompt converter |
| `supporting/transcripts/` | Claude replies and prompts, one folder per Appendix D part, plus the Claude Code log |
| `supporting/claim_audit/` | `claim_audit.py` and its report |
| `supporting/original_notes/` | The earlier separate documents this report replaces |

Raw I/B/E/S and CRSP security-level data are licensed by WRDS and are not included; `supporting/code/charisma/src/` builds the panels from them.

## Rerunning
Python 3.9+ with pandas, numpy, scipy, statsmodels, matplotlib, pyarrow and jupyter. Notebook 2 reads validated results by default (`RUN_PIPELINE = False`). Tests: `cd supporting/code/charisma && python -m pytest -q tests`. Claim audit: `python supporting/claim_audit/claim_audit.py`. Report: `python supporting/code/md_prompts_to_tex.py && tectonic -X compile MFE230GA_Final_Project.tex` (or `pdflatex`, twice).
