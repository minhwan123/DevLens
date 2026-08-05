import pytest

from devlens.application.recommend_learning_path import RecommendLearningPathUseCase
from devlens.domain.models import DeveloperProfile
from devlens.domain.policies import CareerGoalRelevancePolicy, SkillGapPolicy
from devlens.tests.unit.application.fakes import FakeSimilarityService

_ROLE_SKILLS = {"Backend": ["Python", "FastAPI", "Docker"]}

_CATALOG = [
    {
        "item_id": "skill-fastapi",
        "name": "FastAPI",
        "category": "skill",
        "tags": ["FastAPI", "Python"],
        "description": "FastAPI desc",
    },
    {
        "item_id": "skill-docker",
        "name": "Docker",
        "category": "skill",
        "tags": ["Docker"],
        "description": "Docker desc",
    },
    {
        "item_id": "project-x",
        "name": "Project X",
        "category": "project",
        "tags": ["FastAPI"],
        "description": "Project desc",
    },
]


def _make_use_case(
    similarity_service: FakeSimilarityService, roadmap_size: int = 5
) -> RecommendLearningPathUseCase:
    return RecommendLearningPathUseCase(
        similarity_service=similarity_service,
        catalog=_CATALOG,
        skill_gap_policy=SkillGapPolicy(role_required_skills=_ROLE_SKILLS),
        career_goal_policy=CareerGoalRelevancePolicy(role_required_skills=_ROLE_SKILLS),
        roadmap_size=roadmap_size,
    )


def _make_profile() -> DeveloperProfile:
    return DeveloperProfile(
        skills=[],
        domains=[],
        career_goal="Backend",
        project_level="beginner",
        repository_evidences=[],
    )


async def test_recommendations_are_ranked_by_priority_score_descending() -> None:
    fake_similarity = FakeSimilarityService(
        {"skill-fastapi": 0.9, "skill-docker": 0.1, "project-x": 0.5}
    )
    use_case = _make_use_case(fake_similarity)

    result = await use_case.execute(_make_profile(), "Backend")

    ranked_ids = [rec.item.item_id for rec in result.recommendations]
    assert ranked_ids == ["skill-fastapi", "project-x", "skill-docker"]
    assert result.recommendations[0].priority_score == pytest.approx(0.8267, rel=1e-3)


async def test_similarity_service_is_called_with_all_catalog_items() -> None:
    fake_similarity = FakeSimilarityService()
    use_case = _make_use_case(fake_similarity)

    await use_case.execute(_make_profile(), "Backend")

    assert len(fake_similarity.calls) == 1
    query_text, item_ids = fake_similarity.calls[0]
    assert "Backend" in query_text
    assert set(item_ids) == {"skill-fastapi", "skill-docker", "project-x"}


async def test_roadmap_only_includes_skill_category_items_in_ranked_order() -> None:
    fake_similarity = FakeSimilarityService(
        {"skill-fastapi": 0.9, "skill-docker": 0.1, "project-x": 0.5}
    )
    use_case = _make_use_case(fake_similarity)

    result = await use_case.execute(_make_profile(), "Backend")

    assert result.roadmap == ["FastAPI", "Docker"]


async def test_roadmap_size_limits_how_many_skills_are_considered() -> None:
    fake_similarity = FakeSimilarityService(
        {"skill-fastapi": 0.9, "skill-docker": 0.1, "project-x": 0.5}
    )
    use_case = _make_use_case(fake_similarity, roadmap_size=1)

    result = await use_case.execute(_make_profile(), "Backend")

    assert result.roadmap == ["FastAPI"]


async def test_missing_similarity_score_defaults_to_zero() -> None:
    fake_similarity = FakeSimilarityService({})
    use_case = _make_use_case(fake_similarity)

    result = await use_case.execute(_make_profile(), "Backend")

    assert all(rec.similarity == pytest.approx(0.0) for rec in result.recommendations)
