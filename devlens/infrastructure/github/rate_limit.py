from dataclasses import dataclass
from datetime import UTC, datetime

import httpx


@dataclass(frozen=True)
class RateLimitInfo:
    limit: int
    remaining: int
    reset_at: datetime

    @property
    def is_exhausted(self) -> bool:
        return self.remaining <= 0


def parse_rate_limit(headers: httpx.Headers) -> RateLimitInfo | None:
    limit = headers.get("x-ratelimit-limit")
    remaining = headers.get("x-ratelimit-remaining")
    reset = headers.get("x-ratelimit-reset")
    if limit is None or remaining is None or reset is None:
        return None
    return RateLimitInfo(
        limit=int(limit),
        remaining=int(remaining),
        reset_at=datetime.fromtimestamp(int(reset), tz=UTC),
    )
