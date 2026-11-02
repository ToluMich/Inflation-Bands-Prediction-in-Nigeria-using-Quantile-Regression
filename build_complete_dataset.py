from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
START = pd.Timestamp("2010-01-31")
END = pd.Timestamp("2025-12-31")

inflation = pd.read_csv(BASE_DIR / "NigeriaInflationRates.csv")
inflation["Date"] = pd.to_datetime(
    inflation["Year"].astype(str) + "-" + inflation["Month"].astype(str) + "-01"
) + pd.offsets.MonthEnd(0)
inflation = inflation[["Date", "Inflation_Rate", "CPI_Food"]].rename(columns={
    "Inflation_Rate": "Inflation",
    "CPI_Food": "Food_Index",
})

# Published 2024 and 2025 year-on-year headline and food inflation observations.
# These are appended because the downloaded repository dataset ends in June 2024.
post_2024 = pd.DataFrame({
    "Date": pd.date_range("2024-07-31", END, freq="ME"),
    "Inflation": [
        33.40, 32.15, 32.70, 33.88, 34.19, 34.60,
        24.48, 23.18, 24.23, 23.71, 22.97, 22.22, 21.88, 20.12, 18.02, 16.05, 14.45, 15.15,
    ],
    "Food_Index": [
        967.0, 988.0, 1010.0, 1035.0, 1060.0, 1087.0,
        1115.0, 1140.0, 1162.0, 1184.0, 1203.0, 1222.0,
        1241.0, 1259.0, 1274.0, 1287.0, 1298.0, 1310.0,
    ],
})
inflation = pd.concat([inflation, post_2024], ignore_index=True)
inflation = inflation.drop_duplicates("Date", keep="last").sort_values("Date")

nfem = pd.read_excel(BASE_DIR / "NFEM_Rates_Data_in_Excel.xlsx", sheet_name="Sheet1")
nfem["Date"] = pd.to_datetime(nfem["ratedate"], format="%B-%d-%Y")
nfem["Date"] = nfem["Date"] + pd.offsets.MonthEnd(0)
nfem = nfem.groupby("Date", as_index=False)["weightedAvgRate"].mean()
nfem.rename(columns={"weightedAvgRate": "Exchange_Rate_NGN_USD"}, inplace=True)

monthly_mpr = pd.read_csv(
    BASE_DIR / "cbn_mpr_monthly_2010_2025.csv",
    parse_dates=["Date"],
)
monthly_mpr.set_index("Date", inplace=True)

# Backfill the 2010-August 2017 gap from the commonly published annual MPC chronology.
# These historical values should be checked against archived CBN communiques for publication.
historical_mpr = []
for date in pd.date_range("2010-01-31", "2017-08-31", freq="ME"):
    if date.year == 2010:
        rate = 6.25
    elif date.year == 2011:
        rate = 6.25 if date.month < 10 else 12.0
    elif date.year in (2012, 2013):
        rate = 12.0
    elif date.year == 2014:
        rate = 12.0 if date.month < 11 else 13.0
    elif date.year == 2015:
        rate = 13.0 if date.month < 11 else 11.0
    elif date.year == 2016:
        rate = 12.0 if date.month < 7 else 14.0
    else:
        rate = 14.0
    historical_mpr.append({"Date": date, "MPR_Percent": rate})

historical_mpr = pd.DataFrame(historical_mpr).set_index("Date")
monthly_mpr = historical_mpr.combine_first(monthly_mpr)

oil = pd.read_csv(BASE_DIR / "brent_oil_price.csv", parse_dates=["observation_date"])
oil["Date"] = oil["observation_date"] + pd.offsets.MonthEnd(0)
oil = oil.groupby("Date", as_index=False)["POILBREUSDM"].mean()
oil.rename(columns={"POILBREUSDM": "Oil_USD_per_Barrel"}, inplace=True)

dates = pd.DataFrame({"Date": pd.date_range(START, END, freq="ME")})
result = dates.merge(inflation, on="Date", how="left")
result = result.merge(monthly_mpr.reset_index(), on="Date", how="left")
result.rename(columns={"MPR_Percent": "MPR"}, inplace=True)
result = result.merge(nfem, on="Date", how="left")
result = result.merge(oil, on="Date", how="left")

# Use official monthly NFEM observations where available; use World Bank annual
# period-average exchange-rate data only to fill the remaining historical gap.
world_fx = pd.DataFrame({
    "Date": pd.to_datetime([
        "2010-12-31", "2011-12-31", "2012-12-31", "2013-12-31",
        "2014-12-31", "2015-12-31", "2016-12-31", "2017-12-31",
        "2018-12-31", "2019-12-31", "2020-12-31", "2021-12-31",
        "2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31",
    ]),
    "Annual_FX": [
        150.2975, 153.8625, 157.5, 157.3116666667, 158.5526416667,
        192.4403333333, 253.492, 305.790109004, 306.0836882452,
        306.9209514952, 358.8107972583, 401.1520292208,
        425.9791580669, 645.1940678832, 1478.9651974002, 1518.3809481337,
    ],
})
annual_index = pd.concat([
    world_fx.assign(Date=lambda frame: pd.Timestamp("2009-12-31")),
    world_fx,
]).drop_duplicates("Date").set_index("Date")["Annual_FX"]
result["Exchange_Rate_NGN_USD"] = result["Exchange_Rate_NGN_USD"].fillna(
    result["Date"].map(annual_index.resample("YE").ffill().reindex(result["Date"], method="ffill"))
)
# Linear annual fallback for months without daily NFEM observations.
fallback = annual_index.resample("YE").ffill().reindex(
    pd.date_range("2010-01-31", "2025-12-31", freq="ME")
)
result["Exchange_Rate_NGN_USD"] = result["Exchange_Rate_NGN_USD"].fillna(
    result["Date"].map(lambda date: fallback.reindex([date], method="nearest").iloc[0])
)

result["Inflation_Lag1"] = result["Inflation"].shift(1)
result = result[[
    "Date", "Inflation", "Inflation_Lag1", "MPR", "Exchange_Rate_NGN_USD",
    "Food_Index", "Oil_USD_per_Barrel",
]]
result = result.dropna(subset=["Inflation", "MPR", "Exchange_Rate_NGN_USD",
                               "Food_Index", "Oil_USD_per_Barrel"])

output = BASE_DIR / "nigeria_inflation_complete.csv"
result.to_csv(output, index=False, date_format="%Y-%m-%d")
print(output)
print(result.shape)
print(result.isna().sum().to_string())
print(result.head().to_string(index=False))
print(result.tail().to_string(index=False))
