"""Download all external data used by the research exercise into data/raw/.
Ken French Data Library (zipped CSVs) and FRED (fredgraph.csv). Idempotent."""
import io, zipfile, time, pathlib, requests
RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
KF = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
KF_FILES = ["F-F_Research_Data_Factors_CSV.zip", "F-F_Research_Data_5_Factors_2x3_CSV.zip",
            "F-F_Momentum_Factor_CSV.zip", "F-F_ST_Reversal_Factor_CSV.zip", "F-F_LT_Reversal_Factor_CSV.zip",
            "49_Industry_Portfolios_CSV.zip", "Siccodes49.zip"]
FRED = ["EMVENRGYENVREG", "EMVOVERALLEMV", "VIXCLS", "GS10", "TB3MS", "GS2", "BAA", "AAA",
        "MCOILWTICO", "PPIACO", "PALLFNFINDEXM", "CPIAUCSL", "CFNAI", "USREC", "UNRATE", "INDPRO", "T10YIE", "DFII10"]
def get(url, tries=4):
    for k in range(tries):
        try:
            r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status(); return r.content
        except Exception as e:
            print("retry", url, e); time.sleep(3 * (k + 1))
    raise RuntimeError(url)
for f in KF_FILES:
    z = zipfile.ZipFile(io.BytesIO(get(KF + f)))
    for n in z.namelist():
        (RAW / ("kf_" + n.replace(" ", "_"))).write_bytes(z.read(n)); print("KF", n)
for s in FRED:
    (RAW / f"fred_{s}.csv").write_bytes(get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}")); print("FRED", s)
