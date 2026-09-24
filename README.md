# MFE 230GA Final Project

State-dependent climate alpha: a walk-forward test of green-minus-brown industry returns, conditioned on climate-transition attention and macro regimes. The assignment brief is `MFE230GA_Final_Project_2025.pdf` and the current write-up is `writeup.pdf`.

## Layout

```
data/         input CSVs (FF49 industries, FF3 factors, emissions intensity, macro series)
papers/       reference papers
notebooks/    analysis notebooks, each paired with a .py script via jupytext
outputs/      figures and tables produced by the notebooks
```

## Setup

```
uv sync
```

Open `notebooks/climate_alpha_analysis.ipynb` and select the `.venv` kernel. Edits to a notebook or its `.py` twin can be synced with `uv run jupytext --sync notebooks/<name>.ipynb`.
