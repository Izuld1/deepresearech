import json
import pickle
from pathlib import Path





def load_result(cache_path: str):
    """
    反序列化加载执行结果
    """
    with open(cache_path, "rb") as f:
        return pickle.load(f)
    


def save_result(obj, cache_path: str):
    """
    将任意 Python 对象序列化保存
    """
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

def pretty(obj):
    """
    将 Python 对象以“美化后的 JSON 形式”打印到标准输出。

    功能说明：
    - 使用 json.dumps 将对象序列化为 JSON 字符串
    - 设置缩进（indent=2），使结构层级清晰、便于阅读
    - 关闭 ASCII 转义（ensure_ascii=False），以正确显示中文等非 ASCII 字符
    - 仅用于调试或日志查看，不返回任何值

    适用对象：
    - dict、list 等可被 JSON 序列化的 Python 对象

    注意事项：
    - 若对象中包含不可 JSON 序列化的类型（如自定义类、datetime 等），将抛出异常
    - 该函数只负责打印，不适合用于数据持久化或程序逻辑处理
    """
    print(json.dumps(obj, ensure_ascii=False, indent=2))