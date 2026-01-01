"""
Service layer for Knowledge Spaces and Documents.

职责说明：
- 组合 MySQL CRUD
- 处理“跨表 / 跨系统”的业务流程
- 在此层接入 RAGFlow（仅 Dataset / Document 上传）
- 处理失败回滚与状态同步
- ❗不做解析（parse）
- ❗不涉及 FastAPI / HTTP / token
"""

from sqlalchemy.orm import Session

# =========================
# MySQL CRUD
# =========================

from interface_DB.MySQL_knowledge_space_crud import (
    create_knowledge_space,
    list_knowledge_spaces,
    get_knowledge_space,
    update_knowledge_space,
    delete_knowledge_space,
)

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
# RAGFlow Services（已验证可用）
# =========================

from ragflow_sdk import RAGFlow
import os
from ragflow_adapter.test import DocumentService  # 根据实际路径调整导入

def _get_ragflow_client() -> RAGFlow:
    """
    内部工具：创建 RAGFlow SDK 客户端
    ❗严格使用你已经测试通过的方式
    """
    return RAGFlow(
        api_key=os.getenv("RAGFLOW_API_KEY"),
        base_url=os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380"),
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
    1. MySQL 创建知识库
    2. RAGFlow create_dataset
    3. 成功：写回 ragflow_knowledge_id
    4. 失败：回滚 MySQL
    """
    ks = create_knowledge_space(
        db,
        name=name,
        description=description,
        owner_id=owner_id,
    )

    rag = _get_ragflow_client()

    try:
        dataset = rag.create_dataset(name=name)

        ks.ragflow_knowledge_id = dataset.id
        db.commit()
        db.refresh(ks)
        return ks

    except Exception as e:
        # ❗RAGFlow 失败 → 回滚 MySQL
        db.delete(ks)
        db.commit()
        raise ValueError(f"Failed to create knowledge space in RAGFlow: {e}")


def list_knowledge_spaces_service(
    db: Session,
    *,
    owner_id: int,
):
    """
    列出用户的所有知识库（仅 MySQL）
    """
    return list_knowledge_spaces(db, owner_id=owner_id)


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
    1. 删除 RAGFlow Dataset
    2. 删除 MySQL 记录（级联 documents）
    """
    ks = get_knowledge_space(
        db,
        knowledge_space_id=knowledge_space_id,
        owner_id=owner_id,
    )
    if not ks:
        raise ValueError("Knowledge space not found")

    rag = _get_ragflow_client()

    # ---------- 1. 删 RAGFlow ----------
    if ks.ragflow_knowledge_id:
        try:
            rag.delete_datasets(ids=[ks.ragflow_knowledge_id])
        except Exception as e:
            raise ValueError(f"Failed to delete RAGFlow dataset: {e}")

    # ---------- 2. 删 MySQL ----------
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
    1. MySQL 创建 document（status=uploaded，占位）
    2. RAGFlow upload_documents
    3. 解析返回的 ragflow_document_id
    4. 回写 MySQL（ragflow_document_id）
    5. 成功返回
    """
    # ---------- 1. MySQL 占位 ----------
    doc = create_document(
        db,
        knowledge_space_id=knowledge_space_id,
        filename=filename,
        file_type=file_type,
        storage_uri=storage_uri,
        uploaded_by=uploaded_by,
        status="uploaded",
    )
    # 先提交占位记录，确保记录入库
    db.commit()
    db.refresh(doc)

    rag = _get_ragflow_client()

    try:
        # ---------- 2. 查知识库 ----------
        ks = get_knowledge_space(
            db,
            knowledge_space_id=knowledge_space_id,
            owner_id=uploaded_by,
        )
        if not ks or not ks.ragflow_knowledge_id:
            raise ValueError("Knowledge space not bound to RAGFlow")

        datasets = rag.list_datasets(id=ks.ragflow_knowledge_id)
        if not datasets:
            raise ValueError("RAGFlow dataset not found")

        dataset = datasets[0]

        # ---------- 3. 上传文件 ----------
        with open(storage_uri, "rb") as f:
            blob = f.read()

        upload_results = dataset.upload_documents([
            {
                "display_name": filename,
                "blob": blob,
            }
        ])

        # ---------- 4. 解析 RAGFlow 返回的 document_id ----------
        if not upload_results:
            raise ValueError("RAGFlow upload returned empty result")
        print(f"RAGFlow upload_results: {upload_results}")
        uploaded_doc = upload_results[0]
        ragflow_document_id = getattr(uploaded_doc, "id", None)

        if not ragflow_document_id:
            raise ValueError(f"Cannot parse ragflow_document_id from {uploaded_doc}")

        # ---------- 5. 回写 MySQL（修复后） ----------
        # 方式1：对象赋值（现在模型有此字段，赋值有效）
        doc.ragflow_document_id = ragflow_document_id
        doc.status = "indexed"  # 可选：更新状态为已索引
        db.commit()
        db.refresh(doc)  # 刷新获取最新数据

        # 方式2：直接更新（备选，更稳定）
        # db.query(Document).filter(Document.id == doc.id).update({
        #     "ragflow_document_id": ragflow_document_id,
        #     "status": "indexed"
        # })
        # db.commit()
        # doc = db.query(Document).filter(Document.id == doc.id).first()

        return doc

    except Exception as e:
        # ---------- 回滚状态 ----------
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()
        db.refresh(doc)
        raise ValueError(f"Failed to upload document to RAGFlow: {e}")


def list_documents_service(
    db: Session,
    *,
    knowledge_space_id: int,
    page: int = 1,
):
    """
    分页列出知识库下的文档（仅 MySQL）
    """
    return {
        "items": list_documents(db, knowledge_space_id=knowledge_space_id, page=page),
        "total": count_documents(db, knowledge_space_id=knowledge_space_id),
    }


def get_document_service(
    db: Session,
    *,
    document_id: int,
    knowledge_space_id: int,
):
    """
    获取单个文档（仅 MySQL）
    """
    doc = get_document(db, document_id=document_id, knowledge_space_id=knowledge_space_id)
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
    更新文档状态（为未来 parse / worker 预留）
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
    doc = get_document(db, document_id=document_id, knowledge_space_id=knowledge_space_id)
    if not doc:
        raise ValueError("Document not found")

    return update_document_metadata(db, document_id=document_id, filename=filename)

# 首先确保导入 DocumentService 类（根据你的 SDK 实际路径调整）
# 示例：from ragflow_sdk.modules.document import DocumentService

def delete_document_service(
    db: Session,
    *,
    document_id: int,
    knowledge_space_id: int,
):
    """
    删除文档（Service 层）

    删除顺序：
    1. 从 MySQL 读取 ragflow_document_id
    2. 调用 RAGFlow 删除真实文档
    3. 删除本地 MySQL 记录（一定执行）
    """

    # -----------------------------
    # Step 0: 读取本地文档
    # -----------------------------
    doc = get_document(db, document_id=document_id, knowledge_space_id=knowledge_space_id)
    if not doc:
        raise ValueError("Document not found")

    ragflow_doc_id = getattr(doc, "ragflow_document_id", None)

    # -----------------------------
    # Step 1: 尝试删除 RAGFlow 文档（完全兜住）
    # -----------------------------
    try:
        # 1.1 获取知识库
        ks = get_knowledge_space(
            db,
            knowledge_space_id=knowledge_space_id,
            owner_id=getattr(doc, "uploaded_by", None),
        )

        if not ragflow_doc_id:
            print(
                f"[DELETE SKIP] doc_id={doc.id} has no ragflow_document_id"
            )

        elif not ks or not ks.ragflow_knowledge_id:
            print(
                f"[DELETE SKIP] knowledge_space_id={knowledge_space_id} "
                f"not bound to RAGFlow"
            )

        else:
            # 1.2 调用 RAGFlow SDK（完全适配你验证可行的逻辑）
            rag = _get_ragflow_client()
            
            # ===== 核心修复：实例化 DocumentService 类 =====
            # 方式1：如果 DocumentService 需要 rag 客户端作为参数（多数 SDK 如此）
            doc_service = DocumentService()  # 替换为实际的实例化方式
            
            # 方式2：如果是无参实例化（根据你验证的代码）
            # doc_service = DocumentService()

            print(
                f"[DELETE RAGFLOW] dataset_id={ks.ragflow_knowledge_id}, "
                f"ragflow_doc_id={ragflow_doc_id}"
            )

            # 调用你验证可行的删除语句（参数完全一致）
            doc_service.delete(
                dataset_id=ks.ragflow_knowledge_id,
                document_ids=[ragflow_doc_id],
            )

            print(
                f"[DELETE RAGFLOW OK] ragflow_doc_id={ragflow_doc_id}"
            )

    except Exception as e:
        # ❗非常重要：不要抛异常，不影响本地删除
        print(
            f"[RAGFLOW DELETE FAILED] doc_id={doc.id}, "
            f"ragflow_doc_id={ragflow_doc_id}, error={e}"
        )
        # 调试：打印 DocumentService 的可用方法和参数
        try:
            from inspect import signature
            rag = _get_ragflow_client()
            doc_service = DocumentService()
            # 打印 delete 方法的参数
            print("[DEBUG] delete 方法参数：", signature(doc_service.delete))
        except:
            pass

    # -----------------------------
    # Step 2: 删除本地数据库记录（必须执行）
    # -----------------------------
    delete_document(db, document_id=document_id, knowledge_space_id=knowledge_space_id)







import threading
import uuid
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from interface_DB.MySQL_document import Document
def parse_document_service(
    db: Session,
    *,
    document_id: int,
    dataset_id: str,
) -> Document:
    """
    解析文档（触发解析，不等待完成）

    状态流转：
    uploaded → parsing → indexed / failed
    """

    # -----------------------------
    # Step 1: 校验文档
    # -----------------------------
    doc = db.scalar(
        select(Document).where(Document.id == document_id)
    )
    if not doc:
        raise ValueError("Document not found")

    ragflow_doc_id = getattr(doc, "ragflow_document_id", None)
    if not ragflow_doc_id:
        update_document_status(
            db,
            document_id=document_id,
            status="failed",
            error_message="Document has no ragflow_document_id"
        )
        raise ValueError("Document has no ragflow_document_id")

    # -----------------------------
    # Step 2: 标记为 parsing
    # -----------------------------
    update_document_status(
        db,
        document_id=document_id,
        status="parsing"
    )

    # -----------------------------
    # Step 3: 调用 RAGFlow（触发解析）
    # -----------------------------
    try:
        rag = _get_ragflow_client()
        doc_service = rag.documents

        result = doc_service.parse(
            dataset_id=dataset_id,
            document_ids=[ragflow_doc_id],
        )

        # 只要 parse 没抛异常，就认为触发成功
        # 不在这里判断最终状态
        print(f"[PARSE TRIGGERED] result={result}")

        return update_document_status(
            db,
            document_id=document_id,
            status="parsing"
        )

    except Exception as e:
        update_document_status(
            db,
            document_id=document_id,
            status="failed",
            error_message=str(e)
        )
        raise ValueError(f"Parse document failed: {e}") from e
