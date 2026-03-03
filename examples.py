from __future__ import annotations

from typing import Any, Dict

from skill_exec import (
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


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(SumSkill())
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

    result = executor.execute("sum", {"a": 1, "b": 2})
    print("success =", result.success)
    print("data    =", result.data)
    print("error   =", result.error)


if __name__ == "__main__":
    main()

