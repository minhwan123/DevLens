from typing import Literal, Protocol, runtime_checkable

ProficiencyLevel = Literal["beginner", "intermediate", "advanced"]


@runtime_checkable
class Taggable(Protocol):
    """Anything scoreable by SkillGapPolicy/CareerGoalRelevancePolicy, which only ever read
    `.tags` — any type exposing a `tags` list satisfies this structurally."""

    @property
    def tags(self) -> list[str]: ...
