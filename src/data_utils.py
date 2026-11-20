"""Shared data utilities and flexible OLA column-name detection."""
import re
import pandas as pd

ALIASES = {
    "booking_id": ["booking_id", "bookingid", "id"],
    "date": ["date", "booking_date", "ride_date"],
    "time": ["time", "booking_time", "ride_time"],
    "booking_status": ["booking_status", "status", "ride_status"],
    "customer_id": ["customer_id", "customerid", "cust_id"],
    "vehicle_type": ["vehicle_type", "vehicle", "car_type"],
    "pickup_location": ["pickup_location", "pickup", "source"],
    "drop_location": ["drop_location", "drop", "destination"],
    "booking_value": ["booking_value", "ride_fare", "fare", "amount", "price"],
    "payment_method": ["payment_method", "payment", "payment_type"],
    "ride_distance": ["ride_distance", "distance", "distance_km"],
    "driver_ratings": ["driver_ratings", "driver_rating", "driver_rate"],
    "customer_rating": ["customer_rating", "customer_ratings", "customer_rate"],
    "customer_cancellation_reason": [
        "reason_for_cancelling_by_customer", "customer_cancellation_reason",
        "cancellation_reason_customer", "customer_cancel_reason"
    ],
    "driver_cancellation_reason": [
        "driver_cancellation_reason", "reason_for_cancelling_by_driver",
        "cancellation_reason_driver", "driver_cancel_reason"
    ],
    "incomplete_ride_reason": [
        "incomplete_rides_reason", "incomplete_ride_reason", "incomplete_reason"
    ],
    "incomplete_rides": ["incomplete_rides", "incomplete_ride"],
    "cancelled_rides_by_customer": [
        "cancelled_rides_by_customer", "canceled_rides_by_customer",
        "customer_cancelled", "customer_canceled"
    ],
    "cancelled_rides_by_driver": [
        "cancelled_rides_by_driver", "canceled_rides_by_driver",
        "driver_cancelled", "driver_canceled"
    ],
    "v_tat": ["v_tat", "vehicle_tat", "vehicle_turnaround_time"],
    "c_tat": ["c_tat", "customer_tat", "customer_turnaround_time"],
}

def clean_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return re.sub(r"_+", "_", name).strip("_") or "unnamed_column"

def standardize_columns(df):
    out = df.copy()
    out.columns = [clean_name(c) for c in out.columns]
    # Rename common source variants to stable canonical names.
    reverse = {}
    for canonical, variants in ALIASES.items():
        for variant in variants:
            reverse[clean_name(variant)] = canonical
    rename = {c: reverse[c] for c in out.columns if c in reverse}
    # Avoid collisions when both an alias and canonical column exist.
    for old, new in list(rename.items()):
        if new in out.columns and old != new:
            rename.pop(old)
    return out.rename(columns=rename)

def find_best_sheet(excel_file):
    xls = pd.ExcelFile(excel_file)
    preferred = next((s for s in xls.sheet_names if s.strip().lower() == "july"), None)
    if preferred:
        return preferred
    best_sheet, best_rows = xls.sheet_names[0], -1
    for sheet in xls.sheet_names:
        try:
            n = len(pd.read_excel(excel_file, sheet_name=sheet, usecols=[0]))
            if n > best_rows:
                best_sheet, best_rows = sheet, n
        except Exception:
            continue
    return best_sheet

def prepare_bookings(df):
    df = standardize_columns(df)
    df = df.dropna(how="all").copy()
    if "booking_id" in df.columns:
        df["booking_id"] = df["booking_id"].astype("string").str.strip()
    for col in ["date"]:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            df[col] = parsed.dt.strftime("%Y-%m-%d")
    if "time" in df.columns:
        # Keep source time readable; normalize Excel time objects if present.
        df["time"] = df["time"].astype("string").str.strip()
    numeric_cols = [
        "booking_value", "ride_distance", "driver_ratings", "customer_rating",
        "v_tat", "c_tat"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    if "booking_status" in df.columns:
        df["booking_status"] = df["booking_status"].astype("string").str.strip()
    if "date" in df.columns and "time" in df.columns:
        df["booking_datetime"] = pd.to_datetime(
            df["date"].fillna("") + " " + df["time"].fillna(""),
            errors="coerce"
        )
        df["booking_hour"] = df["booking_datetime"].dt.hour
        df["booking_day"] = df["booking_datetime"].dt.day
        df["booking_weekday"] = df["booking_datetime"].dt.day_name()
    if "booking_status" in df.columns:
        # Use exact status values. A substring check for "complete" incorrectly
        # classifies "Incomplete" as a successful booking.
        status = df["booking_status"].fillna("").astype("string").str.strip().str.casefold()
        successful_statuses = {"success", "successful", "completed", "complete"}
        df["is_successful"] = status.isin(successful_statuses).astype(int)
        df["is_cancelled"] = status.str.contains(r"cancel(?:ed|led)?", regex=True, na=False).astype(int)
    if "booking_value" in df.columns and "is_successful" in df.columns:
        df["successful_booking_value"] = df["booking_value"].where(df["is_successful"].eq(1), 0)
    return df

def quality_report(df):
    rows = []
    for col in df.columns:
        rows.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "missing_percent": round(float(df[col].isna().mean() * 100), 2),
            "distinct_values": int(df[col].nunique(dropna=True)),
        })
    return pd.DataFrame(rows)
