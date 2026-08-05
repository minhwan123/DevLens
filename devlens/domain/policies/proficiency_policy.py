from devlens.config.proficiency_thresholds import (
    DEFAULT_PROFICIENCY_THRESHOLDS,
    ProficiencyThresholds,
)
from devlens.domain.models.common import ProficiencyLevel


class ProficiencyPolicy:
    """Maps a supporting-repository count to a ProficiencyLevel via two thresholds.

    Reused both per-skill (how many admitted repos use this tech) and profile-wide (how many
    repos were admitted overall, as a proxy for DeveloperProfile.project_level).
    """

    def __init__(self, thresholds: ProficiencyThresholds = DEFAULT_PROFICIENCY_THRESHOLDS) -> None:
        self._thresholds = thresholds

    def evaluate(self, repo_count: int) -> ProficiencyLevel:
        if repo_count >= self._thresholds.advanced_min_repos:
            return "advanced"
        if repo_count >= self._thresholds.intermediate_min_repos:
            return "intermediate"
        return "beginner"
