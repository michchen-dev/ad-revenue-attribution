"""Dashboard page: data upload, KPI cards, trend charts, dimension breakdown."""

import streamlit as st
import pandas as pd
import numpy as np

from src.data.loader import DataLoader
from src.visualization.trend_charts import plot_revenue_trend, plot_dimension_breakdown, plot_kpi_cards


def init_session():
    defaults = {
        "df": None,
        "daily_df": None,
        "errors": [],
        "uploaded": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()

st.title("广告变现数据波动归因分析")
st.caption("上传广告收入数据，自动检测异常波动并归因分析")

# --- File Upload ---
uploaded = st.file_uploader(
    "上传 CSV 或 Excel 文件",
    type=["csv", "xlsx", "xls"],
    help="必须包含列：date, channel, geo, impressions, revenue, ecpm, fill_rate",
)

if uploaded:
    loader = DataLoader()
    try:
        df = loader.load(uploaded)
        st.session_state.df = df
        st.session_state.errors = loader.errors
        st.session_state.uploaded = True
        st.session_state.daily_df = df.groupby("date").agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum") if "clicks" in df.columns else ("impressions", "sum"),
            revenue=("revenue", "sum"),
            ecpm=("ecpm", "mean"),
            fill_rate=("fill_rate", "mean"),
        ).reset_index()
    except Exception as e:
        st.error(f"文件加载失败: {e}")
        st.stop()

if not st.session_state.uploaded:
    st.info("请上传广告收入数据文件开始分析，或使用内置样本数据体验。")
    if st.button("加载内置样本数据"):
        from pathlib import Path
        sample_path = Path(__file__).parent.parent / "data" / "sample_ad_revenue.csv"
        df = pd.read_csv(sample_path)
        df["date"] = pd.to_datetime(df["date"])
        st.session_state.df = df
        st.session_state.errors = []
        st.session_state.uploaded = True
        st.session_state.daily_df = df.groupby("date").agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum") if "clicks" in df.columns else ("impressions", "sum"),
            revenue=("revenue", "sum"),
            ecpm=("ecpm", "mean"),
            fill_rate=("fill_rate", "mean"),
        ).reset_index()
        st.rerun()
    st.stop()

df = st.session_state.df
daily = st.session_state.daily_df

if st.session_state.errors:
    for err in st.session_state.errors:
        st.warning(err)

# --- Date Filter ---
col1, col2 = st.columns([3, 1])
with col1:
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    date_range = st.date_input("日期范围", [min_date, max_date], min_value=min_date, max_value=max_date)
with col2:
    selected_dims = st.multiselect(
        "分析维度", ["channel", "geo", "ad_format"],
        default=["channel", "geo"],
    )

# --- KPI Cards ---
st.subheader("核心指标")
recent_cutoff = df["date"].max() - pd.Timedelta(days=7)
recent = daily[daily["date"] >= recent_cutoff]
prior = daily[(daily["date"] >= recent_cutoff - pd.Timedelta(days=7)) & (daily["date"] < recent_cutoff)]

rev_now = recent["revenue"].sum()
rev_prior = prior["revenue"].sum()
rev_change = (rev_now - rev_prior) / rev_prior * 100 if rev_prior else 0

ecpm_now = recent["ecpm"].mean()
ecpm_prior = prior["ecpm"].mean()
ecpm_change = (ecpm_now - ecpm_prior) / ecpm_prior * 100 if ecpm_prior else 0

fill_now = recent["fill_rate"].mean()
fill_prior = prior["fill_rate"].mean()
fill_change = (fill_now - fill_prior) / fill_prior * 100 if fill_prior else 0

imp_now = recent["impressions"].sum()
imp_prior = prior["impressions"].sum()
imp_change = (imp_now - imp_prior) / imp_prior * 100 if imp_prior else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("总收入 (7天)", f"${rev_now:,.0f}", f"{rev_change:+.1f}%")
with k2:
    st.metric("平均 eCPM", f"${ecpm_now:.2f}", f"{ecpm_change:+.1f}%")
with k3:
    st.metric("平均填充率", f"{fill_now:.1%}", f"{fill_change:+.1f}%")
with k4:
    st.metric("总展示量 (7天)", f"{imp_now:,.0f}", f"{imp_change:+.1f}%")

# --- Revenue Trend ---
st.subheader("收入趋势")
fig_trend = plot_revenue_trend(daily)
st.plotly_chart(fig_trend, use_container_width=True)

# --- Dimension Breakdown ---
st.subheader("维度拆分")
fig_dims = plot_dimension_breakdown(df, recent, selected_dims)
st.plotly_chart(fig_dims, use_container_width=True)

# --- Data Preview ---
with st.expander("原始数据预览"):
    st.dataframe(df.head(100), use_container_width=True, hide_index=True)
    st.caption(f"共 {len(df):,} 行数据，日期范围 {df['date'].min().date()} ~ {df['date'].max().date()}")
