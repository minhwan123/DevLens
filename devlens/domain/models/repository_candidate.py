from datetime import datetime

from pydantic import BaseModel, field_validator


class RepositoryCandidate(BaseModel):
    """Raw per-repository signals collected from GitHub, prior to quality filtering."""

    repo_name: str
    is_fork: bool
    is_template: bool
    commit_count: int
    contributor_count: int
    last_activity_at: datetime
    readme_length: int
    readme_has_headings: bool
    code_line_count: int
    file_extension_count: int

    @field_validator("last_activity_at")
    @classmethod
    def _require_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("last_activity_at must be timezone-aware")
        return value
