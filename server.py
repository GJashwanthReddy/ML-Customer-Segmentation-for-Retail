"""
Customer Intelligence - Web Application Server
Production Flask backend serving REST API endpoints and modern commercial frontend.
Uses 100% genuine Python ML pipeline from src/.
"""

import os
import sys
import io
from flask import Flask, jsonify, request, render_template, send_file, Response
import pandas as pd
import numpy as np

# Ensure local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_raw_data
from src.data_preprocessing import clean_transactions
from src.rfm_analysis import calculate_rfm, get_rfm_summary_stats, get_rfm_correlations
from src.clustering import (
    preprocess_rfm_for_ml,
    evaluate_k_range,
    fit_kmeans,
    fit_hierarchical,
    compute_pca_2d
)
from src.evaluation import compare_clustering_algorithms, compute_cluster_cross_tab
from src.profiling import generate_cluster_profiles, get_customer_lookup_info

app = Flask(__name__, template_folder="templates", static_folder="static")

# -------------------------------------------------------------
# Global In-Memory Pipeline State
# -------------------------------------------------------------
STATE = {
    "df_raw": None,
    "df_clean": None,
    "audit_stats": None,
    "rfm_df": None,
    "snapshot_date": None,
    "scaled_matrix": None,
    "scaled_df": None,
    "scaler": None,
    "eval_df": None,
    "selected_k": 6,
    "kmeans_model": None,
    "kmeans_labels": None,
    "profile_df": None,
    "personas": None,
    "pca_coords": None,
    "pca_model": None,
    "agg_model": None,
    "agg_labels": None,
    "comp_df": None,
    "cross_tab": None
}


def initialize_pipeline(uploaded_file=None):
    """Executes the complete unsupervised ML pipeline and caches in STATE."""
    print("Initializing Machine Learning Pipeline...")
    if uploaded_file is not None:
        df_raw = load_raw_data(uploaded_file)
    else:
        df_raw = load_raw_data()

    df_clean, audit_stats = clean_transactions(df_raw)
    rfm_df, snapshot_date = calculate_rfm(df_clean)
    scaled_matrix, scaled_df, scaler = preprocess_rfm_for_ml(rfm_df)
    eval_df = evaluate_k_range(scaled_matrix, k_range=range(2, 9))

    k = 6
    kmeans_model, kmeans_labels = fit_kmeans(scaled_matrix, k=k)
    profile_df, personas = generate_cluster_profiles(rfm_df, kmeans_labels)
    pca_coords, pca_model = compute_pca_2d(scaled_matrix)

    agg_model, agg_labels = fit_hierarchical(scaled_matrix, k=k)
    comp_df = compare_clustering_algorithms(scaled_matrix, kmeans_labels, agg_labels, k=k)
    cross_tab = compute_cluster_cross_tab(kmeans_labels, agg_labels)

    STATE["df_raw"] = df_raw
    STATE["df_clean"] = df_clean
    STATE["audit_stats"] = audit_stats
    STATE["rfm_df"] = rfm_df
    STATE["snapshot_date"] = snapshot_date
    STATE["scaled_matrix"] = scaled_matrix
    STATE["scaled_df"] = scaled_df
    STATE["scaler"] = scaler
    STATE["eval_df"] = eval_df
    STATE["selected_k"] = k
    STATE["kmeans_model"] = kmeans_model
    STATE["kmeans_labels"] = kmeans_labels
    STATE["profile_df"] = profile_df
    STATE["personas"] = personas
    STATE["pca_coords"] = pca_coords
    STATE["pca_model"] = pca_model
    STATE["agg_model"] = agg_model
    STATE["agg_labels"] = agg_labels
    STATE["comp_df"] = comp_df
    STATE["cross_tab"] = cross_tab
    print("Pipeline ready.")


# Initialize at startup
initialize_pipeline()


# -------------------------------------------------------------
# Frontend Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------
@app.route("/api/overview")
def api_overview():
    audit = STATE["audit_stats"]
    profile_df = STATE["profile_df"]
    personas = STATE["personas"]
    eval_df = STATE["eval_df"]
    k = STATE["selected_k"]

    sil_score = float(eval_df.loc[eval_df["K"] == k, "Silhouette_Score"].values[0])
    total_rev = float(audit["total_revenue"])
    rev_formatted = f"£{total_rev / 1_000_000:.2f}M" if total_rev >= 1_000_000 else f"£{total_rev:,.0f}"

    top_rev_cluster = profile_df.loc[profile_df["Revenue_Share_Pct"].idxmax()]
    top_rev_persona = top_rev_cluster["Persona"].split("(")[0].strip()
    top_rev_share = float(top_rev_cluster["Customer_Share_Pct"])
    top_rev_pct = float(top_rev_cluster["Revenue_Share_Pct"])
    top_rev_val = float(top_rev_cluster["Total_Revenue"])

    top_segments = []
    for c_id, p_info in list(personas.items())[:4]:
        m = p_info["metrics"]
        top_segments.append({
            "cluster": c_id,
            "name": p_info["name"].split("(")[0].strip(),
            "badge": p_info["badge"],
            "description": p_info["description"],
            "customers": int(m["customers"]),
            "share_pct": float(m["share_pct"]),
            "revenue_pct": float(m["revenue_pct"]),
            "color": p_info["color"]
        })

    return jsonify({
        "kpis": {
            "customers": int(audit["unique_customers"]),
            "transactions": int(audit["final_rows"]),
            "revenue": total_rev,
            "revenue_formatted": rev_formatted,
            "segments": k,
            "silhouette": round(sil_score, 3)
        },
        "insight": {
            "persona": top_rev_persona,
            "share_pct": top_rev_share,
            "revenue_pct": top_rev_pct,
            "revenue_val": f"£{top_rev_val:,.0f}",
            "text": f"{top_rev_persona} represent {top_rev_share}% of customers but contribute {top_rev_pct}% of total retail revenue (£{top_rev_val:,.0f}). Prioritizing retention for this high-value cohort protects the core commercial baseline."
        },
        "top_segments": top_segments
    })


@app.route("/api/customers")
def api_customers():
    rfm_df = STATE["rfm_df"]
    labels = STATE["kmeans_labels"]
    personas = STATE["personas"]

    cust_df = rfm_df.copy()
    cust_df["Cluster"] = labels
    cust_df["Segment"] = cust_df["Cluster"].apply(lambda c: personas[c]["name"])

    # Query Filters
    search = request.args.get("search", "").strip()
    segment = request.args.get("segment", "").strip()
    recency_max = request.args.get("recency_max", type=int)
    monetary_min = request.args.get("monetary_min", type=float)
    page = max(1, request.args.get("page", 1, type=int))
    limit = max(10, min(100, request.args.get("limit", 25, type=int)))

    filtered = cust_df
    if search:
        if search.isdigit():
            filtered = filtered[filtered["CustomerID"] == int(search)]
        else:
            filtered = filtered[filtered["Segment"].str.contains(search, case=False, na=False)]

    if segment and segment != "All":
        filtered = filtered[filtered["Segment"] == segment]

    if recency_max is not None:
        filtered = filtered[filtered["Recency"] <= recency_max]

    if monetary_min is not None:
        filtered = filtered[filtered["Monetary"] >= monetary_min]

    total_records = len(filtered)
    start_idx = (page - 1) * limit
    page_data = filtered.iloc[start_idx:start_idx + limit]

    rows = []
    for _, row in page_data.iterrows():
        c_id = int(row["Cluster"])
        rows.append({
            "customer_id": int(row["CustomerID"]),
            "segment": personas[c_id]["name"].split("(")[0].strip(),
            "cluster": f"C{c_id}",
            "recency": int(row["Recency"]),
            "frequency": int(row["Frequency"]),
            "monetary": round(float(row["Monetary"]), 2),
            "color": personas[c_id]["color"]
        })

    distinct_segments = sorted([p["name"] for p in personas.values()])

    return jsonify({
        "customers": rows,
        "total": total_records,
        "page": page,
        "limit": limit,
        "max_pages": int(np.ceil(total_records / limit)) if total_records > 0 else 1,
        "segments": distinct_segments,
        "max_recency": int(rfm_df["Recency"].max())
    })


@app.route("/api/customer/<int:customer_id>")
def api_customer_profile(customer_id):
    rfm_df = STATE["rfm_df"]
    labels = STATE["kmeans_labels"]
    personas = STATE["personas"]

    info = get_customer_lookup_info(customer_id, rfm_df, labels, personas)
    return jsonify(info)


@app.route("/api/segments")
def api_segments():
    personas = STATE["personas"]
    profile_df = STATE["profile_df"]

    segments = []
    for c_id, p in personas.items():
        m = p["metrics"]
        segments.append({
            "id": c_id,
            "name": p["name"].split("(")[0].strip(),
            "full_name": p["name"],
            "badge": p["badge"],
            "color": p["color"],
            "description": p["description"],
            "strategy": p["strategy"],
            "justification": p["justification"],
            "customers": int(m["customers"]),
            "share_pct": float(m["share_pct"]),
            "revenue_pct": float(m["revenue_pct"]),
            "total_revenue": round(float(m["total_revenue"]), 2),
            "recency_mean": float(m["recency_mean"]),
            "frequency_mean": float(m["frequency_mean"]),
            "monetary_mean": float(m["monetary_mean"])
        })

    baseline = {
        "recency_avg": round(float(profile_df["Recency_Mean"].mean()), 1),
        "frequency_avg": round(float(profile_df["Frequency_Mean"].mean()), 1),
        "monetary_avg": round(float(profile_df["Monetary_Mean"].mean()), 1)
    }

    return jsonify({
        "segments": segments,
        "baseline": baseline
    })


@app.route("/api/analytics")
def api_analytics():
    rfm_df = STATE["rfm_df"]
    eval_df = STATE["eval_df"]
    profile_df = STATE["profile_df"]
    personas = STATE["personas"]
    comp_df = STATE["comp_df"]
    cross_tab = STATE["cross_tab"]
    pca_coords = STATE["pca_coords"]
    pca_model = STATE["pca_model"]
    labels = STATE["kmeans_labels"]

    # 1. RFM Distributions (sampled for web chart performance)
    rfm_sub = rfm_df.sample(min(2000, len(rfm_df)), random_state=42)
    rfm_distributions = {
        "recency": [int(x) for x in rfm_sub["Recency"].tolist()],
        "frequency": [int(x) for x in rfm_sub["Frequency"].tolist() if x <= 50],
        "monetary": [round(float(x), 2) for x in rfm_sub["Monetary"].tolist() if x <= 8000]
    }

    # Summary Statistics
    rfm_stats = get_rfm_summary_stats(rfm_df).to_dict(orient="records")

    # Correlation Matrix
    corr_df = get_rfm_correlations(rfm_df)
    corr_data = {
        "columns": list(corr_df.columns),
        "z": corr_df.values.round(3).tolist()
    }

    # 2. Cluster Evaluation
    k_eval = []
    for _, row in eval_df.iterrows():
        k_eval.append({
            "k": int(row["K"]),
            "inertia": round(float(row["Inertia"]), 2),
            "silhouette": round(float(row["Silhouette_Score"]), 4),
            "selected": int(row["K"]) == STATE["selected_k"]
        })

    # 3. K-Means Volume
    km_profiles = []
    for _, row in profile_df.iterrows():
        c_id = int(row["Cluster"])
        km_profiles.append({
            "cluster": c_id,
            "name": row["Persona"].split("(")[0].strip(),
            "customers": int(row["Customer_Count"]),
            "share_pct": float(row["Customer_Share_Pct"]),
            "revenue_pct": float(row["Revenue_Share_Pct"]),
            "recency_mean": float(row["Recency_Mean"]),
            "frequency_mean": float(row["Frequency_Mean"]),
            "monetary_mean": float(row["Monetary_Mean"]),
            "color": personas[c_id]["color"]
        })

    # 4. Hierarchical Comparison
    comp_metrics = comp_df.to_dict(orient="records")
    cross_tab_data = {
        "columns": [f"H{c}" for c in cross_tab.columns],
        "rows": [f"K{r}" for r in cross_tab.index],
        "values": cross_tab.values.tolist()
    }

    # 5. PCA Coordinates
    # Sample down to 1500 for responsive web rendering
    pca_sample_idx = np.random.RandomState(42).choice(len(pca_coords), size=min(1500, len(pca_coords)), replace=False)
    pca_points = []
    for idx in pca_sample_idx:
        c_id = int(labels[idx])
        pca_points.append({
            "x": round(float(pca_coords[idx, 0]), 3),
            "y": round(float(pca_coords[idx, 1]), 3),
            "cluster": c_id,
            "segment": personas[c_id]["name"].split("(")[0].strip(),
            "id": int(rfm_df.iloc[idx]["CustomerID"]),
            "r": int(rfm_df.iloc[idx]["Recency"]),
            "f": int(rfm_df.iloc[idx]["Frequency"]),
            "m": round(float(rfm_df.iloc[idx]["Monetary"]), 2),
            "color": personas[c_id]["color"]
        })

    var1 = round(float(pca_model.explained_variance_ratio_[0]) * 100, 1)
    var2 = round(float(pca_model.explained_variance_ratio_[1]) * 100, 1)

    return jsonify({
        "rfm": {
            "distributions": rfm_distributions,
            "summary_stats": rfm_stats,
            "correlation": corr_data
        },
        "evaluation": {
            "k_eval": k_eval,
            "selected_k": STATE["selected_k"]
        },
        "kmeans": km_profiles,
        "comparison": {
            "metrics": comp_metrics,
            "cross_tab": cross_tab_data
        },
        "pca": {
            "points": pca_points,
            "explained_variance": {
                "pc1": var1,
                "pc2": var2,
                "total": round(var1 + var2, 1)
            }
        }
    })


@app.route("/api/data")
def api_data():
    audit = STATE["audit_stats"]
    df_clean = STATE["df_clean"]

    # Preview first 15 clean rows
    preview_df = df_clean[["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "TotalPrice", "CustomerID", "Country"]].head(15).copy()
    preview_df["InvoiceDate"] = preview_df["InvoiceDate"].astype(str)
    preview_rows = preview_df.to_dict(orient="records")

    # Preprocessing Hygiene Audit Trail
    audit_table = [
        {"stage": "1. Raw Records Ingested", "count": f"{audit['initial_rows']:,}", "desc": "Original transaction records from retail database"},
        {"stage": "2. Missing CustomerIDs Dropped", "count": f"-{audit['initial_missing_customer']:,}", "desc": "Guest purchases cannot be attributed to individual shopper RFM accounts"},
        {"stage": "3. Cancelled Invoices ('C*')", "count": f"-{audit['cancelled_count']:,}", "desc": "Return orders excluded from gross spending calculations"},
        {"stage": "4. Non-Positive Qty / Price", "count": f"-{audit['invalid_qty_count'] + audit['invalid_price_count']:,}", "desc": "Damaged items, system tests, and accounting adjustments"},
        {"stage": "5. Duplicate Rows Filtered", "count": f"-{audit['duplicate_count']:,}", "desc": "Redundant identical transaction logs removed"},
        {"stage": "6. Clean Production Records", "count": f"{audit['final_rows']:,}", "desc": f"{audit['unique_customers']:,} unique customers spanning {audit['date_min'].strftime('%Y-%m-%d')} to {audit['date_max'].strftime('%Y-%m-%d')}"}
    ]

    # Numerical Column Statistics
    desc_df = df_clean[["Quantity", "UnitPrice", "TotalPrice"]].describe().T[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]].reset_index()
    desc_df = desc_df.rename(columns={"index": "column"}).round(2)
    numeric_stats = desc_df.to_dict(orient="records")

    return jsonify({
        "status": {
            "initial_rows": audit["initial_rows"],
            "final_rows": audit["final_rows"],
            "retention_rate_pct": audit["retention_rate_pct"],
            "unique_customers": audit["unique_customers"],
            "unique_invoices": audit["unique_invoices"]
        },
        "preview": preview_rows,
        "audit_table": audit_table,
        "numeric_stats": numeric_stats
    })


@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        initialize_pipeline(file)
        return jsonify({
            "success": True,
            "message": f"Successfully loaded {STATE['audit_stats']['final_rows']:,} records for {STATE['audit_stats']['unique_customers']:,} customers."
        })
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route("/api/export-csv")
def api_export_csv():
    rfm_df = STATE["rfm_df"]
    labels = STATE["kmeans_labels"]
    personas = STATE["personas"]

    export_df = rfm_df.copy()
    export_df["Cluster"] = labels
    export_df["Segment"] = export_df["Cluster"].apply(lambda c: personas[c]["name"])
    export_df["Cluster_Code"] = export_df["Cluster"].apply(lambda c: f"C{c}")

    csv_data = export_df.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=retail_customers_k{STATE['selected_k']}.csv"}
    )


if __name__ == "__main__":
    print("Starting Retail Customer Intelligence Server on http://localhost:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=False)
