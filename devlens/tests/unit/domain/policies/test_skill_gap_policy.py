import pytest

from devlens.domain.models import DeveloperProfile, RecommendationItem, SkillEvidence
from devlens.domain.policies.skill_gap_policy import SkillGapPolicy

_ROLE_SKILLS = {"Backend": ["Python", "FastAPI", "Docker"]}


def _make_item(tags: list[str]) -> RecommendationItem:
    return RecommendationItem(
        item_id="item", name="Item", category="skill", tags=tags, description="desc"
    )


class _OtherTaggableThing:
    """Minimal stand-in proving the policy works with any Taggable, not just RecommendationItem."""

    def __init__(self, tags: list[str]) -> None:
        self.tags = tags


def _make_profile(skills: list[SkillEvidence]) -> DeveloperProfile:
    return DeveloperProfile(
        skills=skills,
        domains=[],
        career_goal="Backend",
        project_level="beginner",
        repository_evidences=[],
    )


def test_item_covering_part_of_the_gap_gets_partial_weight() -> None:
    policy = SkillGapPolicy(role_required_skills=_ROLE_SKILLS)
    profile = _make_profile(
        [
            SkillEvidence(skill="Python", proficiency="advanced", source_repos=["r"]),
            SkillEvidence(skill="Docker", proficiency="beginner", source_repos=["r"]),
        ]
    )

    weight = policy.weight(_make_item(["Docker"]), profile, "Backend")

    assert weight == pytest.approx(0.5)


def test_item_covering_the_whole_gap_gets_full_weight() -> None:
    policy = SkillGapPolicy(role_required_skills=_ROLE_SKILLS)
    profile = _make_profile(
        [SkillEvidence(skill="Python", proficiency="advanced", source_repos=["r"])]
    )

    weight = policy.weight(_make_item(["FastAPI", "Docker"]), profile, "Backend")

    assert weight == pytest.approx(1.0)


def test_item_covering_no_gap_skill_scores_zero() -> None:
    policy = SkillGapPolicy(role_required_skills=_ROLE_SKILLS)
    profile = _make_profile([])

    weight = policy.weight(_make_item(["React"]), profile, "Backend")

    assert weight == pytest.approx(0.0)


def test_advanced_skill_is_not_counted_as_a_gap() -> None:
    policy = SkillGapPolicy(role_required_skills=_ROLE_SKILLS)
    profile = _make_profile(
        [
            SkillEvidence(skill="Python", proficiency="advanced", source_repos=["r"]),
            SkillEvidence(skill="FastAPI", proficiency="intermediate", source_repos=["r"]),
            SkillEvidence(skill="Docker", proficiency="advanced", source_repos=["r"]),
        ]
    )

    weight = policy.weight(_make_item(["Python", "FastAPI", "Docker"]), profile, "Backend")

    assert weight == pytest.approx(0.0)


def test_unknown_role_has_no_gap() -> None:
    policy = SkillGapPolicy(role_required_skills=_ROLE_SKILLS)
    profile = _make_profile([])

    weight = policy.weight(_make_item(["Python"]), profile, "Unknown Role")

    assert weight == pytest.approx(0.0)


def test_a_differently_shaped_taggable_is_scoreable_via_the_protocol() -> None:
    policy = SkillGapPolicy(role_required_skills=_ROLE_SKILLS)
    profile = _make_profile(
        [SkillEvidence(skill="Python", proficiency="advanced", source_repos=["r"])]
    )

    weight = policy.weight(_OtherTaggableThing(["FastAPI", "Docker"]), profile, "Backend")

    assert weight == pytest.approx(1.0)
