from datetime import datetime


class GitHubClientError(Exception):
    """Base class for GitHub API client errors."""


class GitHubResourceNotFoundError(GitHubClientError):
    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"GitHub resource not found: {path}")


class GitHubRateLimitExceededError(GitHubClientError):
    def __init__(self, reset_at: datetime) -> None:
        self.reset_at = reset_at
        super().__init__(f"GitHub API rate limit exceeded, resets at {reset_at.isoformat()}")
