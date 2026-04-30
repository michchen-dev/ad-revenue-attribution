"""Visualization helpers for the ad revenue attribution tool."""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def plot_revenue_trend(daily_df: pd.DataFrame) -> go.Figure:
    """Revenue trend with 7-day rolling average."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily_df["date"], y=daily_df["revenue"],
        mode="lines+markers", name="日收入",
        line=dict(color="#90CAF9", width=1.5),
        marker=dict(size=4, color="#1E88E5"),
    ))

    rolling = daily_df["revenue"].rolling(7).mean()
    fig.add_trace(go.Scatter(
        x=daily_df["date"], y=rolling,
        mode="lines", name="7日均值",
        line=dict(color="#FF6F00", width=2),
    ))

    # Anomaly marks for high-residual days
    residuals = daily_df["revenue"] - rolling
    std = residuals.std()
    anomaly_mask = abs(residuals) > 2 * std
    if anomaly_mask.any():
        anomaly_dates = daily_df[anomaly_mask]
        fig.add_trace(go.Scatter(
            x=anomaly_dates["date"], y=anomaly_dates["revenue"],
            mode="markers", name="疑似异常",
            marker=dict(color="red", size=10, symbol="x"),
        ))

    fig.update_layout(
        height=400, margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
        xaxis_title=None, yaxis_title="收入 ($)",
        legend=dict(orientation="h", yanchor="top", y=-0.15),
    )
    return fig


def plot_dimension_breakdown(df: pd.DataFrame, recent: pd.DataFrame, dims: list) -> go.Figure:
    """Multi-panel dimension breakdown charts."""
    n = len(dims)
    if n == 0:
        return go.Figure()

    fig = make_subplots(rows=1, cols=n, subplot_titles=[f"按{d}拆分" for d in dims],
                        specs=[[{"type": "pie"} for _ in range(n)]])

    colors = px.colors.qualitative.Set2
    for i, dim in enumerate(dims):
        rev_by_dim = df[df["date"].isin(recent["date"])].groupby(dim)["revenue"].sum().reset_index()
        fig.add_trace(
            go.Pie(labels=rev_by_dim[dim], values=rev_by_dim["revenue"],
                   marker_colors=colors, hole=0.4, textinfo="label+percent"),
            row=1, col=i + 1,
        )

    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20),
                      showlegend=False)
    return fig


def plot_anomaly_timeline(anomalies: pd.DataFrame, daily_df: pd.DataFrame) -> go.Figure:
    """Timeline chart showing revenue with anomaly markers."""
    fig = plot_revenue_trend(daily_df)

    if not anomalies.empty:
        for _, row in anomalies.iterrows():
            direction = "↑ 异常升高" if row.get("direction") == "up" else "↓ 异常下降"
            fig.add_annotation(
                x=row["date"], y=row["revenue"],
                text=f"{direction}<br>{row['change_pct']:+.1f}%",
                showarrow=True, arrowhead=2, arrowsize=1,
                arrowcolor="red", font=dict(size=10, color="red"),
                ax=0, ay=-40 if row.get("direction") == "up" else 40,
            )

    return fig


def plot_contribution_waterfall(attribution: dict) -> go.Figure:
    """Waterfall chart showing how each dimension segment contributes to total change."""
    measures = ["absolute"]
    labels = ["基线收入"]
    values = [attribution["baseline_revenue"]]

    for seg in attribution.get("segments", []):
        measures.append("relative")
        labels.append(f"{seg['dim']}={seg['value']}<br>({seg['contribution_pct']:+.1f}%)")
        values.append(seg["contribution"])

    measures.append("total")
    labels.append("实际收入")
    values.append(attribution["actual_revenue"])

    fig = go.Figure(go.Waterfall(
        name="收入变化归因",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=[f"${v:,.0f}" for v in values],
        connector=dict(line=dict(color="rgb(63, 63, 63)")),
        decreasing=dict(marker=dict(color="#EF5350")),
        increasing=dict(marker=dict(color="#43A047")),
        totals=dict(marker=dict(color="#1E88E5")),
    ))

    fig.update_layout(
        height=450, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title=None, yaxis_title="收入 ($)",
    )
    return fig


def plot_factor_decomposition(factor_decomp: dict) -> go.Figure:
    """Stacked bar chart showing Volume / eCPM / Fill Rate contribution breakdown."""
    factors = ["volume_effect", "ecpm_effect", "fill_effect", "interaction"]
    labels = ["展示量效应", "eCPM 效应", "填充率效应", "交互效应"]
    colors = ["#42A5F5", "#EF5350", "#66BB6A", "#BDBDBD"]

    values = [factor_decomp.get(f, 0) for f in factors]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"${v:+,.0f}" for v in values],
        textposition="outside",
    ))

    fig.update_layout(
        height=350, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title=None, yaxis_title="收入影响 ($)",
    )
    return fig


def plot_drilldown_treemap(attribution: dict) -> go.Figure:
    """Treemap showing hierarchical attribution tree."""
    ids = ["root"]
    labels = ["总收入变化"]
    parents = [""]
    values = [abs(attribution["total_change"])]

    def traverse(node, parent_id):
        for name, child in node.get("children", {}).items():
            cid = f"{parent_id}/{name}"
            ids.append(cid)
            labels.append(name)
            parents.append(parent_id)
            values.append(abs(child["contribution"]))
            traverse(child, cid)

    for key, seg in attribution.get("attribution_tree", {}).items():
        cid = f"root/{key}"
        ids.append(cid)
        labels.append(key)
        parents.append("root")
        values.append(abs(seg["contribution"]))
        traverse(seg, cid)

    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values,
        textinfo="label+value", hovertemplate="%{label}<br>$%{value:,.0f}",
        marker=dict(colors=px.colors.qualitative.Set3[:len(ids)]),
    ))

    fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    return fig
