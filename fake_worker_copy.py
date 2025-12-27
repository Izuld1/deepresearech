# fake_worker.py
import asyncio
from utils.sse_utils import sse_event
from event_bus import event_bus

from core.llm_gateway import build_qwen_gateway_from_env
from steps.step1_clarify import ClarificationState, clarification_step
from steps.step2_plan import generate_research_plan
from steps.step3_subgoals import generate_sub_goals
# from steps.step4_select import run_retrieval_for_subgoal
from steps.step4_se_ev import run_step4_for_subgoal,run_step4
# from steps.step5_adjudicator import evaluate_subgoal_support_with_llm
from steps.step6_draft import generate_paragraphs_for_sub_goals
from utils.pickle_csp import save_result,pretty,load_result
from tests.test_step7 import run_step7_global_edit



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


    gateway = build_qwen_gateway_from_env()
    

    state = ClarificationState()

    print("=== DeepResearch Bootstrap Flow ===")
    print("Step 1: Research Requirement Clarification")
    print("🧠 Fake research started")
    print("Session ID:", session_id)
    queue = get_clarification_queue(session_id)
    print("📩 Initial user input from frontend:")
    print(user_input)
    user_input = user_input["query"]
    collected_answers = []
    # ---------- Step 1 ----------
    # ---------- Step 1: Clarification Loop ----------
    while True:
        # 1️⃣ 用当前用户输入（字符串）调用澄清逻辑
        result = clarification_step(gateway, state, user_input)

        print("\nSystem >")
        pretty(result)

        status = result.get("status")

        # ===============================
        # 2️⃣ 需要澄清 → 问问题 + 等前端
        # ===============================
        if status == "need_clarification":
            questions = result.get("questions", [])

            if questions:
                print("\n===== Clarification Questions =====")
                print("   ".join(questions))

                # 👉 只在 need_clarification 时 emit
                await event_bus.emit(
                    sse_event(
                        "clarification_prompt",
                        {
                            "question": "   ".join(questions),
                        },
                    )
                )

            print("\n[Waiting for frontend clarification answer...]")

            # 🔒 阻塞等待前端回复（关键）
            user_input = await queue.get()

            # ✅ 后端必须打印（你关心的点）
            print("📩 Clarification reply from frontend:")
            print(user_input)

            # 回到 while，继续下一轮澄清
            continue

        # ===============================
        # 3️⃣ 澄清完成
        # ===============================
        if status == "completed":
            requirements = result.get("requirements")

            print("\n[Clarification completed]")
            print("\nFinal requirements:")
            pretty(requirements)

            break

        # ===============================
        # 4️⃣ 异常 / 失败情况
        # ===============================
        if status in ("failed", "completed_with_gaps"):
            print("\n[Clarification ended with unresolved issues]")
            pretty(result)
            return

    save_result(requirements, "cache/step1_requirements.pkl")

    step1_requirements = load_result("cache/step1_requirements.pkl")
    # pretty(step1_requirements)
    step1_little = {
        "goal": step1_requirements["goal"],
        "topic": step1_requirements["topic"],
        "domain": step1_requirements["domain"],
        "audience": step1_requirements["audience"],
        "depth": step1_requirements["depth"],
        "language": step1_requirements["language"],

    }


    await event_bus.emit(
        sse_event(
            "assistant_chunk",
            {
                "content": (
                    "开始研究"
                    "" + step1_little["goal"]
                )
            },
        )
    )
    

    # # =====================================================
    # # 1. 多轮澄清阶段（≤5 轮）
    # # =====================================================
    # clarification_questions = [
    #     "Do you want the research to focus on biological mechanisms, epidemiological evidence, or both?",
    #     "Should the output be written as a narrative review or a structured report?",
    #     "Do you want the discussion to emphasize causal mechanisms or observed correlations?",
    #     "Should the focus be on short-term exposure, long-term exposure, or both?",
    #     "Is this research intended for an academic audience or a general audience?",
    # ]

    # collected_answers = []

    # for i, question in enumerate(clarification_questions):
    #     # 1️⃣ 后端发澄清问题（关键：clarification_prompt）
    #     await event_bus.emit(
    #         sse_event(
    #             "clarification_prompt",
    #             {
    #                 # "question": f"[Clarification {i + 1}] {question}",
    #                 "question": f"{question}",
    #             },
    #         )
    #     )

    #     # 2️⃣ 等待前端回复
    #     user_reply = await queue.get()

    #     # 3️⃣ 后端明确打印（你关心的点）
    #     print(f"📩 Clarification reply {i + 1} from frontend:")
    #     print(user_reply)

    #     collected_answers.append(user_reply)

    #     # 4️⃣ 向前端确认收到（普通 assistant_chunk）
    #     # await event_bus.emit(
    #     #     sse_event(
    #     #         "assistant_chunk",
    #     #         {
    #     #             "content": f"Received: **{user_reply}**."
    #     #         },
    #     #     )
    #     # )

    #     # 可选：提前结束澄清（示例：2 轮即可）
    #     if i >= 1:
    #         break

    print("🧠 Clarification finished. Collected answers:")
    print(collected_answers)

    # =====================================================
    # 2. retrieve 阶段（原本流程）
    # =====================================================
    await asyncio.sleep(0.8)
    await event_bus.emit(
        sse_event("phase_changed", {"phase": "retrieve"})
    )


    print("\n==============================")
    print("Step 2: Research Plan Generation")
    plan = generate_research_plan(
        gateway=gateway,
        requirements=requirements,
    )

    print("\nResearch Plan:")
    pretty(plan)
    save_result(plan, "cache/step2_plan.pkl")
    step2_plan = load_result("cache/step2_plan.pkl")
    step2_little = {
        "sections": step2_plan["sections"],
        "assumptions": step2_plan["assumptions"],
    }





    # ---------- Step 3 ----------
    print("\n==============================")
    print("Step 3: Sub-goals Generation")

    subgoals_result = generate_sub_goals(
        gateway=gateway,
        requirements=requirements,
        plan=plan,
        min_per_section=2,
        max_per_section=5,
    )

    print("\nSub-goals:")
    pretty(subgoals_result)
    save_result(subgoals_result, "cache/step3_subgoals.pkl")
    print("\n[Bootstrap flow finished successfully]")


    # -----------Step 4 select---------------
    print("\n==============================")
    print(subgoals_result.keys())
    print("Step 4: Sub-goal Retrieval Test")
    # step4se_result = run_step4_for_subgoal(
    #     gateway=gateway,
    #     sub_goal=subgoals_result["sub_goals"][0],
    #     aspects=["research_plan", "sub_goals"],
    # )
    step4se_result = run_step4(
        gateway=gateway,
        sub_goals=subgoals_result["sub_goals"],
        # aspects=subgoals_result["research_plan", "sub_goals"],
    )
    print("\n",step4se_result.keys())
    # print()
    # print()
    # print()
    # print()
    # print()
    # print("\n",step4se_result)
    save_result(step4se_result, "cache/step4se_result.pkl")


    print("\n==============================")
    print("Step 6: Generate Draft Paragraphs for Sub-goals")
    step6_paragraphs = generate_paragraphs_for_sub_goals(
        gateway=gateway,
        result=step4se_result
    )
    save_result(step6_paragraphs, "cache/step6_paragraphs.pkl")
    print("=== step6 over ===")

    

    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "retrieval_finished",
            {
                "title": "明确腕骨骨折的主要类型及其诊断标准，为治疗方案的选择提供依据",
                "source": "传统手法结合距下关节与内侧柱双稳定术治疗青少年柔性平足症的临床观察_曾广龙.pdf",
                "sub_goal_id": "SG-1",
            },
        )
    )
    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "retrieval_finished",
            {
                "title": "探讨保守治疗方法（如固定、牵引）在不同类型腕骨骨折中的适应症与疗效",
                "source": "筋骨并重”理论在腕关节镜辅助治疗Herbert_B型舟骨骨折合并TFCC损伤术后康复中的应用_向往.pdf",
                "sub_goal_id": "SG-1",
            },
        )
    )
    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "retrieval_finished",
            {
                "title": "梳理术后或保守治疗后的康复流程，关注功能恢复的时间线与评价指标",
                "source": "记忆合金Ⅰ型钉脚固定器联合克氏针治疗经舟骨月骨周围背侧脱位的临床疗效研究_汤浩.pdf",
                "sub_goal_id": "SG-1",
            },
        )
    )
    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "retrieval_finished",
            {
                "title": "总结近三年内关于腕骨骨折治疗与康复的主要研究发现和发展方向",
                "source": "手术切除跟舟骨桥后趾短伸肌转位和脂肪填塞的疗效对比_李春光.pdf",
                "sub_goal_id": "SG-1",
            },
        )
    )
    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "retrieval_finished",
            {
                "title": "总结近三年内关于腕骨骨折治疗与康复的主要研究发现和发展方向",
                "source": "基于肌肉力学及肌电活动特征评估专用防护鞋及鞋垫治疗副舟骨综合征的有效性_程自申.pdf",
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

    # await asyncio.sleep(1)
    # await event_bus.emit(
    #     sse_event(
    #         "assistant_chunk",
    #         {
    #             "content": (
    #                 "Additionally, dysregulation of the HPA axis has been linked "
    #                 "to depressive symptoms."
    #             )
    #         },
    #     )
    # )

    # =====================================================
    # 4. write 阶段
    # =====================================================
    # await asyncio.sleep(0.8)
    await event_bus.emit(
        sse_event("phase_changed", {"phase": "write"})
    )
    ress = run_step7_global_edit(
        gateway=gateway,
        requirements=step1_little,
        plan=step2_little,
        draft_paragraphs=step6_paragraphs
    )
    # print
    print()
    print()
    print()
    print()
    pretty(ress["content"])
    save_result(ress, "cache/step7_final_doc.pkl")
    await asyncio.sleep(1)
    await event_bus.emit(
        sse_event(
            "final_output",
            {
                "content": (
                    "" + ress["content"]
                    # "## Preliminary Conclusion\n\n"
                    # "The available evidence suggests a potential mediating role of inflammation "
                    # "and HPA axis dysfunction in the association between PM2.5 exposure and depression."
                )
            },
        )
    )

    print("✅ Fake research finished:", session_id)
