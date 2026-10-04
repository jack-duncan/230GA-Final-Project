"""Glue for running ChatGPT's exchange-2 code (chatgpt_code_v1.py, unmodified) on the real data.

Everything here is input plumbing the prompt left unspecified (file locations, how `fac` is built,
which window a mode uses). No function of chatgpt_code_v1.py is edited or monkeypatched in this file.
Harmonization experiments (which DO patch behaviour, to attribute discrepancies) live in align.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
RESEARCH = Path("/home/hashim/projects/GA/project/research")
TEAMDATA = Path("/home/hashim/projects/GA/project/230GA-Final-Project/data")
RAW = RESEARCH / "data" / "raw"
CHECKS = RESEARCH / "exchange" / "02_coding_support" / "checks"
OUT = CHECKS / "out"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(RESEARCH / "lib"))
sys.path.insert(0, str(CHECKS))

from common import load_ff5_mom  # noqa: E402

import chatgpt_code_v1 as g  # noqa: E402  (verbatim extraction, sha256 6cdf0006...)

FAC_COLS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF", "UMD"]


def real_inputs() -> dict:
    """G1 + G2: the prompt's inputs on disk. `fac` = Ken French FF5 (2x3) + UMD, decimals, month-end, from 1963-07
    (exactly what the prompt describes); team FF49 VW file; FRED CSVs in data/raw."""
    fac = load_ff5_mom()[FAC_COLS].copy()
    return dict(ff49=str(TEAMDATA / "ff49_industry_monthly.csv"), fac=fac,
                emv_cat=str(RAW / "fred_EMVENRGYENVREG.csv"), emv_all=str(RAW / "fred_EMVOVERALLEMV.csv"),
                gs10=str(RAW / "fred_GS10.csv"), wti=str(RAW / "fred_MCOILWTICO.csv"), vix=str(RAW / "fred_VIXCLS.csv"))


def save(out: dict, tag: str) -> None:
    """Write every DataFrame/Series output of run_backtest to out/<tag>_*.csv (fits and arrays excluded)."""
    import numpy as np
    import pandas as pd
    for k, v in out.items():
        if isinstance(v, (pd.DataFrame, pd.Series)):
            v.to_csv(OUT / f"{tag}_{k}.csv")
        elif isinstance(v, np.ndarray):
            pd.Series(v, name=k).to_csv(OUT / f"{tag}_{k}.csv", index=False)
