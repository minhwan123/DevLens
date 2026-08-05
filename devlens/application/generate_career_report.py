import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from devlens.application.analyze_repository import AnalyzeRepositoryUseCase, GitHubClientPort
from devlens.application.recommend_learning_path import (
    RecommendationResult,
    RecommendLearningPathUseCase,
    SimilarityPort,
)
from devlens.domain.engines import (
    CareerIntelligenceEngine,
    ImprovementSuggestionEngine,
    RoleFitEngine,
)
from devlens.domain.models import (
    CareerRadarProfile,
    DeveloperProfile,
    ImprovementSuggestion,
    RadarSnapshot,
    RepositoryFilterResult,
    RoleFit,
)
from devlens.domain.policies import SkillGapPolicy
from devlens.infrastructure.llm import build_career_commentary_prompt
from devlens.infrastructure.persistence.snapshot_repository import SnapshotRepository

logger = logging.getLogger(__name__)


class LlmCommentaryPort(Protocol):
    """AI 분석 의견 generation. The LLM only writes prose from already-computed data — it
    never re-ranks or re-scores anything (see PriorityScorePolicy for the real decision).
    A Protocol so tests can inject a fake and skip real Gemini calls."""

    async def generate_commentary(self, prompt: str) -> str: ...


@dataclass
class GenerateCareerReportResult:
    profile: DeveloperProfile
    filter_results: list[RepositoryFilterResult]
    partial: bool
    radar: CareerRadarProfile
    recommendations: RecommendationResult
    suggestions: list[ImprovementSuggestion]
    role_fit: list[RoleFit]
    history: list[RadarSnapshot]
    strengths: list[str]
    growth_areas: list[str]
    ai_commentary: str


class GenerateCareerReportUseCase:
    """The full pipeline: GitHub analysis -> 6-axis radar -> recommendations + roadmap ->
    AI commentary.

    This is the single unit of work a background Job runs (see interface/api). It only
    orchestrates already-built use cases/engines/policies; no new scoring logic lives here.
    """

    def __init__(
        self,
        github_client: GitHubClientPort,
        similarity_service: SimilarityPort,
        commentary_service: LlmCommentaryPort,
        snapshot_repository: SnapshotRepository,
        analyze_use_case: AnalyzeRepositoryUseCase | None = None,
        career_intelligence_engine: CareerIntelligenceEngine | None = None,
        recommend_use_case: RecommendLearningPathUseCase | None = None,
        skill_gap_policy: SkillGapPolicy | None = None,
        improvement_suggestion_engine: ImprovementSuggestionEngine | None = None,
        role_fit_engine: RoleFitEngine | None = None,
    ) -> None:
        self._analyze_use_case = analyze_use_case or AnalyzeRepositoryUseCase(github_client)
        self._career_intelligence_engine = career_intelligence_engine or CareerIntelligenceEngine()
        self._recommend_use_case = recommend_use_case or RecommendLearningPathUseCase(
            similarity_service
        )
        self._commentary_service = commentary_service
        self._snapshot_repository = snapshot_repository
        self._skill_gap_policy = skill_gap_policy or SkillGapPolicy()
        self._improvement_suggestion_engine = (
            improvement_suggestion_engine or ImprovementSuggestionEngine()
        )
        self._role_fit_engine = role_fit_engine or RoleFitEngine()

    async def execute(self, username: str, career_goal: str) -> GenerateCareerReportResult:
        analysis = await self._analyze_use_case.execute(username, career_goal)
        profile = analysis.profile
        radar = self._career_intelligence_engine.analyze(profile)
        recommendations = await self._recommend_use_case.execute(profile, career_goal)
        suggestions = self._improvement_suggestion_engine.suggest(profile.repository_evidences)
        role_fit = self._role_fit_engine.rank_roles(profile)

        snapshot = RadarSnapshot(
            created_at=datetime.now(UTC).isoformat(), career_goal=career_goal, radar=radar
        )
        try:
            await self._snapshot_repository.save(username, snapshot)
            history = await self._snapshot_repository.list_for_username(username)
        except Exception as exc:
            # A snapshot-store outage (disk full, locked file, ...) must not discard the rest
            # of the report — only the trend history degrades to just this run's point,
            # mirroring the Gemini/job-recommendation failure handling elsewhere here.
            history = [snapshot]
            logger.warning("Radar snapshot history unavailable: %s", exc, exc_info=True)

        strengths = sorted(
            skill.skill for skill in profile.skills if skill.proficiency == "advanced"
        )
        growth_areas = sorted(self._skill_gap_policy.gap_skills(profile, career_goal))

        prompt = build_career_commentary_prompt(
            profile=profile,
            radar=radar,
            strengths=strengths,
            growth_areas=growth_areas,
            recommendations=recommendations.recommendations,
            roadmap=recommendations.roadmap,
        )
        try:
            ai_commentary = await self._commentary_service.generate_commentary(prompt)
        except Exception as exc:
            # A Gemini failure (quota exhausted, transient network error, ...) must not
            # discard the GitHub analysis/radar/recommendations already computed above —
            # only this section degrades, mirroring how a GitHub rate limit produces a
            # partial profile instead of failing the whole use case (AnalyzeRepositoryUseCase).
            ai_commentary = (
                f"AI 분석 의견을 생성하지 못했습니다: {exc}. 나머지 리포트는 정상입니다."
            )

        return GenerateCareerReportResult(
            profile=profile,
            filter_results=analysis.filter_results,
            partial=analysis.partial,
            radar=radar,
            recommendations=recommendations,
            suggestions=suggestions,
            role_fit=role_fit,
            history=history,
            strengths=strengths,
            growth_areas=growth_areas,
            ai_commentary=ai_commentary,
        )
