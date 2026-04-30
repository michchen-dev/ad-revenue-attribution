"""Ad Revenue Fluctuation Attribution Analysis Tool — 广告变现数据波动归因分析工具.

Entry point for the Streamlit multi-page app.
"""

import streamlit as st

st.set_page_config(
    page_title="Ad Revenue Attribution",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = {
    "📊 数据仪表盘": "pages/dashboard.py",
    "🔍 异常检测": "pages/anomaly_detection.py",
    "🎯 归因分析": "pages/attribution.py",
    "🤖 AI 洞察": "pages/ai_insights.py",
    "📥 报告导出": "pages/export.py",
}

pg = st.navigation([st.Page(path, label=label) for label, path in pages.items()])

st.sidebar.markdown("---")
st.sidebar.caption("Ad Revenue Attribution Tool v1.0")
st.sidebar.caption("Built for MiMo Orbit Program")

pg.run()
