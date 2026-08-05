from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from devlens.domain.models import RepositoryCandidate


def _make_repository_candidate(**overrides: object) -> RepositoryCandidate:
    defaults: dict[str, object] = {
        "repo_name": "devlens",
        "is_fork": False,
        "is_template": False,
        "commit_count": 10,
        "contributor_count": 1,
        "last_activity_at": datetime(2026, 7, 1, tzinfo=UTC),
        "readme_length": 100,
        "readme_has_headings": True,
        "code_line_count": 200,
        "file_extension_count": 3,
    }
    defaults.update(overrides)
    return RepositoryCandidate(**defaults)


def test_accepts_timezone_aware_last_activity_at() -> None:
    candidate = _make_repository_candidate()

    assert candidate.last_activity_at.tzinfo is not None


def test_rejects_naive_last_activity_at() -> None:
    with pytest.raises(ValidationError):
        _make_repository_candidate(last_activity_at=datetime(2026, 7, 1))
