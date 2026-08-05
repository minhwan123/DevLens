from pydantic import BaseModel

from devlens.domain.models.common import ProficiencyLevel
from devlens.domain.models.repository_evidence import RepositoryEvidence
from devlens.domain.models.skill_evidence import SkillEvidence


class DeveloperProfile(BaseModel):
    schema_version: str = "1.0"
    skills: list[SkillEvidence]
    domains: list[str]
    career_goal: str
    project_level: ProficiencyLevel
    repository_evidences: list[RepositoryEvidence]
