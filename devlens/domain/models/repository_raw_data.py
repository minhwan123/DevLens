from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryRawData(BaseModel):
    """Consolidated raw signals fetched from GitHub for one repository, prior to any analysis."""

    repo_name: str
    is_fork: bool
    is_template: bool
    created_at: datetime
    pushed_at: datetime
    languages: dict[str, int]
    file_paths: list[str]
    readme_text: str | None
    commit_count: int
    contributor_count: int
    manifest_files: dict[str, str] = Field(default_factory=dict)
