from devlens.application.analyze_repository import AnalyzeRepositoryResult
from devlens.application.generate_career_report import GenerateCareerReportUseCase
from devlens.domain.engines import RoleFitEngine
from devlens.domain.models import DeveloperProfile, RepositoryEvidence, SkillEvidence
from devlens.domain.policies import SkillGapPolicy
from devlens.infrastructure.persistence import InMemorySnapshotRepository
from devlens.tests.unit.application.fakes import (
    FakeCommentaryService,
    FakeSimilarityService,
    FakeSnapshotRepository,
)

_ROLE_SKILLS = {"Backend": ["Python", "FastAPI", "Django", "PostgreSQL", "Docker", "Git"]}


class _FakeAnalyzeUseCase:
    """Stubs AnalyzeRepositoryUseCase so this test targets only GenerateCareerReportUseCase's
    own logic (strengths/growth_areas/prompt wiring), not the full GitHub pipeline."""

    def __init__(self, result: AnalyzeRepositoryResult) -> None:
        self._result = result

    async def execute(self, username: str, career_goal: str) -> AnalyzeRepositoryResult:
        return self._result


def _make_profile() -> DeveloperProfile:
    return DeveloperProfile(
        skills=[
            SkillEvidence(skill="Python", proficiency="advanced", source_repos=["devlens"]),
            SkillEvidence(skill="Docker", proficiency="beginner", source_repos=["devlens"]),
        ],
        domains=["backend"],
        career_goal="Backend",
        project_level="advanced",
        repository_evidences=[
            RepositoryEvidence(
                repo_name="devlens",
                tech_stack=["Python", "Docker"],
                has_tests=True,
                has_ci=True,
                has_docker=True,
                commit_frequency=5.0,
                quality_score=0.8,
                readme_quality_score=0.9,
                domain_tags=["backend"],
            )
        ],
    )


def _make_use_case(commentary: FakeCommentaryService) -> GenerateCareerReportUseCase:
    analyze_result = AnalyzeRepositoryResult(
        profile=_make_profile(), filter_results=[], partial=False
    )
    return GenerateCareerReportUseCase(
        github_client=object(),  # type: ignore[arg-type]  # unused: analyze_use_case is stubbed
        similarity_service=FakeSimilarityService(),
        commentary_service=commentary,
        snapshot_repository=InMemorySnapshotRepository(),
        analyze_use_case=_FakeAnalyzeUseCase(analyze_result),
        skill_gap_policy=SkillGapPolicy(role_required_skills=_ROLE_SKILLS),
    )


async def test_strengths_are_the_advanced_skills() -> None:
    result = await _make_use_case(FakeCommentaryService()).execute("octocat", "Backend")

    assert result.strengths == ["Python"]


async def test_growth_areas_are_the_role_gap_skills() -> None:
    result = await _make_use_case(FakeCommentaryService()).execute("octocat", "Backend")

    assert result.growth_areas == ["Django", "Docker", "FastAPI", "Git", "PostgreSQL"]


async def test_ai_commentary_comes_from_the_commentary_service() -> None:
    commentary = FakeCommentaryService("generated commentary text")

    result = await _make_use_case(commentary).execute("octocat", "Backend")

    assert result.ai_commentary == "generated commentary text"
    assert len(commentary.prompts) == 1


async def test_commentary_prompt_cites_skill_evidence_and_growth_areas() -> None:
    commentary = FakeCommentaryService()

    await _make_use_case(commentary).execute("octocat", "Backend")

    prompt = commentary.prompts[0]
    assert "Python (advanced)" in prompt
    assert "devlens" in prompt
    assert "FastAPI" in prompt


async def test_commentary_failure_falls_back_without_failing_the_whole_report() -> None:
    commentary = FakeCommentaryService(fail=True)

    result = await _make_use_case(commentary).execute("octocat", "Backend")

    assert "생성하지 못했습니다" in result.ai_commentary
    assert "boom: quota exceeded" in result.ai_commentary
    # Everything computed before the commentary call must still be intact.
    assert result.strengths == ["Python"]
    assert result.growth_areas == ["Django", "Docker", "FastAPI", "Git", "PostgreSQL"]
    assert len(result.recommendations.recommendations) > 0


async def test_suggestions_are_empty_when_the_repo_meets_every_signal() -> None:
    result = await _make_use_case(FakeCommentaryService()).execute("octocat", "Backend")

    assert result.suggestions == []


async def test_suggestions_are_populated_from_repository_evidence_gaps() -> None:
    analyze_result = AnalyzeRepositoryResult(
        profile=DeveloperProfile(
            skills=[],
            domains=["backend"],
            career_goal="Backend",
            project_level="beginner",
            repository_evidences=[
                RepositoryEvidence(
                    repo_name="devlens",
                    tech_stack=["Python"],
                    has_tests=False,
                    has_ci=True,
                    has_docker=True,
                    commit_frequency=5.0,
                    quality_score=0.8,
                    readme_quality_score=0.9,
                    domain_tags=["backend"],
                )
            ],
        ),
        filter_results=[],
        partial=False,
    )
    use_case = GenerateCareerReportUseCase(
        github_client=object(),  # type: ignore[arg-type]  # unused: analyze_use_case is stubbed
        similarity_service=FakeSimilarityService(),
        commentary_service=FakeCommentaryService(),
        snapshot_repository=InMemorySnapshotRepository(),
        analyze_use_case=_FakeAnalyzeUseCase(analyze_result),
        skill_gap_policy=SkillGapPolicy(role_required_skills=_ROLE_SKILLS),
    )

    result = await use_case.execute("octocat", "Backend")

    assert len(result.suggestions) == 1
    assert result.suggestions[0].repo_name == "devlens"
    assert result.suggestions[0].axis == "software_engineering"


async def test_role_fit_defaults_to_the_top_3_roles() -> None:
    result = await _make_use_case(FakeCommentaryService()).execute("octocat", "Backend")

    assert len(result.role_fit) == 3
    assert all(0 <= fit.fit_score <= 1 for fit in result.role_fit)


async def test_role_fit_uses_an_injected_engine() -> None:
    analyze_result = AnalyzeRepositoryResult(
        profile=_make_profile(), filter_results=[], partial=False
    )
    use_case = GenerateCareerReportUseCase(
        github_client=object(),  # type: ignore[arg-type]  # unused: analyze_use_case is stubbed
        similarity_service=FakeSimilarityService(),
        commentary_service=FakeCommentaryService(),
        snapshot_repository=InMemorySnapshotRepository(),
        analyze_use_case=_FakeAnalyzeUseCase(analyze_result),
        skill_gap_policy=SkillGapPolicy(role_required_skills=_ROLE_SKILLS),
        role_fit_engine=RoleFitEngine(role_required_skills=_ROLE_SKILLS, top_n=1),
    )

    result = await use_case.execute("octocat", "Backend")

    assert len(result.role_fit) == 1
    assert result.role_fit[0].role == "Backend"


async def test_history_has_one_entry_after_the_first_analysis() -> None:
    result = await _make_use_case(FakeCommentaryService()).execute("octocat", "Backend")

    assert len(result.history) == 1
    assert result.history[0].radar == result.radar


async def test_history_accumulates_across_repeated_analyses_of_the_same_username() -> None:
    analyze_result = AnalyzeRepositoryResult(
        profile=_make_profile(), filter_results=[], partial=False
    )
    snapshot_repository = InMemorySnapshotRepository()
    use_case = GenerateCareerReportUseCase(
        github_client=object(),  # type: ignore[arg-type]  # unused: analyze_use_case is stubbed
        similarity_service=FakeSimilarityService(),
        commentary_service=FakeCommentaryService(),
        snapshot_repository=snapshot_repository,
        analyze_use_case=_FakeAnalyzeUseCase(analyze_result),
        skill_gap_policy=SkillGapPolicy(role_required_skills=_ROLE_SKILLS),
    )

    await use_case.execute("octocat", "Backend")
    second_result = await use_case.execute("octocat", "Backend")

    assert len(second_result.history) == 2


async def test_snapshot_store_failure_degrades_without_failing_the_whole_report() -> None:
    analyze_result = AnalyzeRepositoryResult(
        profile=_make_profile(), filter_results=[], partial=False
    )
    use_case = GenerateCareerReportUseCase(
        github_client=object(),  # type: ignore[arg-type]  # unused: analyze_use_case is stubbed
        similarity_service=FakeSimilarityService(),
        commentary_service=FakeCommentaryService(),
        snapshot_repository=FakeSnapshotRepository(fail=True),
        analyze_use_case=_FakeAnalyzeUseCase(analyze_result),
        skill_gap_policy=SkillGapPolicy(role_required_skills=_ROLE_SKILLS),
    )

    result = await use_case.execute("octocat", "Backend")

    # Degrades to just this run's own point instead of failing the whole report.
    assert len(result.history) == 1
    assert result.history[0].radar == result.radar
    assert result.strengths == ["Python"]
