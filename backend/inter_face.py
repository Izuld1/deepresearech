# inter_face.py
import uuid
import asyncio
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from event_bus import event_bus
from fake_worker_copy1 import run_fake_research, get_clarification_queue
from utils.sse_utils import sse_event
from interface_DB.mysql_user import (
    register_user,
    login_user,
    get_current_user,
)



app = FastAPI()

# -----------------------------
# CORS 配置
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Auth 接口
# =========================================================

@app.post("/api/auth/register")
async def api_register(request: Request):
    """
    用户注册
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        user = register_user(
            username=body.get("username"),
            email=body.get("email"),
            password=body.get("password"),
        )
        return JSONResponse(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def api_login(request: Request):
    """
    用户登录
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        result = login_user(
            username=body.get("username"),
            password=body.get("password"),
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/auth/me")
async def api_me(authorization: str = Header(None)):
    """
    校验 token，获取当前用户
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ", 1)[1]

    try:
        user = get_current_user(token)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================================================
# Research 接口（你原有的，未改动）
# =========================================================



# -----------------------------
# 接口 1：启动 research
# -----------------------------
@app.post("/api/research/start")
async def start_research(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = str(uuid.uuid4())

    print("✅ Research started")
    print("Session:", session_id)
    print("Initial user input:", body)

    asyncio.create_task(
        run_fake_research(
            session_id=session_id,
            user_input=body
        )
    )

    return JSONResponse(
        content={
            "session_id": session_id,
            "status": "clarification"
        }
    )

# -----------------------------
# 接口 1.5：澄清回复
# -----------------------------
@app.post("/api/research/clarification")
async def research_clarification(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    print("🟡 Clarification response received:")
    print(body)

    session_id = body.get("session_id")
    answer = body.get("answer")

    # 🔑 核心：把前端回复交给 fake_worker
    queue = get_clarification_queue(session_id)
    await queue.put(answer)

    # 可选确认事件（不影响流程）
    await event_bus.emit(
        sse_event(
            "clarification_ack",
            {
                "session_id": session_id,
                "answer": answer,
            },
        )
    )

    return JSONResponse({"status": "ok"})

# -----------------------------
# 接口 2：SSE 事件流
# -----------------------------
@app.get("/api/research/stream")
async def research_stream(request: Request, session_id: str):
    return StreamingResponse(
        event_bus.stream(),
        media_type="text/event-stream",
    )

# -----------------------------
# 本地启动入口
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "inter_face:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
