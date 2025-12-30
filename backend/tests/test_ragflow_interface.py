# from ragflow_sdk import RAGFlow

# # 初始化 RAGFlow 实例（保留你的原有配置）
# rag_object = RAGFlow(api_key="ragflow-LRCQcaNm8v4n5ea0Qo7ui35or2Hk6TBz4_PJSPbUH7o", base_url="http://localhost:9380")

# # 遍历所有数据集，格式化输出关键字段（改用 . 点语法访问属性）
# print("===== RAGFlow 数据集关键字段信息 =====")
# for index, dataset in enumerate(rag_object.list_datasets(), start=1):
#     print(f"\n第 {index} 个数据集：")
#     print(f"  唯一ID：{dataset.id}")          # 改用 .id 访问，替代 dataset['id']
#     print(f"  数据集名称：{dataset.name}")    # 改用 .name 访问，替代 dataset['name']
#     print(f"  上传文档数：{dataset.document_count}")  # 改用 .document_count 访问
#     print(f"  文本分片数：{dataset.chunk_count}")     # 改用 .chunk_count 访问
#     # 若需追加其他字段，同样用 . 点语法，示例：
#     # print(f"  嵌入模型：{dataset.embedding_model}")
#     # print(f"  权限类型：{dataset.permission}")
from collections import Counter
from typing import Dict, List
from collections import Counter
from typing import Dict, List, Any


class RAGFlowAdapter:
    """
    将 新RAGFlow 检索结果（Response实例列表 / 字典列表），转换为：
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

    def _get_field(self, item: Any, field_name: str, default: Any = None) -> Any:
        """
        统一获取字段：兼容 Response 实例（属性访问）和 字典（键访问）
        """
        try:
            # 先尝试属性访问（适配 Response 实例）
            return getattr(item, field_name, default)
        except:
            # 失败则尝试字典键访问（兼容旧字典格式）
            return item.get(field_name, default) if isinstance(item, dict) else default

    def adapt(self, ragflow_results: List[Any]) -> Dict:
        """
        适配 RAGFlow 结果格式：支持 Response 实例列表 / 字典列表
        """
        # ---------- 0. 初始化所有 chunks ----------
        all_chunks = []
        for chunk in ragflow_results:
            all_chunks.append(chunk)

        # ---------- 1. 使用 chunk_id（id 字段/属性）聚合 ----------
        chunk_map = {}

        for c in all_chunks:
            # 安全获取相似度（兼容 Response 和 字典）
            similarity = self._get_field(c, "similarity", 0.0)
            # 过滤非数字类型或低于最小相似度的Chunk
            if not isinstance(similarity, (int, float)):
                continue
            if similarity < self.min_similarity:
                continue

            # 安全获取 chunk 唯一标识（id 字段/属性）
            cid = self._get_field(c, "id")
            if not cid:
                continue

            # 去重并聚合，记录命中次数
            if cid not in chunk_map:
                # 存储原始实例/字典，并添加命中次数
                chunk_map[cid] = {
                    "item": c,
                    "_hit_count": 1,
                    "similarity": similarity
                }
            else:
                chunk_map[cid]["_hit_count"] += 1
                # 保留更高相似度的那一次数据
                if similarity > chunk_map[cid]["similarity"]:
                    chunk_map[cid]["item"] = c
                    chunk_map[cid]["similarity"] = similarity

        # ---------- 2. 按相似度倒序排序 ----------
        filtered_items = sorted(
            chunk_map.values(),
            key=lambda x: x["similarity"],
            reverse=True
        )

        # ---------- 3. 构造 LLM Context ----------
        contexts = []
        for item_wrap in filtered_items[: self.max_contexts]:
            c = item_wrap["item"]
            contexts.append({
                "text": self._get_field(c, "content", "").strip(),
                "source": self._get_field(c, "document_name", "未知文档"),
            })

        # ---------- 4. 构造 Evidence ----------
        evidences = []
        for item_wrap in filtered_items:
            c = item_wrap["item"]
            evidences.append({
                "doc_name": self._get_field(c, "document_name", "未知文档"),
                "doc_id": self._get_field(c, "document_id", ""),
                "chunk_id": self._get_field(c, "id", ""),
                "hit_count": item_wrap["_hit_count"],
                "similarity": round(item_wrap["similarity"], 4),
                "vector_similarity": round(self._get_field(c, "vector_similarity", 0.0), 4),
                "excerpt": self._get_field(c, "content", "")[:300].strip(),
            })

        # ---------- 5. Meta 信息 ----------
        doc_counter = Counter()
        for item_wrap in filtered_items:
            doc_name = self._get_field(item_wrap["item"], "document_name", "未知文档")
            doc_counter[doc_name] += 1

        meta = {
            "total_chunks": len(filtered_items),
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
    
import json
from ragflow_sdk import RAGFlow

# 初始化 RAGFlow 实例
rag_object = RAGFlow(
    api_key="ragflow-LRCQcaNm8v4n5ea0Qo7ui35or2Hk6TBz4_PJSPbUH7o",
    base_url="http://host.docker.internal:9380"
    # base_url="http://localhost:9380"
)

def search_list_ragflow(query_hints: List[str], kb_ids: List[str] = ["腕骨骨折"], size: int = 10):
    """
    批量查询 RAGFlow：保留 Response 实例，不过滤有效数据
    """
    if size == 10 :
        size = int(0.8 * len(query_hints) * len(kb_ids) * 10)
    results = []
    for i in range(len(query_hints)):
        for j in range(len(kb_ids)):
            dataset = rag_object.list_datasets(name=kb_ids[j])[0]
            # 获取单次检索的 Response 实例列表（有效数据）
            single_retrieve_result = rag_object.retrieve(
                dataset_ids=[dataset.id],
                question=query_hints[i],
                keyword = True
            )
            # 关键修正：直接 extend 保留所有 Response 实例，不做字典过滤
            results.extend(single_retrieve_result)

    adapter = RAGFlowAdapter(
        max_contexts=size,
        # min_similarity=0.85  # 可根据需要开启，暂时关闭避免过滤过多
    )
    adapted = adapter.adapt(results)
    return adapted

# query_hints = [
#         "腕骨骨折 康复效果评估 DASH评分 肌力 活动度",
#         "腕骨骨折 康复 评价指标 功能评分"
#       ]
# aaa = search_list_ragflow(query_hints)

# #  Meta 信息
# meta = aaa["meta"]
# print("=== Meta Information ===")
# print(meta)

# # 可选：打印上下文和证据，验证数据是否有效
# print("\n=== Contexts ===")
# for ctx in aaa["contexts"]:
#     print(f"来源：{ctx['source']}")
#     print(f"文本：{ctx['text'][:100]}...")
#     print("-" * 50)
# query_hints = [
#         "腕骨骨折 康复效果评估 DASH评分 肌力 活动度",
#         "腕骨骨折 康复 评价指标 功能评分"
#       ]
# aaa = search_list_ragflow(query_hints)

# #  Meta 信息
# meta = aaa["meta"]
# print("=== Meta Information ===")
# print(meta)








# assistant = rag_object.list_chats()[0]
# session = assistant.create_session()    

# # print("\n==================== Miss R =====================\n")
# # print("Hello. What can I do for you?")

# # while True:
# question = "导致腕骨骨折的原因都有哪些"
# print("\n==================== Miss R =====================\n")

# cont = ""
# with open("cache/test_output.txt", "w", encoding="utf-8") as f:
#     for ans in session.ask(question, stream=True):
#         print(ans, end='', flush=True,file=f)
#         # cont = ans.content

# from ragflow_sdk import RAGFlow

# rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")


# for dataset in rag_object.list_datasets():
#     print(dataset)

# dataset = rag_object.list_datasets(name="腕骨骨折")
# dataset = dataset[0]
# # print(dataset.id)

# # # name = 'ragflow_test.txt'
# # # path = './test_data/ragflow_test.txt'
# # # documents =[{"display_name":"test_retrieve_chunks.txt","blob":open(path, "rb").read()}]
# # # docs = dataset.upload_documents(documents)
# # # doc = docs[0]
# # # doc.add_chunk(content="This is a chunk addition test")
# mess = rag_object.retrieve(dataset_ids=[dataset.id],question="腕骨骨折 康复效果评估 DASH评分 肌力 活动度",keyword = True)
# import os

# # 获取当前工作目录（返回字符串格式的路径）
# current_work_dir = os.getcwd()
# # 打印输出
# print("当前工作目录：", current_work_dir)
# print(len(mess))
# with open("backend/cache/ragflow_output.json", "w", encoding="utf-8") as f:
#     for mes in mess :
#         print(mes,file=f)
#         # print(json.dumps(mes, ensure_ascii=False, indent=2),file=f)