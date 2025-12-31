"""
Service layer for Knowledge Spaces and Documents.

职责说明：
- 组合 MySQL CRUD
- 处理“跨表 / 跨系统”的业务流程
- 明确预留 RAGFlow 接入位置
- 不涉及 FastAPI / HTTP / token
"""

from sqlalchemy.orm import Session

# Knowledge Space CRUD
from interface_DB.MySQL_knowledge_space_crud import (
    create_knowledge_space,
    list_knowledge_spaces,
    get_knowledge_space,
    update_knowledge_space,
    delete_knowledge_space,
)

# Document CRUD
from interface_DB.MySQL_document_crud import (
    create_document,
    list_documents,
    count_documents,
    get_document,
    update_document_status,
    update_document_metadata,
    delete_document,
)


# =========================================================
# Knowledge Space Services
# =========================================================

def create_knowledge_space_service(
    db: Session,
    *,
    name: str,
    description: str | None,
    owner_id: int,
):
    """
    创建知识库（Service 层）

    流程：
    1. 写入 MySQL（知识库元数据）
    2. 【预留】创建 RAGFlow Dataset
    3. 返回知识库对象
    """
    ks = create_knowledge_space(
        db,
        name=name,
        description=description,
        owner_id=owner_id,
    )

    # =====================================================
    # TODO (RAGFlow):
    # ragflow_dataset_id = ragflow_client.create_dataset(
    #     name=ks.name,
    #     owner_id=owner_id,
    # )
    # update_knowledge_space_ragflow_id(...)
    # =====================================================

    return ks


def list_knowledge_spaces_service(
    db: Session,
    *,
    owner_id: int,
):
    """
    列出用户的所有知识库
    """
    return list_knowledge_spaces(
        db,
        owner_id=owner_id,
    )


def update_knowledge_space_service(
    db: Session,
    *,
    knowledge_space_id: int,
    owner_id: int,
    name: str | None = None,
    description: str | None = None,
    visibility: str | None = None,
):
    """
    更新知识库信息
    """
    return update_knowledge_space(
        db,
        knowledge_space_id=knowledge_space_id,
        owner_id=owner_id,
        name=name,
        description=description,
        visibility=visibility,
    )


def delete_knowledge_space_service(
    db: Session,
    *,
    knowledge_space_id: int,
    owner_id: int,
):
    """
    删除知识库（Service 层）

    流程：
    1. 校验并删除 MySQL 记录
    2. 【预留】删除 RAGFlow Dataset
    """
    ks = get_knowledge_space(
        db,
        knowledge_space_id=knowledge_space_id,
        owner_id=owner_id,
    )
    if not ks:
        raise ValueError("Knowledge space not found")

    # =====================================================
    # TODO (RAGFlow):
    # ragflow_client.delete_dataset(ks.ragflow_id)
    # =====================================================

    delete_knowledge_space(
        db,
        knowledge_space_id=knowledge_space_id,
        owner_id=owner_id,
    )


# =========================================================
# Document Services
# =========================================================

def upload_document_service(
    db: Session,
    *,
    knowledge_space_id: int,
    filename: str,
    file_type: str | None,
    storage_uri: str,
    uploaded_by: int,
):
    """
    上传文档（Service 层）

    流程：
    1. MySQL 中创建 document 记录（uploaded）
    2. 【预留】通知 RAGFlow 进行解析 / embedding
    """
    doc = create_document(
        db,
        knowledge_space_id=knowledge_space_id,
        filename=filename,
        file_type=file_type,
        storage_uri=storage_uri,
        uploaded_by=uploaded_by,
    )

    # =====================================================
    # TODO (RAGFlow):
    # ragflow_client.upload_document(
    #     dataset_id=knowledge_space.ragflow_id,
    #     file_uri=storage_uri,
    #     document_id=doc.id,
    # )
    # =====================================================

    return doc


def list_documents_service(
    db: Session,
    *,
    knowledge_space_id: int,
    page: int = 1,
):
    """
    分页列出知识库下的文档
    """
    return {
        "items": list_documents(
            db,
            knowledge_space_id=knowledge_space_id,
            page=page,
        ),
        "total": count_documents(
            db,
            knowledge_space_id=knowledge_space_id,
        ),
    }


def get_document_service(
    db: Session,
    *,
    document_id: int,
    knowledge_space_id: int,
):
    """
    获取单个文档
    """
    doc = get_document(
        db,
        document_id=document_id,
        knowledge_space_id=knowledge_space_id,
    )
    if not doc:
        raise ValueError("Document not found")
    return doc


def update_document_status_service(
    db: Session,
    *,
    document_id: int,
    status: str,
    error_message: str | None = None,
):
    """
    更新文档状态（通常由 worker / RAGFlow 回调触发）
    """
    return update_document_status(
        db,
        document_id=document_id,
        status=status,
        error_message=error_message,
    )


def rename_document_service(
    db: Session,
    *,
    document_id: int,
    knowledge_space_id: int,
    filename: str,
):
    """
    重命名文档
    """
    doc = get_document(
        db,
        document_id=document_id,
        knowledge_space_id=knowledge_space_id,
    )
    if not doc:
        raise ValueError("Document not found")

    return update_document_metadata(
        db,
        document_id=document_id,
        filename=filename,
    )


def delete_document_service(
    db: Session,
    *,
    document_id: int,
    knowledge_space_id: int,
):
    """
    删除文档（Service 层）

    流程：
    1. 删除 MySQL 记录
    2. 【预留】删除 RAGFlow 文档
    """
    doc = get_document(
        db,
        document_id=document_id,
        knowledge_space_id=knowledge_space_id,
    )
    if not doc:
        raise ValueError("Document not found")

    # =====================================================
    # TODO (RAGFlow):
    # ragflow_client.delete_document(
    #     dataset_id=...,
    #     document_id=doc.id,
    # )
    # =====================================================

    delete_document(
        db,
        document_id=document_id,
        knowledge_space_id=knowledge_space_id,
    )
