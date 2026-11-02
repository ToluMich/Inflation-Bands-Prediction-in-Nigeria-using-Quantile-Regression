from pathlib import Path
import pandas as pd

folder = Path(__file__).resolve().parent
path = folder / "cbn_mpr_decisions_2017_2025.csv"
decisions = pd.read_csv(path, parse_dates=["Decision_Date"])
corrections = {
    "2024-05-21": 26.25,
    "2024-07-23": 26.75,
    "2024-09-24": 27.25,
}
for date, value in corrections.items():
    decisions.loc[decisions["Decision_Date"] == pd.Timestamp(date), "MPR_Percent"] = value

source = "https://www.cbn.gov.ng/monetarypolicy/decisions.html"
extra = pd.DataFrame([
    {"Decision_Date": pd.Timestamp("2024-02-27"), "MPR_Percent": 22.75, "Source": source},
    {"Decision_Date": pd.Timestamp("2024-11-26"), "MPR_Percent": 27.25, "Source": source},
])
decisions = pd.concat([decisions, extra], ignore_index=True)
decisions = decisions.sort_values("Decision_Date").drop_duplicates("Decision_Date")
decisions.to_csv(path, index=False, date_format="%Y-%m-%d")

monthly_index = pd.date_range("2010-01-31", "2025-12-31", freq="ME")
monthly = pd.DataFrame({"Date": monthly_index, "MPR_Percent": pd.NA})
for i, row in monthly.iterrows():
    applicable = decisions[decisions["Decision_Date"].dt.to_period("M") <= row["Date"].to_period("M")]
    if not applicable.empty:
        monthly.at[i, "MPR_Percent"] = applicable.sort_values("Decision_Date").iloc[-1]["MPR_Percent"]
monthly.to_csv(folder / "cbn_mpr_monthly_2010_2025.csv", index=False, date_format="%Y-%m-%d")

print("Monthly MPR rows:", len(monthly))
print("Covered from:", monthly.dropna()["Date"].min())
print("Covered through:", monthly.dropna()["Date"].max())
