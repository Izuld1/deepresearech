SYSTEM_EVIDENCE_ADJUDICATOR_PROMPT = """
你是 DeepResearch 系统中的「研究证据裁决器（Evidence Adjudicator）」。

你的职责不是总结、不是写作、不是生成研究内容，
而是从研究方法论的角度，判断：

“当前证据池，是否在学术与研究层面上，支撑某一个明确的子研究目标。”

你必须严格区分：
- 证据是否“相关”
- 证据是否“足以支撑该研究问题”

你只做判断，不做任何改写、扩展或建议。
""".strip()




USER_EVIDENCE_ADJUDICATOR_PROMPT = """
【子研究目标】
{current_intent}

【原始检索意图提示】
{query_hints}

【证据池概况】
- 命中文献数（docs_hit）：{docs_hit}
- 证据分块数量（total_chunks）：{total_chunks}

【证据内容（节选）】
{evidence_text}

--------------------
你的任务是判断：以上证据，是否在研究层面支撑该子研究目标。

你必须给出以下三种裁决之一（只能选一个）：

1. sufficient
   - 多篇文献从不同角度直接讨论该研究问题
   - 证据内容与研究目标高度匹配
   - 可支撑独立研究段落或章节

2. partial
   - 证据与研究目标“相关”，但不直接
   - 多为背景、侧面论述、或局部支撑
   - 若继续使用该子目标，研究表述需明显弱化或泛化

3. insufficient
   - 证据与研究目标弱相关或不相关
   - 无法构成研究论证基础
   - 不应继续作为独立子研究目标

--------------------
【示例 1】
研究目标：某算法在医疗影像中的诊断性能
证据：仅讨论算法结构，无任何医疗实验
→ 裁决：insufficient

【示例 2】
研究目标：不同患者年龄对治疗方案选择的影响
证据：部分文献提及年龄因素，但非核心变量
→ 裁决：partial

【示例 3】
研究目标：某疾病的影像学诊断方法比较
证据：多篇文献系统比较 X-ray / CT / MRI
→ 裁决：sufficient

--------------------
请严格输出以下 JSON（字段不可增减）：

{{
  "decision": "sufficient | partial | insufficient",
  "rationale": "简要说明裁决理由（研究层面）",
  "confidence": 0.0-1.0
}}
""".strip()



from typing import Dict, Any
from core.llm_gateway import LLMGateway


# def evaluate_subgoal_support_with_llm(
#     *,
#     gateway: LLMGateway,
#     sub_goal: Dict[str, Any],
#     retrieval_result: Dict[str, Any],
# ) -> Dict[str, Any]:
#     """
#     DeepResearch · 子研究目标证据裁决（仅评估）

#     判断：
#     - 当前证据池是否在研究层面“支撑”该子研究目标
#     - 不做轮次控制
#     - 不修改 sub_goal
#     - 不生成新意图

#     返回三态之一：
#     - sufficient
#     - partial
#     - insufficient
#     """

#     evidence_pool = retrieval_result.get("evidence_pool", {})
#     contexts = evidence_pool.get("contexts", [])
#     evidences = evidence_pool.get("evidences", [])

#     # 证据文本（仅用于判断，不是写作）
#     evidence_text = "\n\n".join(
#         c.get("text", "")[:800] for c in contexts
#     )

#     messages = [
#         {
#             "role": "system",
#             "content": SYSTEM_EVIDENCE_ADJUDICATOR_PROMPT,
#         },
#         {
#             "role": "user",
#             "content": USER_EVIDENCE_ADJUDICATOR_PROMPT.format(
#                 current_intent=sub_goal.get("current_intent", ""),
#                 query_hints=", ".join(sub_goal.get("query_hints", [])),
#                 evidence_text=evidence_text,
#                 total_chunks=len(evidences),
#                 docs_hit=evidence_pool.get("meta", {}).get("docs_hit", 0),
#             ),
#         },
#     ]
#     print(messages)
#     result = gateway.ask_json(messages, timeout=60.0)

#     return {
#         "decision": result.get("decision"),
#         "rationale": result.get("rationale"),
#         "confidence": result.get("confidence"),
#     }





def evaluate_subgoal_support_with_llm(
    *,
    gateway: LLMGateway,
    sub_goal: Dict[str, Any],
    retrieval_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    DeepResearch · 子研究目标证据裁决（仅评估）
    """

    # ✅ 正确取证据池
    # pool = (
    #     retrieval_result
    #     .get("result", {})
    #     .get("pool", {})
    # )
    pool = retrieval_result


    contexts = pool.get("contexts", [])
    evidences = pool.get("evidences", [])
    meta = pool.get("meta", {})

    # --- 证据文本（仅用于判断，不是写作）---
    evidence_text = "\n\n".join(
        c.get("text", "")
        for c in contexts   # ⚠️ 建议限制，防止 prompt 失控
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_EVIDENCE_ADJUDICATOR_PROMPT,
        },
        {
            "role": "user",
            "content": USER_EVIDENCE_ADJUDICATOR_PROMPT.format(
                current_intent=sub_goal.get("intent", ""),
                query_hints=", ".join(sub_goal.get('retrieval_trace', []).get('queries', [])),
                evidence_text=evidence_text,
                total_chunks=meta.get("total_chunks", len(contexts)),
                docs_hit=meta.get("docs_hit", 0),
            ),
        },
    ]
    # print(messages)
    result = gateway.ask_json(messages, timeout=60.0)

    return {
        "decision": result.get("decision"),
        "rationale": result.get("rationale"),
        "confidence": result.get("confidence"),
    }
