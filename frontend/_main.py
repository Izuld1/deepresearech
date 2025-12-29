"""
Fake DeepResearch Backend (FastAPI + SSE)

功能：
- 使用 Python FastAPI 实现
- 提供真实 HTTP 接口
- 提供 SSE（Server-Sent Events）流
- 内部使用假数据 + sleep 模拟 research 过程
- 接口与未来真实 deepresearch 保持一致
"""

import time
import json
import uuid
from typing import Generator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse


app = FastAPI()


# -----------------------------
# CORS 配置（非常重要）
# -----------------------------
# 允许前端（Live Server）访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段直接放开
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# 工具函数：SSE 格式化
# -----------------------------
def sse_event(event_type: str, payload: dict) -> str:
    """
    将事件格式化为 SSE 标准文本

    SSE 格式：
    event: <event_name>
    data: <json_string>

    每条事件以两个换行结尾
    """
    data = {
        "type": event_type,
        "payload": payload,
    }
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


# -----------------------------
# 接口 1：启动 research
# -----------------------------
@app.post("/api/research/start")
def start_research():
    """
    启动一次 research
    真实系统中这里会：
    - 创建 session
    - 初始化状态
    - 投递后台任务

    现在我们只返回一个假的 session_id
    """
    session_id = str(uuid.uuid4())

    return JSONResponse(
        content={
            "session_id": session_id
        }
    )


# -----------------------------
# 接口 2：SSE 事件流
# -----------------------------
@app.get("/api/research/stream")
def research_stream(request: Request, session_id: str):
    """
    SSE 接口：持续向前端推送 research 过程事件

    参数：
    - session_id：前端传入的会话 ID
    """

    def event_generator() -> Generator[str, None, None]:
        """
        这是一个生成器函数
        每 yield 一次，就向前端推送一条 SSE 事件
        """

        # 1. phase -> retrieve
        time.sleep(1)
        yield sse_event(
            "phase_changed",
            {"phase": "retrieve"}
        )

        # 2. 模拟检索第一篇文献
        time.sleep(1)
        yield sse_event(
            "retrieval_finished",
            {
                "title": "PM2.5 exposure induces systemic inflammation",
                "source": "PubMed",
                "sub_goal_id": "SG-1"
            }
        )

        # 3. 模拟检索第二篇文献
        time.sleep(1)
        yield sse_event(
            "retrieval_finished",
            {
                "title": "HPA axis dysregulation and depression",
                "source": "PubMed",
                "sub_goal_id": "SG-1"
            }
        )

        # 4. assistant 开始分析（模拟流式输出）
        time.sleep(1)
        yield sse_event(
            "assistant_chunk",
            {
                "content": "Several studies indicate that PM2.5 exposure triggers inflammatory responses..."
            }
        )

        time.sleep(1)
        yield sse_event(
            "assistant_chunk",
            {
                "content": " Additionally, dysregulation of the HPA axis has been linked to depressive symptoms."
            }
        )

        # 5. phase -> write
        time.sleep(1)
        yield sse_event(
            "phase_changed",
            {"phase": "write"}
        )

        # 6. 最终输出
        time.sleep(1)
        yield sse_event(
            "final_output",
            {
                "content": (
                    "## Preliminary Conclusion\n\n"
                    "The available evidence suggests a potential mediating role of inflammation "
                    "and HPA axis dysfunction in the association between PM2.5 exposure and depression."
                )
            }
        )

    # 返回 StreamingResponse，MIME 类型必须是 text/event-stream
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# -----------------------------
# 本地启动入口
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
