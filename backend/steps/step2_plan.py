"""
steps/step2_plan.py
-------------------
Step 2: Research Plan Generation（初始研究结构生成）

职责：
- 基于 Step 1 的 requirements
- 生成“假设性的、可失败的”研究结构
- 只生成章节级研究问题，不写正文、不总结、不论证

设计原则：
- LLM 只负责“给出结构建议”
- 系统负责结构裁决与兜底
- 输出稳定 contract，供 Step 3 使用
"""

from __future__ import annotations

from typing import Dict, Any, List
import uuid

from core.llm_gateway import LLMGateway


# =========================
# 1) Prompt（Step 2 私有）
# =========================

SYSTEM_RESEARCH_PLANNER = """
你是“研究结构规划器（Research Planner）”。

你的任务：
- 基于给定研究需求，生成一个“初始研究结构（Research Plan）”
- 该结构用于后续文献检索与子目标拆分

必须遵守的硬规则：
1. 只生成结构，不生成任何正文或结论
2. 章节数量控制在 3~6 个
3. 每个章节是“研究问题 / 研究视角”，不是写作小节
4. 不要拆到方法实现或实验细节
5. 不引入需求中未出现的新研究方向
6. 不假设任何具体文献内容

输出要求：
- 必须输出严格 JSON
- 字段结构必须完全一致
""".strip()


USER_RESEARCH_PLANNER_INSTRUCTION = """
研究需求（requirements）如下：
{requirements_json}

请生成初始研究结构，严格使用以下 JSON 格式（字段不可增减）：

{{
  "title": str,
  "sections": [
    {{
      "id": str,
      "title": str,
      "intent_hint": str
    }}
  ],
  "assumptions": str
}}
""".strip()


# =========================
# 2) 核心函数
# =========================

def generate_research_plan(
    gateway: LLMGateway,
    requirements: Dict[str, Any],
) -> Dict[str, Any]:
    """
    输入：
      - requirements（来自 Step 1，已被系统裁决）

    输出：
      - ResearchPlan（coarse / hypothesis）
    """

    messages = [
        {"role": "system", "content": SYSTEM_RESEARCH_PLANNER},
        {
            "role": "user",
            "content": USER_RESEARCH_PLANNER_INSTRUCTION.format(
                requirements_json=requirements
            ),
        },
    ]

    raw_plan = gateway.ask_json(messages, timeout=60.0)

    # =========================
    # 3) 系统级裁决与兜底
    # =========================

    sections = raw_plan.get("sections", [])

    # 兜底：章节数量
    if not (3 <= len(sections) <= 6):
        sections = sections[:6]

    normalized_sections: List[Dict[str, Any]] = []

    for idx, sec in enumerate(sections, start=1):
        normalized_sections.append({
            "section_id": f"S{idx}",
            "title": sec.get("title", "").strip(),
            "intent_hint": sec.get("intent_hint", "").strip(),
            "status": "active",          # Step 5 可能会 downgrade / remove
        })

    plan = {
        "plan_id": str(uuid.uuid4()),
        "title": raw_plan.get("title", "").strip(),
        "plan_level": "coarse",          # 明确标记：初始假设结构
        "hypothesis": True,              # ⚠️ 非常关键
        "sections": normalized_sections,
        "assumptions": raw_plan.get("assumptions", ""),
        "source_requirements_snapshot": requirements,
    }

    return plan
