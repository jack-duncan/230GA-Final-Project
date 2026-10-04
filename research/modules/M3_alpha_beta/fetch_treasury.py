"""Cache US Treasury daily par yield curve (home.treasury.gov) 1990-2026 and write the end-of-month 10-year yield to
modules/M3_alpha_beta/data/tsy_10y_eom.csv (date, y10_eom in percent). Used only for the BOND end-of-month robustness
(GS10 is a monthly average of daily yields). Idempotent: skips years already cached.
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M3_alpha_beta/fetch_treasury.py
"""
import pathlib
import time

import pandas as pd
import requests

DATA = pathlib.Path(__file__).resolve().parent / "data"
RAWD = DATA / "treasury_par_yield"
RAWD.mkdir(parents=True, exist_ok=True)
URL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all"
       "?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv")

frames = []
for y in range(1990, 2027):
    f = RAWD / f"par_yield_{y}.csv"
    if not f.exists() or f.stat().st_size < 1000:
        for k in range(4):
            try:
                r = requests.get(URL.format(y=y), timeout=60, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
                f.write_bytes(r.content)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", y, e); time.sleep(3 * (k + 1))
    d = pd.read_csv(f)
    d["Date"] = pd.to_datetime(d["Date"], format="%m/%d/%Y")
    frames.append(d[["Date", "10 Yr"]])
    print(y, len(d))
daily = pd.concat(frames).dropna().sort_values("Date").drop_duplicates("Date")
eom = daily.set_index("Date")["10 Yr"].astype(float).resample("ME").last().rename("y10_eom")
eom.index.name = "date"
eom.to_csv(DATA / "tsy_10y_eom.csv")
print(eom.tail(), len(eom))
