from utils.pickle_csp import load_result

    
if __name__ == "__main__":
    result = load_result("cache/step4se_result.pkl")

    print(result.keys())
    print("=============================")
    # dict_keys(['step', 'sub_goal_results'])
    print(result['step'])
    print(len(result['sub_goal_results']))
    print(result['sub_goal_results'][0].keys()) 

    print("=============================")
    # dict_keys(['sub_goal_id', 'parent_section_id', 'intent', 'result'])
    print(result['sub_goal_results'][0]['sub_goal_id'])
    print(result['sub_goal_results'][0]['parent_section_id'])
    print(result['sub_goal_results'][0]['intent'])
    print(result['sub_goal_results'][0]['result'].keys())

    print("=============================")
    # dict_keys(['status', 'pool', 'evaluation', 'trace', 'reason'])
    print(result['sub_goal_results'][0]['result']['status'])
    print(result['sub_goal_results'][0]['result']['trace'])
    print(result['sub_goal_results'][0]['result']['evaluation'])
    # print(result['sub_goal_results'][0]['result']['reason'])
    print(result['sub_goal_results'][0]['result']['pool'].keys())
    # dict_keys(['pool_id', 'sub_goal_id', 'intent', 'contexts', 'evidences', 'meta', 'retrieval_trace'])
    print("=============================")
    print(result['sub_goal_results'][0]['result']['pool']["pool_id"])
    print(result['sub_goal_results'][0]['result']['pool']["sub_goal_id"])
    print(result['sub_goal_results'][0]['result']['pool']["intent"])
    print(result['sub_goal_results'][0]['result']['pool']["retrieval_trace"]["queries"])
    print(len(result['sub_goal_results'][0]['result']['pool']["contexts"]))  # 打印前两个上下文
    print(len(result['sub_goal_results'][0]['result']['pool']["evidences"]))  # 打印前两个证据
    # print(result['sub_goal_results'][0]['result']['pool']["meta"])
    # dict_keys(['pool_id', 'sub_goal_id', 'intent', 'contexts', 'evidences', 'meta', 'retrieval_trace'])


    print("=============================")
    print("=============================")
    print("=============================")
    print(result['sub_goal_results'][0]['result']['pool']["contexts"][0].keys())
    print(result['sub_goal_results'][0]['result']['pool']["evidences"][0].keys())
    print("=============================")
    print(result['sub_goal_results'][0]['result']['pool']["contexts"])
    # for i in result :
    #     print(type(i))
