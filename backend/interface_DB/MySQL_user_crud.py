# """
# auth.py
# ----------------------------------
# 单文件用户认证模块（注册 + 登录 + Token）

# 特点：
# - 所有逻辑集中在一个文件
# - 适合个人项目 / 初期系统
# - 可直接迁移到 FastAPI
# - admin / role 对前端完全透明
# """

# # ===== 标准库 =====
# import os
# from datetime import datetime, timedelta

# # ===== 第三方库 =====
# from dotenv import load_dotenv
# from sqlalchemy import (
#     create_engine, Column, BigInteger, String,
#     Enum, DateTime
# )
# from sqlalchemy.orm import declarative_base, sessionmaker
# from passlib.context import CryptContext
# from jose import jwt, JWTError

# # -------------------------------------------------
# # 1. 读取环境变量
# # -------------------------------------------------
# load_dotenv()

# DB_URL = (
#     f"mysql+pymysql://{os.environ['DB_USER']}:"
#     f"{os.environ['DB_PASSWORD']}@"
#     f"{os.environ['DB_HOST']}:"
#     f"{os.environ['DB_PORT']}/"
#     f"{os.environ['DB_NAME']}"
# )

# SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
# ALGORITHM = "HS256"
# TOKEN_EXPIRE_MINUTES = 60 * 24   # 1 天


# # -------------------------------------------------
# # 2. 数据库初始化
# # -------------------------------------------------
# engine = create_engine(DB_URL, pool_pre_ping=True)
# SessionLocal = sessionmaker(bind=engine)

# Base = declarative_base()


# # -------------------------------------------------
# # 3. 用户 ORM（对应 users 表）
# # -------------------------------------------------
# class User(Base):
#     __tablename__ = "users"

#     id = Column(BigInteger, primary_key=True, autoincrement=True)
#     username = Column(String(64), unique=True, nullable=False)
#     email = Column(String(128), nullable=True)
#     password_hash = Column(String(255), nullable=False)
#     role = Column(Enum("admin", "user"), default="user")
#     status = Column(Enum("active", "disabled"), default="active")
#     created_at = Column(DateTime, default=datetime.utcnow)


# # -------------------------------------------------
# # 4. 密码工具（bcrypt）
# # -------------------------------------------------
# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     deprecated="auto"
# )

# def hash_password(password: str) -> str:
#     """
#     将明文密码加密为不可逆 hash
#     """
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, password_hash: str) -> bool:
#     """
#     校验明文密码是否匹配 hash
#     """
#     return pwd_context.verify(plain_password, password_hash)


# # -------------------------------------------------
# # 5. Token 工具（JWT）
# # -------------------------------------------------
# def create_token(user_id: int) -> str:
#     """
#     后端生成 token
#     token 内容对前端不透明
#     """
#     expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
#     payload = {
#         "sub": str(user_id),
#         "exp": expire
#     }
#     return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# def get_user_id_from_token(token: str) -> int:
#     """
#     后端验证 token 并解析 user_id
#     前端永远不做这件事
#     """
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return int(payload.get("sub"))
#     except JWTError:
#         raise ValueError("Invalid token")


# # -------------------------------------------------
# # 6. 注册逻辑
# # -------------------------------------------------
# def register_user(username: str, email: str, password: str) -> dict:
#     """
#     注册用户（只能创建 user 角色）
#     """
#     db = SessionLocal()
#     try:
#         # 用户名是否存在
#         exists = db.query(User).filter(User.username == username).first()
#         if exists:
#             raise ValueError("Username already exists")

#         user = User(
#             username=username,
#             email=email,
#             password_hash=hash_password(password),
#             role="user",        # 强制
#             status="active"
#         )

#         db.add(user)
#         db.commit()
#         db.refresh(user)

#         return {
#             "id": user.id,
#             "username": user.username,
#             "email": user.email
#         }
#     finally:
#         db.close()


# # -------------------------------------------------
# # 7. 登录逻辑
# # -------------------------------------------------
# def login_user(username: str, password: str) -> dict:
#     """
#     登录校验：
#     - 校验用户名
#     - 校验密码
#     - 校验账号状态
#     - 成功则返回 token
#     """
#     db = SessionLocal()
#     try:
#         user = db.query(User).filter(User.username == username).first()
#         if not user:
#             raise ValueError("Invalid username or password")

#         if user.status != "active":
#             raise ValueError("User is disabled")

#         if not verify_password(password, user.password_hash):
#             raise ValueError("Invalid username or password")

#         token = create_token(user.id)

#         return {
#             "token": token,
#             "user": {
#                 "id": user.id,
#                 "username": user.username,
#                 "email": user.email
#             }
#         }
#     finally:
#         db.close()


# # -------------------------------------------------
# # 8. 基于 token 获取当前用户（后端用）
# # -------------------------------------------------
# def get_current_user(token: str) -> User:
#     """
#     后端使用：
#     从 token 中解析 user_id 并查询数据库
#     """
#     user_id = get_user_id_from_token(token)

#     db = SessionLocal()
#     try:
#         user = db.query(User).filter(User.id == user_id).first()
#         if not user or user.status != "active":
#             raise ValueError("Invalid user")
#         return user
#     finally:
#         db.close()


# # -------------------------------------------------
# # 9. 本地测试
# # -------------------------------------------------
# if __name__ == "__main__":
#     print("=== Register ===")
#     try:
#         u = register_user("test_user", "test@test.com", "123456")
#         print("Registered:", u)
#     except Exception as e:
#         print("Register error:", e)

#     print("\n=== Login ===")
#     try:
#         res = login_user("test_user", "123456")
#         print("Login success, token:", res["token"])
#     except Exception as e:
#         print("Login error:", e)





"""
auth.py
----------------------------------
用户认证模块（注册 + 登录 + Token）

说明：
- 不再创建 engine / Base
- 统一使用项目主 ORM（MySQL_db.py）
- User ORM 来自 models/user.py
- admin / role 对前端完全透明
"""

# ===== 标准库 =====
import os
from datetime import datetime, timedelta

# ===== 第三方库 =====
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError

# ===== 项目内 DB / ORM =====
from interface_DB.MySQL_db import SessionLocal
from interface_DB.MySQL_user import User

# -------------------------------------------------
# 1. 环境变量
# -------------------------------------------------
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24   # 1 天


# -------------------------------------------------
# 2. 密码工具（bcrypt）
# -------------------------------------------------
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """将明文密码加密为不可逆 hash"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文密码是否匹配 hash"""
    return pwd_context.verify(plain_password, password_hash)


# -------------------------------------------------
# 3. Token 工具（JWT）
# -------------------------------------------------
def create_token(user_id: int) -> str:
    """
    后端生成 token
    token 内容对前端不透明
    """
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_user_id_from_token(token: str) -> int:
    """
    后端验证 token 并解析 user_id
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        return int(user_id)
    except JWTError:
        raise ValueError("Invalid token")


# -------------------------------------------------
# 4. 注册逻辑
# -------------------------------------------------
def register_user(username: str, email: str, password: str) -> dict:
    """
    注册用户（只能创建 user 角色）
    """
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.username == username).first()
        if exists:
            raise ValueError("Username already exists")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="user",        # 强制 user
            status="active"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    finally:
        db.close()


# -------------------------------------------------
# 5. 登录逻辑
# -------------------------------------------------
def login_user(username: str, password: str) -> dict:
    """
    登录校验：
    - 校验用户名
    - 校验密码
    - 校验账号状态
    - 成功则返回 token
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError("Invalid username or password")

        if user.status != "active":
            raise ValueError("User is disabled")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password")

        token = create_token(user.id)

        return {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    finally:
        db.close()


# -------------------------------------------------
# 6. 基于 token 获取当前用户（后端用）
# -------------------------------------------------
def get_current_user(token: str) -> User:
    """
    后端使用：
    从 token 中解析 user_id 并查询数据库
    """
    user_id = get_user_id_from_token(token)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.status != "active":
            raise ValueError("Invalid user")
        return user
    finally:
        db.close()


# -------------------------------------------------
# 7. 本地测试（可选）
# -------------------------------------------------
if __name__ == "__main__":
    print("=== Register ===")
    try:
        u = register_user("test_user", "test@test.com", "123456")
        print("Registered:", u)
    except Exception as e:
        print("Register error:", e)

    print("\n=== Login ===")
    try:
        res = login_user("test_user", "123456")
        print("Login success, token:", res["token"])
    except Exception as e:
        print("Login error:", e)
