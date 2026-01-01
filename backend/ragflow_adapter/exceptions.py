class RAGFlowError(Exception):
    """RAGFlow 通用异常"""


class KnowledgeBaseNotFound(RAGFlowError):
    pass


class DocumentNotFound(RAGFlowError):
    pass


class RAGFlowRequestError(RAGFlowError):
    pass
