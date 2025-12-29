"""
steps/step4_retrieve.py
-----------------------
Step 4: Sub-goal Driven Retrieval（仅检索，不写作）

这是 DeepResearch 的“证据引擎”。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import hashlib
import time


# =========================================================
# 0. Retriever 接口（语义级，Step 4 只依赖这个）
# =========================================================

class RetrieverGateway:
    def retrieve(
        self,
        *,
        sub_goal: Dict[str, Any],
        queries: List[str],
        top_k: int,
        constraints: Dict[str, Any],
    ) -> List["EvidenceItem"]:
        raise NotImplementedError


@dataclass
class EvidenceItem:
    chunk: str
    source: Dict[str, Any]
    score: float
    meta: Dict[str, Any] = field(default_factory=dict)


# =========================================================
# 1. Evidence Pool
# =========================================================

def _hash_text(s: str) -> str:
    return hashlib.md5(s.encode("utf-8", errors="ignore")).hexdigest()


@dataclass
class EvidenceRecord:
    evidence_id: str
    chunk: str
    source: Dict[str, Any]
    score: float
    meta: Dict[str, Any]
    covered_aspects: List[str] = field(default_factory=list)


@dataclass
class EvidencePool:
    pool_id: str
    sub_goal_id: str
    intent: str

    evidence: List[EvidenceRecord] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set)

    def add_many(self, items: List[EvidenceItem]) -> int:
        added = 0
        for it in items:
            text = (it.chunk or "").strip()
            if not text:
                continue
            h = _hash_text(text)
            if h in self._seen:
                continue
            self._seen.add(h)
            self.evidence.append(
                EvidenceRecord(
                    evidence_id=f"E-{h[:8]}",
                    chunk=text,
                    source=it.source,
                    score=float(it.score),
                    meta=it.meta,
                )
            )
            added += 1
        return added


# =========================================================
# 2. Coverage Report（裁决态）
# =========================================================

@dataclass
class CoverageReport:
    aspects: List[str]
    covered_aspects: List[str]
    ratio: float

    decision: str  # "sufficient" | "partial" | "insufficient"


# =========================================================
# 3. Step 4 主流程
# =========================================================

def run_retrieval_loop_for_subgoal(
    *,
    retriever: RetrieverGateway,
    sub_goal: Dict[str, Any],
    requirements: Dict[str, Any],
    llm=None,
    max_rounds: int = 3,
    top_k: int = 10,
    coverage_threshold: float = 0.8,
) -> Dict[str, Any]:

    sub_goal_id = sub_goal["sub_goal_id"]
    intent = sub_goal["current_intent"]

    pool = EvidencePool(
        pool_id=f"POOL-{sub_goal_id}",
        sub_goal_id=sub_goal_id,
        intent=intent,
    )

    queries = sub_goal.get("query_hints") or [intent]
    constraints = requirements.get("literature_scope", {})

    trace = []
    no_growth_rounds = 0

    # ===== Aspect schema（你已有，这里假设已实现）=====
    aspects = sub_goal.get("aspects") or []

    for r in range(1, max_rounds + 1):
        items = retriever.retrieve(
            sub_goal=sub_goal,
            queries=queries,
            top_k=top_k,
            constraints=constraints,
        )

        added = pool.add_many(items)

        trace.append({
            "round": r,
            "queries": list(queries),
            "added": added,
            "total": len(pool.evidence),
            "time": time.time(),
        })

        if added == 0:
            no_growth_rounds += 1
        else:
            no_growth_rounds = 0

        # ===== Coverage（简化示例）=====
        covered = set()
        for rec in pool.evidence:
            covered.update(rec.covered_aspects)

        ratio = len(covered) / len(aspects) if aspects else 0.0

        if ratio >= coverage_threshold:
            decision = "sufficient"
        elif ratio >= 0.4:
            decision = "partial"
        else:
            decision = "insufficient"

        coverage = CoverageReport(
            aspects=aspects,
            covered_aspects=list(covered),
            ratio=ratio,
            decision=decision,
        )

        if decision == "sufficient":
            return {
                "status": "completed",
                "pool": pool,
                "coverage": coverage.__dict__,
                "trace": trace,
            }

        # ===== 提前耗尽判定 =====
        if no_growth_rounds >= 2:
            break

        # ===== Query Rewrite（若可用）=====
        if llm and decision != "sufficient":
            missing = [a for a in aspects if a not in covered]
            new_queries = llm.rewrite_queries(intent, queries, missing)
            if new_queries:
                queries = list(dict.fromkeys(queries + new_queries))

    return {
        "status": "unresolved",
        "pool": pool,
        "coverage": coverage.__dict__,
        "trace": trace,
        "reason": "coverage_insufficient_or_retrieval_exhausted",
    }
