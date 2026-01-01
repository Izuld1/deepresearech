from ragflow_adapter.client import RAGFlowClient
from ragflow_adapter.exceptions import (
    RAGFlowRequestError,
    KnowledgeBaseNotFound,
)

class KnowledgeBaseAdapter:
    def __init__(self):
        self.client = RAGFlowClient().raw()

    def create(self, *, name: str, description: str | None = None) -> str:
        """
        创建知识库
        返回 ragflow_knowledge_id
        """
        try:
            kb = self.client.knowledge_base.create(
                name=name,
                description=description or "",
            )
            return kb.id
        except Exception as e:
            raise RAGFlowRequestError(str(e))

    def delete(self, *, knowledge_base_id: str) -> None:
        """
        删除知识库
        """
        try:
            self.client.knowledge_base.delete(knowledge_base_id)
        except Exception as e:
            raise KnowledgeBaseNotFound(str(e))

    def list(self) -> list[dict]:
        """
        （可选）列出知识库
        """
        try:
            items = self.client.knowledge_base.list()
            return [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "created_at": kb.created_at,
                }
                for kb in items
            ]
        except Exception as e:
            raise RAGFlowRequestError(str(e))
