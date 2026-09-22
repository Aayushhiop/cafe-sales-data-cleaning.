"""
clean_cafe_sales.py
--------------------
Cleans the "Dirty Cafe Sales" public dataset (Kaggle).
Source (original messy file): dirty_cafe_sales.csv

Run:  python clean_cafe_sales.py
Input:  dirty_cafe_sales.csv
Output: cleaned_cafe_sales.csv  +  cleaning_log.txt
"""

import pandas as pd
import numpy as np

RAW_FILE = "dirty_cafe_sales.csv"
OUT_FILE = "cleaned_cafe_sales.csv"
LOG_FILE = "cleaning_log.txt"

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(str(msg))

# ------------------------------------------------------------------
# 1. LOAD  (everything as string first so nothing gets silently mis-typed)
# ------------------------------------------------------------------
df = pd.read_csv(RAW_FILE, dtype=str)
log(f"Loaded raw file: {df.shape[0]} rows, {df.shape[1]} columns")

# ------------------------------------------------------------------
# 2. NORMALISE PLACEHOLDER "MISSING" MARKERS
#    The raw file mixes three different ways of saying "no value":
#    true empty/NaN, the literal string "ERROR", and the literal
#    string "UNKNOWN". We standardise all three to a real NaN so
#    pandas' missing-value tools (isna, fillna, dropna) work correctly.
# ------------------------------------------------------------------
PLACEHOLDERS = ["ERROR", "UNKNOWN", "", " ", "nan", "NaN", "None"]
before_counts = {c: df[c].isna().sum() for c in df.columns}
df = df.replace(PLACEHOLDERS, np.nan)
after_counts = {c: df[c].isna().sum() for c in df.columns}

log("\nMissing values BEFORE standardising placeholders (NaN only):")
for c, v in before_counts.items():
    log(f"  {c}: {v}")
log("\nMissing values AFTER standardising ('ERROR'/'UNKNOWN' -> NaN):")
for c, v in after_counts.items():
    log(f"  {c}: {v}")

# ------------------------------------------------------------------
# 3. REMOVE DUPLICATE RECORDS
# ------------------------------------------------------------------
dup_full = df.duplicated().sum()
dup_id = df.duplicated(subset=["Transaction ID"]).sum()
log(f"\nFully duplicate rows found: {dup_full}")
log(f"Duplicate Transaction IDs found: {dup_id}")
df = df.drop_duplicates()
df = df.drop_duplicates(subset=["Transaction ID"], keep="first")
log(f"Rows after removing duplicates: {len(df)}")

# ------------------------------------------------------------------
# 4. FIX DATA TYPES
#    Everything was read in as text. Convert numeric/date columns to
#    their proper dtypes so calculations and sorting work correctly.
# ------------------------------------------------------------------
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["Price Per Unit"] = pd.to_numeric(df["Price Per Unit"], errors="coerce")
df["Total Spent"] = pd.to_numeric(df["Total Spent"], errors="coerce")
df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")

log("\nData types after conversion:")
log(df.dtypes.to_string())

# ------------------------------------------------------------------
# 5. FIX INCONSISTENT / INVALID VALUES
# ------------------------------------------------------------------
# 5a. Clean text categorical columns: trim whitespace, standardise case
for col in ["Item", "Payment Method", "Location"]:
    df[col] = df[col].astype("string").str.strip()

log("\nItem categories found: " + str(sorted(df["Item"].dropna().unique())))
log("Payment Method categories found: " + str(sorted(df["Payment Method"].dropna().unique())))
log("Location categories found: " + str(sorted(df["Location"].dropna().unique())))

# 5b. Recompute Total Spent = Quantity * Price Per Unit wherever all three
#     numbers are present but inconsistent, and use it to backfill any ONE
#     missing value among Quantity / Price Per Unit / Total Spent when the
#     other two are known (cross-column imputation using the row's own logic).
mask_calc = df["Total Spent"].isna() & df["Quantity"].notna() & df["Price Per Unit"].notna()
df.loc[mask_calc, "Total Spent"] = df.loc[mask_calc, "Quantity"] * df.loc[mask_calc, "Price Per Unit"]
log(f"\nBackfilled 'Total Spent' from Quantity x Price for {mask_calc.sum()} rows")

mask_price = df["Price Per Unit"].isna() & df["Quantity"].notna() & df["Total Spent"].notna() & (df["Quantity"] != 0)
df.loc[mask_price, "Price Per Unit"] = df.loc[mask_price, "Total Spent"] / df.loc[mask_price, "Quantity"]
log(f"Backfilled 'Price Per Unit' from Total / Quantity for {mask_price.sum()} rows")

mask_qty = df["Quantity"].isna() & df["Price Per Unit"].notna() & df["Total Spent"].notna() & (df["Price Per Unit"] != 0)
df.loc[mask_qty, "Quantity"] = df.loc[mask_qty, "Total Spent"] / df.loc[mask_qty, "Price Per Unit"]
log(f"Backfilled 'Quantity' from Total / Price for {mask_qty.sum()} rows")

# 5c. Flag rows where Total Spent doesn't match Quantity * Price (after backfill)
mismatch = (
    df["Quantity"].notna() & df["Price Per Unit"].notna() & df["Total Spent"].notna() &
    (abs(df["Quantity"] * df["Price Per Unit"] - df["Total Spent"]) > 0.01)
)
log(f"\nRows where Total Spent still doesn't equal Quantity x Price after backfill: {mismatch.sum()}")
# Correct Total Spent to the calculated value in these cases (source of truth = qty*price)
df.loc[mismatch, "Total Spent"] = df.loc[mismatch, "Quantity"] * df.loc[mismatch, "Price Per Unit"]

# ------------------------------------------------------------------
# 6. HANDLE REMAINING MISSING VALUES
# ------------------------------------------------------------------
missing_before_fill = df.isna().sum()

# Categorical text columns -> label as "Unknown" (keeps the row, keeps info honest)
for col in ["Item", "Payment Method", "Location"]:
    df[col] = df[col].fillna("Unknown")

# Numeric columns with still-missing values -> leave as NaN (do NOT guess),
# but drop rows only if the row has no usable sales info at all
rows_before = len(df)
df = df.dropna(subset=["Transaction ID"])  # ID is mandatory / primary key
df = df.dropna(how="all", subset=["Quantity", "Price Per Unit", "Total Spent"])
rows_after = len(df)
log(f"\nDropped {rows_before - rows_after} rows that had NO usable Quantity/Price/Total data at all")

log("\nRemaining missing values after cleaning:")
log(df.isna().sum().to_string())

# ------------------------------------------------------------------
# 7. FINAL TOUCHES
# ------------------------------------------------------------------
df["Quantity"] = df["Quantity"].round().astype("Int64")
df["Price Per Unit"] = df["Price Per Unit"].round(2)
df["Total Spent"] = df["Total Spent"].round(2)
df = df.sort_values("Transaction Date", na_position="last").reset_index(drop=True)

log(f"\nFinal cleaned dataset shape: {df.shape}")

# ------------------------------------------------------------------
# 8. SAVE
# ------------------------------------------------------------------
df.to_csv(OUT_FILE, index=False)
with open(LOG_FILE, "w") as f:
    f.write("\n".join(log_lines))

log(f"\nSaved cleaned file to {OUT_FILE}")
log(f"Saved full log to {LOG_FILE}")
