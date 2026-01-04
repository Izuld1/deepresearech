from ragflow_sdk import RAGFlow
from typing import List
def ceshi() :
    rag_object = RAGFlow(
        api_key="ragflow-LRCQcaNm8v4n5ea0Qo7ui35or2Hk6TBz4_PJSPbUH7o",
        # base_url="http://host.docker.internal:9380"
        base_url="http://localhost:9380"
    )

    # dataset = rag_object.create_dataset(name="kb_1")