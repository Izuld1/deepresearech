# """
# steps/stepX_write_paragraph.py
# ------------------------------

# Step X: Evidence-Bound Paragraph Writing（基于证据池的分段写作）

# 职责：
# - 对每一个【已裁决保留的子目标 / section】
# - 仅基于其 evidence_pool 生成对应正文段落
# - 不引入任何外部知识或未检索到的信息

# 设计原则：
# - LLM 只负责“受限表达与归纳”
# - 系统负责边界约束、失败兜底与稳定性
# - 输出为稳定 contract，供后续 report assemble 使用
# """


# SYSTEM_EVIDENCE_BOUND_WRITER = """
# 你是“Evidence-Bound Academic Writer（基于证据的学术写作者）”。

# 你的唯一任务是：
# - 基于【给定证据池】为【指定段落标题】撰写对应学术正文段落。

# 必须严格遵守以下硬性规则（违反任一条均视为错误）：

# 1. 只能使用证据池中明确出现的信息
# 2. 不得引入任何外部背景知识、常识性补充或推断性结论
# 3. 不得扩展证据池中未出现的分类体系、机制或定义
# 4. 不得使用“通常认为 / 普遍认为 / 一般来说”等泛化表达
# 5. 不得出现临床建议、总结性判断或未来研究展望
# 6. 不得引用证据池中未明确出现的作者、年份或文献
# 7. 所有陈述必须能在证据池中找到直接或间接依据

# 写作风格要求：
# - 学术论文正文风格
# - 客观、中性、描述性
# - 允许归纳，但不允许外推

# 如果证据池不足以支撑完整论述：
# - 只能如实描述证据所覆盖的内容范围
# - 不得自行补全缺失部分
# """.strip()


# USER_EVIDENCE_BOUND_WRITER = """
# 【段落标题】
# {section_title}

# 【证据池（仅此可用）】
# {evidence_pool}

# 【写作要求】
# - 生成 1 个学术论文正文段落
# - 字数约 200–350 字
# - 仅围绕段落标题，不扩展到其他主题
# - 不使用小标题、编号或列表
# """.strip()


# from __future__ import annotations

# from typing import Dict, Any, List

# import re

from core.llm_gateway import LLMGateway



# def write_evidence_bound_paragraph(
#     gateway: LLMGateway,
#     section_title: str,
#     evidence_pool: List[Dict[str, Any]],
#     timeout: float = 60.0,
# ) -> Dict[str, Any]:
#     """
#     输入：
#       - section_title: 当前段落标题
#       - evidence_pool: 已裁决的证据池（List[{"text": ..., "source": ...}])

#     输出：
#       - paragraph object（稳定 contract）
#     """

#     # -------------------------
#     # 1. 证据池序列化（系统可控）
#     # -------------------------
#     serialized_evidence = []
#     for idx, ev in enumerate(evidence_pool, start=1):
#         text = ev.get("text", "").strip()
#         source = ev.get("source", "").strip()
#         if not text:
#             continue
#         serialized_evidence.append(
#             f"[Evidence {idx} | Source: {source}]\n{text}"
#         )

#     evidence_text = "\n\n".join(serialized_evidence)

#     # -------------------------
#     # 2. 构造 messages
#     # -------------------------
#     messages = [
#         {"role": "system", "content": SYSTEM_EVIDENCE_BOUND_WRITER},
#         {
#             "role": "user",
#             "content": USER_EVIDENCE_BOUND_WRITER.format(
#                 section_title=section_title,
#                 evidence_pool=evidence_text,
#             ),
#         },
#     ]

#     # -------------------------
#     # 3. 调用 LLM
#     # -------------------------
#     paragraph_text = gateway.ask(
#         messages=messages,
#         timeout=timeout,
#     ).strip()

#     # -------------------------
#     # 4. 系统级基础校验（第一道）
#     # -------------------------
#     _basic_style_guard(paragraph_text)

#     # -------------------------
#     # 5. 返回稳定结构
#     # -------------------------
#     return {
#        
#         # "section_title": section_title,
#         "content": paragraph_text,
#         # "source_count": len(serialized_evidence),
#         "status": "generated",
#     }


# FORBIDDEN_PATTERNS = [
#     r"普遍认为",
#     r"一般来说",
#     r"通常认为",
#     r"提示",
#     r"建议",
#     r"未来研究",
#     r"有助于",
#     r"因此可以",
#     r"这表明",
# ]


# def _basic_style_guard(text: str) -> None:
#     """
#     最低限度的风格与越界检查
#     """
#     for pattern in FORBIDDEN_PATTERNS:
#         if re.search(pattern, text):
#             raise ValueError(
#                 f"Paragraph violates evidence-bound constraint, forbidden pattern found: {pattern}"
#             )

#     if len(text) < 150:
#         raise ValueError("Paragraph too short, likely under-generated.")

#     if len(text) > 600:
#         raise ValueError("Paragraph too long, likely uncontrolled expansion.")

from core.llm_gateway import build_qwen_gateway_from_env
from steps.step6_draft import write_evidence_bound_paragraph,generate_paragraphs_for_sub_goals
from utils.pickle_csp import load_result,save_result,pretty

SYSTEM_GLOBAL_EDITOR = """
你是“全局学术编辑器（Global Academic Editor）”。

你的任务是对【已生成的分段草稿】进行最终整合与编辑，
以形成一篇结构清晰、风格统一、可直接交付的 Markdown 文档。

你必须遵守以下规则：

一、内容边界（非常重要）
1. 你只能使用输入草稿中已经存在的内容
2. 不得引入任何新的医学事实、结论、数据或观点
3. 不得补充原文未涉及的治疗方法或评价指标
4. 允许对已有内容进行重排、合并、压缩或语言统一

二、结构调整规则
1. 移除所有章节标题中的系统编号（如 S1、S2 等）
2. 使用输入中给定的章节标题文本作为最终标题
3. 在全文最开始新增一个【概述段落】：
   - 该段落用于概括全文内容结构
   - 只能基于各章节已有内容进行高度概括
   - 不得引入新的事实或结论
   - 语气为中性、综述性说明

三、写作与风格
1. 统一学术写作风格，避免口语化
2. 保持各章节内部逻辑连贯
3. 不进行不必要的同义替换或大幅改写
4. 不删除已有的实质性段落内容

四、输出格式（严格要求）
1. 输出必须为合法 Markdown
2. 使用 `##` 表示一级章节标题
3. 不要在文档中出现 S1 / S2 / section_id 等系统标识
4. 不得输出任何解释性文字
5. 不得在 JSON 外输出任何 Markdown 或文本
6. 不得使用 ``` 或任何代码块包裹输出
在文档最开始使用一级标题（#）给出全文标题，
标题使用研究主题或研究目标中的表述，不得自行扩展含义。

输出必须是严格 JSON，格式如下（字段不可增减）：

{
  "markdown": "<完整 Markdown 文档>"
}

""".strip()


USER_GLOBAL_EDITOR = """
【用户研究目标】
- 主题：{topic}
- 研究目标：{goal}
- 目标读者：{audience}
- 深度要求：{depth}
- 语言：{language}

【研究结构（章节顺序）】
{sections_outline}

【已生成的段落草稿（请勿新增内容）】
{draft_paragraphs}

请你在不新增任何信息的前提下，完成以下任务：
1. 按研究结构整合段落
2. 统一术语、语气和学术风格
3. 调整段落顺序与逻辑衔接（如有必要）
4. 根据目标读者与深度要求微调表达方式（仅限措辞层面）

请严格按照以下 Markdown 示例格式输出：

示例 1：
## 第一章 章节标题
段落正文内容……

### 小节标题（如有）
段落正文内容……

示例 2：
## 第二章 章节标题
段落正文内容……
段落正文内容……

注意：
- 不要添加超出“概述段落”之外的总结或结论性段落
- 概述段落仅限于对章节内容的结构性说明
- 方括号中的内容仅用于指示段落来源
- 不得在最终 Markdown 中保留任何方括号标记

""".strip()

from typing import Dict, Any, List
from core.llm_gateway import build_qwen_gateway_from_env


def run_step7_global_edit(
    gateway: LLMGateway,
    requirements: Dict[str, Any],
    plan: Dict[str, Any],
    draft_paragraphs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Step 7: 全局整合与风格统一（不新增内容）

    输入：
      - requirements：Step1 的初步研究需求
      - plan：Step2 生成并裁决后的研究结构
      - draft_paragraphs：Step6 生成的小段草稿列表

    输出：
      - final_markdown_doc
    """

    # -------- 1. 章节结构序列化 --------
    sections_outline = []
    for sec in plan.get("sections", []):
        sections_outline.append(
            f"-  {sec['title']}"
        )
    sections_outline_text = "\n".join(sections_outline)

    # -------- 2. 草稿段落序列化（保留溯源信息） --------
    draft_blocks = []
    for p in draft_paragraphs:
        draft_blocks.append(
            f"[{p['parent_section_id']} | {p['sub_goal_id']} | {p['section_title']}]\n{p['content']}"
        )

    draft_text = "\n\n".join(draft_blocks)

    # -------- 3. 构造 messages --------
    messages = [
        {"role": "system", "content": SYSTEM_GLOBAL_EDITOR},
        {
            "role": "user",
            "content": USER_GLOBAL_EDITOR.format(
                topic=requirements.get("topic"),
                goal=requirements.get("goal"),
                audience=requirements.get("audience"),
                depth=requirements.get("depth"),
                language=requirements.get("language"),
                sections_outline=sections_outline_text,
                draft_paragraphs=draft_text,
            ),
        },
    ]

    # -------- 4. 调用 LLM（注意：不是 ask_json） --------
    result = gateway.ask_json(
        messages=messages,
        timeout=120.0,
    )
    markdown_text = result["markdown"]
    return {
        "status": "completed",
        "format": "markdown",
        "content": markdown_text.strip(),
    }

if __name__ == "__main__":
    # gateway = LLMGateway()
    # result = load_result("cache/step4se_result.pkl")
    # gateway = build_qwen_gateway_from_env()


    # paragraphs = generate_paragraphs_for_sub_goals(
    #     gateway=gateway,
    #     result=result
    # )
    # save_result(paragraphs, "cache/step6_test_paragraphs.pkl")

    step1_requirements = load_result("cache/step1_requirements.pkl")
    # pretty(step1_requirements)
    step1_little = {
        "goal": step1_requirements["goal"],
        "topic": step1_requirements["topic"],
        "domain": step1_requirements["domain"],
        "audience": step1_requirements["audience"],
        "depth": step1_requirements["depth"],
        "language": step1_requirements["language"],

    }
    pretty(step1_little)
    print()
    print()
    print()
    print()
    step2_plan = load_result("cache/step2_plan.pkl")
    step2_little = {
        "sections": step2_plan["sections"],
        "assumptions": step2_plan["assumptions"],
    }
    pretty(step2_little)
    print()
    print()
    print()
    print()
    print()
    step3_subgoals = load_result("cache/step3_subgoals.pkl")
    step3_little = {
        "sub_goals": step3_subgoals["sub_goals"],
    }
    pretty(step3_little)
    print()
    print()
    print()
    print()
    print()

    step6_paragraphs = load_result("cache/step6_paragraphs.pkl")
    gateway = build_qwen_gateway_from_env()
    pretty(step6_paragraphs)
    ress = run_step7_global_edit(
        gateway=gateway,
        requirements=step1_little,
        plan=step2_little,
        draft_paragraphs=step6_paragraphs
    )
    # print
    print()
    print()
    print()
    print()
    pretty(ress["content"])
    save_result(ress, "cache/step7_final_doc.pkl")
    # for paragraph in paragraphs:
    #     print("\n=== Generated Paragraph ===\n")
    #     for i in paragraph.keys():
    #         print(f"{i}: {paragraph[i]}")
    #     print("=============================")

    # section_title = result['sub_goal_results'][0]['intent']

    # paragraph = write_evidence_bound_paragraph(
    #     gateway=gateway,
    #     section_title=section_title,
    #     evidence_pool=result['sub_goal_results'][0]['result']['pool']["contexts"]
    #     )


    # print("\n=== Generated Paragraph ===\n")
    # print(paragraph["content"])
