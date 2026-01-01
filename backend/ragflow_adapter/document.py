from ragflow_adapter.client import RAGFlowClient
from ragflow_adapter.exceptions import RAGFlowError


class DocumentAdapter:
    """
    文档 Adapter
    - 上传 / 删除 / 查询状态
    """

    def __init__(self):
        self.client = RAGFlowClient().client

    def upload(
        self,
        *,
        knowledge_base_id: str,
        file_path: str,
        filename: str,
    ) -> str:
        try:
            res = self.client.upload_document(
                knowledge_base_id=knowledge_base_id,
                file_path=file_path,
                filename=filename,
            )
            return res["id"]
        except Exception as e:
            raise RAGFlowError(str(e))

    def get(
        self,
        *,
        knowledge_base_id: str,
        document_id: str,
    ) -> dict:
        try:
            return self.client.get_document(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
            )
        except Exception as e:
            raise RAGFlowError(str(e))

    def delete(
        self,
        *,
        knowledge_base_id: str,
        document_id: str,
    ):
        try:
            self.client.delete_document(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
            )
        except Exception as e:
            raise RAGFlowError(str(e))
