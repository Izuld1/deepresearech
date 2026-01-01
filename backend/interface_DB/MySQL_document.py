# models/document.py
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Enum,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.sql import func
from interface_DB.MySQL_db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, index=True)

    knowledge_space_id = Column(
        BigInteger,
        ForeignKey("knowledge_spaces.id"),
        nullable=False,
        index=True,
    )

    filename = Column(
        String(255),
        nullable=False,
    )

    file_type = Column(
        Enum("pdf", "docx", "txt", "md", "html", "url"),
        nullable=True,
    )

    storage_uri = Column(
        String(255),
        nullable=False,
    )

    status = Column(
        Enum("uploaded", "parsed", "indexed", "failed"),
        nullable=False,
        default="uploaded",
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    uploaded_by = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # ========== 关键添加：补充 ragflow_document_id 字段 ==========
    ragflow_document_id = Column(
        String(64),  # 匹配数据库中 VARCHAR(64) 的定义
        nullable=True,  # 初始为空，上传后赋值
        index=True,  # 可选：添加索引，方便查询
    )