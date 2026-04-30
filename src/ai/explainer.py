"""AI-powered natural language explainer for ad revenue anomalies.

Uses Claude API (or compatible MiMo API) to generate human-readable
attribution narratives from structured analysis results.
"""

import json


def build_prompt(attribution: dict) -> str:
    """Build a structured prompt for the LLM based on attribution results."""
    factors = attribution.get("factor_decomp", {})

    segments_summary = []
    for seg in attribution.get("segments", [])[:5]:
        segments_summary.append(
            f"  - {seg['dim']}={seg['value']}: 贡献 ${seg['contribution']:+,.0f} ({seg['contribution_pct']:+.1f}%)"
        )

    prompt = f"""你是一位广告变现数据分析专家。请根据以下数据波动归因结果，用简洁的中文解释发生了什么、为什么发生、以及建议下一步排查方向。

## 收入波动情况
- 分析日期: {attribution.get('target_date', 'N/A')}
- 实际收入: ${attribution.get('actual_revenue', 0):,.2f}
- 基线收入: ${attribution.get('baseline_revenue', 0):,.2f}
- 变化: ${attribution.get('total_change', 0):+,.0f} ({attribution.get('total_change_pct', 0):+.1f}%)

## Top 贡献维度
{chr(10).join(segments_summary) if segments_summary else '无显著维度贡献'}

## 因子分解（展示量 × eCPM × 填充率）
- 展示量效应: ${factors.get('volume_effect', 0):+,.0f}
- eCPM 效应: ${factors.get('ecpm_effect', 0):+,.0f}
- 填充率效应: ${factors.get('fill_effect', 0):+,.0f}
- 交互效应: ${factors.get('interaction', 0):+,.0f}

请按照以下结构回复（不要用 markdown 标题，用加粗文本）：

**一句话总结**: [1句话说明主要波动和根因]

**发生了什么**: [2-3句话描述收入波动情况和关键数据]

**根本原因**: [基于归因数据，指出是哪个维度的哪个因子导致了波动]

**建议行动**: [2-3条具体的排查方向，如检查特定渠道的竞价策略、确认特定地区的填充率等]
"""
    return prompt


def generate_explanation(attribution: dict, api_key: str = None, base_url: str = None) -> str:
    """Generate natural language explanation using Claude API.

    Args:
        attribution: Full attribution analysis result
        api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        base_url: Optional alternative API base URL (for MiMo compatibility)

    Returns:
        Natural language explanation string
    """
    if api_key:
        import os
        os.environ["ANTHROPIC_API_KEY"] = api_key

    try:
        from anthropic import Anthropic

        client_kwargs = {}
        if base_url:
            client_kwargs["base_url"] = base_url

        client = Anthropic(**client_kwargs)
        prompt = build_prompt(attribution)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            temperature=0.3,
            system="你是一位专业的广告变现数据分析师。回答简洁、准确、可操作。",
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    except ImportError:
        return _simulated_explanation(attribution)
    except Exception as e:
        return f"AI 解释生成失败: {e}\n\n可手动参考下方归因结果进行分析。"


def _simulated_explanation(attribution: dict) -> str:
    """Generate a rule-based explanation when API is unavailable."""
    total_change = attribution.get("total_change", 0)
    total_change_pct = attribution.get("total_change_pct", 0)
    direction = "下降" if total_change < 0 else "上升"

    segments = attribution.get("segments", [])
    top_seg = segments[0] if segments else None

    factors = attribution.get("factor_decomp", {})
    volume = factors.get("volume_effect", 0)
    ecpm = factors.get("ecpm_effect", 0)
    fill = factors.get("fill_effect", 0)

    # Find dominant factor
    factor_effects = {"展示量": volume, "eCPM": ecpm, "填充率": fill}
    dominant = max(factor_effects, key=lambda k: abs(factor_effects[k]))

    lines = [
        f"**一句话总结**: 当日收入${direction}{abs(total_change_pct):.1f}%，主要由{top_seg['dim'] if top_seg else '未知维度'}维度变化驱动。",
        "",
        f"**发生了什么**: 分析日期收入为 ${attribution.get('actual_revenue', 0):,.2f}，"
        f"较基线 ${attribution.get('baseline_revenue', 0):,.2f} 变化 ${total_change:+,.0f}"
        f"（{total_change_pct:+.1f}%）。",
    ]

    if top_seg:
        lines.append(
            f"其中 **{top_seg['dim']}={top_seg['value']}** 是最大贡献者，"
            f"贡献了 ${top_seg['contribution']:+,.0f}（{top_seg['contribution_pct']:+.1f}%）。"
        )

    lines.extend([
        "",
        f"**根本原因**: {dominant}效应最大（${factor_effects[dominant]:+,.0f}）。",
    ])

    if dominant == "eCPM":
        lines.append("eCPM下降通常与竞价密度降低、广告主预算缩减或竞价算法调整有关。")
    elif dominant == "展示量":
        lines.append("展示量变化通常与流量波动、用户活跃度或广告请求量变化有关。")
    elif dominant == "填充率":
        lines.append("填充率下降通常与广告库存需求不足、网络连接问题或广告源配置有关。")

    lines.extend([
        "",
        "**建议行动**:",
        f"1. 排查 {top_seg['dim'] + '=' + top_seg['value'] if top_seg else '对应维度'} 的详细数据，确认变化时间点",
        f"2. 检查{dominant}相关指标是否有异常配置或外部因素",
        "3. 对比同维度其他分组的{dominant}变化，判断是否为孤立事件",
    ])

    return "\n".join(lines)
