from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from .executor import SkillExecutor
from .registry import SkillRegistry
from .skill import Skill, SkillRequest, SkillResult


@dataclass
class WorkflowStepResult:
    name: str
    success: bool
    code: str
    data: Any
    error: Optional[str]


class SequentialWorkflowSkill(Skill):
    """
    一个简单的顺序工作流 skill。

    - steps: 由多个 skill 名称组成，按顺序依次执行
    - 输入：使用请求的 payload 作为初始上下文
    - 输出：
      - 成功：返回最终的上下文（中间 step 的字典结果会 merge 进上下文）和每个 step 的执行结果
      - 失败：在某个 step 失败时立即中断，返回失败 step 及之前所有 step 的结果
    """

    def __init__(
        self,
        name: str,
        steps: List[str],
        registry: SkillRegistry,
        description: str = "",
    ) -> None:
        super().__init__(
            name=name,
            description=description or f"顺序工作流: {' -> '.join(steps)}",
        )
        self._steps = steps
        self._registry = registry

    def execute(self, request: SkillRequest) -> SkillResult:
        executor = SkillExecutor(self._registry)

        current_payload: Dict[str, Any] = dict(request.payload)
        step_results: List[WorkflowStepResult] = []

        for step_name in self._steps:
            result = executor.execute(step_name, current_payload, request.metadata)

            step_results.append(
                WorkflowStepResult(
                    name=step_name,
                    success=result.success,
                    code=result.code,
                    data=result.data,
                    error=result.error,
                )
            )

            if not result.success:
                return SkillResult(
                    success=False,
                    data={
                        "failed_step": step_name,
                        "steps": [asdict(r) for r in step_results],
                    },
                    error=f"workflow step {step_name!r} failed",
                    code=result.code,
                )

            # 若某个 step 返回 dict，则 merge 回当前上下文，供后续 step 使用
            if isinstance(result.data, dict):
                current_payload.update(result.data)

        return SkillResult(
            success=True,
            data={
                "final_payload": current_payload,
                "steps": [asdict(r) for r in step_results],
            },
            error=None,
            code="OK",
        )

