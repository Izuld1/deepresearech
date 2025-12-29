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


from ragflow_sdk import RAGFlow

# 初始化 RAGFlow 实例
rag_object = RAGFlow(
    api_key="ragflow-LRCQcaNm8v4n5ea0Qo7ui35or2Hk6TBz4_PJSPbUH7o",
    base_url="http://localhost:9380"
)

for assistant in rag_object.list_chats():
    print(assistant)



assistant = rag_object.list_chats()[0]
session = assistant.create_session()    

# print("\n==================== Miss R =====================\n")
# print("Hello. What can I do for you?")

# while True:
question = "导致腕骨骨折的原因都有哪些"
print("\n==================== Miss R =====================\n")

cont = ""
with open("cache/test_output.txt", "w", encoding="utf-8") as f:
    for ans in session.ask(question, stream=True):
        print(ans, end='', flush=True,file=f)
        # cont = ans.content