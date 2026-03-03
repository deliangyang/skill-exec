from __future__ import annotations

"""
orchestrator 示例：

演示一个极简的任务编排器如何基于 skill-exec 的 SkillExecutor
来按「节点定义 + 上下文」驱动工作流。
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from examples import build_default_registry
from skill_exec import SkillExecutor, SkillRegistry, SkillResult


InputMapper = Callable[[Dict[str, Any]], Dict[str, Any]]
OutputMapper = Callable[[Dict[str, Any], SkillResult], None]


@dataclass
class NodeDef:
    """
    一个简单的节点定义：
    - name: 节点名称（在编排器内部唯一）
    - skill_name: 要调用的 skill 名称
    - input_mapper: 把全局上下文映射为当前 skill 所需的 payload
    - output_mapper: 把当前 skill 的结果合并回全局上下文
    - next_on_success / next_on_failure: 成功或失败时跳转到的下一个节点名称（None 表示结束）
    """

    name: str
    skill_name: str
    input_mapper: InputMapper
    output_mapper: OutputMapper
    next_on_success: Optional[str] = None
    next_on_failure: Optional[str] = None


class SimpleOrchestrator:
    """
    非持久化的极简编排器，仅用于演示：
    - 内存中存一份 NodeDef 的字典
    - run 时从起始节点开始，按 next_on_success / next_on_failure 串行执行
    """

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._executor = SkillExecutor(registry)
        self._nodes: Dict[str, NodeDef] = {}

    def add_node(self, node: NodeDef) -> None:
        self._nodes[node.name] = node

    def run(self, start: str, context: Dict[str, Any]) -> Dict[str, Any]:
        current = start

        while current is not None:
            node = self._nodes[current]
            payload = node.input_mapper(context)
            print(f"[orchestrator] 运行节点 {current}, skill={node.skill_name}, payload={payload}")

            result = self._executor.execute(
                name=node.skill_name,
                payload=payload,
                metadata={"node": current},
            )
            print(
                f"[orchestrator] 节点 {current} 结果: success={result.success}, "
                f"code={result.code}, error={result.error}"
            )

            node.output_mapper(context, result)

            if result.success:
                current = node.next_on_success
            else:
                current = node.next_on_failure

        return context


def build_sample_orchestrator() -> SimpleOrchestrator:
    """
    构建一个简单的两节点工作流：
    - sum_node: 调用 sum skill，对 a + b 求和
    - wait_node: 调用 wait skill，等待一小段时间
    """
    registry = build_default_registry()
    orch = SimpleOrchestrator(registry)

    def sum_input_mapper(ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"a": ctx.get("a", 1), "b": ctx.get("b", 2)}

    def sum_output_mapper(ctx: Dict[str, Any], result: SkillResult) -> None:
        if result.success and isinstance(result.data, dict):
            ctx["sum_result"] = result.data.get("result")

    def wait_input_mapper(ctx: Dict[str, Any]) -> Dict[str, Any]:
        # 这里只是示例，简单地根据 sum_result 决定一个延时
        base_delay = 0.1
        sum_result = float(ctx.get("sum_result", 0.0))
        delay = base_delay + 0.0 * sum_result  # 预留钩子，真实场景可以做更复杂映射
        return {"delay": delay}

    def wait_output_mapper(ctx: Dict[str, Any], result: SkillResult) -> None:
        if result.success and isinstance(result.data, dict):
            ctx["slept"] = result.data.get("slept")

    orch.add_node(
        NodeDef(
            name="sum_node",
            skill_name="sum",
            input_mapper=sum_input_mapper,
            output_mapper=sum_output_mapper,
            next_on_success="wait_node",
            next_on_failure=None,
        )
    )

    orch.add_node(
        NodeDef(
            name="wait_node",
            skill_name="wait",
            input_mapper=wait_input_mapper,
            output_mapper=wait_output_mapper,
            next_on_success=None,
            next_on_failure=None,
        )
    )

    return orch


def main() -> None:
    orch = build_sample_orchestrator()
    context: Dict[str, Any] = {"a": 3, "b": 4}
    print("初始上下文:", context)
    final_ctx = orch.run(start="sum_node", context=context)
    print("[orchestrator] 最终上下文:", final_ctx)


if __name__ == "__main__":
    main()

