from ragflow_adapter.client import RAGFlowClient
from ragflow_adapter.exceptions import (
    RAGFlowRequestError,
    DocumentNotFound,
)

class DocumentAdapter:
    def __init__(self):
        self.client = RAGFlowClient().raw()

    def upload(
        self,
        *,
        knowledge_base_id: str,
        file_path: str,
        filename: str,
    ) -> str:
        """
        上传文档到 RAGFlow
        返回 ragflow_document_id
        """
        try:
            doc = self.client.document.upload(
                knowledge_base_id=knowledge_base_id,
                file_path=file_path,
                filename=filename,
            )
            return doc.id
        except Exception as e:
            raise RAGFlowRequestError(str(e))

    def delete(
        self,
        *,
        knowledge_base_id: str,
        document_id: str,
    ) -> None:
        """
        删除文档
        """
        try:
            self.client.document.delete(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
            )
        except Exception as e:
            raise DocumentNotFound(str(e))

    def get_status(
        self,
        *,
        knowledge_base_id: str,
        document_id: str,
    ) -> dict:
        """
        查询文档处理状态
        """
        try:
            doc = self.client.document.get(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
            )
            return {
                "status": doc.status,        # uploaded / parsing / indexed / failed
                "error_message": doc.error_message,
            }
        except Exception as e:
            raise DocumentNotFound(str(e))

