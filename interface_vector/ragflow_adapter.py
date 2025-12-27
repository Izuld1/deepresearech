from collections import Counter
from typing import Dict, List


class RAGFlowAdapter:
    """
    将 RAGFlow UI 检索结果，转换为：
    - LLM 可用的上下文
    - 用户可解释的证据
    """

    def __init__(
        self,
        *,
        max_contexts: int = 10,
        min_similarity: float = 0.0,
    ):
        self.max_contexts = max_contexts
        self.min_similarity = min_similarity

    def adapt(self, ragflow_results: List[Dict]) -> Dict:
        """
        ragflow_results:
            多次搜索返回结果的列表，
            每个元素结构与单次 RAGFlow 返回一致
        """

        # ---------- 0. 拉平所有 chunks ----------
        all_chunks = []
        for result in ragflow_results:
            all_chunks.extend(result.get("chunks", []))

        # ---------- 1. 使用 chunk_id 聚合 ----------
        chunk_map = {}

        for c in all_chunks:
            similarity = c.get("similarity", 0)
            if similarity < self.min_similarity:
                continue

            cid = c.get("chunk_id")
            if not cid:
                continue

            if cid not in chunk_map:
                chunk_map[cid] = {
                    **c,
                    "_hit_count": 1
                }
            else:
                chunk_map[cid]["_hit_count"] += 1

                # 保留更高相似度的那一次
                if similarity > chunk_map[cid].get("similarity", 0):
                    chunk_map[cid].update(c)

        # ---------- 2. 排序 ----------
        filtered = sorted(
            chunk_map.values(),
            key=lambda c: c.get("similarity", 0),
            reverse=True
        )

        # ---------- 3. 构造 LLM Context ----------
        contexts = []
        for c in filtered[: self.max_contexts]:
            contexts.append({
                "text": c.get("content_with_weight", "").strip(),
                "source": c.get("docnm_kwd"),
                # "score": round(c.get("similarity", 0), 4),
            })

        # ---------- 4. 构造 Evidence ----------
        evidences = []
        for c in filtered:
            evidences.append({
                "doc_name": c.get("docnm_kwd"),
                "doc_id": c.get("doc_id"),
                "chunk_id": c.get("chunk_id"),

                # 新增：该 chunk 出现次数
                "hit_count": c.get("_hit_count", 1),

                "similarity": round(c.get("similarity", 0), 4),
                "vector_similarity": round(c.get("vector_similarity", 0), 4),
                "excerpt": c.get("content_with_weight", "")[:300].strip(),
            })

        # ---------- 5. Meta 信息 ----------
        doc_counter = Counter(
            c.get("docnm_kwd") for c in filtered
        )

        meta = {
            "total_chunks": len(filtered),
            "docs_hit": len(doc_counter),

            "doc_distribution": [
                {
                    "doc_name": doc,
                    "chunks": cnt
                }
                for doc, cnt in doc_counter.most_common()
            ]
        }

        return {
            "contexts": contexts,
            "evidences": evidences,
            "meta": meta,
        }
