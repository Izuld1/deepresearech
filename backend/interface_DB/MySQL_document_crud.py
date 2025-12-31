from sqlalchemy.orm import Session
from sqlalchemy import select, func
from interface_DB.MySQL_document import Document

# =========================
# 常量定义
# =========================

PAGE_SIZE = 20


# =========================
# Create
# =========================
def create_document(
    db: Session,
    *,
    knowledge_space_id: int,
    filename: str,
    file_type: str | None,
    storage_uri: str,
    uploaded_by: int | None,
) -> Document:
    """
    创建文档记录（上传完成后立即调用）
    """
    doc = Document(
        knowledge_space_id=knowledge_space_id,
        filename=filename,
        file_type=file_type,
        storage_uri=storage_uri,
        uploaded_by=uploaded_by,
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# =========================
# Read - list (分页)
# =========================
def list_documents(
    db: Session,
    *,
    knowledge_space_id: int,
    page: int = 1,
) -> list[Document]:
    """
    按知识库分页查询文档
    - page 从 1 开始
    - 每页 20 条
    """
    if page < 1:
        page = 1

    offset = (page - 1) * PAGE_SIZE

    return db.scalars(
        select(Document)
        .where(Document.knowledge_space_id == knowledge_space_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(PAGE_SIZE)
    ).all()


# =========================
# Read - count
# =========================
def count_documents(
    db: Session,
    *,
    knowledge_space_id: int,
) -> int:
    """
    返回知识库下的文档总数
    （用于前端分页）
    """
    return db.scalar(
        select(func.count())
        .where(Document.knowledge_space_id == knowledge_space_id)
    )


# =========================
# Read - single
# =========================
def get_document(
    db: Session,
    *,
    document_id: int,
    knowledge_space_id: int,
) -> Document | None:
    """
    查询单个文档（用于详情 / 删除校验）
    """
    return db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.knowledge_space_id == knowledge_space_id,
        )
    )


# =========================
# Update - 状态 / 错误信息
# =========================
def update_document_status(
    db: Session,
    *,
    document_id: int,
    status: str,
    error_message: str | None = None,
) -> Document:
    """
    更新文档处理状态
    - uploaded
    - parsed
    - indexed
    - failed
    """
    doc = db.scalar(
        select(Document).where(Document.id == document_id)
    )
    if not doc:
        raise ValueError("Document not found")

    doc.status = status

    # 失败时写入错误信息
    if error_message is not None:
        doc.error_message = error_message
    else:
        doc.error_message = None

    db.commit()
    db.refresh(doc)
    return doc


# =========================
# Update - 元信息（可选）
# =========================
def update_document_metadata(
    db: Session,
    *,
    document_id: int,
    filename: str | None = None,
) -> Document:
    """
    更新文档元信息（如重命名）
    """
    doc = db.scalar(
        select(Document).where(Document.id == document_id)
    )
    if not doc:
        raise ValueError("Document not found")

    if filename is not None:
        doc.filename = filename

    db.commit()
    db.refresh(doc)
    return doc


# =========================
# Delete
# =========================
def delete_document(
    db: Session,
    *,
    document_id: int,
    knowledge_space_id: int,
) -> None:
    """
    删除文档（仅删除 MySQL 记录）
    RAGFlow 删除应由业务协调层处理
    """
    doc = get_document(
        db,
        document_id=document_id,
        knowledge_space_id=knowledge_space_id,
    )
    if not doc:
        raise ValueError("Document not found")

    db.delete(doc)
    db.commit()
