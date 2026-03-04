from __future__ import annotations

"""
基于 Prefect 的任务编排集成示例。

说明：
- 使用 Prefect 2.x 的 flow / task 能力；
- 把 skill-exec 中的 SkillExecutor 作为 task 内部的执行单元；
- 在 Prefect 的 flow 中以「DAG」形式编排多个 skill。

运行前需要：
- 安装依赖： pip install -r requirements.txt
- （可选）安装并启动 Prefect Orion UI 以可视化运行情况。
"""

from typing import Any, Dict

from prefect import flow, task

from examples import build_default_registry
from skill_exec import SkillExecutor, SkillRegistry, SkillResult


def build_executor() -> SkillExecutor:
    registry: SkillRegistry = build_default_registry()
    return SkillExecutor(registry)


@task
def run_skill(executor: SkillExecutor, name: str, payload: Dict[str, Any]) -> SkillResult:
    """
    一个通用的 Prefect task，用于执行任意 skill。
    """
    result = executor.execute(name=name, payload=payload, metadata={"from": "prefect_flow"})
    print(f"[prefect] run_skill name={name} success={result.success} code={result.code} error={result.error}")
    return result


@flow(name="skill-exec-prefect-flow")
def skill_exec_flow(a: float = 1.0, b: float = 2.0, delay: float = 0.1) -> Dict[str, Any]:
    """
    一个简单的 Prefect flow：
    - 先调用 sum skill 求和；
    - 然后调用 wait skill 等待一段时间；
    - 最后返回汇总结果。
    """
    executor = build_executor()

    sum_result = run_skill(executor, "sum", {"a": a, "b": b})
    wait_result = run_skill(executor, "wait", {"delay": delay})

    return {
        "sum": {
            "success": sum_result.success,
            "code": sum_result.code,
            "data": sum_result.data,
            "error": sum_result.error,
        },
        "wait": {
            "success": wait_result.success,
            "code": wait_result.code,
            "data": wait_result.data,
            "error": wait_result.error,
        },
    }


def main() -> None:
    # 直接本地触发一次 flow 运行，便于快速验证。
    result = skill_exec_flow(a=3, b=4, delay=0.1)
    print("[prefect] flow result:", result)


if __name__ == "__main__":
    main()

