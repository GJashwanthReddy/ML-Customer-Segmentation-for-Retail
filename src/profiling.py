"""
Customer Segment Profiling and Business Intelligence Module
Computes cluster-level aggregates, dynamically assigns behavioral personas,
and generates actionable retail marketing recommendations.
Guarantees distinct, non-duplicate persona assignments grounded in real RFM metrics.
"""

from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np


# Palette mapped consistently to cluster IDs
PALETTE_MAP = {
    0: "#10B981",  # Emerald Green
    1: "#3B82F6",  # Blue
    2: "#F59E0B",  # Amber / Orange
    3: "#8B5CF6",  # Purple
    4: "#EF4444",  # Coral Red
    5: "#06B6D4",  # Cyan
    6: "#EC4899",  # Pink
    7: "#64748B"   # Slate
}


def generate_cluster_profiles(rfm_df: pd.DataFrame, cluster_labels: np.ndarray) -> Tuple[pd.DataFrame, Dict[int, Dict[str, Any]]]:
    """
    Computes statistical profiles for each customer cluster:
    - Customer Count & Percentage Share
    - Recency (Mean, Median)
    - Frequency (Mean, Median)
    - Monetary (Mean, Median, Total Revenue, Revenue Share %)
    - Dynamically maps cluster traits to academic and retail personas with 100% distinct names.

    Returns:
        (profile_summary_df, persona_details_dict)
    """
    df = rfm_df.copy()
    df["Cluster"] = cluster_labels
    total_customers = len(df)
    total_revenue = df["Monetary"].sum()

    grouped = df.groupby("Cluster")
    
    cluster_records = []
    for c_id, group in grouped:
        c_count = len(group)
        c_pct = (c_count / total_customers) * 100
        c_revenue = group["Monetary"].sum()
        c_rev_pct = (c_revenue / total_revenue) * 100 if total_revenue > 0 else 0

        cluster_records.append({
            "Cluster": int(c_id),
            "Customer_Count": c_count,
            "Customer_Share_Pct": round(c_pct, 1),
            "Recency_Mean": round(group["Recency"].mean(), 1),
            "Recency_Median": round(group["Recency"].median(), 1),
            "Frequency_Mean": round(group["Frequency"].mean(), 1),
            "Frequency_Median": round(group["Frequency"].median(), 1),
            "Monetary_Mean": round(group["Monetary"].mean(), 1),
            "Monetary_Median": round(group["Monetary"].median(), 1),
            "Total_Revenue": round(c_revenue, 2),
            "Revenue_Share_Pct": round(c_rev_pct, 1)
        })

    profile_df = pd.DataFrame(cluster_records)
    k = len(profile_df)

    # Calculate Relative Ranks
    # Recency: 1 = lowest recency (most recent buyers)
    profile_df["r_rank"] = profile_df["Recency_Mean"].rank(ascending=True)
    # Frequency: 1 = highest frequency (most orders)
    profile_df["f_rank"] = profile_df["Frequency_Mean"].rank(ascending=False)
    # Monetary: 1 = highest spend (most gross revenue)
    profile_df["m_rank"] = profile_df["Monetary_Mean"].rank(ascending=False)

    # Composite Value Score (lower score = higher overall business value)
    profile_df["val_score"] = (profile_df["m_rank"] * 0.45) + (profile_df["f_rank"] * 0.35) + (profile_df["r_rank"] * 0.20)

    # Sort clusters by composite business value
    sorted_df = profile_df.sort_values("val_score").copy()

    personas: Dict[int, Dict[str, Any]] = {}
    used_categories = set()

    # 1. Top cluster by composite value is ALWAYS the Champions
    top_c = int(sorted_df.iloc[0]["Cluster"])
    personas[top_c] = {
        "name": "Champions (VIP High-Spenders)",
        "badge": "VIP Champion",
        "priority": "Critical - Maximize Retention",
        "color": PALETTE_MAP.get(top_c, "#10B981"),
        "description": "Highest lifetime expenditure and order frequency with recent transactions. Core revenue driver.",
        "strategy": "Exclusive loyalty rewards, early product previews, personal concierge, brand ambassador gifts."
    }
    used_categories.add("Champions")

    # 2. Cluster with worst recency (highest days since purchase) is ALWAYS Hibernating / Lost
    rem = sorted_df[sorted_df["Cluster"] != top_c].copy()
    worst_r_c = int(rem.sort_values("Recency_Mean", ascending=False).iloc[0]["Cluster"])
    personas[worst_r_c] = {
        "name": "Hibernating / Lost Customers",
        "badge": "Dormant",
        "priority": "Low Cost Automation",
        "color": PALETTE_MAP.get(worst_r_c, "#EF4444"),
        "description": "Longest period of inactivity, minimal order frequency, and low monetary value.",
        "strategy": "Automated low-cost email win-back drip, seasonal clearance promotions, unsubscribe list hygiene."
    }
    used_categories.add("Hibernating")

    # 3. For remaining clusters, assign distinct personas according to exact behavioral position
    rem = rem[rem["Cluster"] != worst_r_c].copy()

    for _, r_row in rem.iterrows():
        c_id = int(r_row["Cluster"])
        r = r_row["Recency_Mean"]
        f = r_row["Frequency_Mean"]
        m = r_row["Monetary_Mean"]
        r_rank = r_row["r_rank"]
        m_rank = r_row["m_rank"]
        f_rank = r_row["f_rank"]

        # High spend and repeat purchases -> Loyal High-Value
        if "Loyal" not in used_categories and (m_rank <= 2 or f_rank <= 2):
            personas[c_id] = {
                "name": "Loyal High-Value Customers",
                "badge": "Loyal",
                "priority": "High - Basket Expansion",
                "color": PALETTE_MAP.get(c_id, "#4F46E5"),
                "description": "Consistent regular shoppers with dependable repeat purchases and above-average spending.",
                "strategy": "Upsell premium bundles, point multipliers, category cross-sell recommendations."
            }
            used_categories.add("Loyal")
        # Inactivity higher than median -> At-Risk
        elif "At-Risk" not in used_categories and r > profile_df["Recency_Mean"].median():
            personas[c_id] = {
                "name": "At-Risk Customers (Needs Attention)",
                "badge": "At Risk",
                "priority": "Urgent - Churn Prevention",
                "color": PALETTE_MAP.get(c_id, "#F59E0B"),
                "description": "Previously valuable shoppers who have not made a purchase recently. High danger of defection.",
                "strategy": "Personalized 'We miss you' incentives, targeted reactivation discounts, feedback surveys."
            }
            used_categories.add("At-Risk")
        # Recent but low frequency -> Recent Explorers
        elif "New" not in used_categories and f <= profile_df["Frequency_Mean"].median() and r <= profile_df["Recency_Mean"].median():
            personas[c_id] = {
                "name": "Recent Explorers (New Shoppers)",
                "badge": "New Shopper",
                "priority": "Nurture - Build Frequency",
                "color": PALETTE_MAP.get(c_id, "#06B6D4"),
                "description": "Transacted recently but have low lifetime transaction counts and initial order values.",
                "strategy": "Welcome onboarding sequence, educational product recommendations, second-purchase discount vouchers."
            }
            used_categories.add("New")
        # Moderate frequency and spend with recent activity -> Potential Loyalists
        elif "Potential" not in used_categories:
            personas[c_id] = {
                "name": "Potential Loyalists (High Momentum)",
                "badge": "Promising",
                "priority": "Growth - Frequency Acceleration",
                "color": PALETTE_MAP.get(c_id, "#3B82F6"),
                "description": "Recent buyers with moderate order frequency and accelerating expenditure.",
                "strategy": "Membership program invitations, bundle promotions, limited-time category discount incentives."
            }
            used_categories.add("Potential")
        else:
            personas[c_id] = {
                "name": f"Segment {c_id}: Steady Buyers",
                "badge": "Steady",
                "priority": "Standard Engagement",
                "color": PALETTE_MAP.get(c_id, "#8B5CF6"),
                "description": "Active customer cohort with steady transactional behavior and balanced repeat habits.",
                "strategy": "Standard promotional messaging, category spotlights, seasonal catalogs."
            }

    # Attach persona details to summary DataFrame
    profile_df["Persona"] = profile_df["Cluster"].apply(lambda c: personas[c]["name"])
    profile_df["Badge"] = profile_df["Cluster"].apply(lambda c: personas[c]["badge"])
    profile_df["Marketing_Priority"] = profile_df["Cluster"].apply(lambda c: personas[c]["priority"])
    profile_df["Color"] = profile_df["Cluster"].apply(lambda c: personas[c]["color"])

    # Attach full metrics and explicit RFM justification to personas dictionary
    for _, row in profile_df.iterrows():
        c_id = int(row["Cluster"])
        r_val = row["Recency_Mean"]
        f_val = row["Frequency_Mean"]
        m_val = row["Monetary_Mean"]
        r_rk = int(row["r_rank"])
        f_rk = int(row["f_rank"])
        m_rk = int(row["m_rank"])

        justification = (
            f"Recency: {r_val}d (Rank {r_rk}/{k}) · "
            f"Frequency: {f_val} orders (Rank {f_rk}/{k}) · "
            f"Spend: £{m_val:,.1f} (Rank {m_rk}/{k})"
        )
        personas[c_id]["justification"] = justification
        personas[c_id]["r_rank"] = r_rk
        personas[c_id]["f_rank"] = f_rk
        personas[c_id]["m_rank"] = m_rk

        personas[c_id]["metrics"] = {
            "customers": int(row["Customer_Count"]),
            "share_pct": row["Customer_Share_Pct"],
            "recency_mean": r_val,
            "frequency_mean": f_val,
            "monetary_mean": m_val,
            "total_revenue": row["Total_Revenue"],
            "revenue_pct": row["Revenue_Share_Pct"],
            "r_rank": r_rk,
            "f_rank": f_rk,
            "m_rank": m_rk
        }

    profile_df["Justification"] = profile_df["Cluster"].apply(lambda c: personas[c]["justification"])

    # Drop helper ranking columns
    profile_df = profile_df.drop(columns=["r_rank", "f_rank", "m_rank", "val_score"])

    return profile_df, personas


def get_customer_lookup_info(
    customer_id: int,
    rfm_df: pd.DataFrame,
    cluster_labels: np.ndarray,
    personas: Dict[int, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Looks up individual customer record and returns their RFM and cluster persona info.
    """
    df = rfm_df.copy()
    df["Cluster"] = cluster_labels
    match = df[df["CustomerID"] == customer_id]
    
    if match.empty:
        return {"found": False, "customer_id": customer_id}
    
    row = match.iloc[0]
    c_id = int(row["Cluster"])
    persona_info = personas.get(c_id, {})

    return {
        "found": True,
        "customer_id": customer_id,
        "recency": int(row["Recency"]),
        "frequency": int(row["Frequency"]),
        "monetary": float(row["Monetary"]),
        "cluster": c_id,
        "persona_name": persona_info.get("name", f"Cluster {c_id}"),
        "badge": persona_info.get("badge", "Customer"),
        "color": persona_info.get("color", "#2563EB"),
        "description": persona_info.get("description", ""),
        "recommended_strategy": persona_info.get("strategy", ""),
        "priority": persona_info.get("priority", "")
    }
