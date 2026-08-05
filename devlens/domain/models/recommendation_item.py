from typing import Literal

from pydantic import BaseModel

RecommendationCategory = Literal["skill", "project", "dataset"]


class RecommendationItem(BaseModel):
    """A catalog entry the Recommendation Engine can rank: a skill, project idea, or dataset."""

    item_id: str
    name: str
    category: RecommendationCategory
    tags: list[str]
    description: str
