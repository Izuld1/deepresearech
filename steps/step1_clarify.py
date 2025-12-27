"""
steps/step1_clarify.py
----------------------
Step 1: Research Requirement Clarification（需求澄清）

设计原则：
- Step 1 只负责澄清业务逻辑，不直接依赖具体 LLM SDK
- 通过 LLMGateway 注入分析能力（dependency injection）
- 输出稳定的 Research Contract（dict），供后续步骤消费

系统立场（非常重要）：
- 默认采用【封闭研究空间】：
  除非用户明确允许，否则只使用本地 / 已上传文献
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import copy

from core.llm_gateway import LLMGateway


# =========================
# 1) Prompt 模板（Step 1 私有）
# =========================
import datetime

SYSTEM_REQUIREMENTS_ANALYST = """
你是“研究需求澄清助手”。

你的任务：
- 将用户研究需求解析为结构化 JSON
- 如果信息不足，提出澄清问题

规则：
1. 总澄清轮数 ≤ 5（包含当前轮）
2. 每轮最多提出 1~3 个问题
3. 问题要具体、可选项化、简短
4. 如果已经足够明确，不要再问
5. 必须输出【严格 JSON】，不允许任何额外文字
注意事项：
- 请优先识别那些会影响研究范围、检索策略或结构划分的歧义。
- 如果用户没有明确使用外部文献，默认只使用自己的知识库，系统有默认数据库。默认只使用自己数据。默认不使用外部数据也可以完成任务。
- 当前时间为

"""+ f'{datetime.datetime.now()}'.strip()

JSON_SCHEMA_INSTRUCTION = """
请根据对话上下文，输出以下 JSON（字段不可增减）：

{
  "goal": str,
  "topic": str,
  "domain": str,
  "output_type": "survey"|"report"|"outline",
  "audience": "academic"|"engineering"|"business"|"general",
  "depth": "shallow"|"medium"|"deep",
  "language": "zh"|"en",
  "literature_scope": {
    "only_uploaded": bool,
    "time_range": str,
    "must_include": list[str],
    "must_exclude": list[str]
  },
  "constraints": {
    "no_external_knowledge": bool,
    "citation_style": "inline"|"numbered"|"none",
    "length": "short"|"medium"|"long"
  },
  "missing_fields": list[str],
  "ambiguities": list[str],
  "next_questions": list[str]
}

默认规则（供模型参考，系统仍会兜底）：
- output_type 默认 "survey"
- audience 默认 "academic"
- depth 默认 "medium"
- language 默认 "zh"
- constraints.length 默认 "medium"
- constraints.citation_style 默认 "numbered"
- 如果用户未明确说明，literature_scope.only_uploaded 默认为 true
""".strip()


# =========================
# 2) 状态对象（可持久化）
# =========================

@dataclass
class ClarificationState:
    conversation: List[Dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    max_turns: int = 5
    requirements: Optional[Dict[str, Any]] = None


ClarificationResult = Dict[str, Any]


# =========================
# 3) 强制字段规则（系统裁判）
# =========================

REQUIRED_FIELDS = [
    "goal",
    "topic",
    "output_type",
    "audience",
    "constraints.length",
]

FORCE_QUESTION_MAP = {
    "goal": "本次研究的核心目标是什么？（如：方法对比 / 研究趋势 / 问题分类）",
    "topic": "研究的具体主题是什么？请尽量具体。",
    "output_type": "输出形式希望是什么？（survey/综述 | report/报告 | outline/大纲）",
    "audience": "目标读者是谁？（academic/学术 | engineering/工程 | business/商业 | general/通用）",
    "constraints.length": "最终文本长度希望？（short/短 | medium/中 | long/长）",
}


def _generate_force_question(field: str) -> str:
    return FORCE_QUESTION_MAP.get(field, f"请补充 {field} 的信息。")


# =========================
# 4) LLM 调用（Step 内部）
# =========================

def analyze_requirements(
    gateway: LLMGateway,
    conversation: List[Dict[str, str]],
) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_REQUIREMENTS_ANALYST},
        *conversation,
        {"role": "user", "content": JSON_SCHEMA_INSTRUCTION},
    ]
    return gateway.ask_json(messages, timeout=60.0)


# =========================
# 5) 工具函数
# =========================

def _get_nested_field(req: Dict[str, Any], path: str) -> Optional[Any]:
    cur: Any = req
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def normalize_requirements(
    requirements: Dict[str, Any],
    conversation: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    系统级兜底规则（非常关键）：

    核心原则：
    - 默认：封闭研究空间（只使用本地 / 上传文献）
    - 只有在【用户显式授权】时，才允许使用外部知识
    """

    req = copy.deepcopy(requirements)

    literature = req.setdefault("literature_scope", {})
    constraints = req.setdefault("constraints", {})

    # =========================
    # 1️⃣ 判断：用户是否显式允许外部知识
    # =========================
    user_allows_external = False

    for msg in conversation:
        if msg["role"] != "user":
            continue
        text = msg["content"]
        if any(
            kw in text
            for kw in [
                "可以使用外部",
                "可以用网络",
                "不限于我的文献",
                "不只使用上传的",
                "可以查网络",
                "允许外部资料",
            ]
        ):
            user_allows_external = True
            break

    # =========================
    # 2️⃣ 强制设定 only_uploaded
    # =========================
    if user_allows_external:
        literature["only_uploaded"] = False
    else:
        literature["only_uploaded"] = True

    # =========================
    # 3️⃣ 推导生成约束（非常重要）
    # =========================
    if literature["only_uploaded"] is True:
        constraints["no_external_knowledge"] = True
    else:
        # 只有用户授权时，才允许 False
        constraints["no_external_knowledge"] = False

    req["literature_scope"] = literature
    req["constraints"] = constraints

    return req



# =========================
# 6) 完成判定
# =========================
def is_important_ambiguity(text: str) -> bool:
    """
    判断该歧义是否会显著影响后续研究结构 / 检索策略
    """
    keywords = [
        "是否", "范围", "是否包括", "是否排除",
        "特定", "侧重", "重点", "是否需要",
    ]
    return any(k in text for k in keywords)


def is_clarification_complete(
    requirements: Dict[str, Any],
    turn_count: int,
    max_turns: int,
) -> Tuple[bool, List[str]]:
    """
    统一规则（与你当前目标完全一致）：

    - 在 turn_count < max_turns 时：
        只要存在任何问题（missing / ambiguity / next_questions）
        → 一定继续澄清

    - 只有在 turn_count >= max_turns 时：
        才允许结束（即使还有问题）
    """

    missing_fields = requirements.get("missing_fields", []) or []
    ambiguities = requirements.get("ambiguities", []) or []
    next_questions = requirements.get("next_questions", []) or []

    # 还有轮次 & 还有问题 → 继续问
    if turn_count < max_turns and (missing_fields or ambiguities or next_questions):
        # 优先使用 LLM 给出的 next_questions
        questions = next_questions[:3]

        # 如果 LLM 没给问题，用 missing_fields 兜底生成
        if not questions:
            questions = [_generate_force_question(f) for f in missing_fields[:3]]

        return False, questions

    # 到达上限，或没有任何问题 → 结束
    return True, []



# =========================
# 7) 对外单步接口
# =========================

def clarification_step(
    gateway: LLMGateway,
    state: ClarificationState,
    user_message: str,
) -> ClarificationResult:
    """
    单步澄清推进（API / 前端友好）
    """

    # 1) 记录用户输入
    state.conversation.append({"role": "user", "content": user_message})
    state.turn_count += 1

    # 2) 调用 LLM 解析需求
    requirements = analyze_requirements(gateway, state.conversation)
    state.requirements = requirements

    # 3) 判定是否继续澄清
    is_complete, questions = is_clarification_complete(
        requirements=requirements,
        turn_count=state.turn_count,
        max_turns=state.max_turns,
    )

    meta = {
        "turn_count": state.turn_count,
        "max_turns": state.max_turns,
    }

    # 4) 继续澄清
    if not is_complete:
        if questions:
            assistant_msg = (
                "为了更准确地执行研究任务，请确认：\n"
                + "\n".join(f"- {q}" for q in questions)
            )
            state.conversation.append(
                {"role": "assistant", "content": assistant_msg}
            )

        return {
            "status": "need_clarification",
            "questions": questions,
            "requirements_preview": requirements,
            "meta": meta,
        }

    # 5) 结束（无论是否还有 gaps，都进入下一步）
    return {
        "status": "completed",
        "requirements": requirements,
        "meta": meta,
    }

