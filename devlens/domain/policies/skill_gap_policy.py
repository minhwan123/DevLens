from devlens.config.role_requirements import DEFAULT_ROLE_REQUIRED_SKILLS
from devlens.domain.models.common import Taggable
from devlens.domain.models.developer_profile import DeveloperProfile


class SkillGapPolicy:
    """How much a catalog item closes the gap between a target role and a developer profile.

    A role's required skill is a "gap" if the profile lacks it entirely or only has it at
    beginner level. The weight is the fraction of the *overall* gap that this item's tags cover,
    so items addressing more (or rarer) missing skills score higher.
    """

    def __init__(
        self, role_required_skills: dict[str, list[str]] = DEFAULT_ROLE_REQUIRED_SKILLS
    ) -> None:
        self._role_required_skills = role_required_skills

    def weight(self, item: Taggable, profile: DeveloperProfile, target_role: str) -> float:
        gap_skills = self.gap_skills(profile, target_role)
        if not gap_skills:
            return 0.0
        covered = set(item.tags) & gap_skills
        return len(covered) / len(gap_skills)

    def gap_skills(self, profile: DeveloperProfile, target_role: str) -> set[str]:
        """Required skills the profile is missing or only has at beginner level.

        Exposed publicly (not just via `weight`) so reporting code (Step 11's AI Career
        Report) can list these as "growth areas" without recomputing the same rule.
        """
        required = self._role_required_skills.get(target_role, [])
        proficiency_by_skill = {skill.skill: skill.proficiency for skill in profile.skills}
        return {
            skill
            for skill in required
            if skill not in proficiency_by_skill or proficiency_by_skill[skill] == "beginner"
        }
