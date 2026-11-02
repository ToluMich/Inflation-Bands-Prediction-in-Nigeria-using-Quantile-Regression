import pandas as pd
import statsmodels.formula.api as smf


data = pd.read_csv(
    r"nigeria_inflation_complete.csv",
    parse_dates=["Date"],
).sort_values("Date").reset_index(drop=True)

data["Inflation_Next_Month"] = data["Inflation"].shift(-1)
data["Inflation_Lag1"] = data["Inflation"]
data["MPR_Lag1"] = data["MPR"]
data["FX_Rate_Lag1"] = data["Exchange_Rate_NGN_USD"]
data["Food_Index_Lag1"] = data["Food_Index"]

columns = [
    "Inflation_Next_Month",
    "Inflation_Lag1",
    "MPR_Lag1",
    "FX_Rate_Lag1",
    "Food_Index_Lag1",
]
data = data.dropna(subset=columns)

train = data[data["Date"] < "2023-01-01"].copy()
test = data[(data["Date"] >= "2023-01-01") & (data["Date"] < "2025-12-01")].copy()

formula = (
    "Inflation_Next_Month ~ Inflation_Lag1 + MPR_Lag1 + "
    "FX_Rate_Lag1 + Food_Index_Lag1"
)

print("TRAIN_TEST", len(train), len(test))
for quantile in [0.10, 0.50, 0.90]:
    model = smf.quantreg(formula, data=train).fit(q=quantile)
    print("QUANTILE", quantile)
    print("PARAMETERS")
    print(model.params.to_string())
    print("PVALUES")
    print(model.pvalues.to_string())
    print("PSEUDO_R2", model.prsquared)
