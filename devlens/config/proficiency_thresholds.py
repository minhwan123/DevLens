from dataclasses import dataclass


@dataclass(frozen=True)
class ProficiencyThresholds:
    """Minimum admitted-repository count required to reach each ProficiencyLevel."""

    intermediate_min_repos: int = 2
    advanced_min_repos: int = 4


DEFAULT_PROFICIENCY_THRESHOLDS = ProficiencyThresholds()
