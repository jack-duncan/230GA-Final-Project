"""Fact-check C05: ChatGPT critique #4 and idea 4.

Claims checked
- "eight industries missing, including Oil, the most obvious transition-risk industry"
- "Aircraft and Shipbuilding in the top five by emissions intensity is surprising; check the mapping and where Coal ranks"
- Fix: "Rebuild intensity from EPA supply-chain GHG factors (NAICS -> SIC -> FF49) covering all 49, and rerun with Oil and Coal in"
- Idea 4: "supply-chain factors include upstream emissions, a different concept from your snapshot"
Independent spot check from the raw EPA v1.3 file with hand-picked NAICS codes for each FF49 SIC range, then compared
with the full crosswalk-based mapping built by module M4 (data/derived/ff49_emissions_epa.csv).
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import pandas as pd
from common import load_team, RAW, DERIVED

pd.set_option("display.width", 200)
OUT = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
team = load_team()["emissions"].sort_values(ascending=False)
print("=== Team file: n =", len(team), " top 10 (highest intensity) ===")
print(team.head(10).round(4).to_string())
print("Coal rank from top:", list(team.index).index("Coal") + 1, "of", len(team))
print("Oil in team file:", "Oil" in team.index)
print("Util / Fun ratio in team file:", round(team["Util"] / team["Fun"], 0))

epa = pd.read_csv(RAW / "epa_sc_ghg_naics_v13.csv")
epa.columns = ["naics", "title", "ghg", "unit", "sef_nomargin", "margin", "sef", "useeio"]
print("\nEPA v1.3 NAICS codes:", len(epa), "| electricity generation codes 2211xx present:",
      epa.naics.astype(str).str.startswith("2211").any())
print("EPA max/min factor ratio:", round(epa.sef.max() / epa.sef.min(), 1))
epa["pct_rank_high"] = epa.sef.rank(ascending=False, pct=True)
picks = {
    "Aero (SIC 372x)": [336411, 336412, 336413],
    "Ships (SIC 3730-31, 3740-43)": [336611, 336510],
    "Steel (iron and steel mills)": [331110],
    "BldMt (cement)": [327310],
    "Coal (SIC 12xx)": [212111, 212112, 212113],
    "Oil (SIC 13xx extraction)": [211120, 211130],
    "Util ex electricity (gas dist, water)": [221210, 221310],
}
rows = []
for k, codes in picks.items():
    s = epa[epa.naics.isin(codes)]
    rows.append({"group": k, "codes": len(s), "mean_sef_kgCO2e_per_2022usd": s.sef.mean(),
                 "best_pct_rank_from_top": s.pct_rank_high.min()})
spot = pd.DataFrame(rows)
print("\n=== EPA supply-chain factors (with margins), spot check ===")
print(spot.round(3).to_string(index=False))

m4 = pd.read_csv(DERIVED / "ff49_emissions_epa.csv").set_index("ff49")
m4["rank_epa_from_top"] = m4.epa_sc_mean.rank(ascending=False).astype(int)
m4["rank_team_from_top"] = m4.team_intensity.rank(ascending=False)
m4["rank_direct_from_top"] = m4.useeio_direct_mean.rank(ascending=False).astype(int)
print("\n=== M4 full mapping: ranks from top (1 = most intensive) for key industries ===")
print(m4.loc[["Util", "Ships", "Aero", "Steel", "BldMt", "Coal", "Oil", "Chems", "Trans", "Mines"],
             ["team_intensity", "rank_team_from_top", "epa_sc_mean", "rank_epa_from_top", "rank_direct_from_top"]].round(3).to_string())
print("\nEPA top 5:", list(m4.epa_sc_mean.sort_values(ascending=False).index[:5]))
spot.to_csv(OUT + "c05_epa_spot.csv", index=False)
