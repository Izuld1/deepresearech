# interface_DB/models/user.py
from sqlalchemy import Column, BigInteger, String, Enum, DateTime
from sqlalchemy.sql import func
from interface_DB.MySQL_db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(128), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("admin", "user"), default="user")
    status = Column(Enum("active", "disabled"), default="active")
    created_at = Column(DateTime, server_default=func.now())
