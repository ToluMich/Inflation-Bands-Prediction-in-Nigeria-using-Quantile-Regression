from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.formula.api as smf


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "nigeria_inflation_complete.csv"
QUANTILES = [0.10, 0.50, 0.90]

df = pd.read_csv(DATA_FILE, parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
df.rename(
    columns={
        "Exchange_Rate_NGN_USD": "FX_Rate",
        "Food_Index": "Food_Index",
    },
    inplace=True,
)

required_columns = ["Date", "Inflation", "MPR", "FX_Rate", "Food_Index"]
missing_columns = [column for column in required_columns if column not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df["Inflation_Next_Month"] = df["Inflation"].shift(-1)

# At forecast origin month t, these predictors are lagged relative to the
# target month t+1. Inflation in month t is the lagged inflation feature.
df["Inflation_Lag1"] = df["Inflation"]
df["MPR_Lag1"] = df["MPR"]
df["FX_Rate_Lag1"] = df["FX_Rate"]
df["Food_Index_Lag1"] = df["Food_Index"]

model_columns = [
    "Date",
    "Inflation_Next_Month",
    "Inflation_Lag1",
    "MPR_Lag1",
    "FX_Rate_Lag1",
    "Food_Index_Lag1",
]
df = df.dropna(subset=model_columns).reset_index(drop=True)
df["Forecast_Month"] = df["Date"] + pd.offsets.MonthEnd(1)

train_df = df[df["Date"] < "2023-01-01"].copy()
test_df = df[(df["Date"] >= "2023-01-01") & (df["Date"] < "2025-12-01")].copy()

formula = (
    "Inflation_Next_Month ~ Inflation_Lag1 + MPR_Lag1 + "
    "FX_Rate_Lag1 + Food_Index_Lag1"
)

models = {}
for tau in QUANTILES:
    model = smf.quantreg(formula, data=train_df)
    models[tau] = model.fit(q=tau)
    test_df[f"q_{int(tau * 100)}"] = models[tau].predict(test_df)

# Quantile estimates fitted independently can cross slightly. Reorder the
# three estimates by the observed quantile ordering at each forecast month.
ordered_quantiles = test_df[["q_10", "q_50", "q_90"]].apply(
    lambda row: pd.Series(sorted(row.to_numpy()), index=row.index),
    axis=1,
)
test_df[["q_10", "q_50", "q_90"]] = ordered_quantiles

test_df["In_Band"] = (
    test_df["Inflation_Next_Month"].ge(test_df["q_10"])
    & test_df["Inflation_Next_Month"].le(test_df["q_90"])
)
coverage = 100 * test_df["In_Band"].mean()

coverage_table = pd.DataFrame(
    {
        "Metric": [
            "Target coverage",
            "Test forecast months",
            "Forecasts inside band",
            "Empirical coverage",
        ],
        "Value": [
            "80.00%",
            int(len(test_df)),
            int(test_df["In_Band"].sum()),
            f"{coverage:.2f}%",
        ],
    }
)

print("\n" + "=" * 40)
print("OUT-OF-SAMPLE 80% PREDICTION BAND")
print("=" * 40)
print(coverage_table.to_string(index=False))
print("=" * 40)

coverage_table.to_csv(BASE_DIR / "quantile_regression_coverage.csv", index=False)

predictions = test_df[
    [
        "Forecast_Month",
        "Inflation_Next_Month",
        "q_10",
        "q_50",
        "q_90",
        "In_Band",
    ]
].rename(
    columns={
        "Inflation_Next_Month": "Actual_Inflation",
        "Forecast_Month": "Date",
    }
)
predictions.to_csv(BASE_DIR / "next_month_inflation_predictions.csv", index=False, date_format="%Y-%m-%d")

plt.figure(figsize=(12, 6))
plt.plot(
    predictions["Date"],
    predictions["Actual_Inflation"],
    color="black",
    linewidth=2,
    marker="o",
    markersize=4,
    label="Actual NBS inflation",
)
plt.plot(
    predictions["Date"],
    predictions["q_50"],
    color="#0072B2",
    linestyle="--",
    linewidth=2,
    label="Median forecast (tau=0.50)",
)
plt.plot(
    predictions["Date"],
    predictions["q_10"],
    color="#D55E00",
    linestyle="-.",
    linewidth=1.5,
    label="Lower quantile (tau=0.10)",
)
plt.plot(
    predictions["Date"],
    predictions["q_90"],
    color="#009E73",
    linestyle="-.",
    linewidth=1.5,
    label="Upper quantile (tau=0.90)",
)
plt.fill_between(
    predictions["Date"],
    predictions["q_10"],
    predictions["q_90"],
    color="#CC79A7",
    alpha=0.18,
    label="80% prediction band (tau=0.10 to 0.90)",
)
plt.title("Nigeria Next-Month Inflation Forecast and 80% Quantile Bands (2023-2025)")
plt.xlabel("Forecast month")
plt.ylabel("Inflation rate (%)")
plt.grid(True, linestyle=":", alpha=0.6)
plt.legend(loc="upper left")
plt.tight_layout()
plt.show()

print(f"Predictions: {BASE_DIR / 'next_month_inflation_predictions.csv'}")
print(f"Coverage table: {BASE_DIR / 'quantile_regression_coverage.csv'}")
