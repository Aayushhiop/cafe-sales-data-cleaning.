# Dirty Cafe Sales — Data Cleaning Project

## Dataset
**Source:** [Dirty Cafe Sales](https://www.kaggle.com/datasets/ahmedmohamed2003/cafe-sales-dirty-data-for-cleaning-training) (Kaggle, public dataset)
A synthetic cafe point-of-sale dataset (10,000 transactions, 8 columns) deliberately generated with common real-world data-quality problems, making it a good sandbox for practicing cleaning.

**Columns:** `Transaction ID`, `Item`, `Quantity`, `Price Per Unit`, `Total Spent`, `Payment Method`, `Location`, `Transaction Date`

## Files in this repo
| File | Description |
|---|---|
| `dirty_cafe_sales.csv` | Original raw dataset |
| `clean_cafe_sales.py` | Python (pandas) script that performs all cleaning steps |
| `cleaned_cafe_sales.csv` | Final cleaned dataset |
| `cleaning_log.txt` | Auto-generated log with full before/after counts from the last run |

## Issues found in the raw data

1. **Inconsistent missing-value markers** — "missing" data was represented three different ways: a true empty cell, the literal text `"ERROR"`, and the literal text `"UNKNOWN"`. Pandas only recognizes real empty cells as NaN by default, so the other two were invisible to standard missing-value checks until standardized.
   - `Payment Method`: 2,579 blank + 306 "ERROR" + 293 "UNKNOWN" = 3,178 missing
   - `Location`: 3,265 blank + 358 "ERROR" + 338 "UNKNOWN" = 3,961 missing
   - `Item`: 333 blank + 292 "ERROR" + 344 "UNKNOWN" = 969 missing
   - `Quantity`, `Price Per Unit`, `Total Spent`, `Transaction Date` also had smaller amounts of missing data (roughly 460–530 rows each)

2. **Incorrect data types** — every column was read in as plain text (object/string), including numeric columns (`Quantity`, `Price Per Unit`, `Total Spent`) and the date column (`Transaction Date`), because the placeholder strings `"ERROR"`/`"UNKNOWN"` mixed in with the numbers forced pandas to treat the whole column as text.

3. **Duplicate records** — checked for both full-row duplicates and duplicate `Transaction ID`s. None were found in this dataset, but the check is included in the script for reproducibility on other data.

4. **Inconsistent / invalid values**
   - Numeric fields (`Quantity`, `Price Per Unit`, `Total Spent`) sometimes disagreed with each other (e.g. `Total Spent ≠ Quantity × Price Per Unit`).
   - Categorical text fields (`Item`, `Payment Method`, `Location`) had stray whitespace and the "ERROR"/"UNKNOWN" placeholders mixed into otherwise clean category lists.

## Cleaning steps performed (see `clean_cafe_sales.py`)

1. Loaded the file with every column as text first, so no information was lost/misread on import.
2. Replaced all placeholder values (`"ERROR"`, `"UNKNOWN"`, blank strings) with proper `NaN` across the whole dataset.
3. Checked for and removed full-row duplicates and duplicate `Transaction ID`s (0 found).
4. Converted `Quantity`, `Price Per Unit`, `Total Spent` to numeric types and `Transaction Date` to a proper datetime type.
5. Trimmed whitespace on text columns.
6. **Cross-column repair:** wherever exactly one of `Quantity` / `Price Per Unit` / `Total Spent` was missing but the other two were known, recalculated the missing value using `Total = Quantity × Price`. This recovered ~1,400 values without guessing.
7. Recomputed `Total Spent` for any row where the three numbers didn't agree, using `Quantity × Price Per Unit` as the source of truth.
8. For categorical columns (`Item`, `Payment Method`, `Location`) that were still missing after all the above, filled with the explicit label `"Unknown"` rather than guessing a category — this preserves the row for analysis (e.g. total revenue) while being honest that the category is not known.
9. Left genuinely unrecoverable numeric/date values as `NaN` (about 0.4% of rows) rather than inventing numbers — these rows are still usable for any analysis that doesn't depend on that specific field.
10. Rounded `Quantity` to whole numbers and prices to 2 decimal places, sorted by `Transaction Date`.

## Result

| | Before | After |
|---|---|---|
| Rows | 10,000 | 10,000 |
| Item categories | 11 (incl. "ERROR"/"UNKNOWN"/blank) | 9 (8 real items + "Unknown") |
| Payment Method categories | 6 (incl. "ERROR"/"UNKNOWN"/blank) | 4 (3 real methods + "Unknown") |
| Location categories | 5 (incl. "ERROR"/"UNKNOWN"/blank) | 3 (2 real locations + "Unknown") |
| Numeric columns as text | Yes | No — proper int/float/datetime |
| Rows with mismatched Qty×Price≠Total | 100s | 0 |

No rows were dropped — every transaction ID is preserved; only genuinely unrecoverable individual fields remain blank, clearly distinguishable from valid data.

## How to reproduce
```bash
pip install pandas
python clean_cafe_sales.py
```
This reads `dirty_cafe_sales.csv` and writes `cleaned_cafe_sales.csv` + `cleaning_log.txt`.
