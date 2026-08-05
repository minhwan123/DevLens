import pytest

from devlens.domain.models import RecommendationItem
from devlens.domain.policies.career_goal_relevance_policy import CareerGoalRelevancePolicy

_ROLE_SKILLS = {"Backend": ["Python", "FastAPI", "Docker"]}


def _make_item(tags: list[str]) -> RecommendationItem:
    return RecommendationItem(
        item_id="item", name="Item", category="skill", tags=tags, description="desc"
    )


class _OtherTaggableThing:
    """Minimal stand-in proving the policy works with any Taggable, not just RecommendationItem."""

    def __init__(self, tags: list[str]) -> None:
        self.tags = tags


def test_partial_tag_overlap_scores_partial_relevance() -> None:
    policy = CareerGoalRelevancePolicy(role_required_skills=_ROLE_SKILLS)

    relevance = policy.evaluate(_make_item(["FastAPI", "React"]), "Backend")

    assert relevance == pytest.approx(0.5)


def test_full_tag_overlap_scores_full_relevance() -> None:
    policy = CareerGoalRelevancePolicy(role_required_skills=_ROLE_SKILLS)

    relevance = policy.evaluate(_make_item(["FastAPI", "Docker"]), "Backend")

    assert relevance == pytest.approx(1.0)


def test_no_overlap_scores_zero() -> None:
    policy = CareerGoalRelevancePolicy(role_required_skills=_ROLE_SKILLS)

    relevance = policy.evaluate(_make_item(["React"]), "Backend")

    assert relevance == pytest.approx(0.0)


def test_item_with_no_tags_scores_zero() -> None:
    policy = CareerGoalRelevancePolicy(role_required_skills=_ROLE_SKILLS)

    relevance = policy.evaluate(_make_item([]), "Backend")

    assert relevance == pytest.approx(0.0)


def test_unknown_role_scores_zero() -> None:
    policy = CareerGoalRelevancePolicy(role_required_skills=_ROLE_SKILLS)

    relevance = policy.evaluate(_make_item(["FastAPI"]), "Unknown Role")

    assert relevance == pytest.approx(0.0)


def test_a_differently_shaped_taggable_is_scoreable_via_the_protocol() -> None:
    policy = CareerGoalRelevancePolicy(role_required_skills=_ROLE_SKILLS)

    relevance = policy.evaluate(_OtherTaggableThing(["FastAPI", "Docker"]), "Backend")

    assert relevance == pytest.approx(1.0)
