"""
Service layer for Knowledge Spaces and Documents.

职责说明：
- 组合 MySQL CRUD
- 处理“跨表 / 跨系统”的业务流程
- 在此层接入 RAGFlow
- 处理失败回滚与状态同步
- 不涉及 FastAPI / HTTP / token
"""

from sqlalchemy.orm import Session

# =========================
# MySQL CRUD
# =========================

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

# =========================
# RAGFlow Adapter
# =========================

from ragflow_adapter.knowledge_base import KnowledgeBaseAdapter
from ragflow_adapter.document import DocumentAdapter
from ragflow_adapter.exceptions import RAGFlowError

kb_adapter = KnowledgeBaseAdapter()
doc_adapter = DocumentAdapter()


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
    1. 先创建 MySQL 知识库记录
    2. 调用 RAGFlow 创建知识库
    3. 成功：写回 ragflow_knowledge_id
    4. 失败：回滚 MySQL
    """
    ks = create_knowledge_space(
        db,
        name=name,
        description=description,
        owner_id=owner_id,
    )

    try:
        # ---------- 调用 RAGFlow ----------
        ragflow_kb_id = kb_adapter.create(
            name=name,
            description=description,
        )

        # ---------- 写回 MySQL ----------
        ks.ragflow_knowledge_id = ragflow_kb_id
        db.commit()
        db.refresh(ks)
        return ks

    except RAGFlowError as e:
        # ---------- 回滚 MySQL ----------
        db.delete(ks)
        db.commit()
        raise ValueError(f"Failed to create knowledge space in RAGFlow: {e}")


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
    更新知识库信息（仅 MySQL 元信息）
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

    顺序：
    1. 删除 RAGFlow 知识库
    2. 删除 MySQL 记录（级联 documents）
    """
    ks = get_knowledge_space(
        db,
        knowledge_space_id=knowledge_space_id,
        owner_id=owner_id,
    )
    if not ks:
        raise ValueError("Knowledge space not found")

    # ---------- 先删 RAGFlow ----------
    if ks.ragflow_knowledge_id:
        try:
            kb_adapter.delete(
                knowledge_base_id=ks.ragflow_knowledge_id
            )
        except RAGFlowError as e:
            raise ValueError(f"Failed to delete RAGFlow knowledge space: {e}")

    # ---------- 再删 MySQL ----------
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
    1. MySQL 创建 document（status=uploaded）
    2. 调用 RAGFlow 上传文档
    3. 成功：写入 ragflow_document_id
    4. 失败：更新状态为 failed + error_message
    """
    # ---------- 1. MySQL ----------
    doc = create_document(
        db,
        knowledge_space_id=knowledge_space_id,
        filename=filename,
        file_type=file_type,
        storage_uri=storage_uri,
        uploaded_by=uploaded_by,
    )

    try:
        # ---------- 2. 查知识库 ----------
        ks = get_knowledge_space(
            db,
            knowledge_space_id=knowledge_space_id,
            owner_id=uploaded_by,
        )
        if not ks or not ks.ragflow_knowledge_id:
            raise ValueError("Knowledge space not bound to RAGFlow")

        # ---------- 3. 调用 RAGFlow ----------
        ragflow_doc_id = doc_adapter.upload(
            knowledge_base_id=ks.ragflow_knowledge_id,
            file_path=storage_uri,
            filename=filename,
        )

        # ---------- 4. 成功写回 ----------
        doc.ragflow_document_id = ragflow_doc_id
        db.commit()
        db.refresh(doc)
        return doc

    except Exception as e:
        # ---------- 失败写入状态 ----------
        update_document_status(
            db,
            document_id=doc.id,
            status="failed",
            error_message=str(e),
        )
        raise ValueError(f"Failed to upload document to RAGFlow: {e}")


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
    更新文档状态（RAGFlow 状态同步 / worker 调用）
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
    重命名文档（仅 MySQL）
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

    顺序：
    1. 删除 RAGFlow 文档
    2. 删除 MySQL 记录
    """
    doc = get_document(
        db,
        document_id=document_id,
        knowledge_space_id=knowledge_space_id,
    )
    if not doc:
        raise ValueError("Document not found")

    # ---------- 删 RAGFlow ----------
    if doc.ragflow_document_id:
        try:
            ks = get_knowledge_space(
                db,
                knowledge_space_id=knowledge_space_id,
                owner_id=doc.uploaded_by,
            )
            if ks and ks.ragflow_knowledge_id:
                doc_adapter.delete(
                    knowledge_base_id=ks.ragflow_knowledge_id,
                    document_id=doc.ragflow_document_id,
                )
        except RAGFlowError as e:
            raise ValueError(f"Failed to delete document in RAGFlow: {e}")

    # ---------- 删 MySQL ----------
    delete_document(
        db,
        document_id=document_id,
        knowledge_space_id=knowledge_space_id,
    )
