"""M4_emissions: is the team's industry emissions ranking sound, and does a complete supply-chain measure change who is
Green and Brown and what the Green-minus-Brown spread does?

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M4_emissions/run.py

Steps
 1. Provenance of the team's emissions_ff_industry.csv (text search of the PS1/HW1 sources, structural fingerprints).
 2. EPA Supply Chain GHG Emission Factors v1.3 (kg CO2e per 2022 USD) mapped NAICS 2017 -> SIC 1987 -> FF49 through
    Census concordances; unweighted mean/median by FF49 (no output weights). Electricity (EPA-excluded) patched from
    USEEIO v2.0.1. Writes data/derived/ff49_emissions_epa.csv and the mapping files.
 3. Ranking comparison (Spearman, top/bottom 5 and 8), Aero/Ships forensic.
 4. Green-minus-Brown under both rankings; PRIMARY test = FF5+UMD alpha of EPA 5v5 GB post-2010 (NW 6 lags).
    Energy variants (Oil and Coal in Brown). Exploratory re-run of the team's Short-Brown timing rule on the EPA Brown leg.
 4b. Added after independent verification: leg-membership sensitivity of the primary test (Chips for Smoke, drop-one),
    CAPM beta decomposition of recent windows, Holm over the 12 Aero/Ships calibration tests, Kendall and calendar-year
    mean tests added to the ledger. Turnover is two-way traded notional (buys plus sells).
"""
from __future__ import annotations
import json, pathlib, re, sys
import numpy as np
import pandas as pd
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lib")); sys.path.insert(0, str(HERE))
from common import (PERIODS, TABLES, DERIVED, RAW, TEAM, load_team, leg_returns, load_ff5_mom, load_kf_ff3,
                    load_kf_industries, nw_ols, perf, holm, bh)
from plotstyle import *  # noqa: F401,F403
import matplotlib.pyplot as plt
import mapping as mp
import team_strategy as ts

MOD = "M4_emissions"
GA = ROOT.parents[1]                       # /home/hashim/projects/GA
LEDGER: list[dict] = []
KEY: list[dict] = []
pd.set_option("display.width", 200)


def ledger(test_id, question, statistic_name, statistic, p, n, kind, note=""):
    LEDGER.append({"test_id": test_id, "module": MOD, "question": question, "statistic_name": statistic_name,
                   "statistic": float(statistic) if statistic is not None and np.isfinite(statistic) else np.nan,
                   "p_value_two_sided": float(p) if p is not None and np.isfinite(p) else np.nan,
                   "n_obs": int(n), "primary_or_exploratory": kind, "note": note})


def key(name, value, source, note=""):
    KEY.append({"name": name, "value": value, "source_table": source, "note": note})


def save(df: pd.DataFrame, name: str, tex: dict | None = None, index=False):
    df.to_csv(TABLES / f"{MOD}_{name}.csv", index=index)
    if tex is not None:
        t = tex.get("df", df)
        s = t.to_latex(index=tex.get("index", False), escape=True, float_format=tex.get("fmt", "%.2f"),
                       caption=tex.get("caption"), label=tex.get("label"), na_rep="--")
        (TABLES / f"{MOD}_{name}.tex").write_text(s)


# =============================================================================== 1. provenance
def provenance():
    team_path = TEAM / "data" / "emissions_ff_industry.csv"
    ps1_path = GA / "Emissions_FF_Industry.csv"
    a = pd.read_csv(team_path); b = pd.read_csv(ps1_path)
    identical = a.equals(b) or (a.values.tolist() == b.values.tolist())
    pat = re.compile(r"(?i)(scope|tco2|kg\s*co2|tonne|metric ton|units?\b|source|vintage|epa\b|bea\b|trucost|msci|eora|exiobase|oecd|input-output|per unit of output|emissions per|emissions/output|snapshot)")
    rows = [{"source": str(ps1_path), "what_it_says": "PS1 course file; identical to the team file" if identical else "differs from team file",
             "construction_documented": "no", "units_documented": "no", "vintage_documented": "no"}]
    for f in ["230GA__PS1.ipynb", "HW1_merged.tex", "Q5_answer.md", "Q4_corrections.md"]:
        p = GA / f
        txt = p.read_text(errors="ignore")
        if f.endswith(".ipynb"):
            nb = json.loads(txt); txt = "\n".join("".join(c["source"]) for c in nb["cells"])
        hits = sorted(set(m.group(0).lower() for m in pat.finditer(txt)))
        n_emis = len(re.findall(r"(?i)emission", txt))
        if f == "230GA__PS1.ipynb":
            say = "reads EM_PATH='Emissions_FF_Industry.csv' and sorts on emissions_intensity; no text on construction, units, scope or year"
        elif f == "Q4_corrections.md":
            say = "no mention of the emissions file"
        else:
            say = "describes it only as emissions per unit of output, a single snapshot covering 41 of 49 industries; no source, units, scope or year"
        rows.append({"source": str(p), "what_it_says": say, "n_mentions_emission": n_emis, "keyword_hits": "; ".join(hits),
                     "construction_documented": "no", "units_documented": "no", "vintage_documented": "no"})
    rows.append({"source": str(TEAM / "writeup.pdf"), "what_it_says": "'a single snapshot of emissions intensity by industry... 41 of the 49'; no source or units",
                 "construction_documented": "no", "units_documented": "no", "vintage_documented": "no"})
    rows.append({"source": str(TEAM / "notebooks" / "climate_alpha_analysis.py"), "what_it_says": "loads the CSV and ranks it; attributes the 8 gaps to the underlying data",
                 "construction_documented": "no", "units_documented": "no", "vintage_documented": "no"})
    prov = pd.DataFrame(rows)
    save(prov, "provenance")

    # structural fingerprints of the team file
    e = load_team()["emissions"]
    ties = e.groupby(e.round(10)).apply(lambda s: ", ".join(sorted(s.index)) if len(s) > 1 else None).dropna()
    fp = pd.DataFrame({"tie_group_value": ties.index, "industries_sharing_value": ties.values})
    save(fp, "team_file_ties")
    key("team_max_over_min", e.max() / e.min(), f"{MOD}_ff49_intensity.csv", "Util / Fun in the team file")
    key("team_n_industries", len(e), f"{MOD}_ff49_intensity.csv")
    key("team_n_tie_groups", len(fp), f"{MOD}_team_file_ties.csv")
    return prov, identical


# =============================================================================== 2. EPA intensity by FF49
def build_intensity():
    fac, info = mp.naics_factors()
    links, nmap = mp.build_mapping()
    team = load_team()["emissions"]
    ff49 = list(load_team()["industries"].columns)
    prim = mp.aggregate_ff49(fac, nmap, "primary").reindex(ff49)
    anyl = mp.aggregate_ff49(fac, nmap, "any_link").reindex(ff49)
    out = pd.DataFrame(index=pd.Index(ff49, name="ff49"))
    out["epa_sc_mean"] = prim["epa_sc_mean"]; out["epa_sc_median"] = prim["epa_sc_median"]
    out["epa_sc_nomargin_mean"] = prim["epa_sc_nomargin_mean"]; out["n_naics"] = prim["n_naics"].astype(int)
    out["team_intensity"] = team.reindex(ff49)
    out["rank_epa"] = out["epa_sc_mean"].rank(method="first").astype(int)          # 1 = lowest intensity (cleanest)
    out["rank_team"] = out["team_intensity"].rank(method="first")                   # 1..41, NaN for the 8 missing
    out["epa_sc_nomargin_median"] = prim["epa_sc_nomargin_median"]
    out["epa_sc_mean_anylink"] = anyl["epa_sc_mean"]; out["n_naics_anylink"] = anyl["n_naics"].astype(int)
    out["useeio_direct_mean"] = prim["useeio_direct_mean"]; out["useeio_direct_median"] = prim["useeio_direct_median"]
    out["useeio_direct_co2_mean"] = prim["useeio_direct_co2_mean"]; out["useeio_total_mean"] = prim["useeio_total_mean"]
    in41 = out["team_intensity"].notna()
    out["rank_epa_median"] = out["epa_sc_median"].rank(method="first").astype(int)
    out["rank_epa_nomargin"] = out["epa_sc_nomargin_mean"].rank(method="first").astype(int)
    out["rank_epa_anylink"] = out["epa_sc_mean_anylink"].rank(method="first").astype(int)
    out["rank_epa_within41"] = out.loc[in41, "epa_sc_mean"].rank(method="first")
    out["rank_direct_ghg"] = out["useeio_direct_mean"].rank(method="first").astype(int)
    out["in_team_file"] = in41
    out = out.sort_values("epa_sc_mean")
    out.reset_index().to_csv(DERIVED / "ff49_emissions_epa.csv", index=False)

    # mapping files
    siclist = (links.drop_duplicates(["naics17", "sic"]).groupby(["naics17", "ff49"])["sic"]
               .apply(lambda s: " ".join(f"{int(x):04d}" for x in sorted(s))).rename("sic_codes").reset_index())
    mfile = nmap.merge(siclist, on=["naics17", "ff49"], how="left").merge(
        fac.rename(columns={"naics": "naics17", "sef": "epa_sc", "sef_nomargin": "epa_sc_nomargin", "useeio": "useeio_code"})
           [["naics17", "epa_sc", "epa_sc_nomargin", "margin", "useeio_code", "useeio_match", "useeio_direct", "useeio_direct_co2", "useeio_total", "source"]],
        on="naics17", how="left")
    mfile["has_epa_factor"] = mfile["epa_sc"].notna()
    mfile = mfile[["naics17", "naics17_title", "ff49", "primary", "any_link", "n_sic", "n_sic_total", "share", "sic_codes",
                   "override_note", "has_epa_factor", "epa_sc", "epa_sc_nomargin", "margin", "useeio_code", "useeio_match",
                   "useeio_direct", "useeio_direct_co2", "useeio_total", "source"]]
    mfile.to_csv(DERIVED / "ff49_naics_mapping_epa.csv", index=False)
    links.to_csv(DERIVED / "naics17_sic87_ff49_links.csv", index=False)

    epa_codes = set(fac.loc[fac["source"] == "EPA v1.3", "naics"])
    mapped_prim = set(nmap.loc[nmap["primary"], "naics17"])
    ties = nmap[nmap["primary"]].groupby("naics17").size()
    summ = pd.DataFrame([
        ("epa_naics_codes", len(epa_codes), "6-digit 2017 NAICS codes in EPA v1.3 (electricity 2211xx excluded by EPA)"),
        ("epa_codes_mapped_primary", len(epa_codes & mapped_prim), "EPA codes assigned to at least one FF49 industry"),
        ("epa_codes_unmapped", len(epa_codes - mapped_prim), "codes with no SIC predecessor: " + ", ".join(str(c) for c in sorted(epa_codes - mapped_prim))),
        ("electricity_codes_patched", len(mp.ELEC_NAICS17), "221111-221122 added with the patched factor"),
        ("primary_ties", int((ties > 1).sum()), "NAICS codes whose SIC links tie between FF49 industries (included in each tied industry)"),
        ("manual_links", len(mp.MANUAL_LINKS), "; ".join(f"{k}: {v[1]}" for k, v in mp.MANUAL_LINKS.items())),
        ("overrides", len(mp.OVERRIDES), "; ".join(f"{k}->{v[0]}" for k, v in mp.OVERRIDES.items())),
        ("elec_patch_kg_per_2022usd", info["elec_patch_kg_per_2022usd"], "USEEIO v2.0.1 N(221100) x median ratio"),
        ("elec_useeio_total_2012usd", info["elec_useeio_total_2012usd"], "USEEIO v2.0.1 total GHG per 2012 USD, electricity"),
        ("scale_median_epa13_over_useeio", info["scale_median"], f"median over {info['n_ratio']} EPA codes; IQR {info['scale_iqr_lo']:.3f}-{info['scale_iqr_hi']:.3f}"),
        ("epa_naics_min", fac.loc[fac["source"] == "EPA v1.3", "sef"].min(), "lowest with-margins factor, kg CO2e/2022 USD"),
        ("epa_naics_max", fac.loc[fac["source"] == "EPA v1.3", "sef"].max(), "highest with-margins factor (327310 cement)"),
    ], columns=["item", "value", "note"])
    save(summ, "mapping_summary")
    for _, r in summ.iterrows():
        key(r["item"], r["value"], f"{MOD}_mapping_summary.csv", r["note"])

    tab = out.reset_index()[["ff49", "epa_sc_mean", "epa_sc_median", "epa_sc_nomargin_mean", "n_naics", "team_intensity",
                             "rank_epa", "rank_team", "useeio_direct_mean", "useeio_direct_co2_mean"]]
    save(tab, "ff49_intensity", tex={"caption": "FF49 supply-chain GHG intensity (EPA v1.3, kg CO2e per 2022 USD, unweighted mean and median of mapped 2017 NAICS factors) versus the team file (units undocumented). Rank 1 = lowest intensity. Direct columns: USEEIO v2.0.1 own-industry GHG and CO2 per 2012 USD of output.",
                                     "label": "tab:m4_intensity", "fmt": "%.3f"})
    key("epa_ff49_max_over_min", out["epa_sc_mean"].max() / out["epa_sc_mean"].min(), f"{MOD}_ff49_intensity.csv", "Util / Banks")
    epa_only = fac[fac["source"] == "EPA v1.3"]["sef"]
    key("epa_naics_max_over_min", epa_only.max() / epa_only.min(), f"{MOD}_mapping_summary.csv", "cement / lowest NAICS, EPA v1.3 with margins")
    key("team_min_over_util", out["team_intensity"].min() / out.at["Util", "team_intensity"], f"{MOD}_ff49_intensity.csv", "Fun / Util in the team file")
    key("epa_naics_min_over_elec", epa_only.min() / info["elec_patch_kg_per_2022usd"], f"{MOD}_mapping_summary.csv", "lowest EPA NAICS factor / electricity factor")
    um = nmap[nmap["primary"] & (nmap["ff49"] == "Util")].merge(fac, left_on="naics17", right_on="naics")
    key("util_mean_without_electricity_patch", um.loc[um["source"] == "EPA v1.3", "sef"].mean(), "ff49_naics_mapping_epa.csv (data/derived)",
        "Util mean over its non-electricity NAICS only (gas distribution, water, gas pipelines); compare Chems " + f"{out.at['Chems', 'epa_sc_mean']:.3f}")
    key("direct_ff49_max_over_min", out["useeio_direct_mean"].max() / out["useeio_direct_mean"].min(), f"{MOD}_ff49_intensity.csv")
    key("useeio_total_ff49_max_over_min", out["useeio_total_mean"].max() / out["useeio_total_mean"].min(), "data/derived/ff49_emissions_epa.csv",
        "USEEIO v2.0.1 total (supply-chain) GHG per 2012 USD, FF49 means; a second supply-chain dataset from the same EPA model family")
    srt = out["epa_sc_mean"].sort_values()
    key("epa_green5_margin_5th_vs_6th", srt.iloc[5] - srt.iloc[4], f"{MOD}_ff49_intensity.csv",
        f"EPA mean of the 6th-lowest ({srt.index[5]} {srt.iloc[5]:.4f}) minus the 5th-lowest ({srt.index[4]} {srt.iloc[4]:.4f}), kg CO2e per 2022 USD")
    key("epa_brown5_margin_5th_vs_6th", srt.iloc[-5] - srt.iloc[-6], f"{MOD}_ff49_intensity.csv",
        f"EPA mean of the 5th-highest ({srt.index[-5]} {srt.iloc[-5]:.4f}) minus the 6th-highest ({srt.index[-6]} {srt.iloc[-6]:.4f})")
    return out, fac, nmap, info


# =============================================================================== 3. ranking comparison
MEASURES = {"epa_sc_mean": "EPA v1.3 with margins, mean (primary)", "epa_sc_median": "EPA with margins, median",
            "epa_sc_nomargin_mean": "EPA without margins, mean", "epa_sc_mean_anylink": "EPA with margins, any-link mapping",
            "useeio_total_mean": "USEEIO v2.0.1 total (2012 USD)", "useeio_direct_mean": "USEEIO v2.0.1 direct GHG",
            "useeio_direct_co2_mean": "USEEIO v2.0.1 direct CO2 only"}


def members(s: pd.Series, n: int, side: str):
    s = s.dropna().sort_values()
    return list(s.index[:n]) if side == "green" else list(s.index[::-1][:n])


def compare_rankings(out: pd.DataFrame, fac: pd.DataFrame):
    d = out[out["in_team_file"]]
    rows = []
    for c, lab in MEASURES.items():
        rho, p = stats.spearmanr(d[c], d["team_intensity"])
        tau, pt = stats.kendalltau(d[c], d["team_intensity"])
        rows.append({"measure": c, "label": lab, "n": len(d), "spearman_rho": rho, "spearman_p": p, "kendall_tau": tau, "kendall_p": pt})
        ledger(f"rank_spearman_team_vs_{c}", "Q3 ranking agreement: team file vs measure (41 common industries)", "Spearman rho",
               rho, p, len(d), "exploratory", lab)
        ledger(f"rank_kendall_team_vs_{c}", "Q3 ranking agreement: team file vs measure (41 common industries)", "Kendall tau",
               tau, pt, len(d), "exploratory", lab + "; same hypothesis as the Spearman row, different statistic")
    for c in ["epa_sc_median", "epa_sc_nomargin_mean", "epa_sc_mean_anylink"]:
        rho, p = stats.spearmanr(out[c], out["epa_sc_mean"])
        rows.append({"measure": c + "_vs_epa_sc_mean", "label": "EPA variant vs EPA primary (49 industries)", "n": len(out),
                     "spearman_rho": rho, "spearman_p": p, "kendall_tau": np.nan, "kendall_p": np.nan})
        ledger(f"rank_spearman_epa_primary_vs_{c}", "Q3 stability of the EPA ranking to aggregation/mapping choices", "Spearman rho",
               rho, p, len(out), "robustness")
    sp = pd.DataFrame(rows)
    save(sp, "spearman", tex={"df": sp[["label", "n", "spearman_rho", "spearman_p", "kendall_tau"]],
                              "caption": "Rank agreement between the team emissions file and alternative intensity measures (41 common FF49 industries), and stability of the EPA ranking (49 industries).",
                              "label": "tab:m4_spearman", "fmt": "%.3f"})

    # membership
    team = out["team_intensity"]
    mem = []
    rankings = {"team": team, "epa": out["epa_sc_mean"], "epa_within41": out["epa_sc_mean"].where(out["in_team_file"]),
                "epa_median": out["epa_sc_median"], "epa_nomargin": out["epa_sc_nomargin_mean"], "epa_anylink": out["epa_sc_mean_anylink"],
                "direct_ghg": out["useeio_direct_mean"], "direct_co2": out["useeio_direct_co2_mean"]}
    for n in (5, 8):
        for side in ("green", "brown"):
            tm = members(team, n, side)
            for rk, s in rankings.items():
                m = members(s, n, side)
                mem.append({"n": n, "side": side, "ranking": rk, "members": ", ".join(m), "overlap_with_team": len(set(m) & set(tm)),
                            "in_team_only": ", ".join(sorted(set(tm) - set(m))), "new_vs_team": ", ".join(sorted(set(m) - set(tm)))})
    mem = pd.DataFrame(mem)
    save(mem, "membership", tex={"df": mem[mem["ranking"].isin(["team", "epa", "epa_within41", "epa_median", "direct_ghg"])][["n", "side", "ranking", "members", "overlap_with_team"]],
                                 "caption": "Green (lowest) and Brown (highest) industries under each ranking. epa\\_within41 restricts the EPA ranking to the 41 industries in the team file.",
                                 "label": "tab:m4_membership", "fmt": "%.0f"})

    # key industries
    kl = ["Util", "Ships", "Aero", "Steel", "BldMt", "Chems", "Trans", "Mines", "Coal", "Oil", "Agric", "Other", "Gold", "Food",
          "Fun", "RlEst", "Drugs", "Telcm", "Fin", "Banks", "Insur", "Softw", "Hardw", "Smoke"]
    k = out.loc[kl].copy()
    k["team_rank_from_top_of41"] = 42 - k["rank_team"]
    k["epa_rank_from_top_of49"] = 50 - k["rank_epa"]
    k["epa_median_rank_from_top_of49"] = 50 - k["rank_epa_median"]
    k["direct_ghg_rank_from_top_of49"] = 50 - k["rank_direct_ghg"]
    kk = k.reset_index()[["ff49", "team_intensity", "team_rank_from_top_of41", "epa_sc_mean", "epa_rank_from_top_of49",
                          "epa_median_rank_from_top_of49", "useeio_direct_mean", "direct_ghg_rank_from_top_of49", "n_naics"]]
    save(kk, "key_industries", tex={"caption": "Where the contested industries land. Rank 1 = most intensive. Team ranks are out of 41, EPA and direct ranks out of 49.",
                                    "label": "tab:m4_key_industries", "fmt": "%.3f"})

    # Aero / Ships NAICS forensic
    codes = {336411: "Aero (mfg)", 336412: "Aero (mfg)", 336413: "Aero (mfg)", 336611: "Ships (mfg)", 336510: "Ships (mfg)",
             336612: "boat building (Rubbr/Toys tie)", 481111: "air transportation (FF49 Trans)", 481112: "air transportation (FF49 Trans)",
             483111: "water transportation (FF49 Trans)", 483211: "water transportation (FF49 Trans)", 482111: "rail transportation (FF49 Trans)",
             484121: "truck transportation (FF49 Trans)", 486110: "pipeline transportation (FF49 Trans)", 331110: "iron and steel mills (Steel)",
             327310: "cement (BldMt)", 221112: "fossil electric power (Util, patched)"}
    a = fac.set_index("naics").loc[list(codes)][["title", "sef", "sef_nomargin", "useeio_direct", "useeio_direct_co2"]].reset_index()
    a.insert(2, "role", a["naics"].map(codes))
    save(a, "aero_ships_naics", tex={"df": a.drop(columns=["sef_nomargin"]), "caption": "NAICS-level intensities behind the Aero and Ships question. sef: EPA v1.3 with margins, kg CO2e per 2022 USD; direct: USEEIO v2.0.1 own emissions per 2012 USD of output.",
                                    "label": "tab:m4_aero_ships", "fmt": "%.3f"})

    # calibration: which mapping of Aero/Ships fits the team's numbers?
    alt = {"Aero": {"mfg": [336411, 336412, 336413], "transport": [481111, 481112, 481211, 481212, 481219]},
           "Ships": {"mfg": [336611, 336510], "transport": [483111, 483112, 483113, 483114, 483211, 483212]}}
    col_naics = {"epa_sc_mean": "sef", "useeio_direct_mean": "useeio_direct", "useeio_direct_co2_mean": "useeio_direct_co2"}
    cal = []
    base = out[out["in_team_file"]].drop(index=["Aero", "Ships"])
    for c, nc in col_naics.items():
        x = np.log(base[c]); y = np.log(base["team_intensity"])
        X = np.column_stack([np.ones(len(x)), x]); beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta; dfree = len(y) - 2; s2 = (resid ** 2).sum() / dfree; XtXi = np.linalg.inv(X.T @ X)
        for ind, alts in alt.items():
            act = np.log(out.at[ind, "team_intensity"])
            for which, cl in alts.items():
                v = fac.set_index("naics").loc[cl, nc].mean()
                x0 = np.array([1.0, np.log(v)]); pred = x0 @ beta; se = np.sqrt(s2 * (1 + x0 @ XtXi @ x0))
                tstat = (act - pred) / se; p = 2 * stats.t.sf(abs(tstat), dfree)
                cal.append({"measure": c, "industry": ind, "mapping": which, "measure_value": v, "team_value": np.exp(act),
                            "predicted_team_value": np.exp(pred), "log_residual": act - pred, "t_prediction": tstat, "p_two_sided": p,
                            "slope": beta[1], "r2_fit": 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum(), "n_fit": len(y)})
                ledger(f"aero_ships_calib_{c}_{ind}_{which}", "Q3 forensic: is the team's value consistent with this mapping?",
                       "prediction t (log team on log measure, 39 industries)", tstat, p, len(y), "exploratory",
                       f"{ind} mapped to {which}; large |t| = team value inconsistent with that mapping")
    cal = pd.DataFrame(cal)
    cal["team_over_predicted"] = cal["team_value"] / cal["predicted_team_value"]      # >1: team value above the fit
    cal["holm_p_12"] = holm(cal["p_two_sided"]).values                                  # family = the 12 calibration tests
    cal["bh_p_12"] = bh(cal["p_two_sided"]).values
    save(cal, "aero_ships_calibration", tex={"df": cal[["measure", "industry", "mapping", "measure_value", "team_value", "predicted_team_value", "team_over_predicted", "t_prediction", "p_two_sided", "holm_p_12"]],
                                             "caption": "Leave-two-out calibration: regress log team intensity on log measure over the other 39 industries, then predict Aero and Ships using their own manufacturing NAICS or the air/water transportation NAICS. team\\_over\\_predicted = team value / predicted value. holm\\_p\\_12: Holm-adjusted over these 12 tests.",
                                             "label": "tab:m4_calibration", "fmt": "%.3f"})
    return sp, mem, kk, cal


def fig_scatter(out: pd.DataFrame):
    d = out[out["in_team_file"]].copy()
    tg, tb = members(d["team_intensity"], 5, "green"), members(d["team_intensity"], 5, "brown")
    eg, eb = members(out["epa_sc_mean"], 5, "green"), members(out["epa_sc_mean"], 5, "brown")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
    ax = axes[0]
    col = np.where(d.index.isin(tg), GREEN, np.where(d.index.isin(tb), ORANGE, MUTED))
    ax.scatter(d["team_intensity"], d["epa_sc_mean"], c=col, s=26, zorder=3)
    ax.set_xscale("log"); ax.set_yscale("log")
    x, y = np.log(d["team_intensity"]), np.log(d["epa_sc_mean"])
    b1, b0 = np.polyfit(x, y, 1); res = y - (b0 + b1 * x)
    lab = set(tg) | set(tb) | set(res.abs().sort_values().index[-6:]) | {"Coal", "Chems", "Agric", "Trans", "Mines"}
    for i in lab:
        ax.annotate(i, (d.at[i, "team_intensity"], d.at[i, "epa_sc_mean"]), xytext=(4, 3), textcoords="offset points", fontsize=7, color=INK2)
    ax.set_xlabel("Team file intensity (units undocumented, log scale)")
    ax.set_ylabel("EPA supply-chain intensity, kg CO2e per 2022 USD (log)")
    ax.set_title("(a) Levels: team file vs EPA v1.3 (41 industries)")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=GREEN, label="Team Green"), Line2D([], [], marker="o", ls="", color=ORANGE, label="Team Brown"),
         Line2D([], [], marker="o", ls="", color=MUTED, label="Other industries")]
    ax.legend(handles=h, loc="upper left")
    ax = axes[1]
    r = out.copy(); r["team_top"] = 42 - r["rank_team"]; r["epa_top"] = 50 - r["rank_epa"]
    rr = r[r["in_team_file"]]
    col2 = np.where(rr.index.isin(eb), ORANGE, np.where(rr.index.isin(eg), GREEN, MUTED))
    ax.scatter(rr["team_top"], rr["epa_top"], c=col2, s=26, zorder=3)
    for i in set(tb) | set(eb) | set(tg) | set(eg):
        if i in rr.index:
            ax.annotate(i, (rr.at[i, "team_top"], rr.at[i, "epa_top"]), xytext=(4, 3), textcoords="offset points", fontsize=7, color=INK2)
    ax.axhspan(0.5, 5.5, color=ORANGE, alpha=0.06, lw=0); ax.axvspan(0.5, 5.5, color=ORANGE, alpha=0.06, lw=0)
    ax.set_xlabel("Team rank (1 = most intensive, of 41)"); ax.set_ylabel("EPA rank (1 = most intensive, of 49)")
    ax.invert_xaxis(); ax.invert_yaxis()
    h2 = [Line2D([], [], marker="o", ls="", color=GREEN, label="EPA Green"), Line2D([], [], marker="o", ls="", color=ORANGE, label="EPA Brown"),
          Line2D([], [], marker="o", ls="", color=MUTED, label="Other industries")]
    ax.legend(handles=h2, loc="upper left")
    ax.set_title("(b) Ranks, 41 common industries (shaded: top 5 of each)")
    savefig(fig, f"{MOD}_intensity_scatter")


# =============================================================================== 4. returns
RPERIODS = ["full_1970", "post2010", "validation", "holdout", "covid", "inflation_rates", "last18", "last12"]
PER = {p: PERIODS[p] for p in RPERIODS}
PER["pre2010"] = ("1970-01-31", "2009-12-31")           # exploratory split of the full sample (complement of post2010)
PER["energy_rally"] = ("2021-01-31", "2022-12-31")      # exploratory custom window (WTI and energy equities rally)
PER["cal2021"] = ("2021-01-31", "2021-12-31")
PER["cal2022"] = ("2022-01-31", "2022-12-31")
MODELS = {"CAPM": ["Mkt-RF"], "FF3": ["Mkt-RF", "SMB", "HML"], "FF5UMD": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]}


def psub(s, p):
    a, b = PER[p]
    return s.loc[a:b]


def leg_turnover(ind: pd.DataFrame, names: list) -> pd.Series:
    """Two-way traded notional (buys plus sells) per unit of leg notional needed at month-end to restore equal
    weights after drift: sum_i |w_drift_i - 1/n|. Buys and sells each equal half of this, so a cost of c per unit
    traded is charged on the full amount. Excludes the initial build of the legs and the rebalancing inside the
    value-weighted industry portfolios themselves (not observable from industry returns)."""
    R = ind[names]
    grow = 1 + R
    w = grow.div(grow.sum(axis=1), axis=0)
    return (w - 1 / len(names)).abs().sum(axis=1)


def build_specs(out: pd.DataFrame):
    team = out["team_intensity"]
    epa = out["epa_sc_mean"]
    epa41 = epa.where(out["in_team_file"])
    S = {}
    def add(name, g, b, role, desc):
        S[name] = {"green": g, "brown": b, "role": role, "desc": desc}
    add("team5", members(team, 5, "green"), members(team, 5, "brown"), "comparison", "team file ranking, 5 vs 5 (team baseline)")
    add("epa5", members(epa, 5, "green"), members(epa, 5, "brown"), "primary", "EPA v1.3 with margins, mean, 49 industries, 5 vs 5")
    add("team8", members(team, 8, "green"), members(team, 8, "brown"), "comparison", "team file ranking, 8 vs 8")
    add("epa8", members(epa, 8, "green"), members(epa, 8, "brown"), "robustness", "EPA mean, 8 vs 8")
    add("epa_median5", members(out["epa_sc_median"], 5, "green"), members(out["epa_sc_median"], 5, "brown"), "robustness", "EPA median aggregation, 5 vs 5")
    add("epa_nomargin5", members(out["epa_sc_nomargin_mean"], 5, "green"), members(out["epa_sc_nomargin_mean"], 5, "brown"), "robustness", "EPA without margins, 5 vs 5")
    add("epa_anylink5", members(out["epa_sc_mean_anylink"], 5, "green"), members(out["epa_sc_mean_anylink"], 5, "brown"), "robustness", "EPA, any-link mapping, 5 vs 5")
    add("epa41_5", members(epa41, 5, "green"), members(epa41, 5, "brown"), "robustness", "EPA ranking restricted to the team's 41 industries, 5 vs 5")
    add("epa41_8", members(epa41, 8, "green"), members(epa41, 8, "brown"), "robustness", "EPA ranking restricted to the team's 41 industries, 8 vs 8")
    exo = epa.drop(index="Other")
    add("epa5_exOther", members(exo, 5, "green"), members(exo, 5, "brown"), "robustness", "EPA mean excluding FF49 Other (thin residual portfolio), 5 vs 5")
    add("epa_median8", members(out["epa_sc_median"], 8, "green"), members(out["epa_sc_median"], 8, "brown"), "robustness", "EPA median aggregation, 8 vs 8")
    exas = team.drop(index=["Aero", "Ships"])
    add("team5_ex_aero_ships", S["team5"]["green"], members(exas, 5, "brown"), "exploratory", "team Green; team Brown with Aero and Ships removed from the ranking (next in line: Chems, Trans)")
    # energy variants (exploratory)
    add("team5_brown_plus_oil_coal", S["team5"]["green"], S["team5"]["brown"] + ["Oil", "Coal"], "exploratory", "team Green; team Brown plus Oil and Coal (7 industries)")
    add("epa5_brown_plus_oil", S["epa5"]["green"], S["epa5"]["brown"] + ["Oil"], "exploratory", "EPA Green; EPA Brown plus Oil (6 industries)")
    exoc = epa.drop(index=["Oil", "Coal"])
    add("epa5_brown_ex_oil_coal", S["epa5"]["green"], members(exoc, 5, "brown"), "exploratory", "EPA Green; EPA Brown with Oil and Coal excluded from the ranking")
    return S


def returns_analysis(out: pd.DataFrame):
    ind = load_team()["industries"]
    ff3 = load_kf_ff3(); ff5 = load_ff5_mom()
    S = build_specs(out)
    legs = pd.DataFrame([{"spec": k, "role": v["role"], "desc": v["desc"], "green": ", ".join(v["green"]), "brown": ", ".join(v["brown"])} for k, v in S.items()])
    save(legs, "legs", tex={"df": legs[legs["spec"].isin(["team5", "epa5", "team8", "epa8", "epa41_5", "epa_median5", "team5_brown_plus_oil_coal"])][["spec", "green", "brown"]],
                            "caption": "Leg membership of the Green-minus-Brown specifications (equal-weighted legs of value-weighted FF49 industry returns).",
                            "label": "tab:m4_legs"})
    series, gleg, bleg, costs = {}, {}, {}, {}
    for k, v in S.items():
        g, b, gb = leg_returns(ind, v["green"], v["brown"])
        series[k] = gb.loc["1970-01-31":"2026-07-31"]; gleg[k] = g.loc["1970-01-31":"2026-07-31"]; bleg[k] = b.loc["1970-01-31":"2026-07-31"]
        costs[k] = (leg_turnover(ind, v["green"]) + leg_turnover(ind, v["brown"])).loc["1970-01-31":"2026-07-31"]
    series["epa5_minus_team5"] = series["epa5"] - series["team5"]
    costs["epa5_minus_team5"] = pd.Series(np.nan, index=series["team5"].index)
    rets = pd.DataFrame(series); rets.index.name = "date"
    rets.to_csv(TABLES / f"{MOD}_gb_monthly_returns.csv")

    rf = ff3["RF"]
    perf_rows, alpha_rows = [], []
    for k, r in series.items():
        role = S[k]["role"] if k in S else "exploratory"
        for p in PER:
            s = psub(r, p).dropna()
            pf = perf(s)
            tov = psub(costs[k], p).dropna()
            pf.update({"spec": k, "period": p, "start": s.index.min().strftime("%Y-%m"), "end": s.index.max().strftime("%Y-%m"),
                       "ann_turnover": 12 * tov.mean() if len(tov) else np.nan,
                       "ann_cost_10bp": 12 * 0.001 * tov.mean() if len(tov) else np.nan})
            pf["ann_ret_net_10bp"] = pf["ann_ret"] - pf["ann_cost_10bp"] if np.isfinite(pf.get("ann_cost_10bp", np.nan)) else np.nan
            p_mean = 2 * stats.norm.sf(abs(pf["t_mean_nw"]))
            pf["p_mean_nw"] = p_mean
            perf_rows.append(pf)
            kind_mean = "exploratory" if role in ("comparison", "exploratory") else "robustness"
            if p in ("cal2021", "cal2022"):        # calendar-year slices are descriptive: always exploratory
                kind_mean = "exploratory"
            ledger(f"mean_{k}_{p}", "Q4 GB mean return different from zero", "NW(6) t of mean", pf["t_mean_nw"], p_mean, pf["n"], kind_mean,
                   f"{S[k]['desc'] if k in S else 'EPA5 GB minus team5 GB'}; {pf['start']} to {pf['end']}"
                   + ("; 12-month calendar slice, descriptive" if p in ("cal2021", "cal2022") else ""))
            if p in ("cal2021", "cal2022"):        # 12 observations: no factor regressions for calendar-year slices
                continue
            for mname, cols in MODELS.items():
                F = (ff5 if mname == "FF5UMD" else ff3)[cols]
                res = nw_ols(s, F, lags=6)
                row = {"spec": k, "period": p, "model": mname, "n": int(res.nobs), "alpha_ann": 12 * res.params["const"],
                       "t_alpha": res.tvalues["const"], "p_alpha": res.pvalues["const"], "r2": res.rsquared}
                for c in cols:
                    row[f"b_{c}"] = res.params[c]; row[f"t_{c}"] = res.tvalues[c]
                alpha_rows.append(row)
                if k == "epa5" and p == "post2010" and mname == "FF5UMD":
                    kind = "primary"
                elif role in ("primary", "robustness"):
                    kind = "robustness"
                else:
                    kind = "exploratory"
                ledger(f"alpha_{mname}_{k}_{p}", f"Q4 GB {mname} alpha", f"NW(6) t of alpha ({mname})", row["t_alpha"], row["p_alpha"], row["n"], kind,
                       f"{S[k]['desc'] if k in S else 'EPA5 GB minus team5 GB'}; {p} {PER[p][0][:7]} to {PER[p][1][:7]}; alpha_ann={row['alpha_ann']:.4f}"
                       + ("; <=18 obs, 7 params: fragile" if row["n"] <= 18 and mname == "FF5UMD" else ""))
    perf_df = pd.DataFrame(perf_rows)[["spec", "period", "start", "end", "n", "ann_ret", "ann_vol", "sharpe", "t_mean_nw", "p_mean_nw", "max_dd", "hit_rate",
                                       "ann_turnover", "ann_cost_10bp", "ann_ret_net_10bp"]]
    alpha_df = pd.DataFrame(alpha_rows)
    main = ["team5", "epa5", "team8", "epa8"]
    save(perf_df, "perf", tex={"df": perf_df[perf_df["spec"].isin(main) & perf_df["period"].isin(RPERIODS)][["spec", "period", "n", "ann_ret", "ann_vol", "sharpe", "t_mean_nw", "max_dd", "ann_turnover"]],
                               "caption": "Green-minus-Brown performance under the team and EPA rankings (annualized; t is Newey-West with 6 lags; turnover is two-way traded notional per year, buys plus sells summed over both legs, from monthly re-equal-weighting; it excludes the initial build and the rebalancing inside the value-weighted industry portfolios). Full sample starts 1970-01; all windows end 2026-07.",
                               "label": "tab:m4_perf", "fmt": "%.2f"})
    tex_alpha = alpha_df[alpha_df["spec"].isin(main) & alpha_df["period"].isin(["full_1970", "post2010", "validation", "holdout", "last18", "last12"]) & (alpha_df["model"] == "FF5UMD")]
    save(alpha_df, "alphas", tex={"df": tex_alpha[["spec", "period", "n", "alpha_ann", "t_alpha", "b_Mkt-RF", "b_SMB", "b_HML", "b_RMW", "b_CMA", "b_UMD", "r2"]],
                                  "caption": "FF5+UMD regressions of Green-minus-Brown (NW 6 lags). alpha annualized. last12/last18 have 12/18 observations for 7 parameters and are descriptive only.",
                                  "label": "tab:m4_alphas", "fmt": "%.2f"})

    # compact CAPM/FF3/FF5UMD alpha grid for team5 vs epa5
    GP = RPERIODS[:2] + ["pre2010"] + RPERIODS[2:]
    grid = alpha_df[alpha_df["spec"].isin(["team5", "epa5", "epa5_minus_team5"]) & alpha_df["period"].isin(GP)]
    gw = grid.pivot_table(index=["spec", "period"], columns="model", values=["alpha_ann", "t_alpha"]).reindex(GP, level=1)
    gw.columns = [f"{a}_{m}" for a, m in gw.columns]
    gw = gw.reset_index()
    save(gw, "alpha_grid", tex={"df": gw, "caption": "Annualized alphas and NW(6) t-statistics under CAPM, FF3 and FF5+UMD: team 5v5, EPA 5v5 and their difference.",
                                "label": "tab:m4_alpha_grid", "fmt": "%.2f"})

    # primary test
    pr = alpha_df[(alpha_df["spec"] == "epa5") & (alpha_df["period"] == "post2010") & (alpha_df["model"] == "FF5UMD")].iloc[0]
    prim = pd.DataFrame([{"test": "EPA 5v5 Green-minus-Brown FF5+UMD alpha, 2010-01 to 2026-07, NW(6)", "n": pr["n"], "alpha_ann": pr["alpha_ann"],
                          "t_alpha": pr["t_alpha"], "p_two_sided": pr["p_alpha"], "reject_5pct": pr["p_alpha"] < 0.05,
                          "b_Mkt-RF": pr["b_Mkt-RF"], "b_SMB": pr["b_SMB"], "b_HML": pr["b_HML"], "b_RMW": pr["b_RMW"], "b_CMA": pr["b_CMA"], "b_UMD": pr["b_UMD"],
                          "t_HML": pr["t_HML"], "t_RMW": pr["t_RMW"], "t_CMA": pr["t_CMA"], "r2": pr["r2"]}])
    save(prim, "primary_test", tex={"df": prim.drop(columns=["test"]), "caption": "Primary test: EPA 5v5 Green-minus-Brown FF5+UMD alpha, post-2010, NW(6).", "label": "tab:m4_primary", "fmt": "%.3f"})

    # FF5UMD alpha across the pre-specified EPA specifications, with multiplicity adjustment within each window
    fams = []
    for p in ("post2010", "full_1970", "pre2010", "holdout"):
        fam = alpha_df[(alpha_df["period"] == p) & (alpha_df["model"] == "FF5UMD") & alpha_df["spec"].isin([k for k, v in S.items() if v["role"] in ("primary", "robustness")])].copy()
        fam["holm_p"] = holm(fam.set_index("spec")["p_alpha"]).values
        fam["bh_p"] = bh(fam.set_index("spec")["p_alpha"]).values
        fams.append(fam)
    fam = pd.concat(fams)[["period", "spec", "n", "alpha_ann", "t_alpha", "p_alpha", "holm_p", "bh_p", "b_SMB", "b_HML", "t_HML", "b_RMW", "b_CMA", "t_CMA", "b_UMD"]]
    save(fam, "post2010_family", tex={"df": fam[fam["period"] == "post2010"].drop(columns=["period"]),
                                      "caption": "Post-2010 FF5+UMD alpha across the pre-specified EPA specifications, with Holm and BH adjusted p-values (family = these 9 specifications).",
                                      "label": "tab:m4_family", "fmt": "%.3f"})

    # legs regressions (excess returns), team5 vs epa5, FF5UMD
    lrows = []
    for k in ["team5", "epa5", "team5_brown_plus_oil_coal", "epa5_brown_ex_oil_coal"]:
        for side, dct in (("green", gleg), ("brown", bleg)):
            y = (dct[k] - rf).dropna()
            for p in ["full_1970", "post2010", "holdout", "energy_rally"]:
                s = psub(y, p)
                res = nw_ols(s, ff5[MODELS["FF5UMD"]], lags=6)
                row = {"spec": k, "leg": side, "period": p, "n": int(res.nobs), "ann_excess_ret": 12 * s.mean(), "alpha_ann": 12 * res.params["const"],
                       "t_alpha": res.tvalues["const"], "p_alpha": res.pvalues["const"]}
                for c in MODELS["FF5UMD"]:
                    row[f"b_{c}"] = res.params[c]; row[f"t_{c}"] = res.tvalues[c]
                lrows.append(row)
                ledger(f"legalpha_FF5UMD_{k}_{side}_{p}", "Q4 leg-level FF5+UMD alpha (excess returns)", "NW(6) t of alpha", row["t_alpha"], row["p_alpha"],
                       row["n"], "exploratory", f"{k} {side} leg; {p}")
    legreg = pd.DataFrame(lrows)
    save(legreg, "leg_regressions", tex={"df": legreg[legreg["spec"].isin(["team5", "epa5"]) & legreg["period"].isin(["full_1970", "post2010", "holdout"])][
        ["spec", "leg", "period", "ann_excess_ret", "alpha_ann", "t_alpha", "b_Mkt-RF", "b_SMB", "b_HML", "b_RMW", "b_CMA", "b_UMD"]],
        "caption": "Leg-level FF5+UMD regressions (excess returns, NW 6 lags).", "label": "tab:m4_legs_reg", "fmt": "%.2f"})

    # energy table
    erows = []
    for k in ["team5", "team5_brown_plus_oil_coal", "epa5", "epa5_brown_plus_oil", "epa5_brown_ex_oil_coal"]:
        for p in ["cal2021", "cal2022", "energy_rally", "inflation_rates", "holdout", "post2010", "full_1970"]:
            gbp = psub(series[k], p); bp = psub(bleg[k], p)
            a = alpha_df[(alpha_df["spec"] == k) & (alpha_df["period"] == p) & (alpha_df["model"] == "FF5UMD")]
            a = a.iloc[0] if len(a) else {"alpha_ann": np.nan, "t_alpha": np.nan}
            erows.append({"spec": k, "period": p, "start": PER[p][0][:7], "end": PER[p][1][:7], "n": len(gbp),
                          "gb_ann_ret": 12 * gbp.mean(), "gb_cum_ret": (1 + gbp).prod() - 1, "brown_leg_ann_ret": 12 * bp.mean(),
                          "brown_leg_cum_ret": (1 + bp).prod() - 1, "gb_alpha_ff5umd": a["alpha_ann"], "gb_t_ff5umd": a["t_alpha"]})
    en = pd.DataFrame(erows)
    save(en, "energy", tex={"df": en[en["period"].isin(["cal2021", "cal2022", "energy_rally", "holdout"])][["spec", "period", "n", "gb_ann_ret", "gb_cum_ret", "brown_leg_cum_ret", "gb_alpha_ff5umd", "gb_t_ff5umd"]],
                            "caption": "Oil and Coal in the Brown leg during the 2021-2022 energy rally and the holdout (energy\\_rally = 2021-01 to 2022-12, exploratory window). Cumulative returns are compounded; alphas FF5+UMD, NW(6), not estimated for the 12-month calendar slices; the 24-month window has 24 observations for 7 parameters.",
                            "label": "tab:m4_energy", "fmt": "%.3f"})
    # portfolio breadth: number of firms in each leg industry (Ken French counts, Aug 2026 vintage)
    nf = load_kf_industries("nfirms")
    nrows = []
    for k in ["team5", "epa5"]:
        for side in ("green", "brown"):
            for i in S[k][side]:
                s = nf[i]
                nrows.append({"spec": k, "leg": side, "industry": i, "nfirms_1970_01": s.get(pd.Timestamp("1970-01-31")),
                              "nfirms_2010_01": s.get(pd.Timestamp("2010-01-31")), "nfirms_2026_07": s.get(pd.Timestamp("2026-07-31")),
                              "min_nfirms_1970_on": s.loc["1970":"2026-07"].min(), "min_nfirms_2010_on": s.loc["2010":"2026-07"].min()})
    nfd = pd.DataFrame(nrows)
    save(nfd, "leg_breadth", tex={"caption": "Number of firms in each leg industry (Ken French 49-industry counts).", "label": "tab:m4_breadth", "fmt": "%.0f"})
    return S, series, gleg, bleg, perf_df, alpha_df, prim, fam, en


def fig_cum(series, bleg, S):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0))
    for ax, start, title in [(axes[0], "1970-01-31", "(a) 1970-01 to 2026-07 (log scale)"), (axes[1], "2010-01-31", "(b) Post-2010 (primary test window)")]:
        for k, c, lab in [("team5", MUTED, "Team ranking (Fun, RlEst, Drugs, Telcm, Fin minus Util, Ships, Aero, Steel, BldMt)"),
                          ("epa5", BLUE, "EPA ranking (" + ", ".join(S["epa5"]["green"]) + " minus " + ", ".join(S["epa5"]["brown"]) + ")")]:
            s = series[k].loc[start:]
            w = (1 + s).cumprod()
            ax.plot(w.index, w.values, color=c, label=lab if ax is axes[0] else lab.split(" (")[0])
        ax.axvspan(pd.Timestamp("2022-08-31"), pd.Timestamp("2026-07-31"), color=GRID, alpha=0.6, lw=0)
        ax.axhline(1, color=INK2, lw=0.6)
        if start == "1970-01-31":
            ax.set_yscale("log")
        ax.set_title(title); ax.set_ylabel("Growth of $1, Green minus Brown (5 vs 5)")
    axes[1].text(pd.Timestamp("2022-10-31"), axes[1].get_ylim()[1] * 0.98, "holdout", fontsize=7, color=INK2, va="top")
    axes[0].legend(loc="upper left", fontsize=6.5); axes[1].legend(loc="upper left")
    savefig(fig, f"{MOD}_cum_gb")

    # energy: Brown legs and GB 2020-2026
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    cfg = [("team5", MUTED, "Team Brown"), ("team5_brown_plus_oil_coal", VIOLET, "Team Brown + Oil + Coal"), ("epa5", BLUE, "EPA Brown"),
           ("epa5_brown_ex_oil_coal", AQUA, "EPA Brown, Oil and Coal excluded")]
    for k, c, lab in cfg:
        w = (1 + bleg[k].loc["2020-01-31":]).cumprod()
        axes[0].plot(w.index, w.values, color=c, label=lab)
        w2 = (1 + series[k].loc["2020-01-31":]).cumprod()
        axes[1].plot(w2.index, w2.values, color=c, label=lab.replace("Brown", "GB"))
    for ax in axes:
        ax.axvspan(pd.Timestamp("2021-01-31"), pd.Timestamp("2022-12-31"), color=YELLOW, alpha=0.12, lw=0)
        ax.axvline(pd.Timestamp("2022-08-31"), color=INK2, lw=0.6, ls="--")
        ax.axhline(1, color=INK2, lw=0.6)
    axes[0].set_title("(a) Brown leg, growth of $1 from 2020-01"); axes[0].set_ylabel("Growth of $1 (raw return)")
    axes[1].set_title("(b) Green minus Brown, growth of $1 from 2020-01"); axes[1].set_ylabel("Growth of $1")
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    extra = [Patch(color=YELLOW, alpha=0.25, label="2021-22 energy rally"), Line2D([], [], color=INK2, lw=0.6, ls="--", label="holdout start (2022-08)")]
    hs, _ = axes[0].get_legend_handles_labels()
    axes[0].legend(handles=hs + extra, loc="upper left", fontsize=7); axes[1].legend(loc="lower left", fontsize=7)
    savefig(fig, f"{MOD}_energy_legs")


# =============================================================================== 4b. post-verification robustness
def primary_sensitivity(out: pd.DataFrame, S: dict):
    """Robustness of the primary test to leg membership (added after independent verification, not pre-specified).
    Smoke enters EPA Green by 0.001 kg/$ over Chips and is a 1-NAICS, 3-10 firm portfolio, so: (i) swap in the
    6th-lowest industry (Chips) for Smoke; (ii) drop each of the 10 leg members in turn (4-industry leg)."""
    ind = load_team()["industries"]; ff5 = load_ff5_mom()[MODELS["FF5UMD"]]
    g0, b0 = S["epa5"]["green"], S["epa5"]["brown"]
    srt = out["epa_sc_mean"].sort_values()
    sixth = srt.index[5]
    var = [("epa5 (primary)", g0, b0, "primary spec, reference row"),
           (f"{sixth} replaces {g0[-1]} in Green", g0[:-1] + [sixth], b0, "6th-lowest EPA industry in place of the 5th")]
    var += [(f"drop {x} (Green, 4 industries)", [y for y in g0 if y != x], b0, "drop-one") for x in g0]
    var += [(f"drop {x} (Brown, 4 industries)", g0, [y for y in b0 if y != x], "drop-one") for x in b0]
    rows = []
    for lab, g, b, what in var:
        gb = leg_returns(ind, g, b)[2].loc["1970-01-31":"2026-07-31"]
        periods = ["post2010", "holdout", "full_1970"] if what != "drop-one" else ["post2010"]
        for p in periods:
            s = psub(gb, p).dropna()
            res = nw_ols(s, ff5, lags=6)
            rows.append({"variant": lab, "kind": what, "green": ", ".join(g), "brown": ", ".join(b), "period": p, "n": int(res.nobs),
                         "ann_ret": 12 * s.mean(), "alpha_ann": 12 * res.params["const"], "t_alpha": res.tvalues["const"], "p_alpha": res.pvalues["const"]})
            if lab != "epa5 (primary)":      # the reference row is already in the ledger as the primary test / robustness rows
                ledger(f"sens_FF5UMD_{re.sub(r'[^A-Za-z0-9]+', '_', lab).strip('_')}_{p}", "Q4 robustness of the primary test to leg membership",
                       "NW(6) t of alpha (FF5UMD)", res.tvalues["const"], res.pvalues["const"], int(res.nobs), "robustness",
                       f"{lab}; {p}; alpha_ann={12 * res.params['const']:.4f}; added after independent verification (not pre-specified)")
    sens = pd.DataFrame(rows)
    save(sens, "primary_sensitivity", tex={"df": sens[sens["period"] == "post2010"][["variant", "n", "ann_ret", "alpha_ann", "t_alpha", "p_alpha"]],
                                           "caption": "Sensitivity of the primary test (EPA 5v5, FF5+UMD, 2010-01 to 2026-07, NW 6 lags) to leg membership: the 6th-lowest industry in place of the 5th Green member, and each leg member dropped in turn. Added after independent verification; not pre-specified.",
                                           "label": "tab:m4_sensitivity", "fmt": "%.3f"})
    return sens


def recent_decomposition(series: dict):
    """Split the raw GB return in each window into CAPM alpha + beta x mean market excess return (exact identity for OLS
    with a constant), and report the FF5+UMD market beta alongside. Descriptive: no new tests (the alphas are in the ledger)."""
    ff5 = load_ff5_mom(); ff3 = load_kf_ff3()      # CAPM on the FF3-file market factor, as in M4_emissions_alphas.csv
    rows = []
    for k in ["epa5", "team5", "epa5_minus_team5"]:
        for p in ["post2010", "holdout", "last18", "last12"]:
            s = psub(series[k], p).dropna()
            capm = nw_ols(s, ff3[["Mkt-RF"]], lags=6)
            f5 = nw_ols(s, ff5[MODELS["FF5UMD"]], lags=6)
            mkt = 12 * ff3["Mkt-RF"].reindex(s.index).mean()
            b = capm.params["Mkt-RF"]
            rows.append({"spec": k, "period": p, "n": len(s), "ann_ret": 12 * s.mean(), "ann_mkt_excess": mkt, "capm_beta": b,
                         "capm_beta_x_mkt": b * mkt, "capm_alpha_ann": 12 * capm.params["const"], "share_of_ret_from_beta": b * mkt / (12 * s.mean()),
                         "ff5umd_beta_mkt": f5.params["Mkt-RF"], "ff5umd_n_params": len(f5.params)})
    dec = pd.DataFrame(rows)
    save(dec, "recent_beta", tex={"df": dec.drop(columns=["ff5umd_n_params"]),
                                  "caption": "Raw Green-minus-Brown return = CAPM alpha + CAPM beta x mean market excess return (annualized). FF5+UMD market beta shown for comparison; last18 and last12 have 18 and 12 observations for 7 parameters and are descriptive only.",
                                  "label": "tab:m4_recent_beta", "fmt": "%.3f"})
    return dec


# =============================================================================== 5. exploratory: team timing rule on EPA Brown
def team_rule_rerun(S):
    t = load_team(); ind, ff3, att = t["industries"], t["ff3"], t["macro"]["attention"]
    variants = {"team_brown": S["team5"]["brown"], "team_brown_ex_aero_ships": S["team5_ex_aero_ships"]["brown"],
                "epa_brown": S["epa5"]["brown"], "epa41_brown": S["epa41_5"]["brown"]}
    windows = {"post2010": PERIODS["post2010"], "validation": PERIODS["validation"], "holdout": PERIODS["holdout"], "covid": PERIODS["covid"],
               "inflation_rates": PERIODS["inflation_rates"], "last18": PERIODS["last18"], "last12": PERIODS["last12"]}
    rows = []
    for vname, brown in variants.items():
        res = ts.short_brown_strategies(ind[brown].mean(axis=1), ff3, att)
        for hold in ("hold3", "hold6"):
            net = res[hold]["net_return"]
            for w, (a, b) in windows.items():
                st = ts.period_stats(net, ff3, a, b)
                if st is None:
                    continue
                tov = 12 * res[hold]["turnover"].loc[a:b].mean()
                p = 2 * stats.norm.sf(abs(st["alpha_ff3_t_hac6"]))
                rows.append({"brown_leg": vname, "members": ", ".join(brown), "hold": hold, "period": w, **st, "p_alpha": p, "ann_turnover": tov})
                ledger(f"teamrule_{vname}_{hold}_{w}", "Exploratory: team Short-Brown timing rule with the Brown leg swapped", "NW(6) t of FF3 alpha (team code)",
                       st["alpha_ff3_t_hac6"], p, st["n_months"], "exploratory", f"{vname} ({', '.join(brown)}), {hold}, {w}; ann_net={st['ann_net']:.4f}")
    df = pd.DataFrame(rows)
    save(df, "team_rule_rerun", tex={"df": df[df["period"].isin(["post2010", "validation", "holdout", "last12"])][["brown_leg", "hold", "period", "n_months", "active_months", "ann_net", "sharpe_net", "alpha_ff3_ann", "alpha_ff3_t_hac6", "b_HML"]],
                                     "caption": "Team Short-Brown timing rule (Original attention signal, 80th percentile, 3/6-month holds, 5\\% residual vol target, team costs) re-run with the Brown leg swapped. team\\_brown reproduces the team's numbers exactly.",
                                     "label": "tab:m4_team_rule", "fmt": "%.3f"})
    return df


# =============================================================================== main
def main():
    prov, identical = provenance()
    out, fac, nmap, info = build_intensity()
    sp, mem, kk, cal = compare_rankings(out, fac)
    fig_scatter(out)
    S, series, gleg, bleg, perf_df, alpha_df, prim, fam, en = returns_analysis(out)
    sens = primary_sensitivity(out, S)
    dec = recent_decomposition(series)
    fig_cum(series, bleg, S)
    tr = team_rule_rerun(S)
    led = pd.DataFrame(LEDGER)
    led.to_csv(TABLES / f"{MOD}_tests_ledger.csv", index=False)
    pd.DataFrame(KEY).to_csv(TABLES / f"{MOD}_key_numbers.csv", index=False)
    print("team file identical to PS1 file:", identical)
    print(out[["epa_sc_mean", "epa_sc_median", "n_naics", "team_intensity", "rank_epa", "rank_team"]].round(3).to_string())
    print(sp.round(3).to_string())
    print(mem[mem.ranking.isin(["team", "epa", "epa_within41"])].to_string())
    print(cal.round(3).to_string())
    print(prim.T.to_string())
    print(fam.round(3).to_string())
    print(en.round(3).to_string())
    print(tr[tr.period.isin(["post2010", "holdout"])].round(3).to_string())
    print(sens.drop(columns=["green", "brown"]).round(4).to_string())
    print(dec.round(4).to_string())
    print("ledger rows:", len(led), " primary:", (led.primary_or_exploratory == "primary").sum())


if __name__ == "__main__":
    main()
