from __future__ import annotations

from typing import Dict, Iterable, Optional

from .skill import Skill


class SkillRegistry:
    """
    skill 注册表，用于集中管理可用的 skill。
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill, overwrite: bool = False) -> None:
        """
        注册一个新的 skill。

        - overwrite=False 时，如果 name 已存在会抛出异常。
        """
        name = skill.name
        if not overwrite and name in self._skills:
            raise ValueError(f"skill {name!r} 已存在，请避免重复注册或显式设置 overwrite=True")
        self._skills[name] = skill

    def get(self, name: str) -> Optional[Skill]:
        """
        根据名称获取 skill，找不到返回 None。
        """
        return self._skills.get(name)

    def require(self, name: str) -> Skill:
        """
        根据名称获取 skill，找不到时抛异常。
        """
        skill = self.get(name)
        if skill is None:
            raise KeyError(f"未找到名为 {name!r} 的 skill")
        return skill

    def all(self) -> Iterable[Skill]:
        """
        返回所有已注册的 skill 实例。
        """
        return self._skills.values()

