# fake_worker.py
"""
DeepResearch Orchestrator (Live / Cache Dual Mode)

设计目标：
1. 完整保留现有 Step1–Step7 流程
2. 完整保留与前端的 SSE 交互方式、次数、事件名
3. 支持 USE_CACHE：
   - False：真实运行（调用 LLM / 检索）
   - True ：读取 cache，但“假装”真实运行（用于前端联调）
"""

import asyncio
from typing import Dict

from utils.sse_utils import sse_event
from event_bus import event_bus

from core.llm_gateway import build_qwen_gateway_from_env

from steps.step1_clarify import ClarificationState, clarification_step
from steps.step2_plan import generate_research_plan
from steps.step3_subgoals import generate_sub_goals
from steps.step4_se_ev import run_step4
from steps.step6_draft import generate_paragraphs_for_sub_goals
from tests.test_step7 import run_step7_global_edit

from utils.pickle_csp import save_result, load_result, pretty
from interface_DB.knowledge_service import search_know_ragflow_id

# ============================================================
# 全局运行模式控制
# ============================================================
USE_CACHE = False   # True = 回放模式 / False = 实时运行


# ============================================================
# Clarification Queue（前后端同步）
# ============================================================
clarification_queues: Dict[str, asyncio.Queue] = {}


def get_clarification_queue(session_id: str) -> asyncio.Queue:
    if session_id not in clarification_queues:
        clarification_queues[session_id] = asyncio.Queue()
    return clarification_queues[session_id]


# ============================================================
# 主流程
# ============================================================
async def run_fake_research(session_id: str, user_input: dict, search_list: list):

    print("🧠 Fake research started")
    print("search_list:", search_list)
    print("Session ID:", session_id)

    gateway = build_qwen_gateway_from_env()
    queue = get_clarification_queue(session_id)

    # =====================================================
    # Step 1: 澄清（始终 Live，因为涉及前端输入）
    # =====================================================
    print("\n==============================")
    print("Step 1: Requirement Clarification")

    state = ClarificationState()
    user_text = user_input["query"]
    user_id = user_input["user_id"]
    knw_rag_list = []
    for i in search_list:
        knw_ragflow_id = search_know_ragflow_id(user_id=user_id,knowledge_space_id=i)
        if knw_ragflow_id:
            knw_rag_list.append(knw_ragflow_id)


    while True:
        result = clarification_step(gateway, state, user_text)
        pretty(result)

        status = result.get("status")

        if status == "need_clarification":
            questions = result.get("questions", [])
            await event_bus.emit(
                sse_event(
                    "clarification_prompt",
                    {"question": "   ".join(questions)},
                )
            )
            print("[Waiting clarification reply from frontend...]")
            user_text = await queue.get()
            print("📩 Clarification reply:", user_text)
            continue

        if status == "completed":
            requirements = result["requirements"]
            break

        print("[Clarification failed]")
        return

    save_result(requirements, "cache/step1_requirements.pkl")

    step1_lite = {
        "goal": requirements["goal"],
        "topic": requirements["topic"],
        "domain": requirements["domain"],
        "audience": requirements["audience"],
        "depth": requirements["depth"],
        "language": requirements["language"],
    }

    await event_bus.emit(
        sse_event(
            "assistant_chunk",
            {"content": f"开始研究：{step1_lite['goal']}"},
        )
    )

    # =====================================================
    # Step 2: Research Plan
    # =====================================================
    print("\n==============================")
    print("Step 2: Research Plan")

    if USE_CACHE:
        plan = load_result("cache/step2_plan.pkl")
    else:
        plan = generate_research_plan(
            gateway=gateway,
            requirements=requirements,
        )
        save_result(plan, "cache/step2_plan.pkl")

    pretty(plan)

    step2_lite = {
        "sections": plan["sections"],
        "assumptions": plan["assumptions"],
    }

    # =====================================================
    # Step 3: Sub-goals
    # =====================================================
    print("\n==============================")
    print("Step 3: Sub-goals")

    if USE_CACHE:
        subgoals_result = load_result("cache/step3_subgoals.pkl")
    else:
        subgoals_result = generate_sub_goals(
            gateway=gateway,
            requirements=requirements,
            plan=plan,
            min_per_section=2,
            max_per_section=5,
        )
        save_result(subgoals_result, "cache/step3_subgoals.pkl")

    pretty(subgoals_result)

    # =====================================================
    # Step 4: Retrieval / Evidence
    # =====================================================
    print("\n==============================")
    print("Step 4: Retrieval")

    await event_bus.emit(
        sse_event("phase_changed", {"phase": "retrieve"})
    )

    if USE_CACHE:
        step4_result = load_result("cache/step4_result.pkl")
    else:
        step4_result = run_step4(
            kb_ids=knw_rag_list,
            gateway=gateway,
            sub_goals=subgoals_result["sub_goals"],
        )
        save_result(step4_result, "cache/step4_result.pkl")

    # ======== 保留你写死的 retrieval_finished 事件（一个不删） ========

    # await asyncio.sleep(1)
    temp_step4_output = load_result("cache/step4_result.pkl")['sub_goal_results']
    for i in range(len(temp_step4_output)):
        for j in range(len(temp_step4_output[i]['result']['pool']["contexts"])):
            print()
            await event_bus.emit(
                sse_event(
                    "retrieval_finished",
                    {
                        "title": temp_step4_output[i]['result']['pool']['intent'],
                        "source": temp_step4_output[i]['result']['pool']['contexts'][j]['source'],
                        "sub_goal_id": temp_step4_output[i]['sub_goal_id'],
                    },
                )
            )
        # await asyncio.sleep(1)
    # await event_bus.emit(
    #     sse_event(
    #         "retrieval_finished",
    #         {
    #             "title": "明确腕骨骨折的主要类型及其诊断标准，为治疗方案的选择提供依据",
    #             "source": "传统手法结合距下关节与内侧柱双稳定术治疗青少年柔性平足症的临床观察_曾广龙.pdf",
    #             "sub_goal_id": "SG-1",
    #         },
    #     )
    # )

    # await asyncio.sleep(1)
    # await event_bus.emit(
    #     sse_event(
    #         "retrieval_finished",
    #         {
    #             "title": "探讨保守治疗方法（如固定、牵引）在不同类型腕骨骨折中的适应症与疗效",
    #             "source": "筋骨并重”理论在腕关节镜辅助治疗Herbert_B型舟骨骨折合并TFCC损伤术后康复中的应用_向往.pdf",
    #             "sub_goal_id": "SG-1",
    #         },
    #     )
    # )

    # await asyncio.sleep(1)
    # await event_bus.emit(
    #     sse_event(
    #         "retrieval_finished",
    #         {
    #             "title": "梳理术后或保守治疗后的康复流程，关注功能恢复的时间线与评价指标",
    #             "source": "记忆合金Ⅰ型钉脚固定器联合克氏针治疗经舟骨月骨周围背侧脱位的临床疗效研究_汤浩.pdf",
    #             "sub_goal_id": "SG-1",
    #         },
    #     )
    # )

    # await asyncio.sleep(1)
    # await event_bus.emit(
    #     sse_event(
    #         "retrieval_finished",
    #         {
    #             "title": "总结近三年内关于腕骨骨折治疗与康复的主要研究发现和发展方向",
    #             "source": "手术切除跟舟骨桥后趾短伸肌转位和脂肪填塞的疗效对比_李春光.pdf",
    #             "sub_goal_id": "SG-1",
    #         },
    #     )
    # )

    # await asyncio.sleep(1)
    # await event_bus.emit(
    #     sse_event(
    #         "retrieval_finished",
    #         {
    #             "title": "总结近三年内关于腕骨骨折治疗与康复的主要研究发现和发展方向",
    #             "source": "基于肌肉力学及肌电活动特征评估专用防护鞋及鞋垫治疗副舟骨综合征的有效性_程自申.pdf",
    #             "sub_goal_id": "SG-1",
    #         },
    #     )
    # )

    # =====================================================
    # Step 6: Draft Paragraphs
    # =====================================================
    print("\n==============================")
    print("Step 6: Draft Paragraphs")

    if USE_CACHE:
        step6_paragraphs = load_result("cache/step6_paragraphs.pkl")
    else:
        step6_paragraphs = generate_paragraphs_for_sub_goals(
            gateway=gateway,
            result=step4_result,
        )
        save_result(step6_paragraphs, "cache/step6_paragraphs.pkl")

    # =====================================================
    # Step 7: Global Edit
    # =====================================================
    print("\n==============================")
    print("Step 7: Global Edit")

    await event_bus.emit(
        sse_event("phase_changed", {"phase": "write"})
    )

    if USE_CACHE:
        final_doc = load_result("cache/step7_final_doc.pkl")
    else:
        final_doc = run_step7_global_edit(
            gateway=gateway,
            requirements=step1_lite,
            plan=step2_lite,
            draft_paragraphs=step6_paragraphs,
        )
        save_result(final_doc, "cache/step7_final_doc.pkl")

    await event_bus.emit(
        sse_event(
            "final_output",
            {"content": final_doc["content"]},
        )
    )

    print("✅ Fake research finished:", session_id)
