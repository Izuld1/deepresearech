# =========================================================
# Step 4B: Evidence Evaluation（仅评估，不检索）
# 现在的评估只有检索结果数量，后续可以添加更多维度
# =========================================================

from typing import Dict, Any, List
def evaluate_evidence_pool(
    *,
    evidence_pool: Dict[str, Any],
    # aspects: List[str],
    coverage_threshold: float = 0.8,
) -> Dict[str, Any]:
    """
    对 EvidencePool 进行评估：
    - 覆盖度
    - 多文献性
    - 共识信号
    """
    
        #     "contexts": contexts,
        #     "evidences": evidences,
        #     "meta": meta,
        # }
    contexts = evidence_pool.get("contexts", [])
    meta = evidence_pool.get("meta", {})
    print(len(contexts))
    if len(contexts) >= 20 :
        decision = "sufficient"
    elif len(contexts) >= 10 :
        decision = "partial"
    else :
        decision = "insufficient"
    quality_signals = {
        "total_chunks": meta.get("total_chunks", 0),
        "docs_hit": meta.get("docs_hit", 0),
    }

    return {
        "decision": decision,
        "quality_signals": quality_signals,
    }
    return 0
    # evidences = evidence_pool.get("evidences", [])

    # ---------- 1. 覆盖度（占位实现，可替换） ----------
    # 目前假设：Evidence 中尚未标注 covered_aspects
    # covered_aspects = set()
    # for e in evidences:
    #     covered_aspects.update(e.get("covered_aspects", []))

    # if aspects:
    #     coverage_ratio = len(covered_aspects) / len(aspects)
    # else:
    #     coverage_ratio = 0.0

    # ---------- 2. 判定 ----------
    if coverage_ratio >= coverage_threshold:
        decision = "sufficient"
    elif coverage_ratio >= 0.4:
        decision = "partial"
    else:
        decision = "insufficient"

    # ---------- 3. 质量信号 ----------
    quality_signals = {
        "total_chunks": meta.get("total_chunks", 0),
        "docs_hit": meta.get("docs_hit", 0),
    }

    return {
        "decision": decision,
        "quality_signals": quality_signals,
    }
