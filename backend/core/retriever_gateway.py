# core/retrieval_gateway.py

from typing import Dict, Any, List, Protocol

class RetrievalGateway(Protocol):
    """
    Step 4 只依赖这个能力接口，不关心实现
    """
    def search(
        self,
        *,
        query_hints: List[str],
        size: int = 10,
    ) -> Dict[str, Any]:
        ...
