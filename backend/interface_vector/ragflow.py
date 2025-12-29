import requests
from interface_vector.ragflow_adapter import RAGFlowAdapter
from typing import Dict, List

def search_ragflow_nginx(
    *,
    base_url: str = "http://localhost",
    kb_id: str = "0f645ecadccb11f0932f3aa1a0b92c19",
    question: str = "",
    cookie: str = "csrftoken=t8TdUhLr32crb7XVmfMa2olsUOdOmmi5; sessionid=22dzy9wiwt1vgdprixyyrb6ggf7860xh; session=.eJwdyzkSgCAMAMC_pLYIETD4GQZMMtqCVI5_9yi32Avy6NryIbDCssWExVhCFecMU6k-klnYPKOrCSbI1rTvsJ5t6Ku_BVJhQ1Zk-hrHWJjmpZBPHlHgfgAYaxzx.aUtuJw.o9els7G8H1RcwV_JuRQOO7GGUL8; ajs_anonymous_id=f977280f-c6cf-4538-8a2a-ccbf2f87b924; _streamlit_xsrf=2|15c91ec1|afb8310121e9df1dec36d36485ad3644|1766556278",
    authorization: str = "IjUyZWQ4NjBjZTA4MjExZjA4NjZhODIzN2EyNDk0MDBkIg.aUtuJw.1KXHjCgcqKceTctGysoaTdTArM4",
    size: int = 10,
    top_k: int = 1024,
    similarity_threshold: float = 0.2,
    vector_similarity_weight: float = 0.3,
    page: int = 1,
):
    # 清洗 header（防止不可见字符）
    cookie = cookie.strip()
    authorization = authorization.strip().strip('"').strip("'")

    headers = {
        "Cookie": cookie,
        "Authorization": authorization,
        "Content-Type": "application/json",
        "Accept": "application/json",

        # 👇 这两个非常关键（Nginx / CSRF 校验）
        "Origin": base_url,
        "Referer": f"{base_url}/dataset/testing/{kb_id}",
    }

    resp = requests.post(
        f"{base_url}/v1/chunk/retrieval_test",
        headers=headers,
        json={
            "kb_id": kb_id,
            "question": question,
            "page": page,
            "size": size,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "vector_similarity_weight": vector_similarity_weight,
            "use_kg": False,
        },
    )

    # HTTP 层
    resp.raise_for_status()

    data = resp.json()

    # 业务层
    if data.get("code") != 0:
        raise RuntimeError(data.get("message"))

    return data["data"]


def search_list_ragflow(query_hints: List[str], kb_ids: List[str] = ["0f645ecadccb11f0932f3aa1a0b92c19"], size: int = 10):
    """
    批量查询 RAGFlow
    """
    if size == 10 :
        size = int(0.8 * len(query_hints) * len(kb_ids) * 10)
    results = []
    for i in range(len(query_hints)):
        for j in range(len(kb_ids)):
            result = search_ragflow_nginx(
                question=query_hints[i],
                kb_id=kb_ids[j],
            )
            results.append(result)
    adapter = RAGFlowAdapter(
        max_contexts=size,
        # min_similarity=0.85
    )
    adapted = adapter.adapt(results)
    return adapted



if __name__ == "__main__":
    pass
    query_hints = [
        "腕骨骨折 康复效果评估 DASH评分 肌力 活动度",
        "腕骨骨折 康复 评价指标 功能评分"
      ]
    aaa = search_list_ragflow(query_hints)


    #  Mata 信息
    meta = aaa["meta"]
    print("=== Meta Information ===")
    print(meta)
        # print("-" * 20)


    # ragflow_result = search_ragflow_nginx(
    #     base_url="http://localhost",
    #     kb_id="0f645ecadccb11f0932f3aa1a0b92c19",
    #     question="腕骨",

    #     # 👉 从 Network → Headers 复制
    #     # cookie="csrftoken=...; sessionid=...; session=...; token=...",
    #     cookie="csrftoken=t8TdUhLr32crb7XVmfMa2olsUOdOmmi5; sessionid=22dzy9wiwt1vgdprixyyrb6ggf7860xh; session=.eJwdyzEOgCAMAMC_dHagCGr9DGlpG11BJuPfNY433A1ldGvlVNhhrQsF9k2zKKIHYklLdM81bQGFYILizfoB-9WGffpbjohiYqrJ_zZHn5mRg1CsSPC8Kcsd-Q.aUYQFw.8DbMUX-PZtkgdYkfn9WH39NqfqM; token=AHeI6yt+DGO2ppzTrDZ/mSQAgYWLDH5nVBauaMvrDDoPGYyaW8eYhIrk2XgQBMphvkUquBXobQRTEmBNQMNYKUOqrSoJnq/IH8NC7Pk3Ha9elYStI/jd4dx9AQx96KhTnL79OCeVOEbj3Bp405iNmPqTonIhDJuVuDr8xKHkSybSVUZrtoBQWU5n/48goL6kh1iyJTDffS2+sqU/s6rlGzzL+J70neBgfLwHaissmbF6ZYnrOqsz3ENxfXFqx15ni8IcrIDmj348RTs7zlI3K9oS6JBKRGeYbITCEUy/16VV/5MxjqrqPGeWOYOFr+wzBthtE7vn6gsGOpMqMWFTjZQZnXWRZf26BP/vcDR544urKCBV0SKtK/GK3ouUVzECgL23V7xZi1FuTEf3wFz7aeYJB9UfYwvk4P9cCzOAvpNeGILIFDH0CwEMFetyR1evkuCtQ1gnFddU49SFGySMect+hT0dYaQ7xmFiadK76ydY9aSIot1DFIRbcWz81U9g3ZGiZFyz744Ew+AEjcWMvp5dWsHkXhtMuPpi6weVNBDbh7udJtfv",
    #     authorization="IjUyMTE5YjZlZGQ0ZjExZjA5MzJmM2FhMWEwYjkyYzE5Ig.aUYQFw.I3tSZ3Ew92eq8MyBm_ovGf5k83I",
    # )
    # # print(result)
    # # print(len(result["chunks"]))
    # adapter = RAGFlowAdapter(
    #     # max_contexts=10,
    #     # min_similarity=0.85
    # )
    # ragflow_result2 = search_ragflow_nginx(
    #     base_url="http://localhost",
    #     kb_id="0f645ecadccb11f0932f3aa1a0b92c19",
    #     question="骨折",

    #     # 👉 从 Network → Headers 复制
    #     # cookie="csrftoken=...; sessionid=...; session=...; token=...",
    #     cookie="csrftoken=t8TdUhLr32crb7XVmfMa2olsUOdOmmi5; sessionid=22dzy9wiwt1vgdprixyyrb6ggf7860xh; session=.eJwdyzEOgCAMAMC_dHagCGr9DGlpG11BJuPfNY433A1ldGvlVNhhrQsF9k2zKKIHYklLdM81bQGFYILizfoB-9WGffpbjohiYqrJ_zZHn5mRg1CsSPC8Kcsd-Q.aUYQFw.8DbMUX-PZtkgdYkfn9WH39NqfqM; token=AHeI6yt+DGO2ppzTrDZ/mSQAgYWLDH5nVBauaMvrDDoPGYyaW8eYhIrk2XgQBMphvkUquBXobQRTEmBNQMNYKUOqrSoJnq/IH8NC7Pk3Ha9elYStI/jd4dx9AQx96KhTnL79OCeVOEbj3Bp405iNmPqTonIhDJuVuDr8xKHkSybSVUZrtoBQWU5n/48goL6kh1iyJTDffS2+sqU/s6rlGzzL+J70neBgfLwHaissmbF6ZYnrOqsz3ENxfXFqx15ni8IcrIDmj348RTs7zlI3K9oS6JBKRGeYbITCEUy/16VV/5MxjqrqPGeWOYOFr+wzBthtE7vn6gsGOpMqMWFTjZQZnXWRZf26BP/vcDR544urKCBV0SKtK/GK3ouUVzECgL23V7xZi1FuTEf3wFz7aeYJB9UfYwvk4P9cCzOAvpNeGILIFDH0CwEMFetyR1evkuCtQ1gnFddU49SFGySMect+hT0dYaQ7xmFiadK76ydY9aSIot1DFIRbcWz81U9g3ZGiZFyz744Ew+AEjcWMvp5dWsHkXhtMuPpi6weVNBDbh7udJtfv",
    #     authorization="IjUyMTE5YjZlZGQ0ZjExZjA5MzJmM2FhMWEwYjkyYzE5Ig.aUYQFw.I3tSZ3Ew92eq8MyBm_ovGf5k83I",
    # )
    # # print(result)
    # # print(len(result["chunks"]))
    # adapter = RAGFlowAdapter(
    #     # max_contexts=10,
    #     # min_similarity=0.85
    # )
    # ragflow_result3 = search_ragflow_nginx(
    #     base_url="http://localhost",
    #     kb_id="0f645ecadccb11f0932f3aa1a0b92c19",
    #     question="治疗",

    #     # 👉 从 Network → Headers 复制
    #     # cookie="csrftoken=...; sessionid=...; session=...; token=...",
    #     cookie="csrftoken=t8TdUhLr32crb7XVmfMa2olsUOdOmmi5; sessionid=22dzy9wiwt1vgdprixyyrb6ggf7860xh; session=.eJwdyzEOgCAMAMC_dHagCGr9DGlpG11BJuPfNY433A1ldGvlVNhhrQsF9k2zKKIHYklLdM81bQGFYILizfoB-9WGffpbjohiYqrJ_zZHn5mRg1CsSPC8Kcsd-Q.aUYQFw.8DbMUX-PZtkgdYkfn9WH39NqfqM; token=AHeI6yt+DGO2ppzTrDZ/mSQAgYWLDH5nVBauaMvrDDoPGYyaW8eYhIrk2XgQBMphvkUquBXobQRTEmBNQMNYKUOqrSoJnq/IH8NC7Pk3Ha9elYStI/jd4dx9AQx96KhTnL79OCeVOEbj3Bp405iNmPqTonIhDJuVuDr8xKHkSybSVUZrtoBQWU5n/48goL6kh1iyJTDffS2+sqU/s6rlGzzL+J70neBgfLwHaissmbF6ZYnrOqsz3ENxfXFqx15ni8IcrIDmj348RTs7zlI3K9oS6JBKRGeYbITCEUy/16VV/5MxjqrqPGeWOYOFr+wzBthtE7vn6gsGOpMqMWFTjZQZnXWRZf26BP/vcDR544urKCBV0SKtK/GK3ouUVzECgL23V7xZi1FuTEf3wFz7aeYJB9UfYwvk4P9cCzOAvpNeGILIFDH0CwEMFetyR1evkuCtQ1gnFddU49SFGySMect+hT0dYaQ7xmFiadK76ydY9aSIot1DFIRbcWz81U9g3ZGiZFyz744Ew+AEjcWMvp5dWsHkXhtMuPpi6weVNBDbh7udJtfv",
    #     authorization="IjUyMTE5YjZlZGQ0ZjExZjA5MzJmM2FhMWEwYjkyYzE5Ig.aUYQFw.I3tSZ3Ew92eq8MyBm_ovGf5k83I",
    # )
    # # print(result)
    # # print(len(result["chunks"]))
    # adapter = RAGFlowAdapter(
    #     max_contexts=10,
    #     # min_similarity=0.85
    # )

    # adapted = adapter.adapt([ragflow_result, ragflow_result2, ragflow_result3])

    # # 给大模型
    # llm_context = "\n\n".join(
    #     f"[来源: {c['source']}]\n{c['text']}"
    #     for c in adapted["contexts"]
    # )
    # print("=== LLM Context ===")
    # print(llm_context)


    # # # 给用户
    # # user_evidences = adapted["evidences"]
    # # print("=== User Evidences ===")
    # # for i in user_evidences:
    # #     for j in i.items():
    # #         print(j)
    # #     print("-" * 20)


    # #  Mata 信息
    # meta = adapted["meta"]
    # print("=== Meta Information ===")
    # print(meta)
    #     # print("-" * 20)