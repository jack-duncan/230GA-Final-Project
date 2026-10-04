# Literature digest: climate green-minus-brown timing (MFE 230GA final project)

Purpose: related-work section and fact-check reference for the final report. Every number below was read from the PDFs listed in the next table, unless a line is explicitly marked "our arithmetic" or "team writeup". Section 12 is from general knowledge, not from the folder, and is labelled as such.

Notation: GMB = green minus brown return spread, BMG = brown minus green. "Carbon premium" = BMG expected or realized return. "Greenium" = expected GMB return (negative when green has lower expected return).

## 0. Sources and page conventions

| # | Paper | File | Page numbers cited as |
|---|---|---|---|
| 1 | Pástor, Stambaugh, Taylor (2021) | papers/Sustainable Investing in Equilibrium.pdf | journal pages (PDF p.1 = p.550) |
| 2 | Pástor, Stambaugh, Taylor (2022) | papers/Dissecting Green Returns.pdf | journal pages (PDF p.1 = p.403) |
| 3 | Bolton, Kacperczyk (2021) | papers/Do Investors Care about Carbon Risk.pdf | journal pages (PDF p.1 = p.517) |
| 4 | Aswani, Raghunandan, Rajgopal (2024) | papers/Are Carbon Emissions Associated with Stock Returns.pdf | journal pages (PDF p.1 = p.75) |
| 5 | Zhang (2025) | papers/Carbon Returns across the Globe.pdf | journal pages (PDF p.1 = p.615) |
| 6 | Eskildsen, Ibert, Jensen, Pedersen (2026) | papers/Realized Returns to Green Investing A Global.pdf | printed pages (PDF page minus 1; PDF p.1 is the unnumbered title page) |
| 7 | Gârleanu, Pedersen (2026) | papers/Climate Risk Pricing.pdf | printed pages (PDF page minus 1) |
| 8 | Călin, Lupu, Topa (2026) | papers/Climate Transition Risk Premium in Equity Markets.pdf | printed pages = PDF pages |
| 9 | Lehnherr, Mehta, Nagel (2024) | ssrn-4938729.pdf | printed pages = PDF pages |

Extraction note for fact-checkers: in the Aswani et al. PDF the minus sign is a special glyph that plain text extraction silently drops (for example Table IV shows "0.675" where the paper has "-0.675"). The numbers below were re-extracted with the sign restored. In Zhang (2025) and Bolton and Kacperczyk (2021) the Greek Delta glyph is dropped, so rows printed as "Emissions" in Panel B of Zhang's Table IV and in Tables VIII and IX are emissions growth (Delta emissions).

## 1. Quick map

| Paper | Type | Sample | One-line result | Stance on GMB |
|---|---|---|---|---|
| PST 2021 | Theory | none | Green has lower expected return (tastes + climate hedge) but outperforms when ESG concerns rise unexpectedly | Expected GMB < 0, realized GMB driven by concern shocks |
| PST 2022 | Empirical, US | Nov 2012 to Dec 2020 | GMB +65 bps/mo realized, but about -4 bps/mo after purging climate-concern and earnings shocks | Realized green outperformance = unexpected concern shocks |
| BK 2021 | Empirical, US firms | 2005 to 2017 | Higher total emissions and emission growth earn higher returns; intensity does not | Carbon (brown) premium in levels, not intensity |
| ARR 2024 | Empirical, US + Europe | 2005 to 2019 | BK result driven by vendor-estimated emissions and size controls; intensity unpriced | No robust carbon premium |
| Zhang 2025 | Empirical, 49 countries | Jun 2009 to Dec 2021 | With point-in-time data, US brown underperforms (-0.39%/mo); BK premium is look-ahead | Realized GMB > 0 in US (transition), zero globally |
| EIJP 2026 | Replication, US + 48 countries | to Dec 2022 | No GMB alpha survives Benjamini-Hochberg; published t-stats show publication bias | Realized returns cannot identify the greenium |
| GP 2026 | Theory + calibration | none | Risk pricing alone can make brown the hedge; greenium below 1 pp in every calibration | Sign ambiguous, magnitude small |
| Călin et al. 2026 | Empirical, index spreads | 2010 to 2026, daily | Clean-minus-brown spread is small on average, regime- and oil-dependent | Conditional, episodic |
| LMN 2024 | Method (factor timing) | 1965 to 2022 | Shrinkage-disciplined timing with many predictors adds about 0.30 Sharpe over static | Not about climate; template for timing |

## 2. Pástor, Stambaugh, Taylor (2021), Sustainable investing in equilibrium

**Citation.** Pástor, Ľ., R. F. Stambaugh, and L. A. Taylor (2021). Sustainable investing in equilibrium. Journal of Financial Economics 142(2), 550-571. doi:10.1016/j.jfineco.2020.12.011.

**Question.** How do investor tastes for green holdings, and climate risk, affect expected returns, portfolios, the size of the ESG industry and real investment?

**Data and sample.** None (theory with a calibration).

**Method.** Single-period equilibrium with a continuum of CARA investors who get non-pecuniary utility d_i g_n from holding firm n with ESG characteristic g_n; market portfolio ESG-neutral (w_m'g = 0). Extension adds a climate variable C to utility.

**Headline findings.**
- Expected excess returns: mu = mu_m beta_m - (dbar/a) g (Proposition 1, Eq. 9, p.554). CAPM alpha of stock n = -(dbar/a) g_n, so green stocks have negative alphas and brown positive (Corollary 2, Eq. 10, p.554).
- Three-fund separation (market, risk-free, ESG portfolio) (Proposition 3, p.554). With no dispersion in ESG tastes everyone holds the market (Corollary 4, p.555).
- Two-factor model: market plus ESG factor; ESG betas equal the characteristics g; ESG factor premium E[f_g] = -dbar/a < 0 (Eqs. 32-33, p.556). The factor can be estimated each period by a no-intercept cross-sectional regression of market-adjusted returns on g (Eq. 34, p.556); a simple version is proportional to r_green - r_brown (Eq. 35, p.556).
- Unexpected ESG-factor return = customer channel z_g plus investor channel (1/a)(dbar_1 - E_0 dbar_1) (Eq. 41, p.557). Proposition 6 (p.557): green outperforms if ESG concerns strengthen unexpectedly through either channel. If they strengthen through the investor channel, green alphas become more negative, so "past outperformance of green stocks makes it especially likely that they will underperform in the future" (p.557).
- Suggested proxies for taste shifts: investor surveys, flows into ESG funds; for customers, consumer surveys, firm revenues or profitability (p.557).
- The model "clearly predicts that green assets underperform brown over a sufficiently long period", long enough for unexpected taste changes to average to zero; "Disentangling alphas from ESG taste shifts is a major challenge for empirical work" (p.552).
- Calibration (sigma_m = 0.20, mu_m = 0.08, p.558): with lambda = 1 the ESG-minus-non-ESG expected return is -2% at Delta = 1% and -8% at Delta = 4% (Eq. 46, p.558). ESG investors' alpha peaks at lambda = 0.5 at -0.5% (Delta = 1%) to -2% (Delta = 4%) (p.559). ESG industry size 24% of market at Delta = 1%, 35% at 2% (p.551), 50% at 4% (p.561).
- Climate extension: expected returns add cbar/(1 - rho^2) times climate betas psi (Proposition 7, Eq. 56, p.561). Citing Choi et al. (2020) and Engle et al. (2020), green stocks are the better climate hedges, so psi_n = -xi g_n and the GMB premium has a taste component and a risk component, both negative (Eqs. 58-60, p.562).
- Conclusion: the model "aims to describe the world of the present and the future, but not necessarily the world of the past" (p.566).

**Implications.**
- (a) Timing on attention: the model links GMB returns to unexpected changes in concerns, contemporaneously. A spike in attention that is already known carries no positive expected GMB; if it reflects stronger investor tastes, subsequent expected GMB is lower (p.557). A "short Brown after attention crosses its 80th percentile" rule is therefore a bet that concerns keep surprising upward, not a bet on a known premium.
- (b) Alpha vs beta: under the model, CAPM alphas of green and brown are exposure to an omitted priced factor (the ESG factor); the paper stresses that the risk-based reading "can miss the underlying economics" because the source is tastes (p.555-556). Any GMB "alpha" relative to FF3 is ESG-factor beta by construction.
- (c) OOS discipline: the explicit warning that realized returns over periods of taste shifts do not estimate expected returns (p.552) is the theoretical basis for a frozen holdout.

## 3. Pástor, Stambaugh, Taylor (2022), Dissecting green returns

**Citation.** Pástor, Ľ., R. F. Stambaugh, and L. A. Taylor (2022). Dissecting green returns. Journal of Financial Economics 146(2), 403-424. doi:10.1016/j.jfineco.2022.07.007.

**Question.** Does green stocks' recent outperformance imply high expected green returns, or unexpected increases in environmental concern?

**Data and sample.** US stocks with MSCI environmental pillar scores and weights, Nov 2012 to Dec 2020 (MSCI coverage jumps in Oct 2012 from roughly 500 to over 2,000 stocks, p.409). Greenness G = -(10 - E_score) x E_weight/100, demeaned value-weighted (Eqs. 1-3, p.409). Climate concern: Ardia et al. Media Climate Change Concerns (MCCC) index, Jan 2003 to Jun 2018 (p.413). German twin green bonds Sep 2020 to Nov 2021.

**Method.** GMB = value-weighted top tercile minus bottom tercile of greenness. Expected return estimated two ways: implied cost of capital (ICC), and the intercept of a regression of GMB on zero-mean shocks, a_hat = rbar - b_hat xbar (Eqs. 4-6, p.412). Climate shocks C_t are prediction errors from AR(1) models fit on the trailing 36 months of MCCC (p.413-414). Panel regressions, industry decomposition, a PST-2021 green factor.

**Headline findings.**
- GMB cumulative outperformance 174% (green 264.9 vs brown 91.3), average 65 bps/month (t = 3.23), monthly Sharpe 0.33 vs market 0.30 (p.409-410; Table 3, p.411).
- Factor-adjusted alphas 47 to 71 bps/month, t between 1.99 and 2.91; lowest is FF3 + UMD alpha 47 bps (t = 2.14) (p.410). Table 3 (p.411) loadings: FF3 column HML -0.26 (t = -3.36), SMB -0.14 (t = -1.49); FF3+UMD column HML -0.18 (t = -1.99), UMD +0.13 (t = 2.00); FF5 column HML -0.21 (t = -2.60), RMW -0.39 (t = -2.90), SMB -0.26 (t = -2.59). GMB "tilts toward large stocks, growth stocks, and recent winners" (p.410).
- ICC: green portfolio 7.6% to 4.9%, brown 8.8% to 6.8%; GMB ICC always negative, range -0.4% to -2.4%, average -1.4% per year, and widening from -1.2% to -1.9% (p.412). Panel ICC on greenness slope t = -11.90 (p.412).
- Simulation (T = 68, R^2 = 20%, true mean -10 bps, sd 2%): the shock-adjusted estimator has about a 0.33 chance of the wrong sign and under 1% chance of a significant wrong sign; with t_xbar = 4 the plain mean has a 25% chance of being significant with the wrong sign (p.413).
- Table 4 (p.415), Nov 2012 to Jun 2018, 68 months: same-month climate shock 4.08 (t = 2.70) alone, 3.75 (t = 2.69) with earnings controls; previous-month shock 2.86 (t = 1.77); earnings announcement returns 0.77 (t = 2.64); intercept 0.05 (t = 0.20) and -0.04 (t = -0.15); R^2 0.14 to 0.25. FF3-alpha version intercept -0.15 (t = -0.66). Equity greenium about -4 bps/month vs ICC about -12 bps/month (p.415). The t-statistic of the average climate shock is 4.01 (p.416).
- Counterfactual GMB without climate and earnings shocks is flat to slightly downward and lies outside the 95% band of the realized path (Fig. 7, p.415-416).
- Anticipation check: in split halves, climate shocks enter somewhat more strongly in the second half (p.416).
- ESG fund assets were about $230 billion of $29 trillion US fund assets in 2020, under 1% (p.416). ESG flows and assets are insignificant once climate concerns are controlled (Table 5, p.418).
- Themes: agreement and summit R^2 = 0.15, societal impact 0.12, financial and regulation 0.12, disaster 0.02; "GMB returns are thus more closely associated with climate-related policy news than with news about disasters" (p.417-418).
- Adding oil price shocks and 30-year Treasury bond returns (a duration control) leaves the counterfactual essentially flat (p.418, details in the online appendix).
- Industry: industry-adjusted GMB mean is four times smaller and insignificant (t = 0.99 vs 3.23) (p.419). In panels, the across-industry greenness coefficient is 3.6 times the within-industry one, 0.25 (t = 2.14) vs 0.07 (t = 1.11) (p.419-420). FAANG does not drive results (p.419).
- Delay: small-cap GMB loads on previous-month shocks, 7.49 (t = 2.99); large-cap GMB on same-month shocks, 3.91 (t = 2.46), previous month 2.79 (t = 1.74) (Table 8, p.421).
- Green factor (scaled to GMB volatility 1.99%): Sharpe 0.29 vs GMB 0.33, correlation 0.72 (p.422). HML CAPM alpha -71 bps (t = -1.93) falls to -15 bps (t = -0.50) with the green factor, loading -0.80 (t = -4.55); UMD alpha 66 bps (t = 1.92) falls to -6 bps (t = -0.22), loading 1.05 (t = 6.18) (Table 9, p.422). "Nearly 80% of HML's negative alpha, and all of UMD's positive alpha" disappear (p.423). Industry-neutral HML CAPM alpha -66 bps (t = -2.69) falls to -23 bps (t = -1.37) (p.423). The green factor's FF3+UMD alpha is 34 bps (t = 2.46) (p.423).
- MSCI industry greenness at end-2019 (Table 2, p.410), relevant to the team's legs: Telecommunication Services +0.84 (rank 3), Pharmaceuticals +0.49, Banks +0.35, Media and Entertainment +0.70; Utilities -1.90, Steel -2.96, Marine Transport -2.83, Building Products -1.62; Aerospace and Defense +0.10 (rank 19 of 64, green side); Real Estate Management and Services -1.20, Real Estate Development -0.55 (brown side).
- German twin bonds: greenium averaged -4.63 bps (t = -6.19), widening from -1.6 to -6.2 bps; long green/short conventional earned 0.12 bps/day (t = 2.19), 37 bps cumulative (Table 1, p.406-407).

**Implications.**
- (a) Timing on attention: the priced object is the innovation in concern, not its level, and the reaction is same-month for large-cap portfolios. Value-weighted FF49 industry portfolios are large-cap dominated, so PST's own evidence leaves little one-month-lag drift to harvest; the small-cap lag (t = 2.99) is the only delayed channel they find. Policy-type news matters more than disasters (R^2 0.12-0.15 vs 0.02).
- (b) Alpha vs beta: GMB carries HML (-0.26), RMW (-0.39 in FF5) and UMD (+0.13) exposure; a green factor explains most of HML's 2010s underperformance. A green-brown spread and a short-value bet are hard to separate in 2012-2020. The a_hat estimator (regress GMB on concern shocks, read the intercept) is a ready Part B tool: a significant raw mean that disappears once concern shocks are controlled is "shock beta", not alpha.
- (c) OOS discipline: the paper itself warns that realized means are misleading when regressors have non-zero sample means (p.413). The EIJP replication (Section 7) shows these results weaken when the sample is extended.

## 4. Bolton and Kacperczyk (2021), Do investors care about carbon risk?

**Citation.** Bolton, P., and M. Kacperczyk (2021). Do investors care about carbon risk? Journal of Financial Economics 142(2), 517-549. doi:10.1016/j.jfineco.2021.05.008.

**Question.** Do firm-level CO2 emissions affect the cross-section of US stock returns (carbon risk premium vs carbon alpha vs divestment)?

**Data and sample.** Trucost EDX emissions (about 1,000 listed firms from fiscal 2005, over 2,900 US firms from 2016) matched to FactSet, 2005-2017; 3,421 of 3,481 Trucost firms matched (p.519, p.521).

**Method.** Pooled monthly regressions of returns on log emission levels, emission growth or intensity (scopes 1, 2, 3) with firm controls, year-month and industry fixed effects, clustered by firm and year (Eq. 1, p.530). Time-series regressions of the monthly carbon premium on nine factors with Newey-West 12 lags (Eq. 2, p.538-539). Institutional ownership regressions.

**Headline findings.**
- Level and growth of emissions earn higher returns; intensity does not (p.519; Table 8, p.532-533).
- Economic size, intro (p.519): one-sd increase in scope 1 level and change raises returns 15 and 26 bps/month (1.8% and 3.1% a year); scope 2: 24 and 18 bps; scope 3: 33 and 31 bps. Section 3.2 (p.530) states 13 bps (1.5%), 23 bps (2.8%) and 30 bps (3.6%) for scope 1, 2, 3 levels without industry effects. Industry fixed effects raise economic significance by 70% to 280% (p.530). (Fact-check: the intro and Section 3.2 numbers differ.)
- Table 8 (p.532): log scope 1 0.043 (SE 0.023) without and 0.164 (SE 0.036) with industry FE; scope 3 0.135 and 0.312. Intensity coefficients insignificant, e.g., scope 1 -0.010 (SE 0.012) (p.533).
- Correlation between scope 1 level and intensity is 0.6; 0.24 for scope 2 and 0.27 for scope 3 (p.523). Emission levels are highly persistent: AR(1) 0.977, 0.955, 0.967; intensities 0.945, 0.946, 0.969 (Table 3, p.524).
- Premium survives factor adjustment and is 10% to 20% smaller (p.539). Table 10 (p.540), 156 months: scope 1 level premium 0.058 (SE 0.026) unconditional, 0.053 (SE 0.023) with factors. The premium series loads on HML at -6.020 (SE 1.598) for scope 1, -4.284 (SE 1.759) scope 2, -6.444 (SE 2.537) scope 3. Intensity premium insignificant.
- In their sample HML averaged 0.00% per month and MOM 0.07% (p.528).
- Look-ahead check: lagging returns 0-12 months, scope 1 level remains significant to month 6 with industry FE (p.536).
- Divestment: one-sd higher scope 1 intensity lowers institutional ownership about 1.3 pp, 6.3% of its cross-sectional sd (p.539). Screening is only on scope 1 intensity and only in salient industries (oil and gas, utilities, autos/transport); excluding them removes divestment (Table 13, p.544) and strengthens the premium (p.541).
- Paris: premium larger in 2016-2017 (scope 1 0.205 vs 0.127, Table 14, p.545) but mostly from newly added firms; excluding them the post-Paris premium is insignificant (p.543). Difference-in-differences: top-quartile scope 1 emitters gain about 10.6% over six months around Dec 2015 (10.615, SE 1.175; p.544, Table 15 p.546).
- 1990s with imputed emissions: no significant premium (Table 16 Panel B, p.547).
- Without controls such as B/M, PPE and leverage, the level premium is insignificant (p.548).
- Industry ranks (Table 6, p.528; text p.523): highest average scope 1 emitters include independent power, electric utilities, airlines, multi-utilities, metals and mining, oil and gas, construction materials; lowest include thrifts and mortgage finance, capital markets, banks, real estate management and REITs, health care technology, biotechnology.

**Implications.**
- (a) Timing: a static cross-sectional study, no attention conditioning. It supplies the counter-prior that brown earns a premium, which a Short-Brown rule must overcome. Its industry ranking is consistent with the team's Green (Fin, RlEst) and Brown (Util, Steel, BldMt) picks, although it ranks on levels, not intensity.
- (b) Alpha vs beta: authors read the premium as priced risk, not alpha. The premium is specification dependent (needs size and other controls; industry FE strengthen it) and loads negatively on HML.
- (c) OOS: contemporaneous and one-month-lag design is the look-ahead problem that Zhang (2025) documents; ARR (2024) and EIJP (2026) show the result does not survive alternative choices.

## 5. Aswani, Raghunandan, Rajgopal (2024), Are carbon emissions associated with stock returns?

**Citation.** Aswani, J., A. Raghunandan, and S. Rajgopal (2024). Are carbon emissions associated with stock returns? Review of Finance 28(1), 75-106. doi:10.1093/rof/rfad013. (Accepted Feb 17, 2023; advance access Apr 3, 2023.)

**Question.** Is the BK emissions-return link real, or driven by vendor-estimated emissions and the choice of unscaled emissions?

**Data and sample.** Trucost US 2005-2019, 2,669 firms, 178,354 firm-months (Table I, p.82); Europe 236,526 firm-months, 36 countries (p.100).

**Method.** Replicate BK's pooled monthly regressions; split disclosed vs vendor-estimated observations; Heckman selection; scale emissions by sales.

**Headline findings.**
- More than 70% of emission figures in standard US databases are vendor-estimated (p.77). Estimated share 86% in 2005 (84% in final sample), low of 54% (53%) in 2015, 77% in 2018 (p.86). Trucost coverage 883-997 firms in 2005-2015, 2,706 in 2016, mostly estimated (p.83).
- Correlation of estimated scope 1 with sales 0.73 vs disclosed 0.25 (p.86). Log scope 1 correlation with log sales 0.699, log market cap 0.525; scope 1 intensity correlation with log market cap 0.060 (Table III, p.85).
- Estimated vs disclosed levels differ systematically: estimated indicator +0.416 (scope 1), -0.675 (scope 2), -0.270 (scope 3) (Table IV, p.89).
- Table V (p.91): no relation without size control (log scope 1 -0.034, SE 0.029; with industry FE -0.048). Adding only size flips signs: log scope 1 0.089 (SE 0.040); with full BK controls 0.060 (SE 0.033), scope 2 0.120, scope 3 0.262. Both industry FE and a size control are needed for significance (p.92). Authors attribute this to multicollinearity.
- Table VI (p.93): firm-disclosed log scope 1 -0.022 (SE 0.047), scope 2 0.028 (SE 0.032); vendor-estimated 0.135, 0.204, 0.300 (all SE-significant at 1%). BK's disclosed-emissions result holds in 1 of 8 industry-definition specifications, only with Trucost industry codes (p.93; footnote 1, p.76).
- Intensity is never positively priced; scope 1 intensity -0.013 (SE 0.005) in the full sample (Table VIII, p.97).
- Europe: without industry FE log scope 1 0.050 (SE 0.017) and intensities positive; with industry FE the relation disappears (log scope 3 turns -0.180) (Table X, p.101-102). "A link between emissions and returns may manifest as distaste for certain industries rather than for specific firms within an industry" (p.103). Emission disclosure 55% of firm-years in Europe vs 25% in the US sample (p.100).

**Implications.**
- (a) Timing: supports an industry-level design (pricing, where present, is industry distaste) and intensity as the ranking variable. No time-series content.
- (b) Alpha vs beta: apparent carbon premia can be size, growth and profitability in disguise because estimated emissions are near-deterministic functions of fundamentals.
- (c) OOS and specification search: conclusions flip with the size control and the industry classification; a direct argument for pre-registering the specification and reporting all variants.

## 6. Zhang (2025), Carbon returns across the globe

**Citation.** Zhang, S. (2025). Carbon returns across the globe. Journal of Finance 80(1), 615-645. doi:10.1111/jofi.13402.

**Question.** Does the BK carbon premium survive point-in-time emissions data, and what drives cross-country carbon returns?

**Data and sample.** S&P Trucost with vendor release dates, CRSP/Compustat and Compustat Global; returns Jun 2009 to Dec 2021 (p.619). Pre-2008 Trucost data are backfilled and excluded (p.623). US is 22% of observations, Japan 14%, developed markets 67% (p.619).

**Method.** Monthly tercile sorts on point-in-time carbon intensity, value-weighted, FF6 alphas; WLS panel regressions; replication of BK with contemporaneous data and sales controls; country-level regressions on flows, concern surveys and policy.

**Headline findings.**
- Release lag: US median 10 months after fiscal year-end (25th pct 6, 75th pct 24); international 7, 12, 22 months (p.623).
- Sales explain 50% of US scope 1 and 71% of scope 2 emissions variation (p.616); log emissions on log sales slope 1.04 (US scope 1) (Table III, p.625). Industry FE raise the R^2 of intensity on characteristics to 78% (scope 1) and 63% (scope 2) in the US: "industry variation drives most of the variation in carbon intensity" (p.627).
- US intensity sorts (Table IV, p.628): scope 1 L 1.44%, M 1.51%, H 1.04%, H-L -0.39%/month (t = -2.47), FF6 alpha -0.40% (t = -2.51); scope 2 H-L -0.27% (t = -1.87), alpha -0.34% (t = -2.40). Scope 1 H-L loadings: RMW +0.33 (t = 3.79), CMA +0.32 (t = 2.89), SMB +0.22 (t = 3.22), HML -0.07 (t = -1.00); scope 2 HML -0.12 (t = -1.94). The brown-minus-green portfolio loses as much as 50%, "a cumulative return of 100% for the green-minus-brown portfolio" (p.629).
- Total-emission sorts: H-L FF6 alpha -0.42 (t = -3.30) and -0.33 (t = -2.17); emission-growth sorts insignificant (Table IV, p.628; p.630).
- Firm-reported emissions only: H-L -0.37 (t = -2.20) and -0.26 (t = -1.79), alphas -0.39 and -0.34 (Table V, p.631). Strongest among large stocks, -0.42 (t = -2.55) (p.631). (Fact-check: the text on p.630 quotes -0.39 and -0.27 for this subsample; the table shows -0.37 and -0.26.)
- Regression: one-sd scope 1 intensity -0.19%/month (t = -2.52), scope 2 -0.21% (t = -2.46); with industry FE -0.13 (t = -1.04) and -0.06 (t = -0.80). "Cross-industry variation carrying more significance" (Table VI p.632; p.633).
- Global country-neutral sorts: scope 1 H-L -0.01% (t = -0.20), alpha -0.06% (t = -0.74) (Table VII, p.633).
- BK replication: contemporaneous emission-growth sorts give H-L +0.47% (t = 3.25, scope 1) and +0.58% (t = 4.34, scope 2) (Table VIII, p.635), but within sales-growth terciles only -0.03, 0.24, 0.10, all insignificant (p.635). Regression: emission growth 0.28 (t = 5.98) falls to 0.01 (t = 0.19) with same-period sales; log emissions 0.22 (t = 2.06) falls to -0.11 (t = -1.50) (Table IX, p.637). (Fact-check: text on p.634 cites 0.41% and 0.6% for the sorts and on p.636 cites 0.19% and 0.23% for the regression; tables show 0.47/0.58 and 0.22/0.24.)
- Countries: G7+AUS value-weighted alpha -0.44% (t = -7.24, scope 1); DM -0.40%; EM +0.20%; China +0.53% (Table X, p.639-640).
- Drivers (Table XI, p.642-643): one-sd higher sustainable flows lowers carbon returns 0.10% (t = -1.37, scope 1) and 0.15% (t = -2.11, scope 2); climate concern -0.11 (t = -1.68) and -0.15 (t = -2.26). Cash-flow news explains up to 7% of carbon-return variation. After these controls, one-sd tighter climate policy raises scope 1 carbon returns 0.13% (t = 2.12); civil law +0.55%.
- Conclusion: prior carbon premium "stems from forward-looking bias"; "equilibrium carbon return may remain muted for an extended period" (p.643-644).

**Implications.**
- (a) Timing: realized brown underperformance lines up with rising sustainable flows and concern, i.e., demand shocks, while tighter policy raises brown's required return. An attention index mixes both. Point-in-time lags of 10-12 months matter for any emissions-based classification.
- (b) Alpha vs beta: the US intensity spread is largely cross-industry and loads on RMW and CMA (green is lower profitability, higher investment). FF3 alone would miss this.
- (c) OOS: the headline US result is a 2009-2021 in-sample estimate; EIJP (Section 7) show it partially reverses in 2022 and the FF6 alpha is not robust to other models or to multiple testing.

## 7. Eskildsen, Ibert, Jensen, Pedersen (2026), Realized returns to green investing: a global replication

**Citation.** Eskildsen, M., M. Ibert, T. I. Jensen, and L. H. Pedersen (2026). Realized returns to green investing: A global replication. Working paper, version of April 6, 2026. (The team writeup cites it as SSRN 6527562; that identifier is not printed in the PDF.)

**Question.** Do realized returns give reliable evidence on the greenium once the full design space and multiple testing are considered?

**Data and sample.** 23 greenness measures (Trucost intensities and levels, MSCI, Sustainalytics, EPA TRI; 19 ex-US) (Table 1, p.7). US from Sep 2009 (Fig. 2, p.9), all analyses to Dec 2022 (p.23), plus 48 other countries. Data lagged by release date (p.22).

**Method.** For each measure, industry-agnostic and industry-neutral tercile GMB, value-weighted with market cap capped at the NYSE 80th percentile (p.8): 46 US factors. Alphas under excess return, CAPM, FF3, FF5+MOM, q5, Newey-West 3 lags: 230 US t-statistics (p.10). Benjamini-Hochberg FDR at 5% (p.10-11). Kolmogorov-Smirnov test of published vs replicated t-stats.

**Headline findings.**
- No GMB alpha is significant after BH, in the US or globally (p.3, p.10-11, p.13). About 8.6% of replicated |t| exceed 1.96 (p.3). Largest replicated t is 3.01 (industry-neutral MSCI weighted ESG score, FF3) (p.12).
- Largest published |t| is -5.15 (BK 2023, Table 6); over 13 years that implies an annual Sharpe of about 1.43, above the maximum 1.06 and median about 0.3 among 153 JKP factors (p.12).
- Published (n = 106) vs replicated (n = 6,786) t-stat distributions differ: KS D = 0.31, p < 0.001; published distribution bimodal near -4 and +2 (p.13-15, Fig. 4 on p.15).
- Power: average realized GMB volatility 5.4% a year; largest expected GMB magnitude from forward-looking estimates 0.78% a year (-39 bps per sd times 2 sd); implied annual Sharpe at most -0.15 (p.15). With T = 13.33 years expected t = -0.55; reaching t = 1.96 needs 167 years; a Sharpe of 0.54 would be needed with current samples, the 79th percentile of factors designed to be profitable (p.16).
- Rising concern creates repricing in which expected and realized returns move in opposite directions (p.16).
- PST reproduction (Table A4, p.29): 71 bps/month (SE 0.23) vs PST's 65; extending to Dec 2022 (N = 122) the mean falls to 0.24 (SE 0.24), insignificant. Extended FF3 loadings: HML -0.39 (SE 0.06); FF6: HML -0.22 (SE 0.09), RMW -0.33 (SE 0.14), CMA -0.26 (SE 0.14). "The GMB factor return reverses after PST's sample period ended in December 2020" while MCCC shocks kept rising to 2022 (p.28, Fig. A1 p.30).
- PST Table 4 extension (Table A5, p.30): same-month concern coefficient 2.16 (SE 1.14) in 2012-2018, 1.11 (SE 0.90) when extended to Dec 2022, 0.54 (SE 0.67) with Feb 2007 to Dec 2022; constant never significant. (Fact-check: coefficient scale differs from PST's own 4.08, presumably a different shock scaling.)
- Zhang reproduction: extending one year to Dec 2022 partially reverses the GMB; S1 intensity mean 13 bps/month; FF6 alphas significant but not with CAPM, FF3 or q5, and not after BH (p.28).
- Industry classification note: they follow Fama-French in using Compustat SIC codes; Kahle and Walkling (1996) find more than 80% disagreement between CRSP and Compustat 4-digit SIC codes (p.27-28, footnote 11).

**Implications.**
- (a) Timing: if the unconditional GMB mean cannot be detected in 13 years, a conditional rule that is active only part of the time has even less power. Their Fig. A1 is the published analogue of the team's holdout reversal.
- (b) Alpha vs beta: extended-sample HML loading -0.39 is larger than PST's; style exposure strengthens as the sample grows.
- (c) OOS and multiple testing: the reference design for the report. BH over all ex ante plausible variants, KS against published t-stats, and a sample-length calculation. Our arithmetic with their formula T = (1.96/SR)^2: SR 0.5 needs 15.4 years, SR 0.3 needs 42.7 years. For the team's 48-month holdout, expected t = 2 x SR, so even a true SR of 0.5 gives expected t of 1.0.

## 8. Gârleanu and Pedersen (2026), Climate risk pricing

**Citation.** Gârleanu, N., and L. H. Pedersen (2026). Climate risk pricing. Working paper, version of May 13, 2026. (The team writeup cites SSRN 5978854; not printed in the PDF.)

**Question.** Do green assets actually hedge climate risk once transition (carbon tax) and physical risk are priced in general equilibrium?

**Data and sample.** None; calibration to emissions and social cost of carbon.

**Method.** Dixit-Stiglitz production economy with firm fossil intensity f_i, stochastic carbon tax tau_t and climate severity phi_t (joint Markov chain), Epstein-Zin utility with unit IES (p.8-12).

**Headline findings.**
- Level-growth tradeoff: a higher tax lowers current consumption and raises growth (Proposition 2, p.17).
- The SDF is U-shaped in the carbon tax; below a critical tax, a tax increase lowers the SDF, a good state (Proposition 4, p.20; Fig. 1, p.3).
- With independent tax and physical-risk jumps, brown firms have lower expected returns than green when taxes are low (Proposition 7, p.22-23): brown pays off when taxes stay too low and climate damage worsens. With stronger jump dependence (taxes rise when physical damage rises) the greenium decreases and can flip sign (Proposition 8, p.23; Fig. 2, p.4).
- "Bet on the other team": climate-concerned investors tilt to brown, skeptics to green (Proposition 9, p.25; Fig. 3, p.32). Offered as a normative benchmark, not a positive prediction (p.7).
- Calibration (p.28-30): gamma = 6, beta = 0.03, alpha = 0.8, mu = 0.03, sigma = 0.08 (risk premium about 3.84%); 90% of firms green, f_b/f_g = 51 so brown is 85% of emissions at zero tax; social cost of carbon $200/tCO2 (EPA $190); tax grid 0 to 320 in 33 steps.
- The climate-risk greenium "can vary, but the magnitude is below one percentage point in all calibrations" (p.6); conclusion repeats "typically below one percentage point per year in absolute value" (p.35).
- Empirical framing: the greenium is found to be mildly negative (Eskildsen et al., 2024) and green stocks outperform when climate concerns rise; the negative greenium "is unlikely to be driven solely by climate-risk hedging demand and may instead reflect investors' preferences" (p.1).
- Carbon burden to value: brown 2.98, green 0.072; unpaid 2.23, below 1 once the initial tax exceeds $70/tCO2 (p.32).

**Implications.**
- (a) Timing: the sign of the green-brown response depends on why attention rises. Policy-driven tightening (good state) favors green; tightening triggered by physical shocks (bad state) weakens or reverses it. A single attention index blends the two; separating policy uncertainty (CPU) from media concern (MCCC) and disaster news is the model-consistent refinement.
- (b) Alpha vs beta: any risk-premium component is under 1 pp a year, so large realized GMB returns are shocks or tastes, not premia.
- (c) OOS: the model says the conditional greenium can change sign across regimes, so a rule tuned in one regime has no theoretical guarantee in the next.

## 9. Călin, Lupu, Topa (2026), Climate transition risk premium in equity markets

**Citation.** Călin, A. C., R. Lupu, and R. A. Topa (2026). Climate transition risk premium in equity markets: Downside asymmetry and regime dependence across Europe, the United States, and the United Kingdom. Borsa Istanbul Review, article 100895. doi:10.1016/j.bir.2026.100895. (Received Apr 16, 2026; accepted Aug 13, 2026; online Aug 20, 2026; volume not yet assigned in the PDF.)

**Question.** Is transition risk priced as a stable clean-minus-brown premium, or conditionally across regimes and markets?

**Data and sample.** Daily 2010-2026, 4,230 observations (p.3, Table 1 p.6). Clean leg is the S&P Global Clean Energy index for all three markets; brown legs STOXX Europe 600 Oil and Gas, S&P 500 Energy, FTSE 350 Oil Gas and Coal; Brent spot; ICE EUA futures; iBoxx green vs corporate bond indices 2023-2026 (p.3).

**Method.** OLS with HC3 errors, PCA factor blocks, 252-day rolling regressions, downside beta on negative-market days, quantile regressions, VaR/CVaR, event windows, bond greenium comparison (p.3-6).

**Headline findings.**
- Mean daily spread about zero: -0.0001 (Europe), -0.0002 (US), -0.0001 (UK) (Table A2.1, p.14).
- Table 1 (p.6): market beta -0.194 (Europe), -0.037 (US, insignificant), -0.379 (UK); Brent -0.113, -0.248, -0.120 (all 1%); carbon -0.0135 (10%), -0.0116, -0.0065; adj R^2 0.058, 0.111, 0.061.
- An industrials/materials/utilities factor adds 0.077, 0.016, 0.085 to adjusted R^2 and stays significant when orthogonalized (Tables 2-3, p.7).
- Downside beta on negative-market days: -0.373 (t = -5.45), -0.271 (t = -3.91), -0.512 (t = -6.61) (Table 4, p.8). No formal comparison with an upside beta.
- 30-day post-event cumulative spread (Table 7, p.11): COVID-19 outbreak +0.30 (Europe), +0.34 (UK), +0.46 (US); Ukraine invasion -0.14, -0.26, -0.44; COP26 -0.03, -0.13, -0.21; 2022 energy-crisis peak +0.25, +0.12, +0.12. Authors say this is cumulative spread, not abnormal returns (p.6, p.14).
- Equity spread vs bond greenium correlation 0.16 (Europe), -0.15 (US), 0.08 (UK) (Table 8, p.12).
- Conclusion: transition pricing is "conditional, asymmetric, and heterogeneous"; unconditional spreads economically small (p.13).

**Implications.**
- (a) Timing: the spread is dominated by oil and industrial-cycle exposure and by one-off events; COVID favored clean, Ukraine favored brown. An attention-conditioned GMB rule will pick up these episodes unless oil and industrial controls are in the hedge.
- (b) Alpha vs beta: supports adding commodity/oil and cyclical (industrials, materials, utilities) exposures to the factor controls (Christhian's test 2).
- (c) OOS: weak discipline. Many specifications, no multiple-testing correction, event windows not benchmarked. For fact-checking, treat as descriptive: the clean leg is identical in all three "markets", the UK spread has daily min -0.488 and max 0.482 with kurtosis 154.9, and Brent daily returns have 25th, 50th and 75th percentiles all 0.0000 (Table A2.1, p.14), which suggests stale or erroneous data.

## 10. Lehnherr, Mehta, Nagel (2024), Optimal factor timing in a high-dimensional setting

**Citation.** Lehnherr, R., M. Mehta, and S. Nagel (2024). Optimal factor timing in a high-dimensional setting. Working paper, August 16, 2024. SSRN 4938729.

**Question.** Can many predictors and many factors be combined into an optimal factor-timing portfolio that works out of sample?

**Data and sample.** US monthly, Jan 1965 to Dec 2022; OOS Jan 1986 to Dec 2022 (p.8, p.10). Factors: FF5 non-market factors (size, B/M, profitability, investment), large-cap versions, and 131 JKP factors (after dropping 6 short-term reversal and 16 short-history factors) (p.9).

**Method.**
- Timing portfolios G_t = X_{t-1} F_t with X z-scored on its trailing mean and sd; E[G_t] = Cov(X_{t-1}, F_t) (Eqs. 1-2, p.4). A constant predictor is included so the static factors are in the set (p.5). Brandt and Santa-Clara (2006): linear conditional weights become an unconditional mean-variance problem over K x J portfolios (p.3, p.5).
- Three shrinkage layers (p.6-7): Ledoit-Wolf (2003) covariance shrinkage to a scaled identity with Schäfer-Strimmer intensity; Kozak-Nagel-Santosh (2020) style weights w = (Sigma + (lambda/T) D)^(-1) (mu + (lambda/T) w0) shrinking toward the static mean-variance portfolio of the original factors (Eq. 4, p.6); factor rotation, rescaling so the absolute implied factor weights sum to one each period (p.7).
- Tuning: minimum 240 months training; lambda chosen on a grid to maximize Sharpe over an expanding set of 12-month validation blocks; weights refit every 12 months and applied to the next 12-month OOS block (p.8, Fig. 1 p.23).
- Predictors (Table 1, p.20): macro = real 1-year yield (1y Treasury minus trailing 12-month inflation), slope (5y minus 1y), 12-month change in the 1y yield, 3-month CRSP VW return, Baa-Treasury spread; factor-specific = 3-month and 12-month factor return, 3-month daily factor volatility, B/M, asset-growth and profitability spreads between long and short legs, weighted like returns (p.9-10).

**Headline findings.**
- FF factors 1986-2022 (Table 1, p.20): size SR 0.04, B/M 0.20, investment 0.46, profitability 0.52 (annual).
- Table 2 (p.21), OOS 1986-2022: 48 timing portfolios SR 0.81 (appraisal 0.79, mean 4.70%, sd 5.82%, worst 12 months -5.62%); without macro 0.67; without factor-specific 0.55; B/M spread only 0.44; 12-month momentum only 0.48; static optimal 0.52; equal weight 0.42. Large-cap FF: 0.55 vs static 0.30 vs equal 0.26. JKP with small predictor set (1,572 portfolios) 1.50 vs static 1.22 vs equal 0.61; large set (18,209) 1.42. Timing adds "roughly 0.30" Sharpe over static in each case (p.14). Sd uses Newey-West with 5 lags.
- Largest average weights: B/M x yield change and investment x yield change (Fig. 4 p.26; p.12). The strategy went short value in 1999, around 2007 and at the onset of COVID in 2020 (p.12).
- Timing beats static and equal weight in rolling 60-month windows except those ending 2003-2008 (p.11); lambda is higher early in the sample (Fig. 2, p.10-11).
- Turnover and cost (Table 3, p.22; p.15-16): FF timing about 586% two-way a year, cost 59 bp a year (about 10 bp per trade, Frazzini, Israel, Moskowitz 2018), cost-adjusted SR 0.71; large-cap 642%, 64 bp, 0.46; JKP 202% and 184%, about 20 bp, 1.39 and 1.32. (Fact-check: Table 3's column labelled "(bp)" prints 0.59; the text says 59 bp, so the column is in percent.)

**Implications.**
- (a) Timing: single-predictor timing does not beat equal weight (value spread only 0.44 vs 0.42); gains come from many predictors combined under shrinkage. Yield changes are the dominant predictor for value and investment factors, consistent with the team's finding that rates flip the signal through the spread's value loading.
- (b) Alpha vs beta: timing returns are evaluated against a static optimal portfolio of the same factors, the right benchmark for Part B (is the timing return more than holding the factors?).
- (c) OOS: tuning is on validation blocks strictly before each OOS year; this is the procedure to copy. Their gains rely on 20-year training windows and 37 OOS years.

## 11. Synthesis

### 11.1 Where the papers agree

1. Expected green-minus-brown returns are small. PST 2022: GMB ICC averages -1.4% a year (p.412) and the shock-purged mean is about -4 bps/month (p.415). EIJP: largest expected GMB magnitude 0.78% a year (p.15). GP: climate-risk greenium below 1 pp in all calibrations (p.6). Călin: mean daily clean-minus-brown near zero (p.14).
2. Realized GMB is driven by shocks to concern, flows and policy, not by a stable premium. PST 2021 Proposition 6 (p.557); PST 2022 concern shocks (Table 4, p.415); Zhang country flows and concern (p.642-643); EIJP repricing argument (p.16); Călin event windows (p.11).
3. Industry-level variation dominates. PST 2022: industry-adjusted GMB t = 0.99 (p.419). Zhang: industry FE explain most intensity variation (p.627) and shrink the return coefficient (p.632-633). BK: divestment only in salient industries (p.541-544). ARR: in Europe any pricing is industry distaste (p.103). This supports the team's FF49 industry design.
4. Intensity is the defensible greenness measure for pricing questions (ARR p.77-78, p.94-96; Zhang p.616, p.619); unscaled emissions proxy for size and sales.
5. Green loads against value and profitability. PST FF3 HML -0.26 (t = -3.36), FF5 RMW -0.39 (t = -2.90) (p.411); EIJP extended HML -0.39 (SE 0.06), RMW -0.33 (SE 0.14) (p.29); Zhang BMG loads RMW +0.33 and CMA +0.32 (p.628), i.e., GMB loads negatively on both.
6. Results are fragile to design and sample. ARR (size control, industry codes), Zhang (release timing), EIJP (BH, extension to 2022).

### 11.2 Where they disagree

1. Sign of the carbon premium. BK: brown earns more (level and growth, 2005-2017). Zhang: brown earns less in the US with point-in-time intensity (2009-2021). PST 2022: green realized more, expected less. ARR and EIJP: nothing robust. GP: theory allows either sign.
2. Whether green hedges climate risk. PST 2021 assumes green is the hedge, citing Choi et al. and Engle et al. (p.562). GP show brown can be the hedge when taxes are below the social cost of carbon (Proposition 7) and the sign depends on how policy and physical shocks co-move (Proposition 8).
3. Within vs across industry. BK find industry FE strengthen the firm-level premium (p.530). PST and Zhang find the action is across industries.
4. Whether realized returns are informative. BK and Zhang interpret realized spreads as premia (with caveats); PST, EIJP and GP argue realized returns over a repricing decade are misleading.

### 11.3 Facts bearing on the team's result

Team numbers below are from the team writeup (230GA-Final-Project/writeup.pdf).

- **COVID concentration.** The team's only significant cell is COVID 2020-2021 (3-month rule alpha 6.03%, t = 3.21; writeup p.3, p.5). The literature reads such concentration as a shock, not a premium: Călin's COVID window +0.30 to +0.46 clean-minus-brown within 30 days (p.11) coexists with a near-zero unconditional mean. PST 2022 show large GMB returns can come with a slightly negative expected return (p.415). LMN's timing model went short value at the COVID onset (p.12), and GMB is short value (PST p.411), so part of a COVID GMB gain is value-timing. The team's Brown leg (Util, Ships, Aero, Steel, BldMt) is industrial and cyclical, the exposure Călin's industrial factor captures (p.7).
- **Holdout reversal and IC sign flip.** Holdout Aug 2022 to Jul 2026 loses 2.1% to 3.8% a year; IC flips from about -0.08 to -0.09 in validation to +0.12 to +0.15 (writeup p.3-4). Precedents: PST's GMB reverses after Dec 2020 while MCCC shocks kept rising (EIJP p.28, Fig. A1 p.30); Zhang's GMB partially reverses in 2022 (EIJP p.28); the PST concern coefficient falls from 2.16 to 1.11 when extended to 2022 (EIJP p.30); Ukraine invasion windows favor brown by 0.14 to 0.44 (Călin p.11). Theory predicts it: after an investor-channel rise in concern, green's future alphas are more negative (PST 2021 p.557); if higher taxes arrive with worse climate news, the greenium shrinks or flips (GP Proposition 8). Power: with a 4-year holdout the expected t-stat is 2 x SR (our arithmetic with EIJP's formula, p.16), so the holdout cannot confirm a small edge, but a significantly negative holdout (t about -1.7 to -2.2) is still evidence against the rule.
- **HML loading.** Raw spread HML -0.24 full sample and -0.35 since 2010; residual after the rolling hedge -0.05 to -0.06 with t about -2 to -2.4 (writeup p.3). This matches PST's -0.26 (t = -3.36, p.411) and EIJP's extended -0.39 (SE 0.06, p.29). A green factor explains about 80% of HML's negative 2012-2020 CAPM alpha (PST p.423), so hedging HML also removes part of what the literature calls the green factor. The residual loading is what a lagged 60-month hedge leaves when the true beta moves with the value premium (see Lewellen and Nagel in Section 12). RMW is the next exposure to test (PST FF5 -0.39; Zhang BMG +0.33), which FF3 omits.
- **Rates flip the signal.** LMN's top predictors for value and investment are yield changes (p.12). PST add 30-year Treasury returns as a duration control and the counterfactual stays flat (p.418). The rate effect is plausibly the spread's value and duration exposure rather than a climate channel; test by adding term and rate factors to the hedge before interpreting it as climate.
- **Momentum.** PST GMB loads +0.13 on UMD (t = 2.00) and the green factor explains all of UMD's 2012-2020 alpha (p.410-411, p.422-423): add UMD to the controls (Christhian's test 2).
- **Signal construction.** PST price the AR(1) innovation of MCCC over a 36-month window, contemporaneously and one month lagged (p.413-414). The team uses a level z-score crossing an expanding 80th percentile. The literature supports the innovation as a contemporaneous regressor for Part B (explaining returns); it offers no evidence that a level threshold predicts next-month returns, and large-cap portfolios react within the month (Table 8, p.421).
- **Emissions snapshot timing.** Zhang's median release lag is 10 months in the US (p.623). A single emissions snapshot applied back to 2010 is mild look-ahead; industry intensity ranks are persistent (BK firm-level intensity AR(1) 0.945 to 0.969, p.524), which limits the damage, but the report should say so.
- **Leg composition.** MSCI end-2019 industry greenness (PST Table 2, p.410) agrees with most of the team's legs: Telecommunication Services +0.84 (Telcm), Pharmaceuticals +0.49 (Drugs), Banks +0.35 (Fin), Utilities -1.90 (Util), Steel -2.96 (Steel), Marine Transport -2.83 (Ships), Construction Materials -2.56 and Building Products -1.62 (BldMt). It disagrees on two: Aerospace and Defense +0.10, on the green side (Aero), and Real Estate Management and Services -1.20 and Real Estate Development -0.55, on the brown side (RlEst). Entertainment-type industries are mixed: Media and Entertainment +0.70, Leisure Products -0.17, Casinos and Gaming -0.54, Hotels and Travel -1.57 (Fun). The mapping from MSCI/GICS industries to FF49 codes is ours, not the paper's. This supports Christhian's per-industry regressions for Fin, Telcm, Drugs, Fun, RlEst.
- **Multiple testing.** The team uses Holm-Bonferroni, which is stricter than EIJP's Benjamini-Hochberg; EIJP's point that BH is invariant to duplicating similar tests (p.11) is a useful argument for reporting BH alongside Holm.

### 11.4 The LMN method applied to industry spreads

What it would look like with the data already in data/raw:

1. **Assets to time (K).** Options: (i) the hedged GB spread plus HML, UMD, RMW, CMA, so the strategy rotates among climate and style exposures; (ii) the 10 leg industries (or all 41 covered FF49 industries) each minus the market; (iii) GB alone. With K = 1 the rotation constraint forces the absolute weight to 1 every month, so timing reduces to sign-flipping; K of at least 2 is needed for the rotation layer to mean anything.
2. **Predictors (J).** Macro, mapped to available FRED series: real short yield (TB3MS minus trailing 12-month CPIAUCSL inflation, since GS1 is not downloaded; DFII10 gives a market real yield from 2003), slope (GS10 minus GS2, or GS10 minus TB3MS), 12-month change in GS2 or TB3MS, 3-month market return (FF3), Baa-Treasury spread (BAA minus GS10). Climate: MCCC AR(1) innovation (PST construction), CPU index change, EMVENRGYENVREG, the team's attention z-score. The raw MCCC file also has topic sub-indices (for example Climate Legislation/Regulations, Carbon Tax, Hurricanes/Floods, Extreme Temperatures) that map onto GP's policy vs physical distinction. Spread-specific "characteristic spreads": B/M spread between green and brown legs (FF49 BE/ME file), size spread (FF49 firm sizes and counts), trailing 3- and 12-month spread return, trailing spread volatility (monthly proxy for LMN's 3-month daily volatility). The emissions-intensity spread is a static snapshot and cannot be a time-series predictor.
3. **Construction.** z-score each predictor on trailing data only; G_t = X_{t-1} F_t for every predictor-asset pair plus the constant; Ledoit-Wolf covariance shrinkage; weights w = (Sigma + (lambda/T) D)^(-1)(mu + (lambda/T) w0) with w0 the static mean-variance weights; convert to implied asset weights and rescale to unit absolute sum.
4. **Tuning and OOS.** LMN need 240 training months plus a validation year. Start dates: team attention 1985 (team writeup p.1), CPU Apr 1987, MCCC Jan 2003 (raw file runs to Jun 2025). With attention the first OOS year is about 2006, with CPU about 2008-2009; with MCCC nothing is left for OOS, so MCCC can only enter with a shorter training window, which LMN's Fig. 2 suggests needs heavier shrinkage. Freeze the predictor list before running, choose lambda only on validation blocks that precede each OOS year, refit annually, and keep the team's Aug 2022 to Jul 2026 holdout untouched until the end.
5. **Benchmarks and costs.** Report the timing portfolio against the static optimal and equal-weight combinations of the same K assets (LMN Table 2 layout). Turnover by LMN Eq. 5, TO = 2 x sum of |h_k,t - h_k,t-1|, charged at 5, 10 and 25 bp per trade (Christhian's test 4; LMN use about 10 bp).
6. **Expectations.** LMN's gain is about 0.30 Sharpe over static with 37 OOS years and many factors; single-predictor timing barely beats equal weight (p.13). With about 20 OOS years and a handful of assets, a 0.30 Sharpe improvement is not detectable at conventional levels (our arithmetic with EIJP's formula: SR 0.3 needs about 43 years for t = 1.96). The honest use in the report is as a disciplined robustness check: if shrinkage sends lambda high and the timing weights collapse to the static portfolio, that is evidence the attention signal adds nothing.
7. **Interpretation link.** If the fitted weights load mainly on rate-change predictors times GB and HML, that reproduces LMN's finding (p.12) and supports the reading that the team's signal is rate and value timing rather than climate timing.

### 11.5 Claim-to-source table for the report

| Claim | Source and page |
|---|---|
| Green has lower expected return in equilibrium (tastes + hedge) | PST 2021 Eq. 9-10 p.554; Eq. 60 p.562 |
| Unexpected concern rises make green outperform | PST 2021 Prop. 6 p.557 |
| Realized GMB 2012-2020 is concern shocks; purged mean about -4 bps/mo | PST 2022 Table 4 p.415 |
| GMB loads HML -0.26 (t -3.36) | PST 2022 Table 3 p.411 |
| Green factor explains about 80% of HML's negative alpha | PST 2022 p.423 |
| Industry-adjusted GMB insignificant (t 0.99) | PST 2022 p.419 |
| Large-cap GMB reacts same month; small caps lag | PST 2022 Table 8 p.421 |
| Policy news matters more than disasters (R^2 0.12-0.15 vs 0.02) | PST 2022 p.417-418 |
| Brown premium in levels and growth, not intensity (2005-2017) | BK 2021 p.519, Table 8 p.532-533 |
| Divestment only in salient industries, on scope 1 intensity | BK 2021 p.539-544 |
| BK result driven by vendor estimates; >70% of figures estimated | ARR 2024 p.77, Table VI p.93 |
| Emissions released with median 10-month lag (US) | Zhang 2025 p.623 |
| US brown underperforms: H-L -0.39%/mo, FF6 alpha -0.40% | Zhang 2025 Table IV p.628 |
| BK premium disappears controlling for same-period sales | Zhang 2025 Tables VIII-IX p.635-637 |
| No GMB alpha survives BH; 167 years needed | EIJP 2026 p.3, p.10-11, p.16 |
| PST's GMB insignificant when extended to 2022; HML -0.39 | EIJP 2026 Table A4 p.29 |
| Climate-risk greenium below 1 pp; sign ambiguous | GP 2026 p.6, Props. 7-8 p.22-23 |
| Concerned investors hedge with brown | GP 2026 Prop. 9 p.25 |
| Clean-minus-brown: COVID +, Ukraine -, oil beta negative | Călin et al. 2026 Table 1 p.6, Table 7 p.11 |
| Shrinkage factor timing adds about 0.30 SR over static | LMN 2024 Table 2 p.21, p.14 |
| Yield changes are the top timing predictors for value | LMN 2024 Fig. 4 p.26, p.12 |

## 12. From general knowledge, not from the folder

These papers are not in the project folder. The citations are ones I am confident in; the descriptions are from memory and contain no numbers. Check the originals before quoting any detail beyond what is written here.

**Industry momentum.**
- Moskowitz, T. J., and M. Grinblatt (1999). Do industries explain momentum? Journal of Finance 54(4), 1249-1290. Industry portfolios sorted on past returns show strong momentum; industry momentum accounts for much of individual-stock momentum, and stock momentum is much weaker once industry momentum is controlled for; unlike individual stocks, industries do not show a one-month reversal, so industry momentum is strongest at short horizons. Relevance: a GB spread built from industries inherits industry momentum, which is another reason to include UMD (or an industry-momentum factor built from the FF49 file) in the hedge.
- Zarattini, C., and G. Antonacci (2024). A century of profitable industry trends. SSRN working paper, abstract 4857230 (as linked in the project brief). A long-only, time-series trend-following rule applied to Fama-French industry portfolios over roughly a century, with channel-breakout entries, trailing stops and volatility-based position sizing, reporting that industry trend following adds value relative to the market. Relevance: a natural benchmark for "is our climate timing just industry trend following?"; the team's Short-Brown entries after attention spikes could coincide with brown industries already in downtrends.

**Timing tests.**
- Treynor, J., and K. Mazuy (1966). Can mutual funds outguess the market? Harvard Business Review 44(4), 131-136. Regression r_p - r_f = a + b(r_m - r_f) + c(r_m - r_f)^2 + e; c > 0 indicates successful timing (convex payoff in the timed return).
- Merton, R. C. (1981). On market timing and investment performance. I. An equilibrium theory of value for market forecasters. Journal of Business 54(3), 363-406. Henriksson, R. D., and R. C. Merton (1981). On market timing and investment performance. II. Statistical procedures for evaluating forecasting skills. Journal of Business 54(4), 513-533. Regression r_p - r_f = a + b(r_m - r_f) + c max(0, r_m - r_f) + e (equivalently up- and down-market betas); c > 0 indicates timing ability, valued as a free put or call.
- Caveat: option-like holdings or dynamic volatility management can produce spurious timing coefficients and offsetting negative intercepts; see Jagannathan, R., and R. A. Korajczyk (1986). Assessing the market timing performance of managed portfolios. Journal of Business 59(2), 217-235.
- Application: replace the market with the timed asset. Regress the Short-Brown strategy on the residual Brown (or GB) return and its square (TM) or its positive part (HM); a positive c with a non-positive a says the rule times the spread rather than earning a constant alpha. Repeat with HML as the "market" to test whether the rule is timing value (Section 11.3).

**Conditional betas.**
- Lewellen, J., and S. Nagel (2006). The conditional CAPM does not explain asset-pricing anomalies. Journal of Financial Economics 82(2), 289-314. If conditional alphas are zero, the unconditional alpha equals (1 - gamma^2/sigma_m^2) cov(beta_t, gamma_t) - (gamma/sigma_m^2) cov(beta_t, sigma_t^2), where gamma_t is the conditional market premium with mean gamma, sigma_t^2 the conditional market variance and sigma_m^2 its unconditional variance; for monthly data the first term is approximately cov(beta_t, gamma_t). They estimate conditional betas directly from short-window regressions (high-frequency returns within each month, quarter or half-year) and find that plausible beta variation is far too small to explain the size, value and momentum alphas. (Verify the exact equation form and numbering against the paper before quoting.)
- Application: the team's residual HML loading (t about -2) is what a lagged 60-month hedge leaves if the true HML beta varies over time. Two checks follow: estimate conditional betas from short windows of daily FF49 and factor returns (the Lewellen-Nagel approach) and test whether conditional alphas remain; and ask whether the strategy's unconditional alpha comes from cov(beta_t on HML, value premium_t), i.e., the rule being short value precisely when value does badly, which is style timing, not climate alpha.

**Data sources and statistical methods cited in the final report** (added 2026-10-02; from general knowledge, not from the folder, under the same caveat as the rest of this section). Each entry gives the citation as printed in the report's bibliography and the report's use of it. The descriptions contain no numbers; check the original before quoting any detail beyond them.

*Data sources.*
- Ardia, D., K. Bluteau, K. Boudt, and K. Inghelbrecht (2023). Climate change concerns and the performance of green vs. brown stocks. Management Science 69(12), 7607-7632. Builds the Media Climate Change Concerns (MCCC) index from US newspaper coverage of climate change, the concern measure PST 2022 use (Section 3). Report use: source of the MCCC series (Table 1, M1, M1b).
- Baker, S. R., N. Bloom, S. J. Davis, and K. J. Kost (2019). Policy news and stock market volatility. NBER Working Paper 25720. Builds a newspaper-based Equity Market Volatility (EMV) tracker scaled to the VIX, with category trackers by the topics the articles mention; FRED publishes them as EMVOVERALLEMV, EMVENRGYENVREG and others. Report use: identifies the team's "attention" series (Section 1.2, M1).
- Gavriilidis, K. (2021). Measuring climate policy uncertainty. SSRN Working Paper 3847388. Builds a newspaper-based US Climate Policy Uncertainty (CPU) index. Report use: source of the CPU series (Table 1, M1, M1b).

*Inference and multiple testing.*
- Newey, W. K., and K. D. West (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica 55(3), 703-708. Heteroskedasticity- and autocorrelation-consistent covariance with Bartlett weights. Report use: every NW(6) t-statistic.
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6(2), 65-70. Step-down Bonferroni procedure that controls the family-wise error rate. Report use: Holm corrections within families.
- Benjamini, Y., and Y. Hochberg (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. Journal of the Royal Statistical Society, Series B 57(1), 289-300. Step-up procedure that controls the false discovery rate for independent tests. Report use: BH corrections.
- Benjamini, Y., and D. Yekutieli (2001). The control of the false discovery rate in multiple testing under dependency. Annals of Statistics 29(4), 1165-1188. Shows that BH also controls the false discovery rate under positive dependence and gives a version valid under any dependence (BH run at q divided by the harmonic sum of the number of tests). Report use: BY on the robustness grids (M7).
- Romano, J. P., and M. Wolf (2005). Stepwise multiple testing as formalized data snooping. Econometrica 73(4), 1237-1282. Bootstrap step-down max-t procedure that controls the family-wise error rate when many strategies are compared with a benchmark. Report use: search-adjusted tests (M7).
- Hansen, P. R. (2005). A test for superior predictive ability. Journal of Business and Economic Statistics 23(4), 365-380. Tests whether the best of many models beats a benchmark, with a studentized statistic that is less sensitive to poor alternatives than White's reality check. Report use: SPA test (M7).
- Bailey, D. H., and M. López de Prado (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. Journal of Portfolio Management 40(5), 94-107. The probability that a Sharpe ratio exceeds the expected maximum of N independent trials, adjusted for skewness, kurtosis and sample length. Report use: the deflated appraisal ratio (M7).
- Nyholt, D. R. (2004). A simple correction for multiple testing for single-nucleotide polymorphisms in linkage disequilibrium with each other. American Journal of Human Genetics 74(4), 765-769. Effective number of independent tests from the variance of the eigenvalues of the tests' correlation matrix. Report use: the effective number of trials (M7, Appendix E).
- Li, J., and L. Ji (2005). Adjusting multiple testing in multilocus analyses using the eigenvalues of a correlation matrix. Heredity 95(3), 221-227. An alternative eigenvalue-based effective number of tests. Report use: sensitivity count for the deflated appraisal ratio (M7, Appendix E).

*Forecasting and performance evaluation.*
- Campbell, J. Y., and S. B. Thompson (2008). Predicting excess stock returns out of sample: Can anything beat the historical average? Review of Financial Studies 21(4), 1509-1531. Out-of-sample R-squared of return forecasts against the historical mean. Report use: M6.
- Clark, T. E., and K. D. West (2007). Approximately normal tests for equal predictive accuracy in nested models. Journal of Econometrics 138(1), 291-311. Adjusted mean-squared-prediction-error test for nested forecasting models. Report use: M6's Clark-West tests.
- Ferson, W. E., and R. W. Schadt (1996). Measuring fund strategy and performance in changing economic conditions. Journal of Finance 51(2), 425-461. Conditional performance evaluation with betas linear in lagged public information variables. Report use: M3's conditional alphas.
- Grinold, R. C., and R. N. Kahn (2000). Active Portfolio Management, 2nd ed. McGraw-Hill. Alpha-driven portfolio construction under a tracking-error budget, and the information ratio. Report use: the M5 optimizer book (Sections 1.4 and 2.6).

*Bibliography check, 2026-10-02.* All 27 entries in the report's bibliography were checked against Crossref, publisher, SSRN or NBER records. Lehnherr, Mehta and Nagel was published as "Optimal factor timing in a high-dimensional setting", Financial Analysts Journal 81(2), 51-66 (2025; SSRN 4938729 is the 2024 working paper). Baker, Bloom, Davis and Kost's NBER Working Paper 25720 was published in the Journal of Financial Economics 175, 104187 (2026). Eskildsen, Ibert, Jensen and Pedersen (2026) is SSRN 6527562. Treynor and Mazuy's initials are J. L. and K. K.
