from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryFilterWeights:
    """Relative importance of each signal in the repository quality score. Should sum to ~1.0."""

    commit_count: float = 0.25
    contributor_count: float = 0.15
    recency: float = 0.20
    readme_quality: float = 0.15
    code_volume: float = 0.15
    file_diversity: float = 0.10


@dataclass(frozen=True)
class RepositoryFilterNormalization:
    """Signal values at (or beyond) which a sub-score saturates to its maximum."""

    commit_count_target: int = 50
    contributor_count_target: int = 3
    recency_full_score_days: int = 30
    recency_zero_score_days: int = 365
    readme_length_target: int = 500
    code_line_count_target: int = 500
    file_extension_count_target: int = 5


DEFAULT_FILTER_WEIGHTS = RepositoryFilterWeights()
DEFAULT_FILTER_NORMALIZATION = RepositoryFilterNormalization()
DEFAULT_FILTER_THRESHOLD = 0.5
