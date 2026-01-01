import os
from ragflow import RAGFlow

class RAGFlowClient:
    """
    RAGFlow 官方 Python SDK 的统一封装
    """

    def __init__(self):
        self.api_key = os.getenv("RAGFLOW_API_KEY")
        self.base_url = os.getenv("RAGFLOW_BASE_URL")

        if not self.api_key or not self.base_url:
            raise RuntimeError("RAGFLOW_API_KEY or RAGFLOW_BASE_URL not set")

        self.client = RAGFlow(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    # 统一暴露底层 client（必要时）
    def raw(self) -> RAGFlow:
        return self.client
