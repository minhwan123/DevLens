import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

from devlens.config.recommendation_catalog import DEFAULT_RECOMMENDATION_CATALOG
from devlens.domain.engines import RoadmapEngine
from devlens.domain.models import DeveloperProfile, Recommendation, RecommendationItem
from devlens.domain.policies import CareerGoalRelevancePolicy, PriorityScorePolicy, SkillGapPolicy


class SimilarityPort(Protocol):
    """cosine_similarity(profile_embedding, item_embedding) via Sentence Transformers + FAISS.

    A Protocol so tests can inject a fake and skip loading the real embedding model.
    """

    def rank(self, query_text: str, items: dict[str, str]) -> dict[str, float]: ...


@dataclass
class RecommendationResult:
    recommendations: list[Recommendation]
    roadmap: list[str]


class RecommendLearningPathUseCase:
    """Ranks catalog items (skills/projects/datasets) for a profile + target role, then builds
    a learning roadmap from the top-ranked skills via topological sort.

    priority_score = w1*skill_gap_weight + w2*similarity + w3*career_goal_relevance. The first
    and third terms are pure domain policies; similarity comes from the embedding infra behind
    SimilarityPort. This use case only orchestrates and never re-implements the formula itself
    (that lives in PriorityScorePolicy).
    """

    def __init__(
        self,
        similarity_service: SimilarityPort,
        catalog: list[dict[str, Any]] | None = None,
        skill_gap_policy: SkillGapPolicy | None = None,
        career_goal_policy: CareerGoalRelevancePolicy | None = None,
        priority_score_policy: PriorityScorePolicy | None = None,
        roadmap_engine: RoadmapEngine | None = None,
        roadmap_size: int = 5,
    ) -> None:
        self._similarity_service = similarity_service
        raw_catalog = catalog if catalog is not None else DEFAULT_RECOMMENDATION_CATALOG
        self._catalog = [RecommendationItem(**entry) for entry in raw_catalog]
        self._skill_gap_policy = skill_gap_policy or SkillGapPolicy()
        self._career_goal_policy = career_goal_policy or CareerGoalRelevancePolicy()
        self._priority_score_policy = priority_score_policy or PriorityScorePolicy()
        self._roadmap_engine = roadmap_engine or RoadmapEngine()
        self._roadmap_size = roadmap_size

    async def execute(self, profile: DeveloperProfile, target_role: str) -> RecommendationResult:
        query_text = summarize_profile_for_embedding(profile)
        item_texts = {item.item_id: item.description for item in self._catalog}
        similarities = await asyncio.to_thread(
            self._similarity_service.rank, query_text, item_texts
        )

        recommendations = [
            self._score_item(item, profile, target_role, similarities.get(item.item_id, 0.0))
            for item in self._catalog
        ]
        recommendations.sort(key=lambda rec: rec.priority_score, reverse=True)

        roadmap = self._build_roadmap(recommendations)
        return RecommendationResult(recommendations=recommendations, roadmap=roadmap)

    def _score_item(
        self,
        item: RecommendationItem,
        profile: DeveloperProfile,
        target_role: str,
        similarity: float,
    ) -> Recommendation:
        skill_gap_weight = self._skill_gap_policy.weight(item, profile, target_role)
        career_goal_relevance = self._career_goal_policy.evaluate(item, target_role)
        priority_score = self._priority_score_policy.combine(
            skill_gap_weight, similarity, career_goal_relevance
        )
        return Recommendation(
            item=item,
            priority_score=priority_score,
            skill_gap_weight=skill_gap_weight,
            similarity=similarity,
            career_goal_relevance=career_goal_relevance,
        )

    def _build_roadmap(self, recommendations: list[Recommendation]) -> list[str]:
        top_skills = [rec.item.name for rec in recommendations if rec.item.category == "skill"]
        return self._roadmap_engine.build_roadmap(top_skills[: self._roadmap_size])


def summarize_profile_for_embedding(profile: DeveloperProfile) -> str:
    skill_summary = ", ".join(f"{skill.skill}({skill.proficiency})" for skill in profile.skills)
    domain_summary = ", ".join(profile.domains)
    return (
        f"Career goal: {profile.career_goal}. Project level: {profile.project_level}. "
        f"Skills: {skill_summary or 'none'}. Domains: {domain_summary or 'none'}."
    )
