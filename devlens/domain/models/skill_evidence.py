from pydantic import BaseModel, Field

from devlens.domain.models.common import ProficiencyLevel


class SkillEvidence(BaseModel):
    skill: str
    proficiency: ProficiencyLevel
    source_repos: list[str] = Field(default_factory=list)
