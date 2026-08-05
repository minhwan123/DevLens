from pydantic import BaseModel, Field

from devlens.domain.models.recommendation_item import RecommendationItem


class Recommendation(BaseModel):
    """A ranked recommendation: the catalog item plus its priority_score and components.

    The component scores are kept alongside the total so the AI Report (Step 11) can explain
    *why* an item was recommended without recomputing anything.
    """

    item: RecommendationItem
    priority_score: float
    skill_gap_weight: float = Field(ge=0, le=1)
    similarity: float = Field(ge=-1, le=1, description="Cosine similarity, so signed")
    career_goal_relevance: float = Field(ge=0, le=1)
