"""
steps/step3_subgoals.py
----------------------
Step 3: Sub-goals Generation（子研究目标拆分）

职责：
- 输入：Step 1 requirements + Step 2 research plan
- 输出：SubGoal 列表（可检索的研究意图）
- 不检索、不写正文、不总结、不论证
- 子目标必须是“信息需求（information need）”，不是写作指令

设计原则：
- LLM 只负责“生成候选 sub-goal 意图”
- 系统负责：
  1) 禁止判断性词汇（better/best/optimal/推荐/应当等）
  2) 输出结构稳定
  3) 给每个 sub-goal 加生命周期字段（fallback_level、history、status）
- Step 3 一般不需要接口化（Orchestrator 内部），但返回结构可直接序列化为 JSON

依赖：
- core.llm_gateway.LLMGateway：只要求提供 ask_json(messages, timeout=...)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re
import uuid

from core.llm_gateway import LLMGateway


# =========================
# 0) 常量与配置
# =========================

# 每个 section 生成多少个 sub-goals（候选）
DEFAULT_MIN_SUBGOALS_PER_SECTION = 2
DEFAULT_MAX_SUBGOALS_PER_SECTION = 5

# fallback 上限（你后面 Step5 会用到；先在 Step3 结构里预留字段）
DEFAULT_MAX_FALLBACK_LEVEL = 2

# judgement / 推断强度倾向词（中英混合，宁可严格）
JUDGEMENT_PATTERNS = [
    r"\bbetter\b", r"\bbest\b", r"\boptimal\b", r"\bmost effective\b", r"\bmost efficient\b",
    r"推荐", r"建议", r"应当", r"必须", r"最优", r"最好", r"最佳", r"优于", r"劣于", r"更好", r"更差",
    r"结论", r"证明", r"证实", r"显著优", r"显著更",
]


def contains_judgement(text: str) -> bool:
    """检测 sub-goal intent 是否包含判断/推荐倾向。"""
    t = (text or "").strip().lower()
    for p in JUDGEMENT_PATTERNS:
        if re.search(p, t, flags=re.IGNORECASE):
            return True
    return False


def sanitize_intent(text: str) -> str:
    """对 intent 做轻量清洗（不做“改写”，只做工程兜底）。"""
    if not text:
        return ""
    t = text.strip()
    # 去掉多余换行/空格
    t = re.sub(r"\s+", " ", t).strip()
    # 去掉末尾句号
    t = t.rstrip("。.;；")
    return t


# =========================
# 1) Prompt（Step 3 私有）
# =========================

SYSTEM_SUBGOAL_DECOMPOSER = """
你是“子研究目标拆分器（Sub-goal Decomposer）”。

你要做的是：把研究结构中的每个章节（section）拆成多个“可检索的信息需求（sub-goals）”。

硬规则（必须遵守）：
1) sub-goal 必须是“要找什么信息”，不是写作指令、不是总结任务、不是结论。
2) 不允许出现任何判断性/推荐性措辞（例如：better/best/optimal/推荐/应当/最佳/优于 等）。
3) 每个 sub-goal 应该足够具体，以便后续能用于向量检索/关键词检索。
4) 不要发明需求之外的新研究方向；必须贴合 requirements 与 section 的标题/提示。
5) 输出必须是严格 JSON，不允许任何额外文字。

输出 JSON schema（字段不可增减）：
{
  "sub_goals": [
    {
      "parent_section_id": str,
      "intent": str,
      "query_hints": [str, ...]
    }
  ]
}

说明：
- parent_section_id 必须来自输入的 section_id
- intent 是信息需求句，例如“手术治疗方案的分类与适应证”“影像学诊断中常用指标与局限”
- query_hints 用于后续检索的不同问法/关键词组合（不需要太多，2~4 条即可）
""".strip()


USER_SUBGOAL_DECOMPOSER_INSTRUCTION = """
给定研究需求（requirements）与初始研究结构（plan），请为每个 section 生成 {min_n}~{max_n} 个 sub-goals。

requirements（已裁决）：
{requirements_json}

plan（已裁决，sections 里包含 section_id/title/intent_hint）：
{plan_json}

注意：
- 只输出 sub_goals 数组
- 子目标必须能用于检索
- 不允许判断性措辞
""".strip()


# =========================
# 2) 对外数据结构（可序列化）
# =========================

@dataclass
class SubGoal:
    """
    SubGoal 是 Step3 的核心产物。
    - intent：信息需求（检索目标）
    - query_hints：检索提示（多问法）
    - lifecycle：为 Step4/5 预留字段（fallback、status、history）
    """
    sub_goal_id: str
    parent_section_id: str

    original_intent: str
    current_intent: str

    query_hints: List[str] = field(default_factory=list)

    # 生命周期与回退轨迹（你后面会用）
    fallback_level: int = 0
    fallback_history: List[str] = field(default_factory=list)

    # 状态机预留：active/downgraded/removed/unresolved 等
    status: str = "active"

    # 工程字段：后续 evidence pool / decisions 会挂在这里
    evidence_pool_id: Optional[str] = None


def subgoal_to_dict(sg: SubGoal) -> Dict[str, Any]:
    """dataclass -> dict（确保 JSON 可序列化）"""
    return {
        "sub_goal_id": sg.sub_goal_id,
        "parent_section_id": sg.parent_section_id,
        "original_intent": sg.original_intent,
        "current_intent": sg.current_intent,
        "query_hints": sg.query_hints,
        "fallback_level": sg.fallback_level,
        "fallback_history": sg.fallback_history,
        "status": sg.status,
        "evidence_pool_id": sg.evidence_pool_id,
    }


# =========================
# 3) 核心：生成候选 sub-goals（LLM）
# =========================

def _ask_llm_for_subgoals(
    gateway: LLMGateway,
    requirements: Dict[str, Any],
    plan: Dict[str, Any],
    min_n: int,
    max_n: int,
) -> Dict[str, Any]:
    """
    调用 LLM 生成候选 sub_goals（仅候选）。
    注意：后续还要经过系统裁决/过滤/规范化。
    """
    messages = [
        {"role": "system", "content": SYSTEM_SUBGOAL_DECOMPOSER},
        {
            "role": "user",
            "content": USER_SUBGOAL_DECOMPOSER_INSTRUCTION.format(
                min_n=min_n,
                max_n=max_n,
                requirements_json=requirements,  # 你 gateway.ask_json 里会处理 dict -> str 或由你自己处理
                plan_json=plan,
            ),
        },
    ]
    return gateway.ask_json(messages, timeout=60.0)


# =========================
# 4) 系统裁决与兜底（关键）
# =========================

def _collect_section_ids(plan: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for sec in plan.get("sections", []) or []:
        sid = sec.get("section_id") or sec.get("id") or sec.get("parent_section_id")
        if sid:
            ids.append(str(sid))
    return ids


def _normalize_query_hints(hints: Any) -> List[str]:
    if hints is None:
        return []
    if isinstance(hints, str):
        hints = [hints]
    if not isinstance(hints, list):
        return []
    out: List[str] = []
    for h in hints:
        if not isinstance(h, str):
            continue
        hh = sanitize_intent(h)
        if hh and hh not in out:
            out.append(hh)
    return out[:4]


def _dedup_by_parent_and_intent(items: List[Tuple[str, str, List[str]]]) -> List[Tuple[str, str, List[str]]]:
    """按 (parent_section_id, intent) 去重。"""
    seen = set()
    out: List[Tuple[str, str, List[str]]] = []
    for parent_id, intent, hints in items:
        key = (parent_id, intent.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append((parent_id, intent, hints))
    return out


def _fallback_default_subgoals_for_section(section: Dict[str, Any]) -> List[Tuple[str, str, List[str]]]:
    """
    LLM 输出异常时的兜底：生成极简 sub-goals（尽量不引入新方向）。
    注意：这不是“高质量研究”，只是保证系统不崩。
    """
    sid = section.get("section_id") or section.get("id") or ""
    title = (section.get("title") or "").strip()
    hint = (section.get("intent_hint") or "").strip()

    base = title if title else hint if hint else "该章节主题"

    # 兜底 sub-goals：尽量“信息需求化”
    candidates = [
        (sid, f"{base} 的关键概念与定义", [f"{base} 定义", f"{base} 关键术语"]),
        (sid, f"{base} 的常见分类/类型与判定标准", [f"{base} 分类", f"{base} 类型 判定标准"]),
    ]
    return candidates


# =========================
# 5) 对外主函数：generate_sub_goals
# =========================

def generate_sub_goals(
    gateway: LLMGateway,
    requirements: Dict[str, Any],
    plan: Dict[str, Any],
    min_per_section: int = DEFAULT_MIN_SUBGOALS_PER_SECTION,
    max_per_section: int = DEFAULT_MAX_SUBGOALS_PER_SECTION,
    max_fallback_level: int = DEFAULT_MAX_FALLBACK_LEVEL,
) -> Dict[str, Any]:
    """
    输入：
      - requirements：Step1 输出（已裁决）
      - plan：Step2 输出（已裁决）

    输出（稳定 contract）：
    {
      "sub_goals": [ ...SubGoal dict... ],
      "meta": {
        "sub_goal_count": int,
        "filtered_judgement_count": int,
        "fallback_used": bool
      }
    }

    说明：
    - Step3 不需要接口化，但输出结构可直接作为 API 返回或写入 DB。
    """

    section_ids = set(_collect_section_ids(plan))
    sections = plan.get("sections", []) or []

    filtered_judgement_count = 0
    fallback_used = False

    # 1) 先让 LLM 生成候选
    try:
        raw = _ask_llm_for_subgoals(gateway, requirements, plan, min_per_section, max_per_section)
        raw_list = raw.get("sub_goals", [])
        if not isinstance(raw_list, list):
            raw_list = []
    except Exception:
        raw_list = []
        fallback_used = True

    # 2) 规范化候选 (parent_section_id, intent, query_hints)
    candidates: List[Tuple[str, str, List[str]]] = []

    for item in raw_list:
        if not isinstance(item, dict):
            continue

        parent_id = str(item.get("parent_section_id", "")).strip()
        intent = sanitize_intent(item.get("intent", ""))
        hints = _normalize_query_hints(item.get("query_hints"))

        if not parent_id or parent_id not in section_ids:
            continue
        if not intent:
            continue

        # judgement 过滤（宁可少，不要污染后续检索）
        if contains_judgement(intent):
            filtered_judgement_count += 1
            continue

        candidates.append((parent_id, intent, hints))

    # 3) 去重
    candidates = _dedup_by_parent_and_intent(candidates)

    # 4) 保障每个 section 至少有 min_per_section 个 subgoals（不足用兜底补齐）
    by_section: Dict[str, List[Tuple[str, str, List[str]]]] = {sid: [] for sid in section_ids}
    for parent_id, intent, hints in candidates:
        by_section[parent_id].append((parent_id, intent, hints))

    final_items: List[Tuple[str, str, List[str]]] = []

    for sec in sections:
        sid = sec.get("section_id") or sec.get("id")
        if not sid:
            continue
        sid = str(sid)

        items = by_section.get(sid, [])
        # 截断到 max_per_section
        items = items[:max_per_section]

        if len(items) < min_per_section:
            fallback_used = True
            fallback_candidates = _fallback_default_subgoals_for_section(sec)
            # 补齐但避免重复
            for fc in fallback_candidates:
                if len(items) >= min_per_section:
                    break
                if (fc[0], fc[1].lower()) not in {(x[0], x[1].lower()) for x in items}:
                    items.append(fc)

        final_items.extend(items)

    # 5) 生成 SubGoal 对象（带 lifecycle 字段）
    sub_goals: List[SubGoal] = []
    for parent_id, intent, hints in final_items:
        sg_id = f"SG-{uuid.uuid4().hex[:8]}"

        # 初始化 fallback 轨迹：从 original == current 开始
        sg = SubGoal(
            sub_goal_id=sg_id,
            parent_section_id=parent_id,
            original_intent=intent,
            current_intent=intent,
            query_hints=hints,
            fallback_level=0,
            fallback_history=[intent],
            status="active",
            evidence_pool_id=None,
        )
        sub_goals.append(sg)

    # 6) 输出 contract（JSON 可序列化）
    return {
        "sub_goals": [subgoal_to_dict(sg) for sg in sub_goals],
        "meta": {
            "sub_goal_count": len(sub_goals),
            "filtered_judgement_count": filtered_judgement_count,
            "fallback_used": fallback_used,
            "max_fallback_level": max_fallback_level,
            "step_2_plan": plan,  # 保留原始 plan 以便后续使用
        },
    }
