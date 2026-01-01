from ragflow_sdk import RAGFlow
from typing import List
rag_object = RAGFlow(
    api_key="ragflow-LRCQcaNm8v4n5ea0Qo7ui35or2Hk6TBz4_PJSPbUH7o",
    # base_url="http://host.docker.internal:9380"
    base_url="http://localhost:9380"
)

# dataset = rag_object.create_dataset(name="kb_1")

# print(dataset)
# print(dataset.id)

from ragflow_sdk import RAGFlow

class KnowledgeBaseService:

    def __init__(self):
        self.rag = RAGFlow(
            api_key="ragflow-LRCQcaNm8v4n5ea0Qo7ui35or2Hk6TBz4_PJSPbUH7o",
            # base_url="http://host.docker.internal:9380"
            base_url="http://localhost:9380"
        )

    def create(self, name: str):
        dataset = self.rag.create_dataset(name=name)
        return dataset.id

    def delete(self, dataset_id: str):
        self.rag.delete_datasets(ids=[dataset_id])

    def list(self):
        return self.rag.list_datasets()


class DocumentService:
    """
    仅负责 RAGFlow 文档（Document）相关操作
    """

    def __init__(self):
        self.rag = RAGFlow(
            api_key="ragflow-LRCQcaNm8v4n5ea0Qo7ui35or2Hk6TBz4_PJSPbUH7o",
            # base_url="http://localhost:9380",
            base_url="http://host.docker.internal:9380"
        )

    # -------------------------
    # 内部工具
    # -------------------------

    def _get_dataset(self, dataset_id: str):
        datasets = self.rag.list_datasets(id=dataset_id)
        if not datasets:
            raise ValueError(f"Dataset not found: {dataset_id}")
        return datasets[0]

    # -------------------------
    # Document APIs
    # -------------------------

    def upload(
        self,
        dataset_id: str,
        file_path: str,
        display_name: str | None = None,
    ):
        """
        上传单个文件到指定 dataset

        返回：None（RAGFlow SDK 设计如此）
        """
        dataset = self._get_dataset(dataset_id)

        with open(file_path, "rb") as f:
            blob = f.read()

        dataset.upload_documents([
            {
                "display_name": display_name or file_path.split("/")[-1],
                "blob": blob,
            }
        ])

    def list(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 30,
    ):
        """
        列出 dataset 下的文档
        """
        dataset = self._get_dataset(dataset_id)
        return dataset.list_documents(
            page=page,
            page_size=page_size,
        )

    def delete(
        self,
        dataset_id: str,
        document_ids: List[str],
    ):
        """
        删除指定文档
        """
        dataset = self._get_dataset(dataset_id)
        dataset.delete_documents(ids=document_ids)

    def parse(
        self,
        dataset_id: str,
        document_ids: List[str],
    ):
        """
        触发文档解析（同步，返回状态）
        """
        dataset = self._get_dataset(dataset_id)
        return dataset.parse_documents(document_ids)
    

def main():
    kb = KnowledgeBaseService()

    # print("▶ Listing datasets (before create)...")
    datasets = kb.list()
    for d in datasets:
        print(f"- {d.id} | {d.name}")

    # print("\n▶ Creating knowledge base...")
    # kb_id = kb.create(name="sdk-test-kb")
    # print("Created KB ID:", kb_id)

    # print("\n▶ Listing datasets (after create)...")
    # datasets = kb.list()
    # for d in datasets:
    #     print(f"- {d.id} | {d.name}")
    kb_id = "7321709ee71411f080a96edd818c37a6"
    # print("\n▶ Deleting knowledge base...")
    # kb.delete(kb_id)
    # print("Deleted KB ID:", kb_id)

    # print("\n▶ Listing datasets (after delete)...")
    # datasets = kb.list()
    # for d in datasets:
    #     print(f"- {d.id} | {d.name}")

    # print("\n✅ Test finished successfully")




    # # ========= 需要你确认/修改的参数 =========
    DATASET_ID = kb_id
    # TEST_FILE_PATH = r"G:\llm_swift\deepresearch\backend\cache\uploads\user_5\48b53b1ec35c42d39517f19625c3d56c.pdf"
    # import os 
    # # ========= 准备测试文件 =========
    # # os.makedirs("test_data", exist_ok=True)
    # with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
    #     f.write("This is a test document for RAGFlow DocumentService.\n")

    doc_service = DocumentService()

    print("\n▶ Listing documents (before upload)...")
    docs = doc_service.list(dataset_id=DATASET_ID)
    for d in docs:
        print(f"- {d.id} | {d.name}")

    # print("\n▶ Uploading document...")
    # doc_service.upload(
    #     dataset_id=DATASET_ID,
    #     file_path=TEST_FILE_PATH,
    #     display_name="sdk-test-doc.txt",
    # )
    # print("Upload finished.")

    # print("\n▶ Listing documents (after upload)...")
    # docs = doc_service.list(dataset_id=DATASET_ID)
    # uploaded_doc_ids = []
    # for d in docs:
    #     print(f"- {d.id} | {d.name}")
    #     if d.name == "sdk-test-doc.txt":
    #         uploaded_doc_ids.append(d.id)

    # if not uploaded_doc_ids:
    #     raise RuntimeError("Uploaded document not found in list.")
    # uploaded_doc_ids = ['d8260a2ce70011f080a96edd818c37a6']
    # print("\n▶ Parsing document...")
    # result = doc_service.parse(
    #     dataset_id=DATASET_ID,
    #     document_ids=uploaded_doc_ids,
    # )
    # for doc_id, status, chunk_count, token_count in result:
    #     print(
    #         f"Document {doc_id} | status={status} | "
    #         f"chunks={chunk_count} | tokens={token_count}"
    #     )

    # print("\n▶ Deleting document...")
    doc_service.delete(
        dataset_id="7321709ee71411f080a96edd818c37a6",
        document_ids="907ce7b8e72d11f080a96edd818c37a6",
    )
    # print("Delete finished.")

    # print("\n▶ Listing documents (after delete)...")
    # docs = doc_service.list(dataset_id=DATASET_ID)
    # for d in docs:
    #     print(f"- {d.id} | {d.name}")

    # print("\n✅ DocumentService test finished successfully")

if __name__ == "__main__":
    main()