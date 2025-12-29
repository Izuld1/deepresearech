# """
# Interactive test for Step 1 + Step 2
# ------------------------------------
# - 用户真实输入
# - 不写死对话
# - Step 1 完成后自动进入 Step 2
# - 所有结构化输出以 JSON 形式美化打印（但内部仍是 dict）
# """

# import json

# from core.llm_gateway import build_qwen_gateway_from_env
# from steps.step1_clarify import ClarificationState, clarification_step
# from steps.step2_plan import generate_research_plan


# # =========================
# # 工具函数：JSON 美化输出
# # =========================

# def pretty_print(title: str, data):
#     """
#     仅用于输出层：
#     - 不改变 data 本身
#     - 只负责把 dict / list 漂亮地打印出来
#     """
#     print(f"\n--- {title} ---")
#     print(
#         json.dumps(
#             data,
#             ensure_ascii=False,
#             indent=2,
#         )
#     )


# def main():
#     gateway = build_qwen_gateway_from_env()
#     state = ClarificationState()

#     print("=== DeepResearch Bootstrap Flow ===")
#     print("Step 1: Research Requirement Clarification")

#     # ---------- Step 1: 对话式澄清 ----------
#     while True:
#         user_input = input("\nUser > ").strip()
#         if not user_input:
#             continue

#         result = clarification_step(gateway, state, user_input)

#         pretty_print("System Response", result)

#         status = result["status"]

#         if status == "need_clarification":
#             print("\n[Need clarification, please answer the questions above]")
#             continue

#         if status == "completed":
#             print("\n[Clarification completed]")
#             requirements = result["requirements"]
#             pretty_print("Final Requirements", requirements)
#             break

#         if status in ("failed", "completed_with_gaps"):
#             print("\n[Clarification ended with unresolved issues]")
#             pretty_print("Clarification Result", result)
#             return

#     # ---------- Step 2: Research Plan ----------
#     print("\n==============================")
#     print("Step 2: Research Plan Generation")

#     plan = generate_research_plan(
#         gateway=gateway,
#         requirements=requirements,
#     )

#     pretty_print("Research Plan", plan)

#     print("\n[Bootstrap flow finished successfully]")


# if __name__ == "__main__":
#     main()



"""
Interactive test for Step 1 + Step 2 + Step 3
---------------------------------------------
- 用户真实输入
- 不写死对话
- Step 1 完成后自动进入 Step 2
- Step 2 完成后自动进入 Step 3
"""


from core.llm_gateway import build_qwen_gateway_from_env
from steps.step1_clarify import ClarificationState, clarification_step
from steps.step2_plan import generate_research_plan
from steps.step3_subgoals import generate_sub_goals
# from steps.step4_select import run_retrieval_for_subgoal
from steps.step4_se_ev import run_step4_for_subgoal,run_step4
# from steps.step5_adjudicator import evaluate_subgoal_support_with_llm
from steps.step6_draft import generate_paragraphs_for_sub_goals
from utils.pickle_csp import save_result,pretty

# import pickle
# from pathlib import Path


# def save_result(obj, cache_path: str):
#     """
#     将任意 Python 对象序列化保存
#     """
#     cache_path = Path(cache_path)
#     cache_path.parent.mkdir(parents=True, exist_ok=True)
#     with open(cache_path, "wb") as f:
#         pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)



def main_run():
    gateway = build_qwen_gateway_from_env()
    

    state = ClarificationState()

    print("=== DeepResearch Bootstrap Flow ===")
    print("Step 1: Research Requirement Clarification")

    # ---------- Step 1 ----------
    while True:
        user_input = input("\nUser > ").strip()
        if not user_input:
            continue

        result = clarification_step(gateway, state, user_input)

        print("\nSystem >")
        pretty(result)
        print("\n=====","".join(result["questions"]))
        status = result["status"]

        if status == "need_clarification":
            print("\n[Need clarification, please answer the questions above]")
            continue

        if status == "completed":
            print("\n[Clarification completed]")
            requirements = result["requirements"]
            print("\nFinal requirements:")
            pretty(requirements)
            break

        if status in ("failed", "completed_with_gaps"):
            print("\n[Clarification ended with unresolved issues]")
            pretty(result)
            return
    save_result(requirements, "cache/step1_requirements.pkl")

    # ---------- Step 2 ----------
    print("\n==============================")
    print("Step 2: Research Plan Generation")
    plan = generate_research_plan(
        gateway=gateway,
        requirements=requirements,
    )

    print("\nResearch Plan:")
    pretty(plan)
    save_result(plan, "cache/step2_plan.pkl")





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
    paragraphs = generate_paragraphs_for_sub_goals(
        gateway=gateway,
        result=step4se_result
    )
    save_result(paragraphs, "cache/step6_paragraphs.pkl")
    print("=== step6 over ===")

    

if __name__ == "__main__":
    main_run()
