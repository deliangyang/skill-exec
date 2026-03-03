from __future__ import annotations

import asyncio
from typing import Any, Dict

from skill_exec import (
    SequentialWorkflowSkill,
    Skill,
    SkillExecutor,
    SkillRegistry,
    SkillRequest,
    SkillResult,
    SkillValidationError,
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
        except (TypeError, ValueError) as exc:
            # 抛出校验异常，由执行器统一转换为 SkillResult
            raise SkillValidationError("参数 a / b 应该是数字或可转换为数字的字符串") from exc

        return SkillResult(success=True, data={"result": a + b})


class WaitSkill(Skill):
    """
    一个异步示例 skill：等待一段时间再返回。

    payload 结构示例：
    {
        "delay": 0.5,
    }
    """

    def __init__(self) -> None:
        super().__init__(name="wait", description="异步等待一段时间")

    async def execute(self, request: SkillRequest) -> SkillResult:
        payload: Dict[str, Any] = request.payload
        delay = float(payload.get("delay", 0.5))
        await asyncio.sleep(delay)
        return SkillResult(success=True, data={"slept": delay})


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(SumSkill())
    registry.register(WaitSkill())
    # 一个简单的工作流：先 sum 再 wait
    registry.register(
        SequentialWorkflowSkill(
            name="sum_then_wait",
            steps=["sum", "wait"],
            registry=registry,
            description="先对 a + b 求和，再等待一段时间",
        )
    )
    return registry


def main() -> None:
    registry = build_default_registry()
    # 简单日志中间件示例
    def log_pre(name: str, request: SkillRequest) -> None:
        print(f"[pre]  即将执行 skill={name}, payload={request.payload}, metadata={request.metadata}")

    def log_post(name: str, request: SkillRequest, result: SkillResult) -> None:
        print(f"[post] 已执行 skill={name}, success={result.success}, data={result.data}, error={result.error}")

    def log_exception(name: str, request: SkillRequest, exc: BaseException) -> None:
        print(f"[error] 执行 skill={name} 时抛出异常: {exc!r}")

    executor = SkillExecutor(
        registry,
        pre_hooks=[log_pre],
        post_hooks=[log_post],
        exception_hooks=[log_exception],
    )

    print("=== 执行 sum ===")
    result = executor.execute("sum", {"a": 1, "b": 2})
    print("success =", result.success)
    print("code    =", result.code)
    print("data    =", result.data)
    print("error   =", result.error)

    print("\n=== 执行异步 wait ===")
    result2 = executor.execute("wait", {"delay": 0.1})
    print("success =", result2.success)
    print("code    =", result2.code)
    print("data    =", result2.data)
    print("error   =", result2.error)

    print("\n=== 执行工作流 sum_then_wait ===")
    result3 = executor.execute("sum_then_wait", {"a": 1, "b": 2, "delay": 0.1})
    print("success =", result3.success)
    print("code    =", result3.code)
    print("data    =", result3.data)
    print("error   =", result3.error)


if __name__ == "__main__":
    main()

