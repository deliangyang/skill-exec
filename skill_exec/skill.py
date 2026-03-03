from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SkillRequest:
    """
    表示一次 skill 调用的输入。

    - payload: 业务输入数据
    - metadata: 额外上下文信息（trace_id、用户信息等）
    """

    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """
    表示一次 skill 调用的输出结果。

    - success: 是否成功
    - data: 成功时返回的数据
    - error: 失败时的错误描述
    """

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class Skill(ABC):
    """
    skill 抽象基类。

    每个具体的 skill 只需要实现 execute 方法。
    """

    name: str
    description: str

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, request: SkillRequest) -> SkillResult:
        """
        执行 skill 的核心逻辑。
        """

    def __repr__(self) -> str:
        return f"<Skill name={self.name!r}>"

