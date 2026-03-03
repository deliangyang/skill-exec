from __future__ import annotations

from typing import Any, Dict

from skill_exec import (
    Skill,
    SkillExecutor,
    SkillRegistry,
    SkillRequest,
    SkillResult,
)


class SumSkill(Skill):
    """
    一个简单示例：对 payload 中的两个数字求和。

    payload 结构示例：
    {
        "a": 1,
        "b": 2,
    }
    """

    def __init__(self) -> None:
        super().__init__(name="sum", description="对两个数字求和")

    def execute(self, request: SkillRequest) -> SkillResult:
        payload: Dict[str, Any] = request.payload
        try:
            a = float(payload.get("a", 0))
            b = float(payload.get("b", 0))
        except (TypeError, ValueError):
            return SkillResult(success=False, error="参数 a / b 应该是数字或可转换为数字的字符串")

        return SkillResult(success=True, data={"result": a + b})


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(SumSkill())
    return registry


def main() -> None:
    registry = build_default_registry()
    executor = SkillExecutor(registry)

    result = executor.execute("sum", {"a": 1, "b": 2})
    print("success =", result.success)
    print("data    =", result.data)
    print("error   =", result.error)


if __name__ == "__main__":
    main()

