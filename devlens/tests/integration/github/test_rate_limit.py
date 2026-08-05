from datetime import UTC, datetime

import httpx

from devlens.infrastructure.github.rate_limit import RateLimitInfo, parse_rate_limit


def test_parse_rate_limit_extracts_all_fields() -> None:
    headers = httpx.Headers(
        {
            "x-ratelimit-limit": "5000",
            "x-ratelimit-remaining": "10",
            "x-ratelimit-reset": "1700000000",
        }
    )

    info = parse_rate_limit(headers)

    assert info == RateLimitInfo(
        limit=5000, remaining=10, reset_at=datetime.fromtimestamp(1700000000, tz=UTC)
    )


def test_parse_rate_limit_returns_none_when_headers_are_missing() -> None:
    assert parse_rate_limit(httpx.Headers({})) is None


def test_is_exhausted_true_when_remaining_is_zero_or_negative() -> None:
    info = RateLimitInfo(limit=5000, remaining=0, reset_at=datetime.now(UTC))

    assert info.is_exhausted is True


def test_is_exhausted_false_when_remaining_is_positive() -> None:
    info = RateLimitInfo(limit=5000, remaining=1, reset_at=datetime.now(UTC))

    assert info.is_exhausted is False
