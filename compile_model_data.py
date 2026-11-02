from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent


def read_world_bank_wide(path: Path) -> pd.Series:
    frame = pd.read_csv(path, skiprows=4, encoding="utf-8-sig")
    row = frame.iloc[0]
    years = [column for column in row.index if column.isdigit()]
    values = pd.to_numeric(row[years], errors="coerce")
    return pd.Series(
        values.to_numpy(),
        index=pd.to_datetime([f"{year}-01-01" for year in years]),
        name=row["Indicator Name"],
    )


oil = pd.read_csv(BASE_DIR / "brent_oil_price.csv", parse_dates=["observation_date"])
oil["Date"] = oil["observation_date"].dt.to_period("M").dt.to_timestamp("M")
oil = oil.groupby("Date", as_index=False)["POILBREUSDM"].mean()
oil.rename(columns={"POILBREUSDM": "Oil_USD_per_Barrel"}, inplace=True)

mpr = pd.read_csv(BASE_DIR / "cbn_mpr_monthly_2010_2025.csv", parse_dates=["Date"])

cpi_path = BASE_DIR / "worldbank_cpi" / "API_NGA_FP.CPI.TOTL_en_csv_v2_224671.csv"
exchange_path = BASE_DIR / "worldbank_exchange" / "API_NGA_PA.NUS.FCRF_en_csv_v2_46660.csv"
cpi = read_world_bank_wide(cpi_path)
exchange_rate = read_world_bank_wide(exchange_path)

dates = pd.date_range("2010-01-31", "2025-12-31", freq="ME")
result = pd.DataFrame({"Date": dates})

result["WorldBank_CPI_Annual_Interpolated"] = (
    cpi.to_frame(name="value")
    .reindex(cpi.index.union(dates))
    .sort_index()["value"]
    .interpolate(method="time")
    .reindex(dates)
    .to_numpy()
)
result["Exchange_Rate_NGN_USD_Annual_Interpolated"] = (
    exchange_rate.to_frame(name="value")
    .reindex(exchange_rate.index.union(dates))
    .sort_index()["value"]
    .interpolate(method="time")
    .reindex(dates)
    .to_numpy()
)

result = result.merge(mpr, on="Date", how="left")
result.rename(columns={"MPR_Percent": "MPR"}, inplace=True)
result = result.merge(oil, on="Date", how="left")

# NBS monthly inflation and food index have not yet been downloaded in this project.
# Empty values are intentional: fabricating them would make the model scientifically misleading.
result["Inflation"] = np.nan
result["CPI"] = np.nan
result["Food_Index"] = np.nan

result = result[
    [
        "Date",
        "Inflation",
        "CPI",
        "WorldBank_CPI_Annual_Interpolated",
        "MPR",
        "Exchange_Rate_NGN_USD_Annual_Interpolated",
        "Food_Index",
        "Oil_USD_per_Barrel",
    ]
]
result.to_csv(BASE_DIR / "nigeria_inflation_model_data.csv", index=False, date_format="%Y-%m-%d")

print(f"Created nigeria_inflation_model_data.csv with {len(result)} monthly rows.")
print("Blank fields:", result[["Inflation", "CPI", "MPR", "Food_Index"]].isna().sum().to_dict())
