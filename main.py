import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf


np.random.seed(42)
dates = pd.date_range(start='2010-01-01', end='2025-12-01', freq='MS')
n = len(dates)

mpr = np.random.normal(14, 2, n).cumsum() / 10 + 12  # Policy Rate
fx_rate = np.linspace(150, 1500, n) + np.random.normal(0, 15, n)  # ₦/USD
oil_price = 70 + 20 * np.sin(np.linspace(0, 10, n)) + np.random.normal(0, 5, n)  # Crude Oil
food_index = np.linspace(100, 400, n) + np.random.normal(0, 10, n)

inflation = 10 + 0.01 * fx_rate + 0.15 * mpr + np.random.normal(0, 1.5, n)
inflation[150:] += np.linspace(0, 15, n - 150)  # Post-2022 surge simulation

df = pd.DataFrame({
    'Date': dates,
    'Inflation': inflation,
    'MPR': mpr,
    'FX_Rate': fx_rate,
    'Oil_Price': oil_price,
    'Food_Index': food_index
})

# ==========================================
# 2. FEATURE ENGINEERING (Lags & Transformations)
# ==========================================
# Creating 1-month lagged predictors (using past data to predict current inflation)
df['Inflation_Lag1'] = df['Inflation'].shift(1)
df['MPR_Lag1'] = df['MPR'].shift(1)
df['FX_Rate_Lag1'] = df['FX_Rate'].shift(1)
df['Food_Index_Lag1'] = df['Food_Index'].shift(1)

# Drop missing values caused by lagging
df = df.dropna().reset_index(drop=True)

# ==========================================
# 3. TRAIN / TEST SPLIT (2010-2022 vs 2023-2025)
# ==========================================
train_mask = df['Date'] < '2023-01-01'
test_mask = df['Date'] >= '2023-01-01'

train_df = df[train_mask].copy()
test_df = df[test_mask].copy()

print(f"Training Samples (2010-2022): {len(train_df)}")
print(f"Testing Samples  (2023-2025): {len(test_df)}")

# Regression Formula Definition
formula = 'Inflation ~ Inflation_Lag1 + MPR_Lag1 + FX_Rate_Lag1 + Food_Index_Lag1 + Oil_Price'

# ==========================================
# 4. FIT QUANTILE REGRESSION MODELS
# ==========================================
quantiles = [0.10, 0.50, 0.90]
models = {}
predictions = {}

for tau in quantiles:
    # Quantile Regression using Statsmodels
    model = smf.quantreg(formula, data=train_df)
    res = model.fit(q=tau)
    models[tau] = res
    
    # Predict on the Test Set (2023-2025)
    test_df[f'q_{int(tau*100)}'] = res.predict(test_df)

# ==========================================
# 5. EVALUATE COVERAGE RATE (80% Interval)
# ==========================================
# A "Hit" occurs if Actual Inflation falls inside [q_10, q_90]
test_df['In_Band'] = (test_df['Inflation'] >= test_df['q_10']) & (test_df['Inflation'] <= test_df['q_90'])

total_test_months = len(test_df)
hits = test_df['In_Band'].sum()
coverage_rate = (hits / total_test_months) * 100

print("\n" + "="*40)
print("     OUT-OF-SAMPLE EVALUATION TABLE     ")
print("="*40)
print(f"Target Coverage      : 80.0%")
print(f"Total Test Months    : {total_test_months}")
print(f"Actual Inside Band   : {hits}")
print(f"Empirical Coverage   : {coverage_rate:.2f}%")
print("="*40)

# ==========================================
# 6. DELIVERABLE VISUALIZATION
# ==========================================
plt.figure(figsize=(12, 6))

# Plot Actual Inflation
plt.plot(test_df['Date'], test_df['Inflation'], color='black', linewidth=2.5, label='Actual NBS Inflation', marker='o')

# Plot Median Point Forecast (q50)
plt.plot(test_df['Date'], test_df['q_50'], color='blue', linestyle='--', label='Median Forecast (τ=0.50)')

# Fill the 80% Prediction Interval (q10 to q90)
plt.fill_between(
    test_df['Date'], 
    test_df['q_10'], 
    test_df['q_90'], 
    color='blue', 
    alpha=0.2, 
    label='80% Prediction Band (τ=0.10 to τ=0.90)'
)

plt.title('Nigeria Inflation Forecast with 80% Quantile Regression Bands (2023–2025 Test Period)', fontsize=14, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Inflation Rate (%)', fontsize=12)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left', fontsize=11)

plt.tight_layout()
plt.show()