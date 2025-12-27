# tests/test_step1_to_step2.py

from core.llm_gateway import build_qwen_gateway_from_env
from steps.step1_clarify import ClarificationState, clarification_step
from steps.step2_plan import generate_research_plan


def test_step1_to_step2_pipeline():
    gateway = build_qwen_gateway_from_env()
    state = ClarificationState()

    # ---- Step 1：澄清 ----
    clarification_step(gateway, state, "我想做一篇腕骨骨折的研究综述")
    clarification_step(gateway, state, "重点对比手术治疗方式")
    result = clarification_step(
        gateway,
        state,
        "只看近五年文献，只使用我上传的资料"
    )

    assert result["status"] == "completed"
    requirements = result["requirements"]

    # ---- Step 2：生成 Research Plan ----
    plan = generate_research_plan(gateway, requirements)

    # ===== 结构断言 =====
    assert plan["plan_level"] == "coarse"
    assert plan["hypothesis"] is True
    assert 3 <= len(plan["sections"]) <= 6

    # ===== 章节检查 =====
    for sec in plan["sections"]:
        assert sec["section_id"].startswith("S")
        assert sec["title"]
        assert sec["intent_hint"]
        assert sec["status"] == "active"

    # ===== 边界继承检查 =====
    assert plan["source_requirements_snapshot"]["literature_scope"]["only_uploaded"] is True
