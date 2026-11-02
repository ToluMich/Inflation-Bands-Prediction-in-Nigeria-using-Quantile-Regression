from pathlib import Path
import pandas as pd

folder = Path(__file__).resolve().parent
decisions = pd.read_csv(folder / "cbn_mpr_decisions_2017_2025.csv")
monthly = pd.read_csv(folder / "cbn_mpr_monthly_2010_2025.csv")

with pd.ExcelWriter(folder / "CBN_MPR_2010_2025.xlsx", engine="openpyxl") as writer:
    decisions.to_excel(writer, sheet_name="MPC Decisions", index=False)
    monthly.to_excel(writer, sheet_name="Monthly MPR", index=False)

    notes = pd.DataFrame({
        "Note": [
            "Official source: https://www.cbn.gov.ng/monetarypolicy/decisions.html",
            "The online decision page currently exposes archived decisions from 2017 onward.",
            "Months before 2017-09 are blank because those archived decisions are not on the page and must be sourced from the corresponding historical CBN Statistical Bulletin or archived communiques.",
            "Monthly values use the latest available MPC decision effective in each calendar month-end row.",
        ]
    })
    notes.to_excel(writer, sheet_name="Coverage Notes", index=False)
