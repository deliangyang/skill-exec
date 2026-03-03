from __future__ import annotations

"""
llm_agent 示例：

演示如何把 skill-exec 中的 Skill 暴露为「工具」，并由（模拟的）LLM 规划一次调用。

这里没有真实连到线上 LLM，只是用 fake_llm_plan 来模拟「LLM 决策要调用哪个工具以及参数」。
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from examples import build_default_registry
from skill_exec import SkillExecutor, SkillRegistry


@dataclass
class ToolSpec:
    name: str
    description: str


def list_tools_for_llm(registry: SkillRegistry) -> List[ToolSpec]:
    """
    通常这里会把每个 skill 映射为 LLM 的 function/tools。
    为简化，只保留 name 和 description。
    """
    tools: List[ToolSpec] = []
    for s in registry.all():
        tools.append(ToolSpec(name=s.name, description=s.description))
    return tools


def fake_llm_plan(user_input: str, tools: List[ToolSpec]) -> Dict[str, Any]:
    """
    这是一个非常简化的「LLM 规划」示例：
    - 如果用户输入包含「等一等 / 等待 / wait」，就调用 wait skill
    - 否则调用 sum skill
    实际上，这一步通常由大模型通过 function calling / tool calling 完成。
    """
    text = user_input.lower()
    tool_name: str
    args: Dict[str, Any]

    if ("等一等" in user_input) or ("等待" in user_input) or ("wait" in text):
        tool_name = "wait"
        args = {"delay": 0.2}
    else:
        tool_name = "sum"
        args = {"a": 1, "b": 2}

    return {"tool_name": tool_name, "args": args}


def main() -> None:
    registry = build_default_registry()
    executor = SkillExecutor(registry)

    tools = list_tools_for_llm(registry)
    print("可用工具列表（从 SkillRegistry 中导出给 LLM）：")
    for t in tools:
        print(f"- {t.name}: {t.description}")

    # 一次简单的对话轮次示例
    user_input = "帮我对两个数字求和"
    print("\n用户输入:", user_input)

    plan = fake_llm_plan(user_input, tools)
    print("（模拟）LLM 规划结果:", plan)

    result = executor.execute(
        name=plan["tool_name"],
        payload=plan["args"],
        metadata={"from": "llm_agent_demo"},
    )

    print("\n工具执行结果将作为 observation 反馈给 LLM：")
    print(
        {
            "success": result.success,
            "code": result.code,
            "data": result.data,
            "error": result.error,
        }
    )


if __name__ == "__main__":
    main()

