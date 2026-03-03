"""
skill-exec 核心包。

对外暴露 Skill、SkillRequest、SkillResult、SkillRegistry、SkillExecutor 等接口。
"""

from .skill import (
    Skill,
    SkillError,
    SkillExecutionError,
    SkillRequest,
    SkillResult,
    SkillValidationError,
)
from .registry import SkillRegistry
from .executor import SkillExecutor, execute_skill
from .workflow import SequentialWorkflowSkill

__all__ = [
    "Skill",
    "SkillError",
    "SkillValidationError",
    "SkillExecutionError",
    "SkillRequest",
    "SkillResult",
    "SkillRegistry",
    "SkillExecutor",
    "SequentialWorkflowSkill",
    "execute_skill",
]

