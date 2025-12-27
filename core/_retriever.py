"""
core/retriever.py
-----------------
Step 4 唯一允许依赖的 Retriever 抽象接口
"""

from typing import Protocol, List, Dict, Any


class Retriever(Protocol):
    """
    Retriever Port（端口）
    所有检索系统（RAGFlow / FAISS / ES / Hybrid）都必须实现它
    """

    def retrieve(
        self,
        *,
        sub_goal: Dict[str, Any],
        queries: List[str],
        top_k: int,
        constraints: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        返回值必须是「证据池格式」，而不是模型生成文本
        """
        ...
