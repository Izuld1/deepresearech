# =========================================================
# Step 4A: Sub-goal Retrieval（仅查询，不评估）
# =========================================================

from typing import Dict, Any, List
from interface_vector.ragflow import search_list_ragflow


# =========================================================
# Step 4A: Sub-goal Retrieval（仅查询，不评估）
# =========================================================

def run_retrieval_for_subgoal(
    *,
    sub_goal: Dict[str, Any],
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
    print(queries)
    result = search_fn(
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


if __name__ == "__main__":
    pass