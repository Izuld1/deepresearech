"""
RAGFlow REST Client
------------------
只负责和 RAGFlow 通信，不知道什么是 sub_goal / evidence
"""

import requests
from typing import List, Dict, Any


class RAGFlowClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def search(
        self,
        dataset_id: str,
        query: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "dataset_id": dataset_id,
            "query": query,
            "top_k": top_k,
            "search_type": "vector",
            "rerank": True,
        }

        resp = requests.post(
            f"{self.base_url}/api/v1/search",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()

        return resp.json().get("data", [])
