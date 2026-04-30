"""Attribution analysis page: contribution waterfall, factor decomposition, drill-down explorer."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.data.baseline import compute_baseline
from src.attribution.drilldown import full_attribution
from src.attribution.factor_decomp import decompose_segments
from src.visualization.trend_charts import (
    plot_contribution_waterfall,
    plot_factor_decomposition,
    plot_drilldown_treemap,
)


st.title("波动归因分析")
st.caption("定位收入波动的根因维度与因子（展示量 / eCPM / 填充率）")

if "df" not in st.session_state or st.session_state.df is None:
    st.info("请先加载数据")
    st.stop()

df = st.session_state.df

# --- Anomaly Selection ---
col_a, col_b = st.columns(2)
with col_a:
    if "anomalies" in st.session_state and not st.session_state.anomalies.empty:
        anomaly_dates = st.session_state.anomalies["date"].dt.date.tolist()
        selected = st.selectbox("选择异常日期", anomaly_dates,
                                format_func=lambda d: f"{d} (被 {st.session_state.anomalies[st.session_state.anomalies['date'].dt.date == d].iloc[0]['methods_flagged']} 标记)")
    else:
        available_dates = sorted(df["date"].dt.date.unique())
        selected = st.selectbox("选择分析日期", available_dates)

with col_b:
    baseline_method = st.selectbox("基线计算方法", ["rolling_7d", "wow", "month_avg"],
                                   format_func=lambda m: {
                                       "rolling_7d": "前7日均值",
                                       "wow": "同比上周同日",
                                       "month_avg": "前30日均值",
                                   }[m])

if not selected:
    st.stop()

baseline = compute_baseline(df, pd.Timestamp(selected), baseline_method)

if baseline.empty:
    st.error("基线数据为空，请选择其他日期或基线方法")
    st.stop()

# --- Run Attribution ---
attribution = full_attribution(df, selected, baseline)

# --- Key Metrics ---
st.subheader("波动概览")
m1, m2, m3 = st.columns(3)
with m1:
    delta_color = "inverse" if attribution["total_change"] < 0 else "normal"
    st.metric("收入变化", f"${attribution['total_change']:+,.0f}",
              f"{attribution['total_change_pct']:+.1f}%", delta_color=delta_color)
with m2:
    st.metric("实际收入", f"${attribution['actual_revenue']:,.2f}")
with m3:
    st.metric("基线收入", f"${attribution['baseline_revenue']:,.2f}")

# --- Contribution Waterfall ---
st.subheader("维度贡献瀑布图")
waterfall_data = {
    "baseline_revenue": attribution["baseline_revenue"],
    "actual_revenue": attribution["actual_revenue"],
    "segments": attribution["segments"][:10],  # Top 10
}
st.plotly_chart(plot_contribution_waterfall(waterfall_data), use_container_width=True)

# --- Top Drivers Table ---
st.subheader("Top 驱动因素")
top_drivers = pd.DataFrame(attribution["segments"][:10])
top_drivers["segment"] = top_drivers.apply(lambda r: f"{r['dim']}={r['value']}", axis=1)
top_drivers = top_drivers[["segment", "contribution", "contribution_pct", "actual", "baseline"]]
top_drivers.columns = ["细分维度", "贡献 ($)", "贡献 %", "实际", "基线"]
st.dataframe(top_drivers, use_container_width=True, hide_index=True)

# --- Factor Decomposition ---
st.subheader("因子分解（展示量 / eCPM / 填充率）")
st.caption("Revenue = Impressions × Fill Rate × eCPM / 1000")

factor_df = decompose_segments(df, selected, baseline, top_n=5)
if not factor_df.empty:
    st.dataframe(factor_df.style.format({
        "volume_effect": "${:+,.0f}",
        "ecpm_effect": "${:+,.0f}",
        "fill_effect": "${:+,.0f}",
        "interaction": "${:+,.0f}",
        "revenue_change": "${:+,.0f}",
        "contribution_pct": "{:+.1f}%",
    }), use_container_width=True, hide_index=True)

    # Factor chart for top segment
    top_seg = factor_df.iloc[0]
    factor_decomp_data = {
        "volume_effect": top_seg["volume_effect"],
        "ecpm_effect": top_seg["ecpm_effect"],
        "fill_effect": top_seg["fill_effect"],
        "interaction": top_seg["interaction"],
    }
    st.plotly_chart(plot_factor_decomposition(factor_decomp_data), use_container_width=True)

# --- Drill-down Treemap ---
st.subheader("归因下钻树图")
st.plotly_chart(plot_drilldown_treemap(attribution), use_container_width=True)

# --- Raw Attribution Tree ---
with st.expander("归因树（JSON）"):
    tree_view = attribution.copy()
    # Remove full segments list to keep it readable
    st.json(tree_view)
