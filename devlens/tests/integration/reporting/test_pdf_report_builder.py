from dataclasses import replace
from io import BytesIO
from unittest.mock import patch

from pypdf import PdfReader

from devlens.application.generate_career_report import GenerateCareerReportResult
from devlens.application.recommend_learning_path import RecommendationResult
from devlens.domain.models import (
    CareerRadarProfile,
    DeveloperProfile,
    ImprovementSuggestion,
    Recommendation,
    RecommendationItem,
    RepositoryEvidence,
    RepositoryFilterResult,
    RoleFit,
    SkillEvidence,
)
from devlens.infrastructure.reporting.pdf_report_builder import (
    _register_korean_fonts,
    build_pdf_report,
)

_KOREAN_REASON = "품질 점수 0.82점으로 기준(0.50점)을 통과했습니다."
_KOREAN_PROJECT_NAME = "실시간 로그 분석 대시보드"
_KOREAN_COMMENTARY = "이 개발자는 devlens 저장소를 근거로 백엔드 역량을 보여주고 있습니다."
_KOREAN_SUGGESTION = "devlens에 테스트가 없습니다. 테스트를 추가하면 점수가 오릅니다."


def _make_result() -> GenerateCareerReportResult:
    profile = DeveloperProfile(
        skills=[SkillEvidence(skill="Python", proficiency="advanced", source_repos=["devlens"])],
        domains=["backend"],
        career_goal="Backend",
        project_level="intermediate",
        repository_evidences=[
            RepositoryEvidence(
                repo_name="devlens",
                tech_stack=["Python"],
                has_tests=True,
                has_ci=True,
                has_docker=True,
                commit_frequency=5.0,
                quality_score=0.82,
                readme_quality_score=0.9,
                domain_tags=["backend"],
            )
        ],
    )
    radar = CareerRadarProfile(
        programming=80,
        project_experience=70,
        software_engineering=60,
        deployment_devops=50,
        documentation=40,
        activity=30,
    )
    item = RecommendationItem(
        item_id="project-log",
        name=_KOREAN_PROJECT_NAME,
        category="project",
        tags=["backend"],
        description="desc",
    )
    recommendation = Recommendation(
        item=item,
        priority_score=0.42,
        skill_gap_weight=0.5,
        similarity=0.5,
        career_goal_relevance=0.5,
    )
    return GenerateCareerReportResult(
        profile=profile,
        filter_results=[
            RepositoryFilterResult(
                repo_name="devlens", accepted=True, score=0.82, reason=_KOREAN_REASON
            )
        ],
        partial=False,
        radar=radar,
        recommendations=RecommendationResult(
            recommendations=[recommendation], roadmap=["Python", "Docker"]
        ),
        suggestions=[
            ImprovementSuggestion(
                repo_name="devlens", axis="software_engineering", message=_KOREAN_SUGGESTION
            )
        ],
        role_fit=[
            RoleFit(
                role="Backend",
                fit_score=0.83,
                matched_skills=["Python"],
                missing_skills=["Docker"],
            )
        ],
        history=[],
        strengths=["Python"],
        growth_areas=["Docker"],
        ai_commentary=_KOREAN_COMMENTARY,
    )


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_pdf_starts_with_a_valid_header() -> None:
    pdf_bytes = build_pdf_report(_make_result(), "octocat", "Backend")

    assert pdf_bytes[:4] == b"%PDF"


def test_pdf_text_includes_english_report_content() -> None:
    text = _extract_text(build_pdf_report(_make_result(), "octocat", "Backend"))

    assert "octocat" in text
    assert "Backend" in text
    assert "Python" in text
    assert "devlens" in text


def test_pdf_includes_the_best_fit_roles_section() -> None:
    text = _extract_text(build_pdf_report(_make_result(), "octocat", "Backend"))

    assert "Best-Fit Roles" in text
    assert "83%" in text


def test_pdf_renders_korean_text_correctly() -> None:
    """Regression guard: reportlab's default fonts have no Korean glyphs, which silently
    renders Korean content as blank/tofu boxes while the PDF otherwise builds "successfully".
    Extracting the actual text is the only way to catch that — byte length/header checks
    alone don't."""
    text = _extract_text(build_pdf_report(_make_result(), "octocat", "Backend"))

    assert _KOREAN_REASON in text
    assert _KOREAN_PROJECT_NAME in text
    assert _KOREAN_COMMENTARY in text
    assert _KOREAN_SUGGESTION in text


def test_partial_result_includes_a_rate_limit_warning() -> None:
    result = replace(_make_result(), partial=True)

    text = _extract_text(build_pdf_report(result, "octocat", "Backend"))

    assert "부분(partial) 결과" in text


def test_ai_commentary_headings_and_blank_blocks_render_without_error() -> None:
    commentary = "# 총평\n\n본문 내용입니다.\n\n\n\n**강조** 텍스트."
    result = replace(_make_result(), ai_commentary=commentary)

    text = _extract_text(build_pdf_report(result, "octocat", "Backend"))

    assert "총평" in text
    assert "본문 내용입니다." in text
    assert "강조" in text


def test_font_registration_falls_back_to_the_built_in_cid_font_without_a_ttf() -> None:
    """Regression guard for the fallback path itself: if no Korean TTF is found on the host
    (e.g. a minimal Docker image), font registration must still succeed."""
    target = "devlens.infrastructure.reporting.pdf_report_builder.os.path.isfile"
    with patch(target, return_value=False):
        body_font, heading_font = _register_korean_fonts()

    assert body_font == "HYSMyeongJo-Medium"
    assert heading_font == "HYGothic-Medium"
