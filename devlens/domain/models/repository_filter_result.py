from pydantic import BaseModel


class RepositoryFilterResult(BaseModel):
    """Outcome of RepositoryFilterPolicy.evaluate. Always carries a human-readable reason."""

    repo_name: str
    accepted: bool
    score: float
    reason: str
