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
    status: str = "uploaded",
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

from typing import Optional
# =========================
# 状态白名单（唯一真源）
# =========================
ALLOWED_STATUSES = {
    "uploaded",
    "indexed",
    "parsing",
    "parsed",
    "failed",
}

# =========================
# Update - 状态 / 错误信息
# =========================
def update_document_status(
    db: Session,
    *,
    document_id: int,
    status: str,
    error_message: Optional[str] = None,
) -> Document:
    """
    更新文档处理状态（唯一入口）

    合法状态：
    - uploaded
    - indexed
    - parsing
    - parsed
    - failed

    规则：
    - status 必须在白名单中
    - failed 状态允许写 error_message
    - 非 failed 状态会清空 error_message
    """

    # ---------- 1. 状态合法性校验 ----------
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid document status: {status}")

    # ---------- 2. 查询文档 ----------
    doc = db.scalar(
        select(Document).where(Document.id == document_id)
    )
    if not doc:
        raise ValueError("Document not found")

    # ---------- 3. 状态写入 ----------
    doc.status = status

    # ---------- 4. 错误信息规则 ----------
    if status == "failed":
        doc.error_message = error_message
    else:
        # 非失败状态，强制清空错误信息
        doc.error_message = None

    # ---------- 5. 提交 ----------
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
def get_filename_by_ragflow_document_id(
    db: Session,
    *,
    ragflow_document_id: str,
) -> str | None:
    """
    通过 ragflow_document_id 查询 filename
    - 用于 RAGFlow chunk / document 回溯
    """
    return db.scalar(
        select(Document.filename)
        .where(Document.ragflow_document_id == ragflow_document_id)
    )







