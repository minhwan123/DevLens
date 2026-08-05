from devlens.config.recommendation_weights import (
    DEFAULT_RECOMMENDATION_WEIGHTS,
    RecommendationWeights,
)


class PriorityScorePolicy:
    """priority_score = w1*skill_gap_weight + w2*similarity + w3*career_goal_relevance.

    Purely arithmetic: the three component scores are computed elsewhere (skill_gap_weight and
    career_goal_relevance are domain-pure; similarity comes from the embedding infra), this
    policy only owns the weighted combination so w1/w2/w3 stay tunable in one place.
    """

    def __init__(self, weights: RecommendationWeights = DEFAULT_RECOMMENDATION_WEIGHTS) -> None:
        self._weights = weights

    def combine(
        self, skill_gap_weight: float, similarity: float, career_goal_relevance: float
    ) -> float:
        return (
            self._weights.skill_gap * skill_gap_weight
            + self._weights.similarity * similarity
            + self._weights.career_goal_relevance * career_goal_relevance
        )
