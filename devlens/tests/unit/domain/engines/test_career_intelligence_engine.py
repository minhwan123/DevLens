import pytest

from devlens.domain.engines.career_intelligence_engine import CareerIntelligenceEngine
from devlens.domain.models import DeveloperProfile, RepositoryEvidence, SkillEvidence

_engine = CareerIntelligenceEngine()


def _make_evidence(**overrides: object) -> RepositoryEvidence:
    defaults: dict[str, object] = {
        "repo_name": "repo-a",
        "tech_stack": ["Python"],
        "has_tests": True,
        "has_ci": True,
        "has_docker": True,
        "commit_frequency": 6.0,
        "quality_score": 0.8,
        "readme_quality_score": 1.0,
        "domain_tags": ["backend", "devops"],
    }
    defaults.update(overrides)
    return RepositoryEvidence(**defaults)


def _make_profile(**overrides: object) -> DeveloperProfile:
    defaults: dict[str, object] = {
        "skills": [],
        "domains": [],
        "career_goal": "AI Engineer",
        "project_level": "beginner",
        "repository_evidences": [],
    }
    defaults.update(overrides)
    return DeveloperProfile(**defaults)


def test_empty_profile_scores_zero_on_every_axis() -> None:
    radar = _engine.analyze(_make_profile())

    assert radar.programming == pytest.approx(0.0)
    assert radar.project_experience == pytest.approx(0.0)
    assert radar.software_engineering == pytest.approx(0.0)
    assert radar.deployment_devops == pytest.approx(0.0)
    assert radar.documentation == pytest.approx(0.0)
    assert radar.activity == pytest.approx(0.0)


def test_mixed_profile_computes_expected_axis_scores() -> None:
    profile = _make_profile(
        skills=[
            SkillEvidence(skill="Python", proficiency="advanced", source_repos=["repo-a"]),
            SkillEvidence(skill="Docker", proficiency="intermediate", source_repos=["repo-a"]),
            SkillEvidence(skill="HTML", proficiency="beginner", source_repos=["repo-b"]),
        ],
        repository_evidences=[
            _make_evidence(
                repo_name="repo-a",
                has_tests=True,
                has_ci=True,
                has_docker=True,
                commit_frequency=6.0,
                quality_score=0.8,
                readme_quality_score=1.0,
                domain_tags=["backend", "devops"],
            ),
            _make_evidence(
                repo_name="repo-b",
                has_tests=False,
                has_ci=False,
                has_docker=False,
                commit_frequency=2.0,
                quality_score=0.6,
                readme_quality_score=0.5,
                domain_tags=[],
            ),
        ],
    )

    radar = _engine.analyze(profile)

    assert radar.programming == pytest.approx(20.0)
    assert radar.project_experience == pytest.approx(51.6667, rel=1e-3)
    assert radar.software_engineering == pytest.approx(50.0)
    assert radar.deployment_devops == pytest.approx(50.0)
    assert radar.documentation == pytest.approx(75.0)
    assert radar.activity == pytest.approx(80.0)


def test_no_single_aggregate_field_is_exposed() -> None:
    radar = _engine.analyze(_make_profile())

    assert set(type(radar).model_fields) == {
        "programming",
        "project_experience",
        "software_engineering",
        "deployment_devops",
        "documentation",
        "activity",
    }


def test_axis_scores_saturate_at_one_hundred() -> None:
    profile = _make_profile(
        skills=[
            SkillEvidence(skill=f"skill-{i}", proficiency="advanced", source_repos=["repo-a"])
            for i in range(20)
        ],
        repository_evidences=[
            _make_evidence(commit_frequency=999.0, quality_score=1.0) for _ in range(10)
        ],
    )

    radar = _engine.analyze(profile)

    assert radar.programming == pytest.approx(100.0)
    assert radar.activity == pytest.approx(100.0)
    assert radar.project_experience == pytest.approx(100.0)
