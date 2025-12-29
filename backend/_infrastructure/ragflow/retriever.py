"""
RAGFlow Retriever Adapter
-------------------------
实现 core.retriever.Retriever 接口
"""

from typing import List, Dict, Any
from core._retriever import Retriever
from _infrastructure.ragflow.client import RAGFlowClient


class RAGFlowRetriever(Retriever):
    def __init__(
        self,
        client: RAGFlowClient,
        kb_registry: Dict[str, str],
    ):
        """
        kb_registry: 逻辑知识库名 -> dataset_id
        """
        self.client = client
        self.kb_registry = kb_registry

    def retrieve(
        self,
        *,
        sub_goal: Dict[str, Any],
        queries: List[str],
        top_k: int,
        constraints: Dict[str, Any],
    ) -> Dict[str, Any]:

        kb_name = constraints.get("kb_name")
        if kb_name not in self.kb_registry:
            raise ValueError(f"Unknown knowledge base: {kb_name}")

        dataset_id = self.kb_registry[kb_name]

        evidence = []
        eid = 1

        for q in queries:
            results = self.client.search(
                dataset_id=dataset_id,
                query=q,
                top_k=top_k,
            )

            for r in results:
                evidence.append({
                    "evidence_id": f"E{eid}",
                    "chunk": r["content"],
                    "source": {
                        "kb": kb_name,
                        "dataset_id": dataset_id,
                        "document_id": r.get("document_id"),
                        "chunk_id": r.get("chunk_id"),
                        "page": r.get("metadata", {}).get("page"),
                    },
                    "score": r.get("score", 0.0),
                    "query": q,
                })
                eid += 1

        return {
            "evidence": evidence,
            "meta": {
                "sub_goal_id": sub_goal["sub_goal_id"],
                "query_count": len(queries),
                "total_hits": len(evidence),
            },
        }
