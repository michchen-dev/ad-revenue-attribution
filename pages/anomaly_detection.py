"""Anomaly detection page: configuration, method agreement matrix, anomaly timeline."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.detection.anomaly import detect_anomalies
from src.detection.methods import ALL_METHODS
from src.visualization.trend_charts import plot_anomaly_timeline


st.title("异常波动检测")
st.caption("多方法投票机制自动识别收入异常波动")

if "df" not in st.session_state or st.session_state.df is None:
    st.info("请先在上传数据页面加载数据")
    st.stop()

daily = st.session_state.daily_df

# --- Configuration ---
with st.sidebar:
    st.subheader("检测配置")
    sensitivity = st.slider("灵敏度", 0.5, 3.0, 1.0, 0.1,
                            help="小于1=更敏感（检出更多），大于1=更保守")
    min_agreement = st.slider("最少方法一致数", 1, 4, 2,
                              help="多少种方法标记同一日期才视为异常")

    st.subheader("检测方法")
    enabled = {}
    for key, (name, _) in ALL_METHODS.items():
        enabled[key] = st.checkbox(name, value=True)

    run = st.button("执行检测", type="primary", use_container_width=True)

# --- Detection Results ---
if run:
    methods = [k for k, v in enabled.items() if v]
    if not methods:
        st.warning("请至少选择一种检测方法")
        st.stop()

    with st.spinner("运行多方法异常检测..."):
        anomalies = detect_anomalies(daily, methods, sensitivity, min_agreement)

    st.session_state.anomalies = anomalies

else:
    anomalies = st.session_state.get("anomalies")

if anomalies is None:
    st.info("配置参数后点击「执行检测」")
    st.stop()

if anomalies.empty:
    st.success("未检测到异常波动")
    st.stop()

st.subheader(f"检测结果：{len(anomalies)} 个异常点")

# --- Summary Metrics ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("异常总数", len(anomalies))
with c2:
    up_count = (anomalies["direction"] == "up").sum()
    st.metric("↑ 上升异常", up_count)
with c3:
    down_count = (anomalies["direction"] == "down").sum()
    st.metric("↓ 下降异常", down_count)

# --- Timeline Chart ---
st.plotly_chart(plot_anomaly_timeline(anomalies, daily), use_container_width=True)

# --- Anomaly Table ---
st.subheader("异常明细")
display_cols = ["date", "direction", "change_pct", "severity", "methods_flagged"]
display_df = anomalies[display_cols].copy()
display_df["date"] = display_df["date"].dt.date
display_df["change_pct"] = display_df["change_pct"].apply(lambda x: f"{x:+.1f}%")
display_df["severity"] = display_df["severity"].apply(lambda x: f"{x:.0%}")
display_df["methods_flagged"] = display_df["methods_flagged"].apply(lambda m: ", ".join(m))
display_df["direction"] = display_df["direction"].map({"up": "↑ 上升", "down": "↓ 下降"})

event = st.dataframe(
    display_df, use_container_width=True, hide_index=True,
    selection_mode="single", on_select="rerun",
)

# --- Method Agreement Matrix ---
st.subheader("检测方法一致性")
if len(methods) >= 2:
    method_votes = pd.DataFrame({
        name: anomalies["methods_flagged"].apply(lambda m: name in m).astype(int)
        for name in [ALL_METHODS[k][0] for k in methods]
    })
    fig = px.imshow(method_votes.T, aspect="auto",
                    labels=dict(x="异常点序号", y="检测方法", color="标记"),
                    color_continuous_scale="RdYlGn",
                    title="方法-异常点 标记矩阵")
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- Selected Anomaly Detail ---
if event and event.selection and "rows" in event.selection:
    selected_idx = event.selection["rows"][0]
    selected = anomalies.iloc[selected_idx]

    st.divider()
    st.subheader(f"异常详情：{selected['date'].date()}")

    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        st.metric("当日收入", f"${selected['revenue']:,.2f}",
                  f"{selected['change_pct']:+.1f}%")
    with dc2:
        st.metric("基线收入", f"${selected['baseline']:,.2f}")
    with dc3:
        st.metric("严重度", f"{selected['severity']:.0%}")

    st.write(f"**标记方法**: {', '.join(selected['methods_flagged'])}")

    if st.button("分析此异常归因", type="primary"):
        st.session_state.selected_anomaly_date = str(selected["date"].date())
        st.switch_page("pages/attribution.py")
