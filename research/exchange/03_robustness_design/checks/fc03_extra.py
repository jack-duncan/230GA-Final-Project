"""Extra fact-check computations for exchange 3: autocorrelation-adjusted DSR, DSR on the appraisal ratio by N, and the EPA spread with MCCC/CPU shock controls (exploratory, not pre-registered).
Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/03_robustness_design/checks/fc03_extra.py"""
import sys, numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from common import _kf_sections, _kf_monthly, RAW, load_ff5_mom
mom = _kf_monthly(list(_kf_sections(RAW / "kf_F-F_Momentum_Factor.csv").values())[0])
print('UMD raw file first month', mom.index.min().date(), 'last', mom.index.max().date())
EG=0.5772156649015329
def emax(N): return 0 if N<=1 else (1-EG)*stats.norm.ppf(1-1/N)+EG*stats.norm.ppf(1-1/(N*np.e))
def z_psr(srm,T,sk,ku,N): return (srm*np.sqrt(T-1)-emax(N))/np.sqrt(1-sk*srm+(ku-1)/4*srm**2)
# autocorrelation-adjusted: scale z by t_NW/t_iid
for lab,sra,T,sk,ku,ratio in [('EPA post2010',0.5204,199,0.353,4.766,1.7246/2.1191),('book post2010',0.6961,199,0.286,3.661,2.5411/2.8349),('book full',0.5553,679,-0.2824,5.7747,4.1444/4.1769)]:
    srm=sra/np.sqrt(12)
    out={N: round(stats.norm.cdf(ratio*z_psr(srm,T,sk,ku,N)),3) for N in [1,2,5,10,100]}
    print(lab,'NW-adjusted DSR', out)
# AR DSR with N = 8 (residual Nyholt of optimizer paths)
arm=0.3999/np.sqrt(12)
for N in [4,6,7,8,10,24]:
    print('AR full N',N, round(stats.norm.cdf(z_psr(arm,679,0.0401,3.4094,N)),4))
# EPA + MCCC robustness
fac=load_ff5_mom()
gb=pd.read_csv('outputs/tables/M4_emissions_gb_monthly_returns.csv',parse_dates=['date']).set_index('date')
att=pd.read_csv('data/derived/attention_measures.csv',parse_dates=['date']).set_index('date')
y=gb['epa5'].loc['2010-01-31':'2026-07-31']
cols6=['Mkt-RF','SMB','HML','RMW','CMA','UMD']
def run(X,lab):
    d=pd.concat([y.rename('y'),X],axis=1,sort=True).dropna()
    m=sm.OLS(d['y'],sm.add_constant(d.drop(columns='y'))).fit(cov_type='HAC',cov_kwds={'maxlags':6})
    last=[c for c in X.columns if c not in cols6]
    print(f"{lab:45s} n={len(d)} alpha={12*m.params['const']:.4f} t={m.tvalues['const']:.2f} "+' '.join(f"{c}:{m.params[c]:.4f}(t {m.tvalues[c]:.2f})" for c in last))
F=fac[cols6]
run(F.join(att['MCCC_shock']),'FF5U + MCCC_shock (same month)')
run(F.join(att['MCCC_shock'].shift(1).rename('MCCC_shock_l1')),'FF5U + MCCC_shock lag1')
run(F.join(att['MCCC_shock']).join(att['MCCC_shock'].shift(1).rename('l1')),'FF5U + shock + lag1')
run(F.join(att['MCCC_transition_shock']),'FF5U + MCCC_transition_shock')
run(F.join(att['CPU_shock']),'FF5U + CPU_shock')
run(fac[['Mkt-RF','SMB','HML']].join(att['MCCC_shock']),'FF3 + MCCC_shock')
run(pd.DataFrame(att['MCCC_shock']),'raw on MCCC_shock only')
# restrict to 2012-11..2020-12 PST window
y0=y
y=y0.loc['2012-11-30':'2020-12-31']; run(F.join(att['MCCC_shock']),'PST window 2012-11..2020-12, FF5U+shock')
run(F,'PST window baseline FF5U')
y=y0
print('corr shock, Mkt', pd.concat([att['MCCC_shock'],fac['Mkt-RF']],axis=1,sort=True).dropna().loc['2010':].corr().iloc[0,1])
