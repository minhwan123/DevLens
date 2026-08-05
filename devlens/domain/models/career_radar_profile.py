from pydantic import BaseModel, Field


class CareerRadarProfile(BaseModel):
    """Six independent 0..100 axis scores for radar-chart visualization.

    Deliberately has no aggregate/total field: this project does not expose a single
    "GitHub Score" to users, by design.
    """

    programming: float = Field(ge=0, le=100)
    project_experience: float = Field(ge=0, le=100)
    software_engineering: float = Field(ge=0, le=100)
    deployment_devops: float = Field(ge=0, le=100)
    documentation: float = Field(ge=0, le=100)
    activity: float = Field(ge=0, le=100)
