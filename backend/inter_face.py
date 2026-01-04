# inter_face.py
import uuid
import os
import asyncio
from fastapi import (
    FastAPI,
    Request,
    Header,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

# =========================
# 事件 / research 相关
# =========================
from event_bus import event_bus
from fake_worker_copy1 import run_fake_research, get_clarification_queue
from utils.sse_utils import sse_event

# =========================
# Auth & DB
# =========================
from interface_DB.MySQL_db import SessionLocal
from interface_DB.MySQL_user_crud import (
    register_user,
    login_user,
    get_current_user,
)

# =========================
# ORM（只 import 用于注册）
# =========================
from interface_DB.MySQL_user import User
from interface_DB.MySQL_knowledge_space import KnowledgeSpace
from interface_DB.MySQL_document import Document
from interface_DB.MySQL_knowledge_space_crud import get_knowledge_space
# =========================
# Service 层
# =========================
from interface_DB.knowledge_service import (
    create_knowledge_space_service,
    list_knowledge_spaces_service,
    update_knowledge_space_service,
    delete_knowledge_space_service,
    upload_document_service,
    list_documents_service,
    rename_document_service,
    delete_document_service,
    parse_document_service,
    check_parse_status_job,
)

# =========================================================
# App 初始化
# =========================================================
app = FastAPI()

# -----------------------------
# CORS 配置（开发期全开）
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# DB 依赖
# =========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# Auth 依赖（统一 token 校验）
# =========================================================
def get_current_user_from_header(
    authorization: str = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ", 1)[1]

    try:
        return get_current_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# =========================================================
# Auth 接口
# =========================================================
@app.post("/api/auth/register")
async def api_register(request: Request):
    body = await request.json()
    try:
        return register_user(
            username=body.get("username"),
            email=body.get("email"),
            password=body.get("password"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def api_login(request: Request):
    body = await request.json()
    try:
        return login_user(
            username=body.get("username"),
            password=body.get("password"),
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/auth/me")
async def api_me(
    user: User = Depends(get_current_user_from_header),
):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }


# =========================================================
# Research 接口（暂不强制鉴权）
# =========================================================
# @app.post("/api/research/start")
# async def start_research(request: Request):
#     try:
#         body = await request.json()
#     except Exception:
#         body = {}

#     session_id = str(uuid.uuid4())

#     asyncio.create_task(
#         run_fake_research(
#             session_id=session_id,
#             user_input=body,
#             search_list=body.get("search_list", []),
#         )
#     )

#     return {
#         "session_id": session_id,
#         "status": "clarification",
#     }
@app.post("/api/research/start")
async def start_research(
    request: Request,
    user: User = Depends(get_current_user_from_header),  # ✅ 引入用户上下文
):
    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = str(uuid.uuid4())

    # ✅ 向后兼容的拆分逻辑
    user_input = body.get("user_input")
    search_list = body.get("search_list", [])

    asyncio.create_task(
        run_fake_research(
            session_id=session_id,
            user_input={
                "query": user_input,
                "user_id": user.id,          # ✅ 明确传递用户身份
            },
            search_list=search_list,
        )
    )

    return {
        "session_id": session_id,
        "status": "clarification",
    }


# @app.post("/api/research/clarification")
# async def research_clarification(request: Request):
#     body = await request.json()

#     session_id = body.get("session_id")
#     answer = body.get("answer")

#     queue = get_clarification_queue(session_id)
#     await queue.put(answer)

#     await event_bus.emit(
#         sse_event(
#             "clarification_ack",
#             {
#                 "session_id": session_id,
#                 "answer": answer,
#             },
#         )
#     )

#     return {"status": "ok"}
@app.post("/api/research/clarification")
async def research_clarification(
    request: Request,
    user: User = Depends(get_current_user_from_header),  # ✅ 新增
):
    body = await request.json()

    session_id = body.get("session_id")
    answer = body.get("answer")

    # ⚠️ 现在只保证“已登录用户”
    # 后续可以校验 session_id 是否属于 user.id

    queue = get_clarification_queue(session_id)
    await queue.put(answer)

    await event_bus.emit(
        sse_event(
            "clarification_ack",
            {
                "session_id": session_id,
                "answer": answer,
            },
        )
    )

    return {"status": "ok"}


# @app.get("/api/research/stream")
# async def research_stream(
#     request: Request,
#     session_id: str,
# ):
#     return StreamingResponse(
#         event_bus.stream(),
#         media_type="text/event-stream",
#     )
@app.get("/api/research/stream")
async def research_stream(
    request: Request,
    session_id: str,
    user: User = Depends(get_current_user_from_header),  # ✅ 新增
):
    # ⚠️ 当前版本只做“登录态校验”
    # 后续可做：session_id → user_id 映射校验

    return StreamingResponse(
        event_bus.stream(),
        media_type="text/event-stream",
    )


# =========================================================
# Knowledge Space 接口（必须登录）
# =========================================================
@app.post("/api/knowledge_spaces")
async def api_create_knowledge_space(
    request: Request,
    user: User = Depends(get_current_user_from_header),
):
    body = await request.json()
    db = SessionLocal()
    try:
        ks = create_knowledge_space_service(
            db,
            name=body.get("name"),
            description=body.get("description"),
            owner_id=user.id,
        )
        return {
            "id": ks.id,
            "name": ks.name,
            "description": ks.description,
            "created_at": ks.created_at,
        }
    finally:
        db.close()


@app.get("/api/knowledge_spaces")
async def api_list_knowledge_spaces(
    user: User = Depends(get_current_user_from_header),
):
    db = SessionLocal()
    try:
        items = list_knowledge_spaces_service(
            db,
            owner_id=user.id,
        )
        return [
            {
                "id": ks.id,
                "name": ks.name,
                "description": ks.description,
                "visibility": ks.visibility,
                "created_at": ks.created_at,
            }
            for ks in items
        ]
    finally:
        db.close()


@app.put("/api/knowledge_spaces/{knowledge_space_id}")
async def api_update_knowledge_space(
    knowledge_space_id: int,
    request: Request,
    user: User = Depends(get_current_user_from_header),
):
    body = await request.json()
    db = SessionLocal()
    try:
        ks = update_knowledge_space_service(
            db,
            knowledge_space_id=knowledge_space_id,
            owner_id=user.id,
            name=body.get("name"),
            description=body.get("description"),
            visibility=body.get("visibility"),
        )
        return {"status": "ok", "id": ks.id}
    finally:
        db.close()


@app.delete("/api/knowledge_spaces/{knowledge_space_id}")
async def api_delete_knowledge_space(
    knowledge_space_id: int,
    user: User = Depends(get_current_user_from_header),
):
    db = SessionLocal()
    try:
        delete_knowledge_space_service(
            db,
            knowledge_space_id=knowledge_space_id,
            owner_id=user.id,
        )
        return {"status": "ok"}
    finally:
        db.close()


# =========================================================
# Document 接口（必须登录）
# =========================================================
# -----------------------------
# 文件上传配置
# -----------------------------
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
UPLOAD_ROOT = "cache/uploads"


# @app.post("/api/documents/upload")
@app.post("/api/documents/upload")
async def api_upload_document_real(
    knowledge_space_id: int = Form(...),   # ✅ 关键在这里
    file: UploadFile = File(...),
    user: User = Depends(get_current_user_from_header),
):
    # 文件大小校验
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    # 构造存储路径
    user_dir = os.path.join(UPLOAD_ROOT, f"user_{user.id}")
    os.makedirs(user_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    storage_path = os.path.join(user_dir, stored_filename)

    try:
        with open(storage_path, "wb") as f:
            f.write(contents)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save file")

    db = SessionLocal()
    try:
        doc = upload_document_service(
            db,
            knowledge_space_id=knowledge_space_id,
            filename=file.filename,
            file_type=ext.lstrip("."),
            storage_uri=storage_path,
            uploaded_by=user.id,
        )
        return {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "created_at": doc.created_at,
        }
    except Exception as e:
        os.remove(storage_path)  # 回滚文件
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.get("/api/documents")
async def api_list_documents(
    knowledge_space_id: int,
    page: int = 1,
    user: User = Depends(get_current_user_from_header),
):
    db = SessionLocal()
    try:
        check_parse_status_job(db,
                               user_id=user.id,
                               knowledge_space_id=knowledge_space_id)  # 检查解析状态
        return list_documents_service(
            db,
            knowledge_space_id=knowledge_space_id,
            page=page,
        )
    finally:
        db.close()






@app.put("/api/documents/{document_id}")
async def api_rename_document(
    document_id: int,
    request: Request,
    user: User = Depends(get_current_user_from_header),
):
    body = await request.json()
    db = SessionLocal()
    try:
        rename_document_service(
            db,
            document_id=document_id,
            knowledge_space_id=body.get("knowledge_space_id"),
            filename=body.get("filename"),
        )
        return {"status": "ok"}
    finally:
        db.close()


@app.delete("/api/documents/{document_id}")
async def api_delete_document(
    document_id: int,
    knowledge_space_id: int,
    user: User = Depends(get_current_user_from_header),
):
    db = SessionLocal()
    try:
        delete_document_service(
            db,
            document_id=document_id,
            knowledge_space_id=knowledge_space_id,
        )
        return {"status": "ok"}
    finally:
        db.close()




@app.post("/api/documents/{document_id}/parse")
async def api_parse_document(
    document_id: int,
    knowledge_space_id: int,
    user: User = Depends(get_current_user_from_header),
):
    """
    触发文档解析（RAGFlow）

    语义：
    - 仅负责“触发解析任务”
    - 不等待解析完成
    - 状态由 Service 层写入 parsing / failed
    """
    db = SessionLocal()
    try:
        # 1. 校验知识库归属（可选但推荐）
        ks = get_knowledge_space(
            db,
            knowledge_space_id=knowledge_space_id,
            owner_id=user.id,
        )
        if not ks or not ks.ragflow_knowledge_id:
            raise ValueError("Knowledge space not bound to RAGFlow")

        # 2. 触发解析
        updated_doc = parse_document_service(
            db,
            document_id=document_id,
            dataset_id=ks.ragflow_knowledge_id,
        )

        return {
            "status": "ok",
            "document_id": document_id,
            "parse_status": updated_doc.status,
        }

    finally:
        db.close()



# =========================================================
# 本地启动
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "inter_face:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
