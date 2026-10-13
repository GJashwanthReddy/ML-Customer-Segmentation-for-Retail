"""
RFM Feature Engineering and Statistical Analysis Module
Extracts Recency, Frequency, and Monetary features from clean transaction data.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def calculate_rfm(df_clean: pd.DataFrame, reference_date: pd.Timestamp = None) -> Tuple[pd.DataFrame, pd.Timestamp]:
    """
    Computes customer-level RFM features from transaction data.

    Parameters:
        df_clean: Cleaned transaction DataFrame containing CustomerID, InvoiceDate, InvoiceNo, TotalPrice.
        reference_date: Optional snapshot date. Defaults to max(InvoiceDate) + 1 day.

    Returns:
        (rfm_df, snapshot_date): RFM DataFrame indexed by CustomerID and the reference snapshot date.
    """
    if reference_date is None:
        # 1 day after the latest transaction ensures recency >= 1 day
        snapshot_date = df_clean["InvoiceDate"].max() + pd.Timedelta(days=1)
    else:
        snapshot_date = pd.to_datetime(reference_date)

    # Group by CustomerID
    rfm = df_clean.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda d: (snapshot_date - d.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("TotalPrice", "sum")
    ).reset_index()

    # Ensure numeric types
    rfm["Recency"] = rfm["Recency"].astype(int)
    rfm["Frequency"] = rfm["Frequency"].astype(int)
    rfm["Monetary"] = rfm["Monetary"].round(2)

    return rfm, snapshot_date


def get_rfm_summary_stats(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes comprehensive descriptive statistics and skewness for RFM features.
    """
    metrics = ["Recency", "Frequency", "Monetary"]
    stats = []

    for m in metrics:
        s = rfm_df[m]
        stats.append({
            "Metric": m,
            "Mean": round(s.mean(), 2),
            "Median": round(s.median(), 2),
            "Std Dev": round(s.std(), 2),
            "Min": round(s.min(), 2),
            "25th %": round(s.quantile(0.25), 2),
            "75th %": round(s.quantile(0.75), 2),
            "Max": round(s.max(), 2),
            "Skewness": round(s.skew(), 2)
        })

    return pd.DataFrame(stats)


def get_rfm_correlations(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Pearson correlation matrix between Recency, Frequency, and Monetary.
    """
    return rfm_df[["Recency", "Frequency", "Monetary"]].corr().round(3)
