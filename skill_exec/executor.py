from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

from .registry import SkillRegistry
from .skill import SkillRequest, SkillResult


class SkillExecutor:
    """
    skill 执行器。

    负责：
    - 根据名称从注册表中找到 skill
    - 封装输入为 SkillRequest
    - 捕获异常并统一转换为 SkillResult
    """

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        name: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SkillResult:
        skill = self._registry.require(name)
        request = SkillRequest(payload=payload, metadata=metadata or {})

        try:
            result = skill.execute(request)
        except Exception as exc:  # noqa: BLE001
            # 这里统一兜底异常，避免异常向上冒泡
            tb = traceback.format_exc()
            return SkillResult(
                success=False,
                data=None,
                error=f"{exc!r}\n{tb}",
            )

        # 如果 skill 自己没有返回 SkillResult，则做一次兜底封装
        if not isinstance(result, SkillResult):
            return SkillResult(success=True, data=result, error=None)

        return result


def execute_skill(
    registry: SkillRegistry,
    name: str,
    payload: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> SkillResult:
    """
    便捷函数：单次执行某个 skill。
    """
    executor = SkillExecutor(registry)
    return executor.execute(name=name, payload=payload, metadata=metadata)

