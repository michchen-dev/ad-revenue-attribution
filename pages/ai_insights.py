"""AI Insights page: natural language explanations of detected anomalies."""

import streamlit as st
import pandas as pd

from src.data.baseline import compute_baseline
from src.attribution.drilldown import full_attribution
from src.attribution.factor_decomp import decompose_segments


st.title("AI 洞察")
st.caption("AI 自动生成收入波动自然语言解释")

if "df" not in st.session_state or st.session_state.df is None:
    st.info("请先加载数据")
    st.stop()

# --- API Configuration ---
with st.sidebar:
    st.subheader("API 配置")
    api_key = st.text_input("Anthropic API Key", type="password",
                            help="留空则使用规则解释模式。也可填入 MiMo API Key 及对应 Base URL")
    base_url = st.text_input("API Base URL (可选)",
                             placeholder="https://api.mimo.xiaomi.com/v1",
                             help="使用 MiMo 模型时填入对应 endpoint")

    st.divider()
    st.subheader("分析日期")
    if "anomalies" in st.session_state and not st.session_state.anomalies.empty:
        dates = st.session_state.anomalies["date"].dt.date.tolist()
        selected_date = st.selectbox("选择异常日期", dates)
    else:
        dates = sorted(st.session_state.df["date"].dt.date.unique())
        selected_date = st.selectbox("选择日期", dates)

    baseline_method = st.selectbox("基线方法", ["rolling_7d", "wow", "month_avg"],
                                   format_func=lambda m: {
                                       "rolling_7d": "前7日均值",
                                       "wow": "同比上周同日",
                                       "month_avg": "前30日均值",
                                   }[m])

    analyze = st.button("生成 AI 洞察", type="primary", use_container_width=True)

if not analyze:
    st.info("配置参数后点击「生成 AI 洞察」")
    st.stop()

# --- Run Analysis ---
df = st.session_state.df
baseline = compute_baseline(df, pd.Timestamp(selected_date), baseline_method)
attribution = full_attribution(df, selected_date, baseline)

# Add factor decomp for top segment
factor_df = decompose_segments(df, selected_date, baseline, top_n=1)
if not factor_df.empty:
    attribution["factor_decomp"] = factor_df.iloc[0].to_dict()

# --- Generate Explanation ---
with st.spinner("AI 正在分析数据..."):
    from src.ai.explainer import generate_explanation
    explanation = generate_explanation(attribution, api_key=api_key if api_key else None,
                                       base_url=base_url if base_url else None)

# --- Display ---
st.subheader("分析结果")
st.markdown(explanation)

# --- Attribution Summary ---
st.divider()
st.subheader("归因摘要")

c1, c2 = st.columns(2)
with c1:
    st.metric("收入变化", f"${attribution['total_change']:+,.0f}",
              f"{attribution['total_change_pct']:+.1f}%")

top3 = attribution["segments"][:3]
for seg in top3:
    st.metric(f"{seg['dim']}={seg['value']}",
              f"${seg['contribution']:+,.0f}",
              f"{seg['contribution_pct']:+.1f}%")

with c2:
    if "factor_decomp" in attribution:
        fd = attribution["factor_decomp"]
        st.metric("展示量效应", f"${fd.get('volume_effect', 0):+,.0f}")
        st.metric("eCPM 效应", f"${fd.get('ecpm_effect', 0):+,.0f}")
        st.metric("填充率效应", f"${fd.get('fill_effect', 0):+,.0f}")
