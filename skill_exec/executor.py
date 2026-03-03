from __future__ import annotations

import traceback
from typing import Any, Dict, Iterable, List, Optional, Protocol, runtime_checkable

from .registry import SkillRegistry
from .skill import (
    SkillError,
    SkillExecutionError,
    SkillRequest,
    SkillResult,
    SkillValidationError,
)


@runtime_checkable
class PreHook(Protocol):
    def __call__(self, name: str, request: SkillRequest) -> None:  # pragma: no cover - 协议接口本身不需要测试
        ...


@runtime_checkable
class PostHook(Protocol):
    def __call__(self, name: str, request: SkillRequest, result: SkillResult) -> None:  # pragma: no cover
        ...


@runtime_checkable
class ExceptionHook(Protocol):
    def __call__(self, name: str, request: SkillRequest, exc: BaseException) -> None:  # pragma: no cover
        ...


class SkillExecutor:
    """
    skill 执行器。

    负责：
    - 根据名称从注册表中找到 skill
    - 封装输入为 SkillRequest
    - 捕获异常并统一转换为 SkillResult
    - 执行可选的前置 / 后置 / 异常钩子（中间件）
    """

    def __init__(
        self,
        registry: SkillRegistry,
        pre_hooks: Optional[Iterable[PreHook]] = None,
        post_hooks: Optional[Iterable[PostHook]] = None,
        exception_hooks: Optional[Iterable[ExceptionHook]] = None,
    ) -> None:
        self._registry = registry
        self._pre_hooks: List[PreHook] = list(pre_hooks or [])
        self._post_hooks: List[PostHook] = list(post_hooks or [])
        self._exception_hooks: List[ExceptionHook] = list(exception_hooks or [])

    @property
    def pre_hooks(self) -> List[PreHook]:
        return self._pre_hooks

    @property
    def post_hooks(self) -> List[PostHook]:
        return self._post_hooks

    @property
    def exception_hooks(self) -> List[ExceptionHook]:
        return self._exception_hooks

    def execute(
        self,
        name: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SkillResult:
        skill = self._registry.require(name)
        request = SkillRequest(payload=payload, metadata=metadata or {})

        for hook in self._pre_hooks:
            hook(name, request)

        try:
            result = skill.execute(request)
        except Exception as exc:  # noqa: BLE001
            for hook in self._exception_hooks:
                hook(name, request, exc)

            # 这里统一兜底异常，避免异常向上冒泡
            if isinstance(exc, SkillValidationError):
                code = "VALIDATION_ERROR"
            elif isinstance(exc, SkillExecutionError):
                code = "EXECUTION_ERROR"
            elif isinstance(exc, SkillError):
                code = "SKILL_ERROR"
            else:
                code = "UNEXPECTED_ERROR"

            tb = traceback.format_exc()
            return SkillResult(
                success=False,
                data=None,
                error=f"{exc!r}\n{tb}",
                code=code,
            )

        # 如果 skill 自己没有返回 SkillResult，则做一次兜底封装
        if not isinstance(result, SkillResult):
            wrapped = SkillResult(success=True, data=result, error=None, code="OK")
        else:
            wrapped = result

        for hook in self._post_hooks:
            hook(name, request, wrapped)

        return wrapped


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

