"""
Data Visualization Module - Modern Retail Light Design
Generates publication-quality, clean, high-resolution Matplotlib and Seaborn figures.
"""

from typing import List, Optional, Dict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Global Consistent Cluster Color Palette
CLUSTER_COLORS = [
    "#10B981",  # Emerald (Champions)
    "#3B82F6",  # Blue (New Explorers)
    "#F59E0B",  # Amber (At-Risk)
    "#8B5CF6",  # Purple (Loyal/Core)
    "#EF4444",  # Red (Hibernating/Lost)
    "#06B6D4",  # Cyan
    "#EC4899",  # Pink
    "#64748B"   # Slate
]

# Set Global Matplotlib Clean Light Theme
plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"]
plt.rcParams["axes.edgecolor"] = "#E2E8F0"
plt.rcParams["axes.linewidth"] = 1.0
plt.rcParams["text.color"] = "#0F172A"
plt.rcParams["axes.labelcolor"] = "#334155"
plt.rcParams["xtick.color"] = "#475569"
plt.rcParams["ytick.color"] = "#475569"
plt.rcParams["grid.color"] = "#F1F5F9"


def _apply_clean_styling(ax, title: str = "", xlabel: str = "", ylabel: str = ""):
    """Applies modern minimalist retail card styling to an axis."""
    ax.set_facecolor("#FFFFFF")
    ax.grid(True, linestyle="--", alpha=0.6, color="#E2E8F0", zorder=0)
    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")
        spine.set_linewidth(1.0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if title:
        ax.set_title(title, fontsize=12, fontweight="600", color="#0F172A", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, fontweight="500", color="#475569", labelpad=8)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, fontweight="500", color="#475569", labelpad=8)


def plot_top_countries(df_clean: pd.DataFrame, top_n: int = 8) -> plt.Figure:
    """Plots top N countries by transaction volume."""
    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#FFFFFF")
    country_counts = df_clean["Country"].value_counts().head(top_n)
    
    colors = sns.color_palette("Blues_r", n_colors=top_n)
    bars = ax.barh(country_counts.index[::-1], country_counts.values[::-1], color=colors[::-1], height=0.65, zorder=3)
    
    # Add count labels
    for bar in bars:
        w = bar.get_width()
        ax.text(w + (country_counts.max() * 0.015), bar.get_y() + bar.get_height() / 2,
                f"{int(w):,}", ha="left", va="center", fontsize=8.5, color="#475569", fontweight="500")

    _apply_clean_styling(ax, title=f"Top {top_n} Geographic Markets", xlabel="Transaction Orders")
    ax.set_xlim(0, country_counts.max() * 1.15)
    plt.tight_layout()
    return fig


def plot_rfm_distributions(rfm_df: pd.DataFrame) -> plt.Figure:
    """Plots clean distribution histograms and KDE curves for raw RFM features."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), facecolor="#FFFFFF")

    # Recency
    sns.histplot(rfm_df["Recency"], kde=True, ax=axes[0], color="#2563EB", bins=28, edgecolor="#FFFFFF", alpha=0.65, zorder=3)
    _apply_clean_styling(axes[0], title="Recency (Days Since Purchase)", xlabel="Days", ylabel="Customer Count")

    # Frequency
    sns.histplot(rfm_df["Frequency"], kde=True, ax=axes[1], color="#059669", bins=28, edgecolor="#FFFFFF", alpha=0.65, zorder=3)
    axes[1].set_xlim(0, rfm_df["Frequency"].quantile(0.98))
    _apply_clean_styling(axes[1], title="Frequency (Order Count)", xlabel="Orders", ylabel="Customer Count")

    # Monetary
    p98 = rfm_df["Monetary"].quantile(0.98)
    sns.histplot(rfm_df["Monetary"][rfm_df["Monetary"] <= p98], kde=True, ax=axes[2], color="#D97706", bins=28, edgecolor="#FFFFFF", alpha=0.65, zorder=3)
    _apply_clean_styling(axes[2], title="Monetary Spend (£)", xlabel="Total Spend (£)", ylabel="Customer Count")

    plt.tight_layout()
    return fig


def plot_rfm_correlation_heatmap(corr_df: pd.DataFrame) -> plt.Figure:
    """Plots clean correlation heatmap of RFM features."""
    fig, ax = plt.subplots(figsize=(5.5, 4), facecolor="#FFFFFF")
    sns.heatmap(
        corr_df,
        annot=True,
        cmap="Blues",
        vmin=-0.2,
        vmax=1.0,
        fmt=".2f",
        linewidths=1.5,
        linecolor="#FFFFFF",
        cbar_kws={"shrink": 0.8},
        annot_kws={"size": 11, "weight": "bold", "color": "#0F172A"},
        ax=ax
    )
    _apply_clean_styling(ax, title="RFM Feature Correlation")
    plt.tight_layout()
    return fig


def plot_elbow_curve(eval_df: pd.DataFrame, selected_k: int = 4) -> plt.Figure:
    """Plots K-Means Elbow Curve (Inertia vs K) with clean design."""
    fig, ax = plt.subplots(figsize=(7, 4.2), facecolor="#FFFFFF")
    ax.plot(eval_df["K"], eval_df["Inertia"], marker="o", color="#2563EB", linewidth=2.5, markersize=8, zorder=4)
    
    if selected_k in eval_df["K"].values:
        sel_inertia = eval_df.loc[eval_df["K"] == selected_k, "Inertia"].values[0]
        ax.plot(selected_k, sel_inertia, marker="o", markersize=12, color="#EF4444", zorder=5, label=f"Selected K = {selected_k}")
        ax.axvline(x=selected_k, color="#EF4444", linestyle="--", alpha=0.5, zorder=2)

    _apply_clean_styling(ax, title="Elbow Method: Inertia vs K", xlabel="Number of Clusters (K)", ylabel="Inertia (Within-Cluster Sum of Squares)")
    ax.set_xticks(eval_df["K"].values)
    ax.legend(loc="upper right", frameon=True, facecolor="#F8FAFC", edgecolor="#E2E8F0")
    plt.tight_layout()
    return fig


def plot_silhouette_curve(eval_df: pd.DataFrame, selected_k: int = 4) -> plt.Figure:
    """Plots Silhouette Score vs K with clean design."""
    fig, ax = plt.subplots(figsize=(7, 4.2), facecolor="#FFFFFF")
    ax.plot(eval_df["K"], eval_df["Silhouette_Score"], marker="s", color="#059669", linewidth=2.5, markersize=8, zorder=4)
    
    if selected_k in eval_df["K"].values:
        sel_sil = eval_df.loc[eval_df["K"] == selected_k, "Silhouette_Score"].values[0]
        ax.plot(selected_k, sel_sil, marker="s", markersize=12, color="#EF4444", zorder=5, label=f"Selected K = {selected_k}")
        ax.axvline(x=selected_k, color="#EF4444", linestyle="--", alpha=0.5, zorder=2)

    _apply_clean_styling(ax, title="Silhouette Score Analysis vs K", xlabel="Number of Clusters (K)", ylabel="Silhouette Score")
    ax.set_xticks(eval_df["K"].values)
    ax.legend(loc="upper right", frameon=True, facecolor="#F8FAFC", edgecolor="#E2E8F0")
    plt.tight_layout()
    return fig


def plot_pca_clusters(
    pca_coords: np.ndarray,
    cluster_labels: np.ndarray,
    pca_model,
    selected_k: int,
    persona_names: Optional[dict] = None,
    filter_clusters: Optional[List[int]] = None
) -> plt.Figure:
    """Plots large 2D PCA projection of customer clusters."""
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#FFFFFF")
    
    df_plot = pd.DataFrame({
        "PC1": pca_coords[:, 0],
        "PC2": pca_coords[:, 1],
        "Cluster": cluster_labels
    })

    if filter_clusters is not None:
        df_plot = df_plot[df_plot["Cluster"].isin(filter_clusters)]

    # Use consistent cluster colors
    palette = {c: CLUSTER_COLORS[c % len(CLUSTER_COLORS)] for c in sorted(df_plot["Cluster"].unique())}

    if persona_names:
        df_plot["Segment_Label"] = df_plot["Cluster"].apply(
            lambda c: f"Cluster {c}: {persona_names.get(c, '')}"
        )
        hue_order = sorted(df_plot["Segment_Label"].unique())
        palette_map = {f"Cluster {c}: {persona_names.get(c, '')}": CLUSTER_COLORS[c % len(CLUSTER_COLORS)] for c in df_plot["Cluster"].unique()}
        sns.scatterplot(
            data=df_plot,
            x="PC1",
            y="PC2",
            hue="Segment_Label",
            hue_order=hue_order,
            palette=palette_map,
            alpha=0.6,
            s=36,
            edgecolor="none",
            ax=ax,
            zorder=3
        )
    else:
        sns.scatterplot(
            data=df_plot,
            x="PC1",
            y="PC2",
            hue="Cluster",
            palette=palette,
            alpha=0.6,
            s=36,
            edgecolor="none",
            ax=ax,
            zorder=3
        )

    var1 = pca_model.explained_variance_ratio_[0] * 100
    var2 = pca_model.explained_variance_ratio_[1] * 100

    _apply_clean_styling(
        ax,
        title=f"2D PCA Projection (Explained Variance: {var1 + var2:.1f}%)",
        xlabel=f"Principal Component 1 ({var1:.1f}% variance)",
        ylabel=f"Principal Component 2 ({var2:.1f}% variance)"
    )
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0, frameon=True, facecolor="#F8FAFC", edgecolor="#E2E8F0")
    plt.tight_layout()
    return fig


def plot_segment_distribution_bar(profile_df: pd.DataFrame) -> plt.Figure:
    """Plots clean horizontal bar chart of customer distribution across segments."""
    fig, ax = plt.subplots(figsize=(7, 3.8), facecolor="#FFFFFF")
    
    # Sort or reverse for top-down display
    df_sorted = profile_df.iloc[::-1]
    labels = [f"C{row['Cluster']}: {row['Persona'].split('(')[0].strip()}" for _, row in df_sorted.iterrows()]
    colors = [CLUSTER_COLORS[int(row["Cluster"]) % len(CLUSTER_COLORS)] for _, row in df_sorted.iterrows()]

    bars = ax.barh(labels, df_sorted["Customer_Count"], color=colors, height=0.6, zorder=3)

    for bar, pct in zip(bars, df_sorted["Customer_Share_Pct"]):
        w = bar.get_width()
        ax.text(w + (profile_df["Customer_Count"].max() * 0.02), bar.get_y() + bar.get_height() / 2,
                f"{int(w):,} ({pct:.1f}%)", ha="left", va="center", fontsize=9, color="#334155", fontweight="500")

    _apply_clean_styling(ax, title="Customer Segment Distribution", xlabel="Number of Customers")
    ax.set_xlim(0, profile_df["Customer_Count"].max() * 1.25)
    plt.tight_layout()
    return fig


def plot_revenue_contribution_donut(profile_df: pd.DataFrame) -> plt.Figure:
    """Plots clean minimalist donut chart for revenue contribution."""
    fig, ax = plt.subplots(figsize=(6, 3.8), facecolor="#FFFFFF")
    
    labels = [f"C{row['Cluster']}: {row['Persona'].split('(')[0].strip()}" for _, row in profile_df.iterrows()]
    colors = [CLUSTER_COLORS[int(row["Cluster"]) % len(CLUSTER_COLORS)] for _, row in profile_df.iterrows()]

    wedges, texts, autotexts = ax.pie(
        profile_df["Revenue_Share_Pct"],
        labels=labels,
        autopct="%1.1f%%",
        pctdistance=0.75,
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.42, edgecolor="#FFFFFF", linewidth=2)
    )

    for autotext in autotexts:
        autotext.set_color("#FFFFFF")
        autotext.set_fontweight("bold")
        autotext.set_fontsize(8.5)

    for text in texts:
        text.set_color("#334155")
        text.set_fontsize(8.5)

    ax.set_title("Revenue Contribution by Segment", fontsize=12, fontweight="600", color="#0F172A", pad=12)
    plt.tight_layout()
    return fig


def plot_cluster_metric_bars(profile_df: pd.DataFrame) -> plt.Figure:
    """Plots comparative mean RFM metrics across clusters with consistent palette."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.8), facecolor="#FFFFFF")
    clusters = [f"Cluster {c}" for c in profile_df["Cluster"]]
    colors = [CLUSTER_COLORS[int(c) % len(CLUSTER_COLORS)] for c in profile_df["Cluster"]]

    # Recency
    axes[0].bar(clusters, profile_df["Recency_Mean"], color=colors, width=0.55, zorder=3)
    _apply_clean_styling(axes[0], title="Avg Recency (Days - Lower is better)", ylabel="Days")

    # Frequency
    axes[1].bar(clusters, profile_df["Frequency_Mean"], color=colors, width=0.55, zorder=3)
    _apply_clean_styling(axes[1], title="Avg Frequency (Orders - Higher is better)", ylabel="Orders")

    # Monetary
    axes[2].bar(clusters, profile_df["Monetary_Mean"], color=colors, width=0.55, zorder=3)
    _apply_clean_styling(axes[2], title="Avg Monetary Spend (£)", ylabel="Spend (£)")

    plt.tight_layout()
    return fig
