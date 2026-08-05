from devlens.config.role_requirements import DEFAULT_ROLE_REQUIRED_SKILLS
from devlens.domain.models.common import Taggable


class CareerGoalRelevancePolicy:
    """Rule-based tag match between a catalog item and a target role, independent of profile.

    Fraction of the item's own tags that also appear in the target role's tag set.
    """

    def __init__(
        self, role_required_skills: dict[str, list[str]] = DEFAULT_ROLE_REQUIRED_SKILLS
    ) -> None:
        self._role_required_skills = role_required_skills

    def evaluate(self, item: Taggable, target_role: str) -> float:
        if not item.tags:
            return 0.0
        role_tags = set(self._role_required_skills.get(target_role, []))
        overlap = set(item.tags) & role_tags
        return len(overlap) / len(item.tags)
