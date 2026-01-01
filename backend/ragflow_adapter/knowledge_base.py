from ragflow_adapter.client import RAGFlowClient
from ragflow_adapter.exceptions import RAGFlowError


class KnowledgeBaseAdapter:
    """
    知识库 Adapter
    - 只做 RAGFlow 调用
    - 不处理 MySQL
    """

    def __init__(self):
        self.client = RAGFlowClient().client

    def create(self, *, name: str, description: str | None = None) -> str:
        try:
            res = self.client.create_knowledge_base(
                name=name,
                description=description or "",
            )
            # 官方返回 dict
            return res["id"]
        except Exception as e:
            raise RAGFlowError(str(e))

    def delete(self, *, knowledge_base_id: str):
        try:
            self.client.delete_knowledge_base(
                knowledge_base_id=knowledge_base_id
            )
        except Exception as e:
            raise RAGFlowError(str(e))
