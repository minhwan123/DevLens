from devlens.config.career_radar_thresholds import (
    DEFAULT_CAREER_RADAR_NORMALIZATION,
    CareerRadarNormalization,
)
from devlens.domain.models.career_radar_profile import CareerRadarProfile
from devlens.domain.models.common import ProficiencyLevel
from devlens.domain.models.developer_profile import DeveloperProfile
from devlens.domain.models.repository_evidence import RepositoryEvidence
from devlens.domain.models.skill_evidence import SkillEvidence
from devlens.domain.policies.scoring_utils import clamped_ratio

_PROFICIENCY_WEIGHTS: dict[ProficiencyLevel, int] = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
}
_MAX_PROFICIENCY_WEIGHT = max(_PROFICIENCY_WEIGHTS.values())


class CareerIntelligenceEngine:
    """Scores a DeveloperProfile across 6 independent radar axes.

    Deliberately produces no single aggregate score (see CareerRadarProfile). Each axis is
    normalized to 0..100 against a configurable target, purely from DeveloperProfile data —
    no external calls.
    """

    def __init__(
        self, normalization: CareerRadarNormalization = DEFAULT_CAREER_RADAR_NORMALIZATION
    ) -> None:
        self._normalization = normalization

    def analyze(self, profile: DeveloperProfile) -> CareerRadarProfile:
        evidences = profile.repository_evidences
        return CareerRadarProfile(
            programming=self._programming_score(profile.skills),
            project_experience=self._project_experience_score(evidences),
            software_engineering=self._software_engineering_score(evidences),
            deployment_devops=self._deployment_devops_score(evidences),
            documentation=self._documentation_score(evidences),
            activity=self._activity_score(evidences),
        )

    def _programming_score(self, skills: list[SkillEvidence]) -> float:
        weighted = sum(_PROFICIENCY_WEIGHTS[skill.proficiency] for skill in skills)
        max_possible = self._normalization.programming_skill_count_target * _MAX_PROFICIENCY_WEIGHT
        return clamped_ratio(weighted, max_possible) * 100

    def _project_experience_score(self, evidences: list[RepositoryEvidence]) -> float:
        if not evidences:
            return 0.0
        breadth = clamped_ratio(
            len(evidences), self._normalization.project_experience_repo_count_target
        )
        avg_quality = sum(evidence.quality_score for evidence in evidences) / len(evidences)
        return (0.5 * breadth + 0.5 * avg_quality) * 100

    def _software_engineering_score(self, evidences: list[RepositoryEvidence]) -> float:
        if not evidences:
            return 0.0
        tests_ratio = sum(1 for evidence in evidences if evidence.has_tests) / len(evidences)
        ci_ratio = sum(1 for evidence in evidences if evidence.has_ci) / len(evidences)
        return (0.5 * tests_ratio + 0.5 * ci_ratio) * 100

    def _deployment_devops_score(self, evidences: list[RepositoryEvidence]) -> float:
        if not evidences:
            return 0.0
        docker_ratio = sum(1 for evidence in evidences if evidence.has_docker) / len(evidences)
        devops_ratio = sum(
            1 for evidence in evidences if "devops" in evidence.domain_tags
        ) / len(evidences)
        return (0.5 * docker_ratio + 0.5 * devops_ratio) * 100

    def _documentation_score(self, evidences: list[RepositoryEvidence]) -> float:
        if not evidences:
            return 0.0
        avg_readme_quality = sum(evidence.readme_quality_score for evidence in evidences) / len(
            evidences
        )
        return avg_readme_quality * 100

    def _activity_score(self, evidences: list[RepositoryEvidence]) -> float:
        if not evidences:
            return 0.0
        avg_commit_frequency = sum(evidence.commit_frequency for evidence in evidences) / len(
            evidences
        )
        target = self._normalization.activity_commit_frequency_target
        return clamped_ratio(avg_commit_frequency, target) * 100
