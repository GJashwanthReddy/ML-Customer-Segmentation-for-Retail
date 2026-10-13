"""
Data Preprocessing Pipeline
Cleans and validates the raw retail transaction dataset for RFM analysis and ML.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def clean_transactions(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw retail transaction data according to academic and industry best practices:
    1. Records initial dataset dimensions and missing value statistics.
    2. Drops records with missing CustomerID (guest purchases cannot be segmented).
    3. Converts CustomerID to integer format.
    4. Converts InvoiceDate to datetime format.
    5. Identifies and removes cancelled invoices (InvoiceNo starting with 'C').
    6. Filters out non-positive quantities (Quantity <= 0) and prices (UnitPrice <= 0).
    7. Computes TotalPrice = Quantity * UnitPrice.
    8. Removes duplicate records.
    9. Gathers audit metrics.

    Returns:
        (df_clean, audit_stats): Tuple of cleaned DataFrame and audit dictionary.
    """
    df = df_raw.copy()
    initial_rows = len(df)
    initial_missing_customer = int(df["CustomerID"].isna().sum())
    missing_by_col = df.isna().sum().to_dict()

    # 1. Drop missing CustomerID
    df = df.dropna(subset=["CustomerID"])
    rows_after_customer_drop = len(df)

    # Convert CustomerID to integer
    df["CustomerID"] = df["CustomerID"].astype(int)

    # 2. Convert InvoiceDate to datetime
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # 3. Identify and remove cancelled transactions (InvoiceNo starting with 'C')
    is_cancelled = df["InvoiceNo"].astype(str).str.upper().str.startswith("C")
    cancelled_count = int(is_cancelled.sum())
    df = df[~is_cancelled]
    rows_after_cancel_drop = len(df)

    # 4. Filter non-positive quantities and prices
    invalid_qty = (df["Quantity"] <= 0).sum()
    invalid_price = (df["UnitPrice"] <= 0).sum()
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    rows_after_val_filter = len(df)

    # 5. Compute transaction total
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

    # 6. Check and remove duplicate rows
    duplicate_count = int(df.duplicated().sum())
    df = df.drop_duplicates()
    final_rows = len(df)

    # 7. Calculate aggregate statistics
    unique_customers = int(df["CustomerID"].nunique())
    unique_invoices = int(df["InvoiceNo"].nunique())
    total_revenue = float(df["TotalPrice"].sum())
    date_min = df["InvoiceDate"].min()
    date_max = df["InvoiceDate"].max()

    audit_stats = {
        "initial_rows": initial_rows,
        "initial_missing_customer": initial_missing_customer,
        "missing_by_col": missing_by_col,
        "rows_after_customer_drop": rows_after_customer_drop,
        "cancelled_count": cancelled_count,
        "invalid_qty_count": int(invalid_qty),
        "invalid_price_count": int(invalid_price),
        "duplicate_count": duplicate_count,
        "final_rows": final_rows,
        "unique_customers": unique_customers,
        "unique_invoices": unique_invoices,
        "total_revenue": total_revenue,
        "date_min": date_min,
        "date_max": date_max,
        "retention_rate_pct": round((final_rows / initial_rows) * 100, 2)
    }

    return df, audit_stats
