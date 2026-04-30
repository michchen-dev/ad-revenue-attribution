"""PDF and HTML report generation for attribution analysis."""

import io
from datetime import datetime
import pandas as pd


def generate_html_report(attribution: dict, factor_df: pd.DataFrame = None) -> str:
    """Generate a self-contained HTML report."""
    segments_html = ""
    for seg in attribution.get("segments", [])[:10]:
        sign = "+" if seg["contribution"] >= 0 else ""
        segments_html += f"""
        <tr>
            <td>{seg['dim']}={seg['value']}</td>
            <td style="color:{'red' if seg['contribution'] < 0 else 'green'}">${seg['contribution']:+,.0f}</td>
            <td>{seg['contribution_pct']:+.1f}%</td>
            <td>${seg['actual']:,.2f}</td>
            <td>${seg['baseline']:,.2f}</td>
        </tr>"""

    factor_html = ""
    if factor_df is not None and not factor_df.empty:
        for _, row in factor_df.iterrows():
            factor_html += f"""
            <tr>
                <td>{row.get('segment', 'N/A')}</td>
                <td>${row.get('volume_effect', 0):+,.0f}</td>
                <td>${row.get('ecpm_effect', 0):+,.0f}</td>
                <td>${row.get('fill_effect', 0):+,.0f}</td>
                <td>${row.get('revenue_change', 0):+,.0f}</td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>广告变现波动归因分析报告</title>
    <style>
        body {{ font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; color: #333; }}
        h1 {{ color: #1E88E5; border-bottom: 2px solid #1E88E5; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #F5F7FA; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
        .metric {{ text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #F5F7FA; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <h1>广告变现数据波动归因分析报告</h1>
    <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    <p>分析日期: {attribution.get('target_date', 'N/A')}</p>

    <div class="summary">
        <h2>波动概览</h2>
        <div class="summary-grid">
            <div class="metric">
                <div class="metric-value" style="color:{'red' if attribution.get('total_change', 0) < 0 else 'green'}">
                    ${attribution.get('total_change', 0):+,.0f}
                </div>
                <div class="metric-label">收入变化 ({attribution.get('total_change_pct', 0):+.1f}%)</div>
            </div>
            <div class="metric">
                <div class="metric-value">${attribution.get('actual_revenue', 0):,.2f}</div>
                <div class="metric-label">实际收入</div>
            </div>
            <div class="metric">
                <div class="metric-value">${attribution.get('baseline_revenue', 0):,.2f}</div>
                <div class="metric-label">基线收入</div>
            </div>
        </div>
    </div>

    <h2>维度贡献分解</h2>
    <table>
        <tr><th>维度</th><th>贡献 ($)</th><th>贡献 %</th><th>实际</th><th>基线</th></tr>
        {segments_html}
    </table>

    <h2>因子分解（展示量 / eCPM / 填充率）</h2>
    <table>
        <tr><th>细分</th><th>展示量效应</th><th>eCPM 效应</th><th>填充率效应</th><th>总变化</th></tr>
        {factor_html if factor_html else '<tr><td colspan="5">无因子分解数据</td></tr>'}
    </table>

    <div class="footer">
        <p>由 Ad Revenue Attribution Tool 自动生成 | MiMo Orbit Program</p>
    </div>
</body>
</html>"""
    return html


def generate_excel_export(df: pd.DataFrame, anomalies: pd.DataFrame = None,
                          attribution: dict = None) -> bytes:
    """Generate Excel workbook with multiple sheets."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="原始数据", index=False)

        daily = df.groupby("date").agg(
            impressions=("impressions", "sum"),
            revenue=("revenue", "sum"),
            ecpm=("ecpm", "mean"),
            fill_rate=("fill_rate", "mean"),
        ).reset_index()
        daily.to_excel(writer, sheet_name="日汇总", index=False)

        if anomalies is not None and not anomalies.empty:
            export_anomalies = anomalies.copy()
            export_anomalies["date"] = export_anomalies["date"].dt.date
            export_anomalies.to_excel(writer, sheet_name="异常点", index=False)

        if attribution and attribution.get("segments"):
            seg_df = pd.DataFrame(attribution["segments"])
            seg_df.to_excel(writer, sheet_name="归因分析", index=False)

    return output.getvalue()
