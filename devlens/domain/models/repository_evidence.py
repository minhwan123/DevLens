from pydantic import BaseModel, Field


class RepositoryEvidence(BaseModel):
    repo_name: str
    tech_stack: list[str]
    has_tests: bool
    has_ci: bool
    has_docker: bool
    commit_frequency: float = Field(description="Average commits per week")
    quality_score: float = Field(description="Repository filter score used to admit this repo")
    readme_quality_score: float = Field(description="0..1 score from README length and structure")
    domain_tags: list[str] = Field(description="Best-effort project domain tags, e.g. backend")
