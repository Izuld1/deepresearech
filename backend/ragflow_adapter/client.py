import os
from ragflow_sdk import RAGFlow

class RAGFlowClient:
    """
    RAGFlow SDK Client 封装
    - 只负责初始化 SDK
    - 不掺杂任何业务逻辑
    """

    def __init__(self):
        api_key = os.getenv("RAGFLOW_API_KEY")
        base_url = os.getenv("RAGFLOW_BASE_URL")

        if not api_key or not base_url:
            raise RuntimeError("RAGFLOW_API_KEY / RAGFLOW_BASE_URL not set")

        self._client = RAGFlow(
            api_key=api_key,
            base_url=base_url,
        )

    @property
    def client(self) -> RAGFlow:
        return self._client
