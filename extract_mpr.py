import calendar
import re
from pathlib import Path

import pandas as pd

SOURCE_MARKDOWN = Path(r"C:\Users\Tolu\AppData\Local\Temp\1793637699227-copilot-tool-output-ad0b7754381f4773b0a0b3c026b0a075.txt")
OUTPUT_DIR = Path(__file__).resolve().parent
SOURCE_URL = "https://www.cbn.gov.ng/monetarypolicy/decisions.html"

text = SOURCE_MARKDOWN.read_text(encoding="utf-8")
sections = re.split(r"(?=\*\*Key Decisions of the Central Bank of Nigeria Monetary Policy Committee)", text)
rows = []

month_names = "January|February|March|April|May|June|July|August|September|October|November|December"

for section in sections:
    header = section.split("\n", 1)[0]
    header = header.strip("* ")
    years = re.findall(r"20\d{2}", header)
    if not years or not (2017 <= int(years[-1]) <= 2025):
        continue

    year = int(years[-1])
    month_match = re.search(month_names, header, re.IGNORECASE)
    if not month_match:
        continue
    month_name = month_match.group(0)
    month = pd.to_datetime(month_name + " 1", format="%B %d").month

    # Use the final day in the meeting date range as the decision-effective date.
    days = [int(value) for value in re.findall(r"\b(\d{1,2})(?:st|nd|rd|th)?\b", header[:header.lower().find(month_name.lower()) + len(month_name) + 25])]
    # Restrict to calendar dates on/after the final meeting month reference.
    day_candidates = [value for value in days if 1 <= value <= calendar.monthrange(year, month)[1]]
    day = max(day_candidates) if day_candidates else 1

    # The MPR decision is the first numbered item containing MPR/Monetary Policy Rate.
    mpr_line_match = re.search(r"(?m)^\s*\d+[.)].*(?:Monetary Policy Rate|\bMPR\b).*?$", section, re.IGNORECASE)
    if not mpr_line_match:
        continue
    mpr_line = mpr_line_match.group(0)
    numbers = [float(value.replace(",", "")) for value in re.findall(r"\b\d+(?:\.\d+)?\b", mpr_line)]
    # Ignore the numbered-list prefix, which is normally 1-4, when choosing a rate.
    rate_candidates = numbers[1:] if numbers and 1 <= numbers[0] <= 9 else numbers

    if not rate_candidates:
        continue
    if re.search(r"\bfrom\b.*\bto\b", mpr_line, re.IGNORECASE):
        from_to = re.findall(r"from\s*(\d+(?:\.\d+)?)\s*(?:per cent\s*)?to\s*(\d+(?:\.\d+)?)", mpr_line, re.IGNORECASE)
        rate = float(from_to[-1][1]) if from_to else rate_candidates[-1]
    else:
        # For retain/reduce/reset decisions, the final percentage in the line is the resulting MPR.
        rate = rate_candidates[-1]

    rows.append({
        "Decision_Date": pd.Timestamp(year=year, month=month, day=day),
        "MPR_Percent": rate,
        "Source": SOURCE_URL,
    })

decisions = pd.DataFrame(rows).drop_duplicates(subset=["Decision_Date"], keep="last")
# Sort chronologically and keep the strongest unique value when wording creates duplicate entries.
decisions = decisions.sort_values("Decision_Date").reset_index(drop=True)
decisions.to_csv(OUTPUT_DIR / "cbn_mpr_decisions_2017_2025.csv", index=False, date_format="%Y-%m-%d")

# Monthly effective MPR. Rules: decisions dated after a month started are applied from the next month-end onward;
# decisions dated within a month are also filled into that month's row using month-end convention.
monthly_index = pd.date_range("2010-01-31", "2025-12-31", freq="ME")
monthly = pd.DataFrame({"Date": monthly_index})
monthly["MPR_Percent"] = pd.NA
for _, decision in decisions.iterrows():
    mask = monthly["Date"] >= pd.Timestamp(decision["Decision_Date"]) - pd.offsets.MonthEnd(0)
    monthly.loc[mask, "MPR_Percent"] = decision["MPR_Percent"]

# The online page extracts 2017 onward; pre-2017 rows remain blank for official-source entry.
monthly.to_csv(OUTPUT_DIR / "cbn_mpr_monthly_2010_2025.csv", index=False, date_format="%Y-%m-%d")

print(f"Extracted {len(decisions)} CBN decisions")
print(decisions.head().to_string(index=False))
print(decisions.tail().to_string(index=False))
