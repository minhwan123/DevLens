import pytest

from devlens.domain.engines.role_fit_engine import RoleFitEngine
from devlens.domain.models import DeveloperProfile, SkillEvidence

_ROLE_SKILLS = {
    "Backend": ["Python", "FastAPI", "Docker"],
    "Frontend": ["JavaScript", "React"],
    "DevOps": ["Docker", "Kubernetes", "Terraform", "AWS"],
}


def _make_profile(skills: list[SkillEvidence]) -> DeveloperProfile:
    return DeveloperProfile(
        skills=skills,
        domains=[],
        career_goal="Backend",
        project_level="beginner",
        repository_evidences=[],
    )


def test_a_profile_matching_every_required_skill_scores_full_fit() -> None:
    engine = RoleFitEngine(role_required_skills=_ROLE_SKILLS, top_n=3)
    profile = _make_profile(
        [
            SkillEvidence(skill="Python", proficiency="advanced", source_repos=["r"]),
            SkillEvidence(skill="FastAPI", proficiency="advanced", source_repos=["r"]),
            SkillEvidence(skill="Docker", proficiency="advanced", source_repos=["r"]),
        ]
    )

    fits = engine.rank_roles(profile)

    backend_fit = next(fit for fit in fits if fit.role == "Backend")
    assert backend_fit.fit_score == pytest.approx(1.0)
    assert backend_fit.missing_skills == []
    assert sorted(backend_fit.matched_skills) == ["Docker", "FastAPI", "Python"]


def test_results_are_ranked_best_fit_first() -> None:
    engine = RoleFitEngine(role_required_skills=_ROLE_SKILLS, top_n=3)
    profile = _make_profile(
        [
            SkillEvidence(skill="Python", proficiency="advanced", source_repos=["r"]),
            SkillEvidence(skill="FastAPI", proficiency="advanced", source_repos=["r"]),
            SkillEvidence(skill="Docker", proficiency="advanced", source_repos=["r"]),
        ]
    )

    fits = engine.rank_roles(profile)

    scores = [fit.fit_score for fit in fits]
    assert scores == sorted(scores, reverse=True)
    assert fits[0].role == "Backend"


def test_top_n_truncates_results() -> None:
    engine = RoleFitEngine(role_required_skills=_ROLE_SKILLS, top_n=1)

    fits = engine.rank_roles(_make_profile([]))

    assert len(fits) == 1


def test_beginner_proficiency_counts_as_missing() -> None:
    engine = RoleFitEngine(role_required_skills=_ROLE_SKILLS, top_n=3)
    profile = _make_profile(
        [SkillEvidence(skill="Python", proficiency="beginner", source_repos=["r"])]
    )

    fits = engine.rank_roles(profile)

    backend_fit = next(fit for fit in fits if fit.role == "Backend")
    assert "Python" in backend_fit.missing_skills
    assert "Python" not in backend_fit.matched_skills


def test_an_empty_profile_scores_zero_on_every_role() -> None:
    engine = RoleFitEngine(role_required_skills=_ROLE_SKILLS, top_n=3)

    fits = engine.rank_roles(_make_profile([]))

    assert all(fit.fit_score == pytest.approx(0.0) for fit in fits)
