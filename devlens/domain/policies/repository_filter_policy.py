from datetime import UTC, datetime

from devlens.config.filter_thresholds import (
    DEFAULT_FILTER_NORMALIZATION,
    DEFAULT_FILTER_THRESHOLD,
    DEFAULT_FILTER_WEIGHTS,
    RepositoryFilterNormalization,
    RepositoryFilterWeights,
)
from devlens.domain.models.repository_candidate import RepositoryCandidate
from devlens.domain.models.repository_filter_result import RepositoryFilterResult
from devlens.domain.policies.readme_scoring import score_readme
from devlens.domain.policies.scoring_utils import clamped_ratio


class RepositoryFilterPolicy:
    """Admits or rejects a repository as portfolio evidence based on a weighted quality score.

    Fork/template repositories are excluded by rule, before any scoring. Everything else is
    scored as a weighted sum of normalized signals and admitted if the score clears `threshold`.
    """

    def __init__(
        self,
        weights: RepositoryFilterWeights = DEFAULT_FILTER_WEIGHTS,
        normalization: RepositoryFilterNormalization = DEFAULT_FILTER_NORMALIZATION,
        threshold: float = DEFAULT_FILTER_THRESHOLD,
    ) -> None:
        self._weights = weights
        self._normalization = normalization
        self._threshold = threshold

    def evaluate(
        self, candidate: RepositoryCandidate, *, now: datetime | None = None
    ) -> RepositoryFilterResult:
        if candidate.is_fork:
            return RepositoryFilterResult(
                repo_name=candidate.repo_name,
                accepted=False,
                score=0.0,
                reason="Fork 저장소는 분석 대상에서 제외됩니다.",
            )
        if candidate.is_template:
            return RepositoryFilterResult(
                repo_name=candidate.repo_name,
                accepted=False,
                score=0.0,
                reason="Template 저장소는 분석 대상에서 제외됩니다.",
            )

        score = self._score(candidate, now=now or datetime.now(UTC))
        accepted = score >= self._threshold
        reason = (
            f"품질 점수 {score:.2f}점으로 기준({self._threshold:.2f}점)을 통과했습니다."
            if accepted
            else f"품질 점수 {score:.2f}점으로 기준({self._threshold:.2f}점)에 미달했습니다."
        )
        return RepositoryFilterResult(
            repo_name=candidate.repo_name, accepted=accepted, score=score, reason=reason
        )

    def _score(self, candidate: RepositoryCandidate, *, now: datetime) -> float:
        norm = self._normalization
        weights = self._weights

        commit_score = clamped_ratio(candidate.commit_count, norm.commit_count_target)
        contributor_score = clamped_ratio(
            candidate.contributor_count, norm.contributor_count_target
        )
        recency_score = _recency_score(candidate.last_activity_at, now, norm)
        readme_score = _readme_score(candidate, norm)
        code_volume_score = clamped_ratio(candidate.code_line_count, norm.code_line_count_target)
        diversity_score = clamped_ratio(
            candidate.file_extension_count, norm.file_extension_count_target
        )

        return (
            weights.commit_count * commit_score
            + weights.contributor_count * contributor_score
            + weights.recency * recency_score
            + weights.readme_quality * readme_score
            + weights.code_volume * code_volume_score
            + weights.file_diversity * diversity_score
        )


def _recency_score(
    last_activity_at: datetime, now: datetime, norm: RepositoryFilterNormalization
) -> float:
    days_since = (now - last_activity_at).days
    if days_since <= norm.recency_full_score_days:
        return 1.0
    if days_since >= norm.recency_zero_score_days:
        return 0.0
    span = norm.recency_zero_score_days - norm.recency_full_score_days
    return 1.0 - (days_since - norm.recency_full_score_days) / span


def _readme_score(candidate: RepositoryCandidate, norm: RepositoryFilterNormalization) -> float:
    return score_readme(
        candidate.readme_length, candidate.readme_has_headings, norm.readme_length_target
    )
