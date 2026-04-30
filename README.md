# Ad Revenue Fluctuation Attribution Analysis Tool
## 广告变现数据波动归因分析工具

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/0xMJ/ad-revenue-attribution/actions/workflows/test.yml/badge.svg)](https://github.com/0xMJ/ad-revenue-attribution/actions/workflows/test.yml)

自动检测广告收入异常波动，并通过三层归因引擎定位根因。回答三个核心问题：
- **何时发生？** 多方法投票异常检测
- **哪里变化？** 按渠道/地区/广告格式分解收入变化贡献
- **为什么变化？** 将收入拆解为 展示量 × eCPM × 填充率 三因子效应

---

## ✨ Features

- **拖拽上传** CSV/Excel 数据，自动 schema 校验
- **多方法异常检测**：Modified Z-Score (MAD) + IQR + 移动平均偏离 + 周期对比 (WoW) + Grubbs 检验，投票确认
- **三层归因引擎**：
  1. 贡献分解 — 定位哪个维度（渠道/地区/格式）贡献了变化
  2. 因子分解 — Revenue = Impressions × Fill Rate × eCPM / 1000 拆解
  3. 递归下钻 — 逐层深挖到最细粒度的根因
- **交互式可视化**：瀑布图、树图、因子分解柱状图
- **AI 自然语言解释**：接入 Claude API / MiMo API 自动生成分析报告
- **一键导出** HTML 报告 / Excel 多 Sheet 数据

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/0xMJ/ad-revenue-attribution.git
cd ad-revenue-attribution

# Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
streamlit run app.py
```

打开浏览器访问 `http://localhost:8501`，上传数据或加载内置样本数据开始分析。

---

## 📊 数据格式

CSV/Excel 文件需包含以下列：

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | date | ✓ | 日期 (YYYY-MM-DD) |
| channel | string | ✓ | 广告渠道 (如 AdMob, Unity) |
| geo | string | ✓ | 地区 (如 US, IN) |
| impressions | int | ✓ | 广告展示量 |
| revenue | float | ✓ | 收入 (美元) |
| ecpm | float | ✓ | 千次展示收入 |
| fill_rate | float | ✓ | 填充率 (0-1) |
| ad_format | string | | 广告格式 (Banner, Interstitial 等) |
| clicks | int | | 点击量 |

内置样本数据包含 90 天、4 个渠道 × 6 个地区 × 4 种广告格式，含人工植入的异常点。

---

## 🧠 归因算法详解

### Layer 1: 异常检测

| 方法 | 原理 | 优势 |
|------|------|------|
| Modified Z-Score | 基于中位数绝对偏差 (MAD) | 对极端值鲁棒 |
| IQR | 四分位距法 | 非参数，不假设分布 |
| 移动平均偏离 | 偏离 7 日滚动均值超 2σ | 捕获趋势变化 |
| 周期对比 | 同比上周同日变化超 20% | 排除周周期性 |
| Grubbs 检验 | 经典正态性异常检验 | 补充验证 |

**投票机制**：至少 2 种方法同时标记才确认异常。

### Layer 2: 贡献分解

```
Contribution(D=v) = Revenue(Target, D=v) - Revenue(Baseline, D=v)
Contribution% = Contribution / Total_Change × 100%
```

### Layer 3: 因子分解

基于广告变现恒等式：

```
Revenue = Impressions × Fill_Rate × eCPM / 1000

展示量效应 = ΔImp × Fill_B × eCPM_B / 1000
填充率效应 = Imp_B × ΔFill × eCPM_B / 1000
eCPM 效应  = Imp_B × Fill_B × ΔeCPM / 1000
交互效应   = ΔRev - 展示量效应 - 填充率效应 - eCPM效应
```

### 递归下钻

在 Top 贡献维度上递归应用贡献分解，构建完整的归因树：
`Channel:AdMob → Geo:US → Format:Banner → eCPM 效应: -$6,000`

---

## 🤖 AI 集成

支持通过 Claude API（或 MiMo API 兼容端点）自动生成自然语言分析报告：

```
配置 → 选择异常日期 → 点击「生成 AI 洞察」
```

输出包含：一句话总结、发生了什么、根本原因、建议行动。

---

## 📁 项目结构

```
ad-revenue-attribution/
├── app.py                      # Streamlit 入口
├── pages/
│   ├── dashboard.py            # 数据仪表盘
│   ├── anomaly_detection.py    # 异常检测
│   ├── attribution.py          # 归因分析
│   ├── ai_insights.py          # AI 洞察
│   └── export.py               # 报告导出
├── src/
│   ├── data/                   # 数据加载、schema 校验、基线计算
│   ├── detection/              # 异常检测方法实现
│   ├── attribution/            # 贡献分解 + 因子分解 + 下钻
│   ├── visualization/          # Plotly 图表
│   ├── ai/                     # AI 自然语言解释
│   └── report/                 # HTML/Excel 报告生成
├── data/
│   ├── sample_ad_revenue.csv   # 90 天样本数据
│   └── generate_sample.py      # 样本数据生成脚本
├── tests/                      # 单元测试
└── .github/workflows/          # CI
```

---

## 🛠️ Tech Stack

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Streamlit | 交互式 Web 界面 |
| 数据处理 | Pandas, NumPy | 数据加载、聚合、转换 |
| 统计分析 | SciPy | 异常检验、分布计算 |
| 可视化 | Plotly | 交互式图表 |
| AI | Claude API / MiMo API | 自然语言解释 |
| 报告 | openpyxl | Excel 多 Sheet 导出 |
| 测试 | pytest | 单元测试 |

---

## 🗺️ Roadmap

- [ ] 实时数据连接器（AdMob API, AppLovin API）
- [ ] Shapley Value 归因验证
- [ ] Slack/企业微信异常告警推送
- [ ] 多语言界面（英文/中文/日文）
- [ ] 时间序列预测（Prophet / ARIMA）对比异常检测

---

## 📄 License

MIT

---

## 🙏 致谢

本项目基于小米 MiMo Orbit 百万亿 Token 创造者激励计划开发。
开发过程中使用 Claude Code + MiMo 系列模型进行 AI 辅助编程。
