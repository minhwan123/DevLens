import pytest

from devlens.config.recommendation_weights import RecommendationWeights
from devlens.domain.policies.priority_score_policy import PriorityScorePolicy


def test_default_weights_sum_to_one_on_full_scores() -> None:
    policy = PriorityScorePolicy()

    score = policy.combine(skill_gap_weight=1.0, similarity=1.0, career_goal_relevance=1.0)

    assert score == pytest.approx(1.0)


def test_default_weights_combine_partial_scores() -> None:
    policy = PriorityScorePolicy()

    score = policy.combine(skill_gap_weight=0.5, similarity=0.25, career_goal_relevance=1.0)

    assert score == pytest.approx(0.5)


def test_custom_weights_change_the_combination() -> None:
    policy = PriorityScorePolicy(
        weights=RecommendationWeights(skill_gap=1.0, similarity=0.0, career_goal_relevance=0.0)
    )

    score = policy.combine(skill_gap_weight=0.7, similarity=1.0, career_goal_relevance=1.0)

    assert score == pytest.approx(0.7)
