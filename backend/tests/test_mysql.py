from sqlalchemy import create_engine, text

# 1. 数据库连接信息（按你当前环境）
DB_URL = (
    "mysql+pymysql://backend_user:123456"
    "@127.0.0.1:13306/deepresearch"
)

engine = create_engine(
    DB_URL,
    echo=True,            # 打印 SQL（测试阶段非常有用）
    pool_pre_ping=True    # 自动检测断线
)

def main():
    with engine.begin() as conn:
        print("✅ Connected to MySQL")

        # 2. 插入一个用户
        result = conn.execute(
            text("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (:username, :email, :password_hash, :role)
            """),
            {
                "username": "test_user",
                "email": "test@example.com",
                "password_hash": "hashed_password_demo",
                "role": "user"
            }
        )
        user_id = result.lastrowid
        print(f"✅ Inserted user id = {user_id}")

        # 3. 创建一个知识库
        result = conn.execute(
            text("""
            INSERT INTO knowledge_spaces (name, description, owner_id, visibility)
            VALUES (:name, :desc, :owner_id, :visibility)
            """),
            {
                "name": "Test Knowledge Space",
                "desc": "This is a test knowledge space",
                "owner_id": user_id,
                "visibility": "private"
            }
        )
        space_id = result.lastrowid
        print(f"✅ Inserted knowledge_space id = {space_id}")

        # 4. 赋予用户 admin 权限
        conn.execute(
            text("""
            INSERT INTO knowledge_space_permissions
            (knowledge_space_id, user_id, permission)
            VALUES (:space_id, :user_id, :permission)
            """),
            {
                "space_id": space_id,
                "user_id": user_id,
                "permission": "admin"
            }
        )
        print("✅ Permission granted")

        # 5. 查询验证
        rows = conn.execute(
            text("""
            SELECT u.username, k.name, p.permission
            FROM users u
            JOIN knowledge_space_permissions p ON u.id = p.user_id
            JOIN knowledge_spaces k ON k.id = p.knowledge_space_id
            """)
        ).fetchall()

        print("📌 Query result:")
        for row in rows:
            print(dict(row._mapping))

if __name__ == "__main__":
    main()
