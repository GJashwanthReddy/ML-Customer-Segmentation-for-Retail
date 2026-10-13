"""
Interactive Plotly Charts Module
Modern, borderless, SaaS-grade interactive charts with hover tooltips and consistent palettes.
"""

from typing import List, Dict, Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Global SaaS Palette
CLUSTER_COLORS = [
    "#10B981",  # 0: Emerald Green
    "#3B82F6",  # 1: Blue
    "#F59E0B",  # 2: Amber
    "#8B5CF6",  # 3: Purple
    "#EF4444",  # 4: Coral Red
    "#06B6D4",  # 5: Cyan
    "#EC4899",  # 6: Pink
    "#64748B"   # 7: Slate
]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, sans-serif", color="#0F172A", size=12),
    margin=dict(l=20, r=20, t=35, b=25),
    hoverlabel=dict(
        bgcolor="#0F172A",
        font_size=12,
        font_family="Inter, -apple-system, sans-serif",
        font_color="#FFFFFF"
    )
)


def get_cluster_color(cluster_id: int) -> str:
    return CLUSTER_COLORS[int(cluster_id) % len(CLUSTER_COLORS)]


def create_segment_distribution_chart(profile_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of customer segment distribution with unclipped labels."""
    df_sorted = profile_df.sort_values("Customer_Count", ascending=True)
    colors = [get_cluster_color(c) for c in df_sorted["Cluster"]]
    max_count = df_sorted["Customer_Count"].max() if len(df_sorted) > 0 else 1000

    fig = go.Figure(go.Bar(
        x=df_sorted["Customer_Count"],
        y=[f"C{row['Cluster']}: {row['Persona'].split('(')[0].strip()}" for _, row in df_sorted.iterrows()],
        orientation="h",
        marker=dict(color=colors, cornerradius=6),
        text=[f"{cnt:,} ({pct}%)" for cnt, pct in zip(df_sorted["Customer_Count"], df_sorted["Customer_Share_Pct"])],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Customers: %{x:,}<br>Share: %{text}<extra></extra>"
    ))

    layout = dict(CHART_LAYOUT)
    layout["margin"] = dict(l=155, r=65, t=10, b=10)
    fig.update_layout(
        **layout,
        height=280,
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False, range=[0, max_count * 1.3]),
        yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=11, color="#1E293B"))
    )
    return fig


def create_customer_vs_revenue_chart(profile_df: pd.DataFrame) -> go.Figure:
    """Side-by-side grouped horizontal bars: Customer Share % vs Revenue Share %."""
    df_sorted = profile_df.sort_values("Revenue_Share_Pct", ascending=True)
    y_labels = [f"C{row['Cluster']}: {row['Persona'].split('(')[0].strip()}" for _, row in df_sorted.iterrows()]

    fig = go.Figure()

    # Customer Share
    fig.add_trace(go.Bar(
        name="Customer Share %",
        y=y_labels,
        x=df_sorted["Customer_Share_Pct"],
        orientation="h",
        marker=dict(color="#94A3B8", cornerradius=4),
        text=[f"{v:.1f}%" for v in df_sorted["Customer_Share_Pct"]],
        textposition="inside",
        hovertemplate="<b>%{y}</b><br>Customer Base: %{x:.1f}%<extra></extra>"
    ))

    # Revenue Share
    fig.add_trace(go.Bar(
        name="Revenue Share %",
        y=y_labels,
        x=df_sorted["Revenue_Share_Pct"],
        orientation="h",
        marker=dict(color="#2563EB", cornerradius=4),
        text=[f"{v:.1f}%" for v in df_sorted["Revenue_Share_Pct"]],
        textposition="inside",
        hovertemplate="<b>%{y}</b><br>Total Revenue: %{x:.1f}%<extra></extra>"
    ))

    layout = dict(CHART_LAYOUT)
    layout["margin"] = dict(l=155, r=25, t=25, b=10)
    fig.update_layout(
        **layout,
        barmode="group",
        height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False, title="Percentage (%)"),
        yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=11, color="#1E293B"))
    )
    return fig


def create_rfm_distribution_chart(rfm_df: pd.DataFrame, metric: str, color: str, title: str) -> go.Figure:
    """Clean histogram with KDE-like distribution."""
    vals = rfm_df[metric]
    if metric == "Monetary":
        vals = vals[vals <= vals.quantile(0.98)]
    elif metric == "Frequency":
        vals = vals[vals <= vals.quantile(0.98)]

    fig = go.Figure(go.Histogram(
        x=vals,
        nbinsx=35,
        marker=dict(color=color, opacity=0.85, line=dict(color="#FFFFFF", width=1)),
        hovertemplate="Range: %{x}<br>Count: %{y:,}<extra></extra>"
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        height=260,
        title=dict(text=title, font=dict(size=13, color="#0F172A", weight=600)),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    )
    return fig


def create_elbow_silhouette_charts(eval_df: pd.DataFrame, selected_k: int):
    """Side-by-side interactive Elbow and Silhouette charts."""
    # Elbow Chart
    fig_elbow = go.Figure()
    fig_elbow.add_trace(go.Scatter(
        x=eval_df["K"],
        y=eval_df["Inertia"],
        mode="lines+markers",
        name="Inertia",
        line=dict(color="#2563EB", width=2.5),
        marker=dict(size=8, color="#2563EB"),
        hovertemplate="K = %{x}<br>Inertia: %{y:,.1f}<extra></extra>"
    ))

    if selected_k in eval_df["K"].values:
        sel_inertia = eval_df.loc[eval_df["K"] == selected_k, "Inertia"].values[0]
        fig_elbow.add_trace(go.Scatter(
            x=[selected_k],
            y=[sel_inertia],
            mode="markers",
            name=f"Selected K={selected_k}",
            marker=dict(size=14, color="#EF4444", symbol="star")
        ))

    fig_elbow.update_layout(
        **CHART_LAYOUT,
        height=320,
        title=dict(text="Elbow Method (Inertia vs K)", font=dict(size=13, weight=600)),
        xaxis=dict(title="Number of Clusters (K)", tickmode="linear", tick0=2, dtick=1, gridcolor="#F1F5F9"),
        yaxis=dict(title="Inertia (WCSS)", gridcolor="#F1F5F9"),
        showlegend=False
    )

    # Silhouette Chart
    fig_sil = go.Figure()
    fig_sil.add_trace(go.Scatter(
        x=eval_df["K"],
        y=eval_df["Silhouette_Score"],
        mode="lines+markers",
        name="Silhouette",
        line=dict(color="#10B981", width=2.5),
        marker=dict(size=8, color="#10B981"),
        hovertemplate="K = %{x}<br>Silhouette: %{y:.4f}<extra></extra>"
    ))

    if selected_k in eval_df["K"].values:
        sel_sil = eval_df.loc[eval_df["K"] == selected_k, "Silhouette_Score"].values[0]
        fig_sil.add_trace(go.Scatter(
            x=[selected_k],
            y=[sel_sil],
            mode="markers",
            name=f"Selected K={selected_k}",
            marker=dict(size=14, color="#EF4444", symbol="star")
        ))

    fig_sil.update_layout(
        **CHART_LAYOUT,
        height=320,
        title=dict(text="Silhouette Score vs K", font=dict(size=13, weight=600)),
        xaxis=dict(title="Number of Clusters (K)", tickmode="linear", tick0=2, dtick=1, gridcolor="#F1F5F9"),
        yaxis=dict(title="Silhouette Score", gridcolor="#F1F5F9"),
        showlegend=False
    )

    return fig_elbow, fig_sil


def create_pca_scatter_chart(
    pca_coords: np.ndarray,
    cluster_labels: np.ndarray,
    rfm_df: pd.DataFrame,
    personas: Dict[int, Dict],
    filter_clusters: Optional[List[int]] = None
) -> go.Figure:
    """Large, interactive 2D PCA projection scatter plot."""
    df_plot = pd.DataFrame({
        "PC1": pca_coords[:, 0],
        "PC2": pca_coords[:, 1],
        "Cluster": cluster_labels,
        "CustomerID": rfm_df["CustomerID"].values,
        "Recency": rfm_df["Recency"].values,
        "Frequency": rfm_df["Frequency"].values,
        "Monetary": rfm_df["Monetary"].values
    })

    if filter_clusters is not None:
        df_plot = df_plot[df_plot["Cluster"].isin(filter_clusters)]

    fig = go.Figure()

    for c in sorted(df_plot["Cluster"].unique()):
        sub = df_plot[df_plot["Cluster"] == c]
        p_name = personas.get(c, {}).get("name", f"Cluster {c}").split("(")[0].strip()
        color = get_cluster_color(c)

        fig.add_trace(go.Scatter(
            x=sub["PC1"],
            y=sub["PC2"],
            mode="markers",
            name=f"C{c}: {p_name}",
            marker=dict(
                size=7,
                color=color,
                opacity=0.7,
                line=dict(width=0.5, color="#FFFFFF")
            ),
            customdata=np.stack((sub["CustomerID"], sub["Recency"], sub["Frequency"], sub["Monetary"]), axis=-1),
            hovertemplate=(
                "<b>Customer #%{customdata[0]:.0f}</b><br>"
                f"Segment: C{c} ({p_name})<br>"
                "Recency: %{customdata[1]:.0f} days<br>"
                "Frequency: %{customdata[2]:.0f} orders<br>"
                "Spend: £%{customdata[3]:,.2f}<br>"
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        **CHART_LAYOUT,
        height=540,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        xaxis=dict(title="Principal Component 1 (Spending & Activity Intensity)", gridcolor="#F1F5F9", zeroline=False),
        yaxis=dict(title="Principal Component 2 (Recency Timing)", gridcolor="#F1F5F9", zeroline=False)
    )
    return fig


def create_segment_radar_comparison(profile_df: pd.DataFrame, selected_cluster_id: int) -> go.Figure:
    """Compares selected cluster's normalized RFM vs the overall retail baseline."""
    sel = profile_df[profile_df["Cluster"] == selected_cluster_id].iloc[0]
    
    # Normalized relative to averages
    avg_r = profile_df["Recency_Mean"].mean()
    avg_f = profile_df["Frequency_Mean"].mean()
    avg_m = profile_df["Monetary_Mean"].mean()

    categories = ["Recency Ratio (Lower is better)", "Frequency Ratio", "Monetary Ratio"]
    sel_vals = [
        round(avg_r / max(sel["Recency_Mean"], 1), 2),  # inverted so higher is better
        round(sel["Frequency_Mean"] / max(avg_f, 1), 2),
        round(sel["Monetary_Mean"] / max(avg_m, 1), 2)
    ]
    baseline_vals = [1.0, 1.0, 1.0]

    color = get_cluster_color(selected_cluster_id)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=f"Cluster {selected_cluster_id} vs Baseline",
        x=categories,
        y=sel_vals,
        marker=dict(color=color, cornerradius=6),
        text=[f"{v}x" for v in sel_vals],
        textposition="outside"
    ))
    fig.add_trace(go.Bar(
        name="Store Baseline (1.0x)",
        x=categories,
        y=baseline_vals,
        marker=dict(color="#CBD5E1", cornerradius=6)
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        barmode="group",
        height=280,
        title=dict(text="RFM Comparison vs Store Average (1.0x)", font=dict(size=12, weight=600)),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
        xaxis=dict(showgrid=False, zeroline=False)
    )
    return fig


def create_kmeans_cluster_profiles_chart(profile_df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart showing Mean Recency, Frequency, and Monetary across clusters."""
    fig = go.Figure()
    clusters = [f"C{row['Cluster']}: {row['Persona'].split('(')[0].strip()}" for _, row in profile_df.iterrows()]
    colors = [get_cluster_color(row["Cluster"]) for _, row in profile_df.iterrows()]

    fig.add_trace(go.Bar(
        x=clusters,
        y=profile_df["Customer_Count"],
        name="Customer Count",
        marker=dict(color=colors, cornerradius=5),
        text=[f"{cnt:,}" for cnt in profile_df["Customer_Count"]],
        textposition="outside"
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        height=320,
        title=dict(text="Customer Volume per Segment", font=dict(size=13, weight=600)),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False, title="Customer Count"),
        showlegend=False
    )
    return fig


def create_hierarchical_comparison_chart(comp_df: pd.DataFrame) -> go.Figure:
    """Side-by-side comparison of K-Means vs Hierarchical across Silhouette and Davies-Bouldin."""
    fig = go.Figure()
    algs = comp_df["Algorithm"].values

    fig.add_trace(go.Bar(
        x=algs,
        y=comp_df["Silhouette Score"],
        name="Silhouette Score (Higher is better)",
        marker=dict(color="#10B981", cornerradius=5),
        text=[f"{v:.4f}" for v in comp_df["Silhouette Score"]],
        textposition="outside"
    ))

    fig.add_trace(go.Bar(
        x=algs,
        y=comp_df["Davies-Bouldin Index"],
        name="Davies-Bouldin Index (Lower is better)",
        marker=dict(color="#6366F1", cornerradius=5),
        text=[f"{v:.4f}" for v in comp_df["Davies-Bouldin Index"]],
        textposition="outside"
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        barmode="group",
        height=300,
        title=dict(text="Validation Metric Benchmark: K-Means vs Hierarchical", font=dict(size=13, weight=600)),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

