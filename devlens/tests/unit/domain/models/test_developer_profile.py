import pytest
from pydantic import ValidationError

from devlens.domain.models import DeveloperProfile, RepositoryEvidence, SkillEvidence


def _make_repository_evidence(**overrides: object) -> RepositoryEvidence:
    defaults: dict[str, object] = {
        "repo_name": "devlens",
        "tech_stack": ["Python", "FastAPI"],
        "has_tests": True,
        "has_ci": False,
        "has_docker": True,
        "commit_frequency": 3.5,
        "quality_score": 0.82,
        "readme_quality_score": 0.9,
        "domain_tags": ["backend"],
    }
    defaults.update(overrides)
    return RepositoryEvidence(**defaults)


def _make_developer_profile(**overrides: object) -> DeveloperProfile:
    defaults: dict[str, object] = {
        "skills": [SkillEvidence(skill="Python", proficiency="advanced", source_repos=["devlens"])],
        "domains": ["backend"],
        "career_goal": "AI Engineer",
        "project_level": "intermediate",
        "repository_evidences": [_make_repository_evidence()],
    }
    defaults.update(overrides)
    return DeveloperProfile(**defaults)


def test_developer_profile_defaults_schema_version() -> None:
    profile = _make_developer_profile()

    assert profile.schema_version == "1.0"


def test_skill_evidence_rejects_invalid_proficiency() -> None:
    with pytest.raises(ValidationError):
        SkillEvidence(skill="Python", proficiency="expert", source_repos=[])  # type: ignore[arg-type]


def test_developer_profile_rejects_invalid_project_level() -> None:
    with pytest.raises(ValidationError):
        _make_developer_profile(project_level="expert")


def test_skill_evidence_allows_empty_source_repos() -> None:
    skill = SkillEvidence(skill="Docker", proficiency="beginner", source_repos=[])

    assert skill.source_repos == []
