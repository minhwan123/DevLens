from datetime import UTC, datetime, timedelta

import pytest

from devlens.config.filter_thresholds import RepositoryFilterWeights
from devlens.domain.models.repository_candidate import RepositoryCandidate
from devlens.domain.policies.repository_filter_policy import RepositoryFilterPolicy

_NOW = datetime(2026, 7, 15, tzinfo=UTC)


def _make_candidate(**overrides: object) -> RepositoryCandidate:
    defaults: dict[str, object] = {
        "repo_name": "devlens",
        "is_fork": False,
        "is_template": False,
        "commit_count": 0,
        "contributor_count": 0,
        "last_activity_at": _NOW - timedelta(days=1000),
        "readme_length": 0,
        "readme_has_headings": False,
        "code_line_count": 0,
        "file_extension_count": 0,
    }
    defaults.update(overrides)
    return RepositoryCandidate(**defaults)


def test_fork_is_rejected_without_scoring() -> None:
    policy = RepositoryFilterPolicy()
    candidate = _make_candidate(is_fork=True)

    result = policy.evaluate(candidate, now=_NOW)

    assert result.accepted is False
    assert result.score == 0.0
    assert "Fork" in result.reason


def test_template_is_rejected_without_scoring() -> None:
    policy = RepositoryFilterPolicy()
    candidate = _make_candidate(is_template=True)

    result = policy.evaluate(candidate, now=_NOW)

    assert result.accepted is False
    assert "Template" in result.reason


def test_high_quality_repository_is_accepted_with_max_score() -> None:
    policy = RepositoryFilterPolicy()
    candidate = _make_candidate(
        commit_count=60,
        contributor_count=5,
        last_activity_at=_NOW - timedelta(days=5),
        readme_length=600,
        readme_has_headings=True,
        code_line_count=800,
        file_extension_count=8,
    )

    result = policy.evaluate(candidate, now=_NOW)

    assert result.accepted is True
    assert result.score == pytest.approx(1.0)


def test_empty_repository_is_rejected_with_zero_score() -> None:
    policy = RepositoryFilterPolicy()
    candidate = _make_candidate()

    result = policy.evaluate(candidate, now=_NOW)

    assert result.accepted is False
    assert result.score == pytest.approx(0.0)
    assert "미달" in result.reason


def test_partial_signals_score_between_zero_and_one() -> None:
    policy = RepositoryFilterPolicy()
    candidate = _make_candidate(
        commit_count=25,
        contributor_count=1,
        last_activity_at=_NOW - timedelta(days=10),
        readme_length=250,
        readme_has_headings=False,
        code_line_count=250,
        file_extension_count=2,
    )

    result = policy.evaluate(candidate, now=_NOW)

    assert result.score == pytest.approx(0.5425)
    assert result.accepted is True


def test_recency_score_decays_linearly_between_full_and_zero_days() -> None:
    policy = RepositoryFilterPolicy(
        weights=RepositoryFilterWeights(
            commit_count=0,
            contributor_count=0,
            recency=1.0,
            readme_quality=0,
            code_volume=0,
            file_diversity=0,
        )
    )
    days_since = 197
    candidate = _make_candidate(last_activity_at=_NOW - timedelta(days=days_since))

    result = policy.evaluate(candidate, now=_NOW)

    expected_recency_score = 1 - (days_since - 30) / (365 - 30)
    assert result.score == pytest.approx(expected_recency_score)


def test_custom_threshold_overrides_default() -> None:
    candidate = _make_candidate(
        commit_count=25,
        contributor_count=1,
        last_activity_at=_NOW - timedelta(days=10),
        readme_length=250,
        code_line_count=250,
        file_extension_count=2,
    )
    lenient_policy = RepositoryFilterPolicy(threshold=0.5)
    strict_policy = RepositoryFilterPolicy(threshold=0.6)

    assert lenient_policy.evaluate(candidate, now=_NOW).accepted is True
    assert strict_policy.evaluate(candidate, now=_NOW).accepted is False


def test_custom_weights_isolate_a_single_signal() -> None:
    policy = RepositoryFilterPolicy(
        weights=RepositoryFilterWeights(
            commit_count=0,
            contributor_count=0,
            recency=0,
            readme_quality=0,
            code_volume=1.0,
            file_diversity=0,
        )
    )
    candidate = _make_candidate(code_line_count=500)

    result = policy.evaluate(candidate, now=_NOW)

    assert result.score == pytest.approx(1.0)
