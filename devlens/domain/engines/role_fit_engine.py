from devlens.config.role_requirements import DEFAULT_ROLE_REQUIRED_SKILLS
from devlens.domain.models.developer_profile import DeveloperProfile
from devlens.domain.models.role_fit import RoleFit
from devlens.domain.policies.skill_gap_policy import SkillGapPolicy


class RoleFitEngine:
    """Reverses SkillGapPolicy's usual question ("what's missing for role X") into "which
    role does this profile already fit best" — scores every known role and ranks them, for
    a "roles that suit you" insight instead of requiring the user to pick a target role first.
    """

    def __init__(
        self,
        role_required_skills: dict[str, list[str]] = DEFAULT_ROLE_REQUIRED_SKILLS,
        skill_gap_policy: SkillGapPolicy | None = None,
        top_n: int = 3,
    ) -> None:
        self._role_required_skills = role_required_skills
        self._skill_gap_policy = skill_gap_policy or SkillGapPolicy(role_required_skills)
        self._top_n = top_n

    def rank_roles(self, profile: DeveloperProfile) -> list[RoleFit]:
        fits = [self._fit_for(profile, role) for role in self._role_required_skills]
        fits.sort(key=lambda fit: fit.fit_score, reverse=True)
        return fits[: self._top_n]

    def _fit_for(self, profile: DeveloperProfile, role: str) -> RoleFit:
        required = self._role_required_skills.get(role, [])
        missing = self._skill_gap_policy.gap_skills(profile, role)
        matched = sorted(skill for skill in required if skill not in missing)
        fit_score = len(matched) / len(required) if required else 0.0
        return RoleFit(
            role=role,
            fit_score=fit_score,
            matched_skills=matched,
            missing_skills=sorted(missing),
        )
