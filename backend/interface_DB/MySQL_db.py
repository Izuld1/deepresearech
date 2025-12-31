# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# DB_URL = os.getenv("DB_URL")


MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("DB_USER")        # 用户名你是放在 DB_USER 里的
MYSQL_PASSWORD = os.getenv("DB_PASSWORD")

if not all([MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD]):
    raise RuntimeError(
        "MySQL environment variables are not fully set. "
        "Expected MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, DB_USER, DB_PASSWORD."
    )

DB_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)



engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()
