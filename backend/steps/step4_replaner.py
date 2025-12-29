from typing import Dict, Any, List

from core.llm_gateway import LLMGateway

# =========================
# 1) Prompt（Step 4 用于生成更宽泛的表达） 
# =========================

SYSTEM_INTENT_EXPANDER = """
你是“研究意图扩展器（Research Intent Expander）”。 

你的任务：
- 基于给定的研究目标，生成更为宽泛的表达方式。
- 请根据当前意图以及检索词，生成一组与原始目标具有相同语义的广泛或变换表述。
- 输出的新的表述应适合用于文献检索，以便在知识库中找到相关信息。

必须遵守的硬规则：
1. 生成的表达方式应具有相同的研究意图。
2. 检索词应覆盖更多的可能的检索方向，确保对相关文献的全面覆盖。
3. 输出严格遵循以下 JSON 格式。

输出要求：
- 必须输出严格 JSON
- 字段结构必须完全一致
""".strip()


USER_INTENT_EXPANDER_INSTRUCTION = """
当前研究目标（intent）如下：
{intent_json}

请生成一个新的意图，并提供相关的检索词，严格使用以下 JSON 格式：

{{
  "current_intent": str,
  "query_hints": [
    str, str, str  # 提供3个或更多的检索提示
  ]
}}
""".strip()


# =========================
# 2) 核心函数
# =========================

def generate_expanded_intent(
    gateway: LLMGateway,
    current_intent: str,
    current_query_hints: List[str],
) -> Dict[str, Any]:
    """
    输入：
      - current_intent: 当前研究意图
      - current_query_hints: 当前的检索词

    输出：
      - 扩展后的研究意图和检索词
    """
    # 构建输入消息
    messages = [
        {"role": "system", "content": SYSTEM_INTENT_EXPANDER},
        {
            "role": "user",
            "content": USER_INTENT_EXPANDER_INSTRUCTION.format(
                intent_json=f'{{"current_intent": "{current_intent}", "query_hints": {current_query_hints}}}'
            ),
        },
    ]

    # 获取模型的响应
    expanded_result = gateway.ask_json(messages, timeout=60.0)

    # 处理模型返回的结果
    return expanded_result


