# step1_test.py

from core.llm_gateway import build_qwen_gateway_from_env
from steps.step1_clarify import ClarificationState, clarification_step

def main():
    gateway = build_qwen_gateway_from_env()
    state = ClarificationState()

    print("=== Step 1: Research Clarification ===")

    while True:
        user_input = input("\nUser > ").strip()
        if not user_input:
            continue

        result = clarification_step(gateway, state, user_input)

        print("\nSystem >")
        print(result)

        status = result["status"]

        if status == "need_clarification":
            print("\n[Need clarification, please answer the questions above]")
            continue

        if status == "completed":
            print("\n[Clarification completed]")
            print("\nFinal requirements:")
            print(result["requirements"])
            break

        if status == "failed":
            print("\n[Clarification failed]")
            print(result)
            break


if __name__ == "__main__":
    main()
