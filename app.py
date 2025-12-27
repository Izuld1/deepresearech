# app.py
import streamlit as st
from tests.test_research_bootstrap_flow import main_run as run_deepresearch

st.set_page_config(page_title="DeepResearch", layout="wide")

st.title("🧠 DeepResearch Assistant")

# 聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 输入框
user_input = st.chat_input("请输入你的研究问题")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = run_deepresearch(user_input)

        st.write(result["final_answer"])

        # 🔍 可选：展开查看中间过程
        with st.expander("🔍 查看研究过程"):
            st.json(result)

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["final_answer"]
    })
