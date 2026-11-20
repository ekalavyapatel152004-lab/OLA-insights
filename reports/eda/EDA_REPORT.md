# OLA Ride Insights — EDA Report

- Curated booking records analysed: **103,024**
- Duplicate booking IDs found in curated table: **0**
- Successful bookings (ETL success flag): **63,967 (62.1%)**
- Cancelled bookings (ETL cancellation flag): **28,933 (28.1%)**
- Columns analysed: **27**

## Data quality notes

- Columns with missing values: **9 of 27**.
- Highest-missingness field: **incomplete_ride_reason (96.19%)**.
- IQR outliers are flagged in `outlier_summary.csv`; they are not automatically deleted.
- Missing payment method values are retained as missing / Not recorded, not guessed.

## Key outputs

- `missing_values_summary.csv` — missingness and distinct-value profile.
- `descriptive_statistics.csv` — descriptive statistics.
- `booking_status_summary.csv` — booking-status counts.
- `outlier_summary.csv` — IQR-based outlier flags.
- `charts/` — EDA chart pack (PNG).

## Interpretation caution

Revenue totals in this report use successful bookings only. Do not interpret missing payment methods as a payment category, and validate business definitions before presenting conclusions.