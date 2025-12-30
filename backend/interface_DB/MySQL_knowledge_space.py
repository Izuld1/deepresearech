# models/knowledge_space.py
from sqlalchemy import Column, BigInteger, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from interface_DB.MySQL_db import Base

class KnowledgeSpace(Base):
    __tablename__ = "knowledge_spaces"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    visibility = Column(
        Enum("private", "shared", "public"),
        default="private",
        nullable=False,
    )
    created_at = Column(DateTime, server_default=func.now())
