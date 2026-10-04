import sys, pathlib, numpy as np, pandas as pd
ROOT=pathlib.Path("/home/hashim/projects/GA/project/research"); T=ROOT/"outputs/tables"
sys.path.insert(0,str(ROOT/"lib")); sys.path.insert(0,str(ROOT/"modules/M1b_alt_signals")); sys.path.insert(0,str(ROOT/"modules/M7_robustness_ledger/verify"))
import statsmodels.api as sm, common as C
FAC=C.load_ff5_mom(); KF3=C.load_kf_ff3()
opt=pd.read_csv(T/"M5_industry_momentum_optimizer_returns_monthly.csv",index_col=0,parse_dates=True)
def nw(y,X):
    r=sm.OLS(y,sm.add_constant(X)).fit(cov_type="HAC",cov_kwds={"maxlags":6},use_t=True); return 12*r.params["const"], r.tvalues["const"]
y=opt["X_unc"].loc["1970-01-31":"2026-07-31"]
print("KF3+UMD", nw(y, KF3[["Mkt-RF","SMB","HML"]].join(FAC["UMD"]).loc[y.index]))
print("FF5file MKT SMB HML + UMD", nw(y, FAC[["Mkt-RF","SMB","HML","UMD"]].loc[y.index]))
for a,b in [("2010-01-31","2022-07-31"),("2010-01-31","2026-07-31"),("1970-01-31","2009-12-31")]:
    yy=opt["X_unc"].loc[a:b]; print("FF5U",a,b,nw(yy,FAC[["Mkt-RF","SMB","HML","RMW","CMA","UMD"]].loc[yy.index]))
import helpers as H
M=H.build_measures(); print("eval_end MCCC",H.eval_end(M["MCCC"]).date(),"CPU",H.eval_end(M["CPU"]).date())
P=pd.read_csv(T/"M7_family_P.csv"); print(P[P.duplicate_of.notna()][["test_id","duplicate_of"]].to_string())
paths=pd.read_csv(T/"M5_industry_momentum_optimizer_paths_monthly.csv",header=[0,1],index_col=0,skiprows=[2],parse_dates=True)
print("X_b-1.00 fallback post1970", paths[("X_b-1.00","fallback")].astype(str).eq("True").sum(), "binding share", paths[("X_b-1.00","binding")].astype(str).eq("True").mean())
fz=pd.read_csv(T/"M7_frozen_pre1970_returns_monthly.csv",index_col=0,parse_dates=True); print(fz.columns.tolist())
led=pd.read_csv(T/"M7_robustness_tests_ledger.csv")
print(led.primary_or_exploratory.value_counts().to_dict())
print("context tags:", led.note.astype(str).str.extract(r"(\[context: \w+\])")[0].value_counts().to_dict())
for pat in ["Li-Ji_V","LiJi","max_N","maxN","2.01","C9_epa","C6_", "C5_"]:
    print(pat, led.test_id[led.test_id.str.contains(pat,regex=False)].tolist()[:40])
print(pd.read_csv(T/"M7_data_provenance.csv").to_string())
print(pd.read_csv(T/"M7_epa_shock_controls.csv").round(5).to_string())
ho=pd.read_csv(T/"M7_holdout_reading.csv"); print(ho[["series","model","alpha","ci90_lo","ci90_hi","delta","mde_80","reading"]].round(5).to_string())
sm_=pd.read_csv(T/"M7_search_members.csv"); print(sm_[(sm_.family=="S-full")&(sm_.rw_pass)][["member","alpha","t","rw_adj_p"]].round(4).to_string())
print(sm_[sm_.member.isin(["opt:X_b-1.00","opt:X_unc","GB:epa5","opt:X_b-0.25","opt:X_b-2.00"])][["family","member","alpha","t","rw_adj_p"]].round(4).to_string())
print(led[led.test_id=="M7_C4_reproduction"].note.iloc[0])
