"""
core/llm_gateway.py
-------------------
一个“极简可替换”的 LLM 网关层（Gateway）。

设计目标：
- 统一封装不同大模型（Qwen / OpenAI / Claude / Gemini ...）的调用方式
- 提供强制 JSON 输出的安全解析（避免每个 step 里重复写容错）
- 让上层业务（step1/step2/step6）只依赖“能力接口”，不依赖某家模型 SDK
- 你必须严格只输出 JSON。不得使用中文标点。输出必须可被 json.loads 直接解析。

注意：
- 这里不做任何业务逻辑（不判断缺字段、不生成问题），只负责：
  1) 发请求
  2) 拿回复
  3) JSON 解析
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
import json
import os


# -------------------------
# 1) 抽象接口：LLMClient
# -------------------------
class LLMClient(Protocol):
    """
    让业务层不依赖具体 SDK。
    任何模型只要实现 complete(messages)->str 即可替换。
    """
    def complete(self, messages: List[Dict[str, str]], *, timeout: Optional[float] = None) -> str:
        ...


# -------------------------
# 2) 具体实现：OpenAI Compatible Client（兼容 Qwen DashScope）
# -------------------------
@dataclass
class OpenAICompatibleClient:
    """
    OpenAI-compatible 的最小实现：
    - 既可用于 OpenAI，也可用于 DashScope compatible-mode，或其他兼容服务
    """
    model: str
    api_key: str
    base_url: str

    def __post_init__(self) -> None:
        # 延迟导入：避免业务层加载时就强依赖 openai 包
        from openai import OpenAI  # type: ignore
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def complete(self, messages: List[Dict[str, str]], *, timeout: Optional[float] = None) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            timeout=timeout,
        )
        return (resp.choices[0].message.content or "").strip()


# -------------------------
# 3) JSON 输出解析器（强制严格 JSON）
# -------------------------
@dataclass
class JSONExtractor:
    """
    统一做 JSON 解析容错：
    - 从文本中截取第一个 {...} 块
    - json.loads 解析
    - 若失败，抛出异常给上层（上层可决定重试或判失败）
    """
    def extract(self, text: str) -> Dict[str, Any]:
        text = text.strip()

        # 容错：截取最外层 JSON 对象
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model output does not contain a JSON object.")

        candidate = text[start:end + 1]
        print("--- JSON Extraction Debug ---")
        print(f"Extracted JSON candidate: {candidate}")
        print("--- JSON Extraction Debug ---")
        return json.loads(candidate)


# -------------------------
# 4) 高层网关：LLMGateway
# -------------------------
from dataclasses import dataclass, field

@dataclass
class LLMGateway:
    """
    业务层调用的主要入口。
    提供：
    - ask_json(): 输入 messages，返回 Dict（严格 JSON）
    """
    client: LLMClient
    extractor: JSONExtractor = field(default_factory=JSONExtractor)

    def ask_json(
        self,
        messages: List[Dict[str, str]],
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        raw = self.client.complete(messages, timeout=timeout)
        return self.extractor.extract(raw)



# -------------------------
# 5) 一个便捷的工厂方法（可选）
# -------------------------
def build_qwen_gateway_from_env() -> LLMGateway:
    """
    用环境变量构建 Qwen（DashScope compatible-mode）的网关。
    这样 Step 1 不需要关心 api_key/base_url/model 的细节。

    Env:
      DASHSCOPE_API_KEY=...
      DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
      DASHSCOPE_MODEL=qwen-plus
    """
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("DASHSCOPE_MODEL", "qwen-plus")

    if not api_key:
        raise RuntimeError("Missing DASHSCOPE_API_KEY in environment variables.")

    client = OpenAICompatibleClient(model=model, api_key=api_key, base_url=base_url)
    return LLMGateway(client=client)
