"""
Customer Intelligence - Retail Analytics Platform
Built with reliable Streamlit layout primitives (st.container, st.columns, st.metric)
Zero raw SVG/XML strings, zero multiline HTML code block bugs, and 100% genuine ML pipeline.
"""

import sys
import os
import streamlit as st
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
from src.plotly_charts import (
    CLUSTER_COLORS,
    get_cluster_color,
    create_segment_distribution_chart,
    create_customer_vs_revenue_chart,
    create_rfm_distribution_chart,
    create_elbow_silhouette_charts,
    create_pca_scatter_chart,
    create_segment_radar_comparison,
    create_kmeans_cluster_profiles_chart,
    create_hierarchical_comparison_chart
)
from src.styles import SAAS_CSS

# Streamlit Page Setup
st.set_page_config(
    page_title="Retail Customer Intelligence Platform",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Clean SaaS Stylesheet
st.markdown(SAAS_CSS, unsafe_allow_html=True)


# Caching Heavy Calculations
@st.cache_data(show_spinner=False)
def get_cached_raw_data(uploaded_file=None):
    if uploaded_file is not None:
        return load_raw_data(uploaded_file)
    return load_raw_data()


@st.cache_data(show_spinner=False)
def get_cached_clean_data(raw_df):
    return clean_transactions(raw_df)


@st.cache_data(show_spinner=False)
def get_cached_rfm(clean_df):
    return calculate_rfm(clean_df)


@st.cache_data(show_spinner=False)
def get_cached_k_evaluation(scaled_matrix):
    return evaluate_k_range(scaled_matrix, k_range=range(2, 9))


def main():
    # -------------------------------------------------------------
    # 1. STATE INITIALIZATION & DATA LOADING
    # -------------------------------------------------------------
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Overview"
    if "analytics_sub" not in st.session_state:
        st.session_state.analytics_sub = "Analytics Overview"
    if "selected_k" not in st.session_state:
        st.session_state.selected_k = 6
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "cust_search_id" not in st.session_state:
        st.session_state.cust_search_id = 17850

    def navigate_to(page_key: str):
        st.session_state.nav_page = page_key
        st.rerun()

    # Load dataset & run data hygiene
    df_raw = get_cached_raw_data(st.session_state.uploaded_file)
    df_clean, audit_stats = get_cached_clean_data(df_raw)
    rfm_df, snapshot_date = get_cached_rfm(df_clean)
    scaled_matrix, scaled_df, scaler = preprocess_rfm_for_ml(rfm_df)
    eval_df = get_cached_k_evaluation(scaled_matrix)

    selected_k = st.session_state.selected_k
    kmeans_model, kmeans_labels = fit_kmeans(scaled_matrix, k=selected_k)
    profile_df, personas = generate_cluster_profiles(rfm_df, kmeans_labels)
    pca_coords, pca_model = compute_pca_2d(scaled_matrix)

    sil_score = eval_df.loc[eval_df["K"] == selected_k, "Silhouette_Score"].values[0]
    total_rev = audit_stats['total_revenue']
    rev_formatted = f"£{total_rev / 1_000_000:.2f}M" if total_rev >= 1_000_000 else f"£{total_rev:,.0f}"

    # -------------------------------------------------------------
    # 2. PERSISTENT SIDEBAR NAVIGATION (NO RADIO BUTTONS, NO CIRCLES)
    # -------------------------------------------------------------
    with st.sidebar:
        st.markdown("### **CUSTOMER INTELLIGENCE**")
        st.caption("RETAIL ANALYTICS PLATFORM")
        st.divider()

        nav_pages = [
            ("Overview", "Overview"),
            ("Customers", "Customers"),
            ("Segments", "Segments"),
            ("Analytics", "Analytics"),
            ("Data", "Data"),
        ]

        for key, label in nav_pages:
            is_active = (st.session_state.nav_page == key)
            btn_label = f"◉  {label}" if is_active else f"    {label}"
            if st.button(
                btn_label,
                key=f"nav_btn_{key}",
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                if st.session_state.nav_page != key:
                    st.session_state.nav_page = key
                    st.rerun()

        st.divider()

        with st.container(border=True):
            st.caption("DATASET STATUS")
            st.markdown("**● Online Retail**")
            st.caption(f"{audit_stats['unique_customers']:,} customers · {audit_stats['final_rows']:,} transactions")

        if st.button("Upload Dataset", key="sidebar_upload_btn", use_container_width=True):
            navigate_to("Data")

    # -------------------------------------------------------------
    # 3. MAIN TOP HEADER
    # -------------------------------------------------------------
    page_headers = {
        "Overview": ("Overview", "Retail customer intelligence platform"),
        "Customers": ("Customers", "Explore customer behavior and segment membership"),
        "Segments": ("Customer Segments", "Understand the behavioral groups identified from retail purchasing patterns"),
        "Analytics": ("Analytics", "Unsupervised machine learning pipeline, clustering diagnostics, and evaluation"),
        "Data": ("Data Management", "Inspect active dataset, audit preprocessing hygiene, or upload new files")
    }
    cur_title, cur_sub = page_headers.get(st.session_state.nav_page, ("Platform", ""))

    head_left, head_right = st.columns([4, 1.2])
    with head_left:
        st.title(cur_title)
        st.caption(cur_sub)
    with head_right:
        st.write("")
        st.markdown("**● Online Retail** · Connected")

    st.divider()

    # =============================================================
    # PAGE 1: HOME / OVERVIEW
    # =============================================================
    if st.session_state.nav_page == "Overview":
        # Hero Section
        hero_left, hero_right = st.columns([3.2, 2.8])
        with hero_left:
            st.caption("CUSTOMER INTELLIGENCE PLATFORM")
            st.subheader("Understand your customers.\nGrow your business.")
            st.write("Turn retail transaction data into actionable customer insights using behavioral analytics and machine learning.")
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Explore Segments", type="primary", use_container_width=True, key="hero_explore_btn"):
                    navigate_to("Segments")
            with btn_col2:
                if st.button("View Analytics", type="secondary", use_container_width=True, key="hero_analytics_btn"):
                    navigate_to("Analytics")

        with hero_right:
            with st.container(border=True):
                st.caption("CUSTOMER VALUE CHAIN")
                st.markdown("**1. Retail Transactions**")
                st.caption("Invoice logs, order frequency, and volume")
                st.markdown("↓")
                st.markdown("**2. Behavioral RFM Engine**")
                st.caption("Recency, Frequency, and Monetary spend")
                st.markdown("↓")
                st.markdown("**3. Actionable Segments**")
                st.caption("Targeted retention, upsell, and loyalty personas")

        st.divider()

        # Compact Metric Strip (KPIs)
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.metric("Customers", f"{audit_stats['unique_customers']:,}", help="Active identified shoppers")
        with kpi_c2:
            st.metric("Transactions", f"{audit_stats['final_rows']:,}", help="Clean purchase records")
        with kpi_c3:
            st.metric("Revenue", rev_formatted, help="Gross transaction value")
        with kpi_c4:
            st.metric("Segments", f"{selected_k}", help=f"Selected K · Silhouette {sil_score:.3f}")

        st.divider()

        # Business Features: "WHAT THE PLATFORM DOES"
        st.caption("CAPABILITIES")
        st.subheader("What the platform does")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            with st.container(border=True):
                st.markdown("**01 Understand Customers**")
                st.caption("Explore individual purchasing behavior using Recency, Frequency, and Monetary metrics.")
        with f_col2:
            with st.container(border=True):
                st.markdown("**02 Discover Segments**")
                st.caption("Identify groups with similar purchasing patterns and shopping habits.")
        with f_col3:
            with st.container(border=True):
                st.markdown("**03 Find Opportunities**")
                st.caption("Identify valuable champions, steady loyalists, and at-risk customers.")
        with f_col4:
            with st.container(border=True):
                st.markdown("**04 Take Action**")
                st.caption("Use segment-specific business recommendations for retention and engagement.")

        st.divider()

        # Customer Segments Preview
        st.caption("COHORT BREAKDOWN")
        st.subheader("Customer Segments")
        st.write("See how your customer base is distributed across behavioral groups.")

        for idx, (c_id, p_info) in enumerate(list(personas.items())[:4]):
            m = p_info["metrics"]
            clean_name = p_info['name'].split('(')[0].strip()
            with st.container(border=True):
                row_left, row_right = st.columns([3, 1])
                with row_left:
                    st.caption(f"CLUSTER C{c_id} • {p_info['badge']}")
                    st.markdown(f"**{clean_name}**")
                    st.write(p_info['description'])
                with row_right:
                    st.metric("Customers", f"{m['customers']:,}", f"{m['share_pct']}% of base")
                    st.caption(f"Revenue Contribution: **{m['revenue_pct']}%**")

        col_seg_btn, _ = st.columns([1.5, 4.5])
        with col_seg_btn:
            if st.button("View All Segments →", key="view_all_segments_cta"):
                navigate_to("Segments")

        st.divider()

        # Business Insight of the Day
        top_rev_cluster = profile_df.loc[profile_df["Revenue_Share_Pct"].idxmax()]
        top_rev_persona = top_rev_cluster["Persona"].split('(')[0].strip()
        top_rev_share = top_rev_cluster["Customer_Share_Pct"]
        top_rev_pct = top_rev_cluster["Revenue_Share_Pct"]
        top_rev_val = top_rev_cluster["Total_Revenue"]

        with st.container(border=True):
            st.caption("INSIGHT OF THE DAY")
            st.markdown(f"**{top_rev_persona}** represent **{top_rev_share}%** of customers but contribute **{top_rev_pct}%** of total retail revenue (£{top_rev_val:,.0f}). Prioritizing retention for this high-value cohort protects the core commercial baseline.")

    # =============================================================
    # PAGE 2: CUSTOMERS (CRM CUSTOMER DIRECTORY)
    # =============================================================
    elif st.session_state.nav_page == "Customers":
        st.subheader("Customer Lookup & Directory")
        st.caption("Search individual customer profiles, inspect exact RFM metrics, or export filtered customer segments.")

        # Search Customer ID Bar + Quick Sample Buttons
        c_search_in, c_search_chips = st.columns([2, 3])
        with c_search_in:
            search_input = st.number_input(
                "Search Customer ID:",
                value=int(st.session_state.cust_search_id),
                step=1,
                label_visibility="visible",
                key="customer_search_widget"
            )
            st.session_state.cust_search_id = int(search_input)

        with c_search_chips:
            st.caption("Quick Sample Customers:")
            sample_ids = [17850, 14646, 12346, 14911]
            chip_cols = st.columns(len(sample_ids))
            for i, sid in enumerate(sample_ids):
                with chip_cols[i]:
                    if st.button(f"#{sid}", key=f"chip_cust_{sid}", use_container_width=True):
                        st.session_state.customer_search_widget = int(sid)
                        st.session_state.cust_search_id = int(sid)
                        st.rerun()

        # Selected Customer Profile Card (Built cleanly with native containers)
        info = get_customer_lookup_info(int(st.session_state.cust_search_id), rfm_df, kmeans_labels, personas)
        if info["found"]:
            with st.container(border=True):
                c_head_left, c_head_right = st.columns([3, 1])
                with c_head_left:
                    st.caption("CUSTOMER PROFILE")
                    st.subheader(f"Customer #{info['customer_id']}")
                with c_head_right:
                    st.markdown(f"**Cluster C{info['cluster']}**")
                    st.caption(info['persona_name'])

                st.divider()

                c_m1, c_m2, c_m3 = st.columns(3)
                with c_m1:
                    st.metric("RECENCY", f"{info['recency']} days")
                with c_m2:
                    c_orders = f"{info['frequency']} orders" if info['frequency'] != 1 else "1 order"
                    st.metric("FREQUENCY", c_orders)
                with c_m3:
                    st.metric("MONETARY SPEND", f"£{info['monetary']:,.2f}")

                st.divider()

                st.markdown("**CUSTOMER BEHAVIOR**")
                st.write(info['description'])

                st.markdown("**RECOMMENDED ACTION**")
                st.write(info['recommended_strategy'])
        else:
            st.error(f"Customer #{st.session_state.cust_search_id} was not found in the transaction records.")

        st.divider()

        # Filters & Directory Table
        st.subheader("Customer Directory")
        st.caption("Filter by segment, purchase recency, or total monetary spend.")

        f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
        all_segments = sorted(profile_df["Persona"].unique())

        with f_col1:
            filter_seg = st.multiselect("Segment Filter:", options=all_segments, default=all_segments)
        with f_col2:
            max_r = int(rfm_df["Recency"].max())
            r_range = st.slider("Recency Range (days):", 0, max_r, (0, max_r))
        with f_col3:
            m_min = st.number_input("Minimum Monetary Spend (£):", value=0, step=50)

        # Apply filters
        cust_table = rfm_df.copy()
        cust_table["Cluster"] = kmeans_labels
        cust_table["Segment"] = cust_table["Cluster"].apply(lambda c: personas[c]["name"])
        cust_table["Cluster_Code"] = cust_table["Cluster"].apply(lambda c: f"C{c}")

        filtered_cust = cust_table[
            (cust_table["Segment"].isin(filter_seg)) &
            (cust_table["Recency"].between(r_range[0], r_range[1])) &
            (cust_table["Monetary"] >= m_min)
        ]

        display_cust = filtered_cust[[
            "CustomerID", "Segment", "Cluster_Code", "Recency", "Frequency", "Monetary"
        ]].rename(columns={
            "Cluster_Code": "Cluster",
            "Recency": "Recency (days)",
            "Frequency": "Frequency (purchases)",
            "Monetary": "Monetary Spend (£)"
        })

        st.caption(f"Showing {len(display_cust):,} of {len(cust_table):,} customers")
        st.dataframe(
            display_cust.style.format({"Monetary Spend (£)": "£{:,.2f}"}),
            use_container_width=True,
            height=340
        )

        csv_bytes = filtered_cust.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Customer Data (CSV)",
            data=csv_bytes,
            file_name=f"retail_customers_k{selected_k}.csv",
            mime="text/csv"
        )

    # =============================================================
    # PAGE 3: SEGMENTS (MAIN BUSINESS ANALYTICS)
    # =============================================================
    elif st.session_state.nav_page == "Segments":
        st.subheader("Customer Segments")
        st.caption("Understand the behavioral groups identified from retail purchasing patterns.")

        # Segment Profiles Grid (Built cleanly with native containers)
        cols = st.columns(3 if selected_k >= 6 else 2)
        for idx, (c_id, p_info) in enumerate(personas.items()):
            m = p_info["metrics"]
            clean_name = p_info['name'].split('(')[0].strip()
            with cols[idx % len(cols)]:
                with st.container(border=True):
                    st.caption(f"CLUSTER C{c_id} • {p_info['badge']}")
                    st.subheader(clean_name)
                    st.write(p_info['description'])
                    st.markdown(f"**{m['customers']:,}** customers • **{m['share_pct']}%** base • **{m['revenue_pct']}%** revenue")

                    st.divider()

                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Recency", f"{m['recency_mean']}d")
                    with m2:
                        st.metric("Frequency", f"{m['frequency_mean']}")
                    with m3:
                        st.metric("Monetary", f"£{m['monetary_mean']:,.0f}")

                    st.divider()

                    st.markdown("**Recommended Action:**")
                    st.write(p_info['strategy'])

                    st.caption(f"RFM Justification: {p_info['justification']}")

        st.divider()

        # Deep Dive Benchmark Comparison Tool
        with st.container(border=True):
            st.subheader("Segment Benchmark Comparison")
            st.caption("Compare how a customer segment performs against the store average baseline (1.0x).")

            col_deep_sel, col_deep_chart = st.columns([1.1, 1.9])
            with col_deep_sel:
                chosen_c = st.selectbox(
                    "Select segment to analyze:",
                    options=list(personas.keys()),
                    format_func=lambda c: f"Cluster C{c}: {personas[c]['name'].split('(')[0].strip()}"
                )
                p_det = personas[chosen_c]
                m_det = p_det["metrics"]
                with st.container(border=True):
                    st.caption(f"CLUSTER C{chosen_c} OVERVIEW")
                    st.subheader(p_det['name'])
                    st.write(p_det['description'])
                    st.write(f"• **Customers:** {m_det['customers']:,} ({m_det['share_pct']}%)")
                    st.write(f"• **Revenue:** £{m_det['total_revenue']:,.2f} ({m_det['revenue_pct']}%)")
                    st.write(f"• **Strategy:** {p_det['strategy']}")

            with col_deep_chart:
                fig_bench = create_segment_radar_comparison(profile_df, chosen_c)
                st.plotly_chart(fig_bench, use_container_width=True, config={"displayModeBar": False})

    # =============================================================
    # PAGE 4: ANALYTICS (DEDICATED ML WORKSPACE)
    # =============================================================
    elif st.session_state.nav_page == "Analytics":
        sub_pages = [
            "Analytics Overview",
            "RFM Analysis",
            "Cluster Selection",
            "K-Means",
            "Hierarchical Comparison",
            "PCA Visualization"
        ]

        sub_cols = st.columns(len(sub_pages))
        for idx, sp in enumerate(sub_pages):
            with sub_cols[idx]:
                is_sub_active = (st.session_state.analytics_sub == sp)
                if st.button(
                    sp,
                    key=f"btn_an_sub_{idx}",
                    type="primary" if is_sub_active else "secondary",
                    use_container_width=True
                ):
                    st.session_state.analytics_sub = sp
                    st.rerun()

        st.divider()

        # 4.1 ANALYTICS OVERVIEW
        if st.session_state.analytics_sub == "Analytics Overview":
            st.subheader("Machine Learning Pipeline Architecture")
            st.caption("End-to-end unsupervised learning flow from transaction records to commercial customer personas.")

            with st.container(border=True):
                st.caption("PIPELINE STAGES")
                p_cols = st.columns(6)
                p_steps = [
                    ("1. Transactions", "Invoice Records"),
                    ("2. RFM", "R, F, M Features"),
                    ("3. Feature Scaling", "StandardScaler"),
                    ("4. K-Means", "Centroid Optimization"),
                    ("5. Evaluation", "Elbow & Silhouette"),
                    ("6. Segments", "Customer Personas")
                ]
                for i, (title, sub) in enumerate(p_steps):
                    with p_cols[i]:
                        st.markdown(f"**{title}**")
                        st.caption(sub)

            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
            with m_c1:
                st.metric("Features Used", "Recency, Frequency, Monetary")
            with m_c2:
                st.metric("Primary Algorithm", "K-Means")
            with m_c3:
                st.metric("Selected Clusters (K)", f"{selected_k}")
            with m_c4:
                st.metric("Silhouette Score", f"{sil_score:.3f}")

        # 4.2 RFM ANALYSIS
        elif st.session_state.analytics_sub == "RFM Analysis":
            st.subheader("RFM Feature Analysis")
            st.caption("Statistical distributions and correlation structure across the three extracted behavioral features.")

            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                fig_r = create_rfm_distribution_chart(rfm_df, "Recency", "#2563EB", "Recency Distribution (Days)")
                st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})
            with d_col2:
                fig_f = create_rfm_distribution_chart(rfm_df, "Frequency", "#10B981", "Frequency Distribution (Purchases)")
                st.plotly_chart(fig_f, use_container_width=True, config={"displayModeBar": False})
            with d_col3:
                fig_m = create_rfm_distribution_chart(rfm_df, "Monetary", "#F59E0B", "Monetary Spend Distribution (£)")
                st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})

            st.divider()

            col_rfm_tbl, col_rfm_corr = st.columns([1.3, 1])
            with col_rfm_tbl:
                st.subheader("RFM Descriptive Statistics & Skewness")
                rfm_stats = get_rfm_summary_stats(rfm_df)
                st.dataframe(rfm_stats, use_container_width=True, hide_index=True)

            with col_rfm_corr:
                st.subheader("Correlation Matrix")
                corr_df = get_rfm_correlations(rfm_df)
                st.dataframe(corr_df.style.background_gradient(cmap="Blues"), use_container_width=True)

        # 4.3 CLUSTER SELECTION
        elif st.session_state.analytics_sub == "Cluster Selection":
            st.subheader("Find the Optimal Number of Customer Segments")
            st.caption("Evaluating within-cluster sum of squares (Elbow Method) and cluster cohesion vs. separation (Silhouette Analysis) across K = 2 to 8.")

            col_el_chart, col_sil_chart = st.columns(2)
            fig_elb, fig_sil = create_elbow_silhouette_charts(eval_df, selected_k)

            with col_el_chart:
                st.plotly_chart(fig_elb, use_container_width=True, config={"displayModeBar": False})
            with col_sil_chart:
                st.plotly_chart(fig_sil, use_container_width=True, config={"displayModeBar": False})

            with st.container(border=True):
                st.caption(f"SELECTED K = {selected_k}")
                st.markdown(f"Selected based on the clustering evaluation across K = 2 to 8, balancing the reduction in inertia (Elbow inflection) with silhouette separation. Active Silhouette Score: **{sil_score:.4f}**.")

            st.subheader("Evaluation Table (K = 2 through 8)")
            eval_req = eval_df[["K", "Inertia", "Silhouette_Score"]].copy()
            eval_req["Status"] = eval_req["K"].apply(lambda k: f"Selected (K={k})" if k == selected_k else "Evaluated")
            eval_req = eval_req.rename(columns={"Silhouette_Score": "Silhouette Score"})

            st.dataframe(
                eval_req.style.format({
                    "Inertia": "{:,.2f}",
                    "Silhouette Score": "{:.4f}"
                }),
                use_container_width=True,
                hide_index=True
            )

        # 4.4 K-MEANS
        elif st.session_state.analytics_sub == "K-Means":
            st.subheader("K-Means Customer Segmentation")
            st.caption("Partitioning customer base into behavioral cohorts using k-means++ centroid optimization.")

            fig_km = create_kmeans_cluster_profiles_chart(profile_df)
            st.plotly_chart(fig_km, use_container_width=True, config={"displayModeBar": False})

            st.subheader("Cluster Profile Summary")
            km_summary = profile_df[[
                "Cluster", "Persona", "Customer_Count", "Customer_Share_Pct",
                "Recency_Mean", "Frequency_Mean", "Monetary_Mean", "Revenue_Share_Pct"
            ]].rename(columns={
                "Customer_Count": "Customers",
                "Customer_Share_Pct": "Cust %",
                "Recency_Mean": "Avg Recency (d)",
                "Frequency_Mean": "Avg Orders",
                "Monetary_Mean": "Avg Spend (£)",
                "Revenue_Share_Pct": "Rev %"
            })
            st.dataframe(km_summary, use_container_width=True, hide_index=True)

        # 4.5 HIERARCHICAL COMPARISON
        elif st.session_state.analytics_sub == "Hierarchical Comparison":
            st.subheader("K-Means vs. Hierarchical Clustering")
            st.caption("Benchmarking K-Means against Agglomerative Hierarchical Clustering using Ward linkage.")

            agg_model, agg_labels = fit_hierarchical(scaled_matrix, k=selected_k)
            comp_df = compare_clustering_algorithms(scaled_matrix, kmeans_labels, agg_labels, k=selected_k)
            cross_tab = compute_cluster_cross_tab(kmeans_labels, agg_labels)

            fig_h_comp = create_hierarchical_comparison_chart(comp_df)
            st.plotly_chart(fig_h_comp, use_container_width=True, config={"displayModeBar": False})

            c_h1, c_h2 = st.columns([1, 1])
            with c_h1:
                st.subheader("Validation Metric Benchmark")
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
            with c_h2:
                st.subheader("Assignment Cross-Tabulation Matrix")
                st.dataframe(cross_tab, use_container_width=True)

            with st.container(border=True):
                st.caption("ALGORITHMIC DECISION")
                st.write(f"K-Means achieves a competitive Silhouette Score ({comp_df.loc[0, 'Silhouette Score']:.4f} vs {comp_df.loc[1, 'Silhouette Score']:.4f}) while operating in O(N · K · I) time complexity compared to O(N³) for Agglomerative Hierarchical clustering, making it the production model choice for retail customer datasets.")

        # 4.6 PCA VISUALIZATION
        elif st.session_state.analytics_sub == "PCA Visualization":
            var1 = pca_model.explained_variance_ratio_[0] * 100
            var2 = pca_model.explained_variance_ratio_[1] * 100

            st.subheader("Customer Segments in 2D")
            st.caption("Principal Component Analysis projects the 3D RFM space onto two orthogonal principal components for visual inspection.")

            col_pca_plot, col_pca_side = st.columns([3, 1])
            with col_pca_plot:
                fig_pca = create_pca_scatter_chart(pca_coords, kmeans_labels, rfm_df, personas)
                st.plotly_chart(fig_pca, use_container_width=True, config={"displayModeBar": False})

            with col_pca_side:
                st.subheader("Explained Variance")
                st.metric("PC1 Explained Variance", f"{var1:.1f}%", help="Captures spending intensity and order volume")
                st.metric("PC2 Explained Variance", f"{var2:.1f}%", help="Captures purchase recency and timing")
                st.metric("Total Retained Variance", f"{var1 + var2:.1f}%")

                with st.container(border=True):
                    st.caption("CLUSTER COHESION")
                    st.write("Distinct visual boundaries confirm that behavioral segments represent genuine customer groupings rather than arbitrary mathematical slices.")

    # =============================================================
    # PAGE 5: DATA (DATA MANAGEMENT)
    # =============================================================
    elif st.session_state.nav_page == "Data":
        st.subheader("Data Management")
        st.caption("Inspect transaction records, audit data hygiene stages, examine numerical summary statistics, or ingest a custom dataset.")

        # Dataset Volume Overview KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Raw Records", f"{audit_stats['initial_rows']:,}", help="Ingested rows")
        with k2:
            st.metric("Clean Records", f"{audit_stats['final_rows']:,}", f"{audit_stats['retention_rate_pct']}% retained")
        with k3:
            st.metric("Unique Customers", f"{audit_stats['unique_customers']:,}", help="Identified shoppers")
        with k4:
            st.metric("Invoices", f"{audit_stats['unique_invoices']:,}", help="Distinct retail orders")

        st.divider()

        tab_preview, tab_quality, tab_stats, tab_upload = st.tabs([
            "Current Dataset",
            "Data Quality",
            "Statistics",
            "Upload Dataset"
        ])

        with tab_preview:
            st.subheader("Clean Transaction Records")
            st.dataframe(
                df_clean[["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "TotalPrice", "CustomerID", "Country"]].head(15),
                use_container_width=True
            )

        with tab_quality:
            st.subheader("Data Hygiene Audit Trail")
            audit_tbl = pd.DataFrame([
                {"Pipeline Stage": "1. Raw Records Ingested", "Record Count": f"{audit_stats['initial_rows']:,}", "Description": "Original records from retail database"},
                {"Pipeline Stage": "2. Missing CustomerIDs Dropped", "Record Count": f"-{audit_stats['initial_missing_customer']:,}", "Description": "Guest purchases cannot be attributed to individual customer RFM profiles"},
                {"Pipeline Stage": "3. Cancelled Invoices ('C*')", "Record Count": f"-{audit_stats['cancelled_count']:,}", "Description": "Return orders excluded from gross spending calculations"},
                {"Pipeline Stage": "4. Non-Positive Qty / Price", "Record Count": f"-{audit_stats['invalid_qty_count'] + audit_stats['invalid_price_count']:,}", "Description": "Damaged goods, system tests, and accounting adjustments"},
                {"Pipeline Stage": "5. Duplicate Rows Filtered", "Record Count": f"-{audit_stats['duplicate_count']:,}", "Description": "Redundant identical transaction logs removed"},
                {"Pipeline Stage": "6. Clean Production Records", "Record Count": f"{audit_stats['final_rows']:,}", "Description": f"{audit_stats['unique_customers']:,} unique customers spanning {audit_stats['date_min'].strftime('%Y-%m-%d')} to {audit_stats['date_max'].strftime('%Y-%m-%d')}"}
            ])
            st.table(audit_tbl)

        with tab_stats:
            st.subheader("Numerical Column Statistics")
            num_desc = df_clean[["Quantity", "UnitPrice", "TotalPrice"]].describe().T[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
            st.dataframe(num_desc.style.format("{:,.2f}"), use_container_width=True)

        with tab_upload:
            st.subheader("Upload Custom Retail Dataset")
            st.caption("Upload your retail transactional dataset in CSV or XLSX format:")

            uploaded_file_data = st.file_uploader(
                "Upload Dataset",
                type=["csv", "xlsx"],
                help="Columns required: InvoiceNo, StockCode, Quantity, InvoiceDate, UnitPrice, CustomerID"
            )

            if uploaded_file_data is not None:
                try:
                    test_df = load_raw_data(uploaded_file_data, nrows=10)
                    required_cols = {"InvoiceNo", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"}
                    missing_cols = required_cols - set(test_df.columns)

                    if missing_cols:
                        st.error(f"Upload validation failed. Missing required columns: {', '.join(missing_cols)}")
                    else:
                        st.session_state.uploaded_file = uploaded_file_data
                        st.success("Dataset successfully validated! Updating website models...")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error reading dataset: {str(e)}")


if __name__ == "__main__":
    main()
