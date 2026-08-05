from dataclasses import dataclass


@dataclass(frozen=True)
class CareerRadarNormalization:
    """Signal values at which each CareerIntelligenceEngine radar axis saturates to 100."""

    programming_skill_count_target: int = 10
    project_experience_repo_count_target: int = 6
    activity_commit_frequency_target: float = 5.0


DEFAULT_CAREER_RADAR_NORMALIZATION = CareerRadarNormalization()


@dataclass(frozen=True)
class ImprovementSuggestionThresholds:
    """Signal values below which ImprovementSuggestionEngine flags a repository for an axis."""

    readme_quality_score_threshold: float = 0.5
    commit_frequency_threshold: float = 2.0


DEFAULT_IMPROVEMENT_SUGGESTION_THRESHOLDS = ImprovementSuggestionThresholds()
