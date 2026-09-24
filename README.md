# MFE 230GA Final Project

State-dependent climate alpha: a walk-forward test of green-minus-brown industry returns, conditioned on climate-transition attention and macro regimes. The assignment brief is `MFE230GA_Final_Project_2025.pdf` and the current write-up is `writeup.pdf`.

## Layout

```
ai/           prompts used for the deliverable, with output summaries and evaluations
data/         input CSVs (FF49 industries, FF3 factors, emissions intensity, macro series)
papers/       reference papers
notebooks/    analysis notebooks, each paired with a .py script via jupytext
outputs/      figures and tables produced by the notebooks
```

## Setup

1. Install uv if you don't have it:

   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   (or `brew install uv` on macOS)

2. Clone the repo and create the environment. `uv sync` installs Python 3.12 if needed and all dependencies into `.venv/`:

   ```
   git clone https://github.com/jack-duncan/230GA-Final-Project.git
   cd 230GA-Final-Project
   uv sync
   ```

3. Open `notebooks/climate_alpha_analysis.ipynb` in VS Code, Cursor, or Jupyter and select the `.venv` Python kernel. To use Jupyter in the browser: `uv run --with jupyterlab jupyter lab`.

## Running the analysis

Run the notebook top to bottom, or run its script from the repo root:

```
uv run python notebooks/climate_alpha_analysis.py
```

Figures are written to `outputs/figures/` and tables to `outputs/tables/`.

## Notebooks and scripts

Each notebook has a matching `.py` script (jupytext percent format, configured in `jupytext.toml`). Edit whichever is convenient, then sync so the other matches:

```
uv run jupytext --sync notebooks/climate_alpha_analysis.ipynb
```

Claude Code edits the scripts and syncs them to the notebooks automatically through the hook in `.claude/settings.json`; see `CLAUDE.md`.

## Adding dependencies

```
uv add <package>
```

Commit the updated `pyproject.toml` and `uv.lock`.

## Documenting AI use

Log every substantial AI interaction in `ai/` using the template in `ai/README.md`.
