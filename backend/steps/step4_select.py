# =========================================================
# Step 4A: Sub-goal Retrieval（仅查询，不评估）
# =========================================================

from typing import Dict, Any, List
import os

print(os.getcwd())
# from interface_DB.ragflow import search_list_ragflow
from tests.test_ragflow_interface import search_list_ragflow

# =========================================================
# Step 4A: Sub-goal Retrieval（仅查询，不评估）
# =========================================================

def run_retrieval_for_subgoal(
    *,
    sub_goal: Dict[str, Any],
    kb_ids:list,
    search_fn = search_list_ragflow,                     # 已绑定权限 / 会话上下文的搜索函数
    size: int = 10,
) -> Dict[str, Any]:
    """
    对单个 sub-goal 执行一次“完整查询”：
    - 使用所有 query_hints
    - 知识库选择由 search_fn 内部处理（权限 / 范围控制）
    - 合并为一个 EvidencePool
    - 不做覆盖度判断
    """
    # print(sub_goal.keys())
    sub_goal_id = sub_goal["sub_goal_id"]
    intent = sub_goal["current_intent"]
    queries = sub_goal.get("query_hints") or [intent]

    # ---------- 1. 调用搜索接口 ----------
    # search_fn 内部已完成：
    # - 多 query
    # - 权限控制下的 KB 选择
    # - adapter 统一
    # print(queries)
    result = search_fn(
        kb_ids=kb_ids,
        query_hints=queries,
        size=size,
    )

    # ---------- 2. 构造 EvidencePool ----------
    pool = {
        "pool_id": f"POOL-{sub_goal_id}",
        "sub_goal_id": sub_goal_id,
        "intent": intent,

        # adapter 输出（LLM / 用户共用）
        "contexts": result.get("contexts", []),
        "evidences": result.get("evidences", []),
        "meta": result.get("meta", {}),

        # 检索态 trace（不暴露具体 KB）
        "retrieval_trace": {
            "queries": queries,
            "total_chunks": result.get("meta", {}).get("total_chunks", 0),
        }
    }

    return {
        "status": "retrieved",
        "evidence_pool": pool,
    }

def test_run_retrieval_for_subgoal_real(kb_ids):
    """
    最小真实测试：
    - 真实调用 search_list_ragflow
    - 不做 mock
    - 不依赖任何第三方库
    """

    # ---------- 1. 构造最小 sub_goal ----------
    sub_goal = {
        "sub_goal_id": "SG-test-001",
        "current_intent": "PM2.5 炎症 抑郁",
        "query_hints": [
            "PM2.5 炎症",
            "空气污染 抑郁"
        ]
    }

    # ---------- 2. 执行检索 ----------
    result = run_retrieval_for_subgoal(
        kb_ids,
        sub_goal=sub_goal,
        # size=5,   # 控制最小检索量，避免跑太久
    )
    print(result)
    # ---------- 3. 基础结构断言 ----------
    assert isinstance(result, dict), "返回结果必须是 dict"
    assert result.get("status") == "retrieved", "status 必须为 retrieved"

    pool = result.get("evidence_pool")
    assert isinstance(pool, dict), "evidence_pool 必须存在且为 dict"

    # ---------- 4. EvidencePool 关键字段 ----------
    assert pool.get("pool_id") == "POOL-SG-test-001"
    assert pool.get("sub_goal_id") == "SG-test-001"
    assert pool.get("intent") == "PM2.5 炎症 抑郁"

    # ---------- 5. 检索结果字段 ----------
    assert "contexts" in pool, "contexts 字段缺失"
    assert "evidences" in pool, "evidences 字段缺失"
    assert "meta" in pool, "meta 字段缺失"

    assert isinstance(pool["contexts"], list)
    assert isinstance(pool["evidences"], list)
    assert isinstance(pool["meta"], dict)

    # ---------- 6. retrieval_trace ----------
    trace = pool.get("retrieval_trace")
    assert isinstance(trace, dict), "retrieval_trace 必须存在"

    assert trace.get("queries") == sub_goal["query_hints"]
    assert isinstance(trace.get("total_chunks", 0), int)

    print("✅ run_retrieval_for_subgoal 真实测试通过")

if __name__ == "__main__":
    pass
    test_run_retrieval_for_subgoal_real()