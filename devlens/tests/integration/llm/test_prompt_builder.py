from devlens.domain.models import (
    CareerRadarProfile,
    DeveloperProfile,
    Recommendation,
    RecommendationItem,
    SkillEvidence,
)
from devlens.infrastructure.llm.prompt_builder import build_career_commentary_prompt


def _make_profile() -> DeveloperProfile:
    return DeveloperProfile(
        skills=[SkillEvidence(skill="Python", proficiency="advanced", source_repos=["devlens"])],
        domains=["backend"],
        career_goal="Backend",
        project_level="intermediate",
        repository_evidences=[],
    )


def _make_radar() -> CareerRadarProfile:
    return CareerRadarProfile(
        programming=80,
        project_experience=70,
        software_engineering=60,
        deployment_devops=50,
        documentation=40,
        activity=30,
    )


def _make_recommendation(name: str, priority: float) -> Recommendation:
    item = RecommendationItem(
        item_id=name, name=name, category="skill", tags=[name], description=f"{name} desc"
    )
    return Recommendation(
        item=item,
        priority_score=priority,
        skill_gap_weight=0.5,
        similarity=0.5,
        career_goal_relevance=0.5,
    )


def test_prompt_includes_profile_context_and_skill_evidence() -> None:
    prompt = build_career_commentary_prompt(
        profile=_make_profile(),
        radar=_make_radar(),
        strengths=["Python"],
        growth_areas=["Docker"],
        recommendations=[],
        roadmap=[],
    )

    assert "Backend" in prompt
    assert "intermediate" in prompt
    assert "Python (advanced)" in prompt
    assert "devlens" in prompt
    assert "Python" in prompt.split("[강점]")[1].split("[")[0]
    assert "Docker" in prompt.split("[성장 필요 영역")[1].split("[")[0]


def test_prompt_limits_recommendations_to_top_five() -> None:
    recommendations = [_make_recommendation(f"skill-{i}", 1.0 - i * 0.1) for i in range(7)]

    prompt = build_career_commentary_prompt(
        profile=_make_profile(),
        radar=_make_radar(),
        strengths=[],
        growth_areas=[],
        recommendations=recommendations,
        roadmap=[],
    )

    for i in range(5):
        assert f"skill-{i}" in prompt
    for i in range(5, 7):
        assert f"skill-{i}" not in prompt


def test_prompt_includes_roadmap_in_order() -> None:
    prompt = build_career_commentary_prompt(
        profile=_make_profile(),
        radar=_make_radar(),
        strengths=[],
        growth_areas=[],
        recommendations=[],
        roadmap=["Docker", "FastAPI", "AWS"],
    )

    assert "Docker -> FastAPI -> AWS" in prompt


def test_prompt_handles_empty_profile_gracefully() -> None:
    empty_profile = DeveloperProfile(
        skills=[],
        domains=[],
        career_goal="Backend",
        project_level="beginner",
        repository_evidences=[],
    )

    prompt = build_career_commentary_prompt(
        profile=empty_profile,
        radar=_make_radar(),
        strengths=[],
        growth_areas=[],
        recommendations=[],
        roadmap=[],
    )

    assert "추출된 스킬 없음" in prompt
    assert "뚜렷한 강점 없음" in prompt
    assert "추천 항목 없음" in prompt
    assert "로드맵 없음" in prompt
