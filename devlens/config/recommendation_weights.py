from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationWeights:
    """w1/w2/w3 in priority_score = w1*skill_gap + w2*similarity + w3*career_goal_relevance."""

    skill_gap: float = 0.4
    similarity: float = 0.4
    career_goal_relevance: float = 0.2


DEFAULT_RECOMMENDATION_WEIGHTS = RecommendationWeights()
