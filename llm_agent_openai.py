from __future__ import annotations

"""
基于 OpenAI 的 LLM Agent 集成示例。

说明：
- 使用 OpenAI 官方 Python SDK 的 chat completions + tools（function calling）能力；
- 把 SkillRegistry 中的所有 skill 暴露为 LLM 可调用的 tools；
- 当 LLM 请求调用某个 tool 时，转而通过 SkillExecutor 执行对应 skill；
- 再把 SkillResult 作为 tool 调用结果返回给 LLM。

运行前需要：
- 安装依赖： pip install -r requirements.txt
- 设置环境变量： export OPENAI_API_KEY=你的key
"""

import json
from typing import Any, Dict, List

from openai import OpenAI

from examples import build_default_registry
from skill_exec import SkillExecutor, SkillRegistry


def build_tools_schema(registry: SkillRegistry) -> List[Dict[str, Any]]:
    """
    把每个 skill 映射为一个通用的 tool。

    为了简化，我们把所有参数 schema 统一声明为 "任意对象"，真正的约束由具体 skill 自己负责。
    你可以在此基础上扩展为更精细的 JSON Schema。
    """
    tools: List[Dict[str, Any]] = []
    for s in registry.all():
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": s.name,
                    "description": s.description or f"skill {s.name}",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                    },
                },
            }
        )
    return tools


def run_llm_with_tools() -> None:
    registry = build_default_registry()
    executor = SkillExecutor(registry)

    tools = build_tools_schema(registry)

    client = OpenAI()

    # 一轮简单的对话示例：让模型自己决定是否调用工具
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": "你是一个可以调用多个工具的助手。遇到数值计算相关请求时，请优先调用工具而不是自己心算。",
        },
        {
            "role": "user",
            "content": "请帮我算一下 1 加 2 再等一小会儿，然后告诉我你总共等了多久，并给个自然语言解释。",
        },
    ]

    # 第一次请求：模型可能会返回 tool_calls 计划
    first = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    choice = first.choices[0]
    tool_calls = choice.message.tool_calls or []

    if not tool_calls:
        print("模型未调用工具，直接回答：", choice.message.content)
        return

    # 收集所有 tool 调用结果
    tool_results_messages: List[Dict[str, Any]] = []

    for call in tool_calls:
        func = call.function
        tool_name = func.name
        args = json.loads(func.arguments or "{}")

        print(f"[llm_agent_openai] 模型请求调用工具: {tool_name}({args})")

        result = executor.execute(
            name=tool_name,
            payload=args,
            metadata={"from": "openai_llm_agent"},
        )

        tool_results_messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "name": tool_name,
                "content": json.dumps(
                    {
                        "success": result.success,
                        "code": result.code,
                        "data": result.data,
                        "error": result.error,
                    },
                    ensure_ascii=False,
                ),
            }
        )

    # 把工具执行结果作为后续对话输入，让模型进行汇总/解释
    followup_messages = messages + [choice.message.model_dump()] + tool_results_messages

    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=followup_messages,
    )

    print("\n==== 最终回答 ====")
    print(final.choices[0].message.content)


def main() -> None:
    run_llm_with_tools()


if __name__ == "__main__":
    main()

