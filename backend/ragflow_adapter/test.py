"""
最小 RAGFlow SDK 测试文件

验证：
1. 能否创建知识库
2. 能否上传文件
3. 能否删除文档 & 知识库
"""

import os
from knowledge_base import KnowledgeBaseAdapter
from document import DocumentAdapter


TEST_FILE = "test_upload.txt"


def prepare_test_file():
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write("This is a test file for RAGFlow upload.")


def main():
    prepare_test_file()

    kb = KnowledgeBaseAdapter()
    doc = DocumentAdapter()

    print("▶ Creating knowledge base...")
    kb_id = kb.create(
        name="ragflow-test-kb",
        description="test kb from sdk",
    )
    print("✓ KB ID:", kb_id)

    print("▶ Uploading document...")
    doc_id = doc.upload(
        knowledge_base_id=kb_id,
        file_path=TEST_FILE,
        filename="test_upload.txt",
    )
    print("✓ Document ID:", doc_id)

    print("▶ Fetching document status...")
    info = doc.get(
        knowledge_base_id=kb_id,
        document_id=doc_id,
    )
    print("✓ Document info:", info)

    print("▶ Deleting document...")
    doc.delete(
        knowledge_base_id=kb_id,
        document_id=doc_id,
    )
    print("✓ Document deleted")

    print("▶ Deleting knowledge base...")
    kb.delete(
        knowledge_base_id=kb_id,
    )
    print("✓ Knowledge base deleted")

    os.remove(TEST_FILE)
    print("🎉 All tests passed")


if __name__ == "__main__":
    main()
