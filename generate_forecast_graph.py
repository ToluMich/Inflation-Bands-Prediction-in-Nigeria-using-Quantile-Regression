from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PREDICTIONS_FILE = BASE_DIR / "next_month_inflation_predictions.csv"
OUTPUT_FILE = BASE_DIR / "nigeria_inflation_quantile_bands.png"

predictions = pd.read_csv(PREDICTIONS_FILE, parse_dates=["Date"])

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
    linewidth=2,
    linestyle="--",
    label="Median forecast (tau=0.50)",
)
plt.plot(
    predictions["Date"],
    predictions["q_10"],
    color="#D55E00",
    linewidth=1.5,
    linestyle="-.",
    label="Lower quantile (tau=0.10)",
)
plt.plot(
    predictions["Date"],
    predictions["q_90"],
    color="#009E73",
    linewidth=1.5,
    linestyle="-.",
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
plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.close()
print(OUTPUT_FILE)
