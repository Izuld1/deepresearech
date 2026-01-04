# steps/step4_retrieve.py

from typing import Dict, Any, List
from core.retriever_gateway import RetrievalGateway
from steps.step4_select import run_retrieval_for_subgoal
from steps.step4_eval import evaluate_evidence_pool
from steps.step4_replaner import generate_expanded_intent
from steps.step5_adjudicator import evaluate_subgoal_support_with_llm

def run_step4_for_subgoal(
    *,
    gateway: RetrievalGateway,
    sub_goal: Dict[str, Any],
    kb_ids,
    # aspects: List[str],
    max_rounds: int = 3,
    size: int = 10,
    coverage_threshold: float = 0.8,
) -> Dict[str, Any]:
    """
    Step 4: Sub-goal Driven Retrieval
    - 仅检索 + 裁决
    - 不写作、不总结、不生成结论
    """

    trace = []
    #  ====================步骤4=====================
    for r in range(1, max_rounds + 1):
        print(f"==============================\nStep 4: Round {r} Retrieval")

        # ===== Step 4A: Retrieve =====
        retrieval_result = run_retrieval_for_subgoal(
            # gateway=gateway,
            kb_ids=kb_ids,
            sub_goal=sub_goal,
            size=size,
        )
        # "contexts": result.get("contexts", []),
        # "evidences": result.get("evidences", []),
        # "meta": result.get("meta", {}),
        print(retrieval_result.keys())  # 打印检索结果结构，检查 'evidence_pool' 是否存在

        if r == 1 :
            pool = retrieval_result["evidence_pool"]
        else:
            # # pool["evidence_pool"]["contexts"] = list(set(pool["evidence_pool"]["contexts"].append(retrieval_result["evidence_pool"]["contexts"])))
            # # pool["evidence_pool"]["evidences"] = list(set(pool["evidence_pool"]["evidences"].append(retrieval_result["evidence_pool"]["evidences"])))
            # # 正确的合并方式是使用 `extend()` 而不是 `append()`。
            # pool["evidence_pool"]["contexts"].extend(retrieval_result["evidence_pool"]["contexts"])
            # pool["evidence_pool"]["evidences"].extend(retrieval_result["evidence_pool"]["evidences"])

            # # 使用 set 去重
            # pool["evidence_pool"]["contexts"] = list(set(pool["evidence_pool"]["contexts"]))
            # pool["evidence_pool"]["evidences"] = list(set(pool["evidence_pool"]["evidences"]))
            pool["contexts"].extend(
                retrieval_result["evidence_pool"]["contexts"]
            )
            pool["evidences"].extend(
                retrieval_result["evidence_pool"]["evidences"]
            )

            # 可选：基于 chunk_id 去重（推荐）
            pool["contexts"] = {
                (c["text"], c["source"]): c
                for c in pool["contexts"]
            }.values()

            pool["evidences"] = {
                e["chunk_id"]: e
                for e in pool["evidences"]
            }.values()

            pool["contexts"] = list(pool["contexts"])
            pool["evidences"] = list(pool["evidences"])




        trace.append({
            "round": r, # 仅一轮
            "total_chunks": pool.get("meta", {}).get("total_chunks", 0),
        })

        # ===== Step 4B: Evaluate =====
        evaluation = evaluate_evidence_pool(
            evidence_pool=pool,
            # aspects=aspects,
            coverage_threshold=coverage_threshold,
        )

        if evaluation["decision"] == "sufficient":
            # return {
            #     "status": "completed",
            #     "pool": pool,
            #     "evaluation": evaluation,
            #     "trace": trace,
            # }
            break



        # 流程级终止（不在此做 query rewrite）
        if evaluation["decision"] == "insufficient":
            # 示例调用：
            current_intent =  sub_goal["current_intent"] #"患者年龄、职业与活动水平对治疗方案的影响"
            current_query_hints = sub_goal["query_hints"]

            # 假设 gateway 是已创建的 LLMGateway 实例
            expanded_intent = generate_expanded_intent(gateway, current_intent, current_query_hints)

            print(expanded_intent)

            sub_goal["current_intent"] = expanded_intent["current_intent"]
            sub_goal["query_hints"] = expanded_intent["query_hints"]
            sub_goal["fallback_history"].append(sub_goal["current_intent"])









    #  ====================步骤4=====================
    #  ====================步骤5=====================
    print("+++++++++++++++++++++++++++")
    for r in range(11, max_rounds + 11):
        print(f"==============================\nStep 5: Round {r-10} Evidence Adjudication")
        if r != 11:
            # ===== Step 4A: Retrieve =====
            retrieval_result = run_retrieval_for_subgoal(
                # gateway=gateway,
                kb_ids=kb_ids,
                sub_goal=sub_goal,
                size=size,
            )
            # "contexts": result.get("contexts", []),
            # "evidences": result.get("evidences", []),
            # "meta": result.get("meta", {}),
            print(retrieval_result.keys())  # 打印检索结果结构，检查 'evidence_pool' 是否存在

        # if r == 1 :
        #     pool = retrieval_result["evidence_pool"]
        if r != 11:
            # # pool["evidence_pool"]["contexts"] = list(set(pool["evidence_pool"]["contexts"].append(retrieval_result["evidence_pool"]["contexts"])))
            # # pool["evidence_pool"]["evidences"] = list(set(pool["evidence_pool"]["evidences"].append(retrieval_result["evidence_pool"]["evidences"])))
            # # 正确的合并方式是使用 `extend()` 而不是 `append()`。
            # pool["evidence_pool"]["contexts"].extend(retrieval_result["evidence_pool"]["contexts"])
            # pool["evidence_pool"]["evidences"].extend(retrieval_result["evidence_pool"]["evidences"])

            # # 使用 set 去重
            # pool["evidence_pool"]["contexts"] = list(set(pool["evidence_pool"]["contexts"]))
            # pool["evidence_pool"]["evidences"] = list(set(pool["evidence_pool"]["evidences"]))
            pool["contexts"].extend(
                retrieval_result["evidence_pool"]["contexts"]
            )
            pool["evidences"].extend(
                retrieval_result["evidence_pool"]["evidences"]
            )

            # 可选：基于 chunk_id 去重（推荐）
            pool["contexts"] = {
                (c["text"], c["source"]): c
                for c in pool["contexts"]
            }.values()

            pool["evidences"] = {
                e["chunk_id"]: e
                for e in pool["evidences"]
            }.values()

            pool["contexts"] = list(pool["contexts"])
            pool["evidences"] = list(pool["evidences"])




            trace.append({
                "round": r, # 仅一轮
                "total_chunks": pool.get("meta", {}).get("total_chunks", 0),
            })

        # # ===== Step 4B: Evaluate =====
        # evaluation = evaluate_evidence_pool(
        #     evidence_pool=pool,
        #     # aspects=aspects,
        #     coverage_threshold=coverage_threshold,
        # )
        evaluation = evaluate_subgoal_support_with_llm(
            gateway=gateway,
            sub_goal=pool,
            retrieval_result=pool,
        )
        print(evaluation)

        if evaluation["decision"] == "sufficient":
            return {
                "status": "completed",
                "pool": pool,
                "evaluation": evaluation,
                "trace": trace,
            }



        # 流程级终止（不在此做 query rewrite）
        if evaluation["decision"] == "insufficient":
            # 示例调用：
            current_intent =  sub_goal["current_intent"] #"患者年龄、职业与活动水平对治疗方案的影响"
            current_query_hints = sub_goal["query_hints"]

            # 假设 gateway 是已创建的 LLMGateway 实例
            expanded_intent = generate_expanded_intent(gateway, current_intent, current_query_hints)

            print(expanded_intent)

            sub_goal["current_intent"] = expanded_intent["current_intent"]
            sub_goal["query_hints"] = expanded_intent["query_hints"]
            sub_goal["fallback_history"].append(sub_goal["current_intent"])

    print("+++++++++++++++++++++++++++")


    #  ====================步骤5=====================
    return {
        "status": "unresolved",
        "pool": pool,
        "evaluation": evaluation,
        "trace": trace,
        "reason": "coverage_insufficient",
    }




def run_step4(
    *,
    kb_ids,
    gateway: RetrievalGateway,
    sub_goals: List[Dict[str, Any]],
    # aspect_map: Dict[str, List[str]],
) -> Dict[str, Any]:
    """
    Step 4（整体）：
    - 对每一个 sub_goal 独立执行证据检索与评估
    - 不做跨 sub_goal 合并
    """

    results = []

    for sg in sub_goals:
        print("\n\n==============================")
        sg_id = sg["sub_goal_id"]
        print(f"Running Step 4 for sub-goal {sg_id}...")

        result = run_step4_for_subgoal(
            kb_ids=kb_ids,
            gateway=gateway,
            sub_goal=sg,
            # aspects=aspect_map.get(sg_id, []),
        )

        results.append({
            "sub_goal_id": sg_id,
            "parent_section_id": sg.get("parent_section_id"),
            "intent": sg.get("current_intent"),
            "result": result,
        })

    return {
        "step": "step4",
        "sub_goal_results": results,
    }
