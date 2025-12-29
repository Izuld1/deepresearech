# # core/retrievers/ragflow_retriever.py

# from typing import List, Dict, Any
# import requests

# from core.retriever_gateway import RetrieverGateway, EvidenceItem


# class RAGFlowRetriever(RetrieverGateway):
#     def __init__(
#         self,
#         *,
#         base_url: str,
#         api_key: str,
#         knowledge_base: str,
#         default_top_k: int = 10,
#         score_threshold: float = 0.0,
#         timeout: int = 30,
#     ):
#         self.base_url = base_url.rstrip("/")
#         self.api_key = api_key
#         self.knowledge_base = knowledge_base
#         self.default_top_k = default_top_k
#         self.score_threshold = score_threshold
#         self.timeout = timeout

#     def retrieve(
#         self,
#         *,
#         sub_goal: Dict[str, Any],
#         queries: List[str],
#         top_k: int,
#         constraints: Dict[str, Any],
#         timeout: float | None = None,
#     ) -> List[EvidenceItem]:

#         payload = {
#             "knowledge_base": self.knowledge_base,
#             "queries": queries,
#             "top_k": top_k or self.default_top_k,
#             "filters": {
#                 "only_uploaded": constraints.get("only_uploaded", True),
#                 "time_range": constraints.get("time_range", ""),
#                 "language": constraints.get("language", "zh"),
#                 "domain": constraints.get("domain", ""),
#                 "topic": constraints.get("topic", ""),
#             }
#         }

#         resp = requests.post(
#             f"{self.base_url}/api/retrieve",
#             headers={"Authorization": f"Bearer {self.api_key}"},
#             json=payload,
#             timeout=timeout or self.timeout,
#         )
#         resp.raise_for_status()

#         data = resp.json()

#         results: List[EvidenceItem] = []
#         for hit in data.get("results", []):
#             if hit.get("score", 0.0) < self.score_threshold:
#                 continue

#             results.append(
#                 EvidenceItem(
#                     chunk=hit.get("content", ""),
#                     source={
#                         "doc_id": hit.get("doc_id"),
#                         "title": hit.get("title"),
#                         "kb": self.knowledge_base,
#                     },
#                     score=float(hit.get("score", 0.0)),
#                     meta=hit,
#                 )
#             )

#         return results
