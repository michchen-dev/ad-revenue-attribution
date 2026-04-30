"""Export page: HTML/PDF report and Excel data export."""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.data.baseline import compute_baseline
from src.attribution.drilldown import full_attribution
from src.attribution.factor_decomp import decompose_segments
from src.report.generator import generate_html_report, generate_excel_export


st.title("报告导出")
st.caption("导出归因分析报告或原始数据")

if "df" not in st.session_state or st.session_state.df is None:
    st.info("请先加载数据")
    st.stop()

df = st.session_state.df

# --- Report Configuration ---
st.subheader("报告配置")

c1, c2 = st.columns(2)
with c1:
    if "anomalies" in st.session_state and not st.session_state.anomalies.empty:
        dates = st.session_state.anomalies["date"].dt.date.tolist()
        export_date = st.selectbox("分析日期", dates)
    else:
        all_dates = sorted(df["date"].dt.date.unique())
        export_date = st.selectbox("分析日期", all_dates)

    baseline_method = st.selectbox("基线方法", ["rolling_7d", "wow", "month_avg"],
                                   format_func=lambda m: {
                                       "rolling_7d": "前7日均值",
                                       "wow": "同比上周同日",
                                       "month_avg": "前30日均值",
                                   }[m])

with c2:
    st.caption("导出选项")
    include_raw = st.checkbox("包含原始数据", value=True)
    include_anomalies = st.checkbox("包含异常检测结果", value=True)
    include_attribution = st.checkbox("包含归因分析", value=True)

# --- Generate ---
if st.button("生成报告", type="primary"):
    with st.spinner("正在生成报告..."):
        baseline = compute_baseline(df, pd.Timestamp(export_date), baseline_method)
        attribution = full_attribution(df, export_date, baseline)
        factor_df = decompose_segments(df, export_date, baseline, top_n=5)

        # HTML Report
        html = generate_html_report(attribution, factor_df)

        # Excel Export
        anomalies = st.session_state.get("anomalies") if include_anomalies else None
        attr_for_excel = attribution if include_attribution else None
        excel_bytes = generate_excel_export(df, anomalies, attr_for_excel)

        # Display
        st.success("报告生成完成")

        tab1, tab2 = st.tabs(["HTML 报告预览", "下载"])

        with tab1:
            st.components.v1.html(html, height=800, scrolling=True)

        with tab2:
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "下载 HTML 报告",
                    data=html,
                    file_name=f"attribution_report_{export_date}.html",
                    mime="text/html",
                    use_container_width=True,
                )
            with col_b:
                st.download_button(
                    "下载 Excel 数据",
                    data=excel_bytes,
                    file_name=f"ad_revenue_data_{export_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )


# --- Quick Export ---
st.divider()
st.subheader("快速数据导出")

quick_date = st.date_input("导出日期范围",
                           [df["date"].min().date(), df["date"].max().date()])

quick_df = df[(df["date"].dt.date >= quick_date[0]) & (df["date"].dt.date <= quick_date[1])]

if not quick_df.empty:
    csv = quick_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"下载 CSV ({len(quick_df):,} 行)",
        data=csv,
        file_name=f"ad_revenue_{quick_date[0]}_{quick_date[1]}.csv",
        mime="text/csv",
    )
