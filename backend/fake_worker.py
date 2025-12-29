# fake_worker.py
import asyncio
from utils.sse_utils import sse_event
from event_bus import event_bus

# ===============================
# 澄清消息队列（按 session 区分）
# ===============================
clarification_queues: dict[str, asyncio.Queue] = {}


def get_clarification_queue(session_id: str) -> asyncio.Queue:
    if session_id not in clarification_queues:
        clarification_queues[session_id] = asyncio.Queue()
    return clarification_queues[session_id]


async def run_fake_research(session_id: str, user_input: dict):
    """
    多轮澄清版本（≤5 轮）：
    - clarification_prompt 发澄清问题
    - await queue.get() 等前端回复
    - 每轮都 print 前端输入
    - 然后进入原本 research 流程
    """

    print("🧠 Fake research started")
    print("Session ID:", session_id)

    print("📩 Initial user input from frontend:")
    print(user_input)

    queue = get_clarification_queue(session_id)

    # =====================================================
    # 1. 多轮澄清阶段（≤5 轮）
    # =====================================================
    clarification_questions = [
        "Do you want the research to focus on biological mechanisms, epidemiological evidence, or both?",
        "Should the output be written as a narrative review or a structured report?",
        "Do you want the discussion to emphasize causal mechanisms or observed correlations?",
        "Should the focus be on short-term exposure, long-term exposure, or both?",
        "Is this research intended for an academic audience or a general audience?",
    ]

    collected_answers = []

    for i, question in enumerate(clarification_questions):
        # 1️⃣ 后端发澄清问题（关键：clarification_prompt）
        await event_bus.emit(
            sse_event(
                "clarification_prompt",
                {
                    # "question": f"[Clarification {i + 1}] {question}",
                    "question": f"{question}",
                },
            )
        )

        # 2️⃣ 等待前端回复
        user_reply = await queue.get()

        # 3️⃣ 后端明确打印（你关心的点）
        print(f"📩 Clarification reply {i + 1} from frontend:")
        print(user_reply)

        collected_answers.append(user_reply)

        # 4️⃣ 向前端确认收到（普通 assistant_chunk）
        # await event_bus.emit(
        #     sse_event(
        #         "assistant_chunk",
        #         {
        #             "content": f"Received: **{user_reply}**."
        #         },
        #     )
        # )

        # 可选：提前结束澄清（示例：2 轮即可）
        if i >= 1:
            break

    print("🧠 Clarification finished. Collected answers:")
    print(collected_answers)

    # =====================================================
    # 2. retrieve 阶段（原本流程）
    # =====================================================
    await asyncio.sleep(0.8)
    await event_bus.emit(
        sse_event("phase_changed", {"phase": "retrieve"})
    )

    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "retrieval_finished",
            {
                "title": "PM2.5 exposure induces systemic inflammation",
                "source": "PubMed",
                "sub_goal_id": "SG-1",
            },
        )
    )

    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "retrieval_finished",
            {
                "title": "HPA axis dysregulation and depression",
                "source": "PubMed",
                "sub_goal_id": "SG-1",
            },
        )
    )

    # =====================================================
    # 3. analyze / assistant
    # =====================================================
    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "assistant_chunk",
            {
                "content": (
                    "Several studies indicate that PM2.5 exposure triggers inflammatory "
                    "responses, which may interact with stress-regulation systems."
                )
            },
        )
    )

    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "assistant_chunk",
            {
                "content": (
                    "Additionally, dysregulation of the HPA axis has been linked "
                    "to depressive symptoms."
                )
            },
        )
    )

    # =====================================================
    # 4. write 阶段
    # =====================================================
    await asyncio.sleep(0.8)
    await event_bus.emit(
        sse_event("phase_changed", {"phase": "write"})
    )

    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "final_output",
            {
                "content": (
                    "## Preliminary Conclusion\n\n"
                    "The available evidence suggests a potential mediating role of inflammation "
                    "and HPA axis dysfunction in the association between PM2.5 exposure and depression."
                )
            },
        )
    )

    print("✅ Fake research finished:", session_id)
