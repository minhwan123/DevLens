from pydantic import BaseModel

from devlens.application.jobs import JobStatus
from devlens.domain.models import (
    CareerRadarProfile,
    DeveloperProfile,
    ImprovementSuggestion,
    RadarSnapshot,
    Recommendation,
    RepositoryFilterResult,
    RoleFit,
)


class AnalyzeRequest(BaseModel):
    username: str
    career_goal: str


class AnalyzeJobCreatedResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobResultResponse(BaseModel):
    profile: DeveloperProfile
    filter_results: list[RepositoryFilterResult]
    partial: bool
    radar: CareerRadarProfile
    recommendations: list[Recommendation]
    suggestions: list[ImprovementSuggestion]
    role_fit: list[RoleFit]
    history: list[RadarSnapshot]
    roadmap: list[str]
    strengths: list[str]
    growth_areas: list[str]
    ai_commentary: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: JobResultResponse | None = None
    error: str | None = None
