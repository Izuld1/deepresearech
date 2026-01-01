# # models/knowledge_space.py
# from sqlalchemy import Column, BigInteger, String, Text, Enum, DateTime, ForeignKey
# from sqlalchemy.sql import func
# from interface_DB.MySQL_db import Base

# class KnowledgeSpace(Base):
#     __tablename__ = "knowledge_spaces"

#     id = Column(BigInteger, primary_key=True, index=True)
#     name = Column(String(128), nullable=False)
#     description = Column(Text)
#     owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
#     visibility = Column(
#         Enum("private", "shared", "public"),
#         default="private",
#         nullable=False,
#     )
#     created_at = Column(DateTime, server_default=func.now())



# models/knowledge_space.py

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Enum,
    DateTime,
    ForeignKey,
)
from sqlalchemy.sql import func

from interface_DB.MySQL_db import Base


class KnowledgeSpace(Base):
    __tablename__ = "knowledge_spaces"

    # -----------------------------
    # 主键与基础信息
    # -----------------------------
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)

    # -----------------------------
    # 所属用户
    # -----------------------------
    owner_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # -----------------------------
    # 可见性控制
    # -----------------------------
    visibility = Column(
        Enum("private", "shared", "public"),
        default="private",
        nullable=False,
        index=True,
    )

    # -----------------------------
    # 外部系统（RAGFlow）关联字段
    # -----------------------------
    ragflow_knowledge_id = Column(
        String(255),
        nullable=True,
        comment="Knowledge ID in external RAGFlow system",
    )

    # -----------------------------
    # 创建时间
    # -----------------------------
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
