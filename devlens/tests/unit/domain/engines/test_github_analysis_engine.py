from datetime import UTC, datetime, timedelta

import pytest

from devlens.domain.engines.github_analysis_engine import GithubAnalysisEngine
from devlens.domain.models.repository_raw_data import RepositoryRawData

_CREATED_AT = datetime(2025, 1, 1, tzinfo=UTC)


def _make_raw_data(**overrides: object) -> RepositoryRawData:
    defaults: dict[str, object] = {
        "repo_name": "devlens",
        "is_fork": False,
        "is_template": False,
        "created_at": _CREATED_AT,
        "pushed_at": _CREATED_AT + timedelta(weeks=10),
        "languages": {"Python": 8000, "HTML": 2000},
        "file_paths": [
            "src/main.py",
            "src/app/manage.py",
            "tests/test_main.py",
            "Dockerfile",
            ".github/workflows/ci.yml",
            "README.md",
        ],
        "readme_text": "# DevLens\n\n" + "x" * 500,
        "commit_count": 100,
        "contributor_count": 4,
    }
    defaults.update(overrides)
    return RepositoryRawData(**defaults)


def test_analyze_detects_react_from_package_json_dependencies() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["package.json"],
        readme_text=None,
        manifest_files={"package.json": '{"dependencies": {"react": "^18.2.0"}}'},
    )

    analysis = engine.analyze(raw)

    assert "React" in analysis.tech_stack
    assert "frontend" in analysis.domain_tags


def test_analyze_detects_framework_from_package_json_dev_dependencies() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["package.json"],
        readme_text=None,
        manifest_files={"package.json": '{"devDependencies": {"vue": "^3.0.0"}}'},
    )

    analysis = engine.analyze(raw)

    assert "Vue.js" in analysis.tech_stack


def test_analyze_ignores_unknown_npm_packages() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["package.json"],
        readme_text=None,
        manifest_files={"package.json": '{"dependencies": {"lodash": "^4.0.0"}}'},
    )

    analysis = engine.analyze(raw)

    assert analysis.tech_stack == ["Python", "HTML"]


def test_analyze_handles_malformed_package_json_gracefully() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["package.json"],
        readme_text=None,
        manifest_files={"package.json": "{not valid json"},
    )

    analysis = engine.analyze(raw)

    assert analysis.tech_stack == ["Python", "HTML"]


def test_analyze_detects_fastapi_from_requirements_txt_with_version_pins_and_comments() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["requirements.txt"],
        readme_text=None,
        manifest_files={
            "requirements.txt": (
                "fastapi>=0.110  # web framework\n"
                "\n"
                "# dev tools\n"
                "pytest==7.0\n"
                "-e git+https://github.com/example/pkg.git#egg=foo\n"
            )
        },
    )

    analysis = engine.analyze(raw)

    assert "FastAPI" in analysis.tech_stack
    assert "backend" in analysis.domain_tags


def test_analyze_detects_multiple_packages_from_pyproject_toml_pep621_dependencies() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["pyproject.toml"],
        readme_text=None,
        manifest_files={
            "pyproject.toml": (
                "[project]\n"
                'dependencies = ["fastapi>=0.110", "pandas~=2.0", "numpy"]\n'
            )
        },
    )

    analysis = engine.analyze(raw)

    assert "FastAPI" in analysis.tech_stack
    assert "Pandas" in analysis.tech_stack
    assert "NumPy" in analysis.tech_stack


def test_analyze_detects_packages_from_pyproject_toml_poetry_section() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["pyproject.toml"],
        readme_text=None,
        manifest_files={
            "pyproject.toml": (
                "[tool.poetry.dependencies]\n"
                'python = "^3.12"\n'
                'torch = "^2.0"\n'
            )
        },
    )

    analysis = engine.analyze(raw)

    assert "PyTorch" in analysis.tech_stack


def test_analyze_handles_malformed_pyproject_toml_gracefully() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["pyproject.toml"],
        readme_text=None,
        manifest_files={"pyproject.toml": "not [ valid toml"},
    )

    analysis = engine.analyze(raw)

    assert analysis.tech_stack == ["Python", "HTML"]


def test_analyze_dedupes_tag_from_marker_and_manifest() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["src/app/manage.py", "requirements.txt"],
        readme_text=None,
        manifest_files={"requirements.txt": "django>=4.0\n"},
    )

    analysis = engine.analyze(raw)

    assert analysis.tech_stack.count("Django") == 1


def test_analyze_manifest_tags_appended_after_language_and_marker_tags() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["src/app/manage.py", "Dockerfile", "requirements.txt"],
        readme_text=None,
        manifest_files={"requirements.txt": "fastapi>=0.110\n"},
    )

    analysis = engine.analyze(raw)

    assert analysis.tech_stack == ["Python", "HTML", "Django", "Docker", "FastAPI"]


def test_analyze_derives_tech_stack_from_languages_and_markers() -> None:
    engine = GithubAnalysisEngine()

    analysis = engine.analyze(_make_raw_data())

    assert analysis.tech_stack == ["Python", "HTML", "Django", "Docker", "GitHub Actions"]


def test_analyze_detects_tests_ci_and_docker() -> None:
    engine = GithubAnalysisEngine()

    analysis = engine.analyze(_make_raw_data())

    assert analysis.has_tests is True
    assert analysis.has_ci is True
    assert analysis.has_docker is True


def test_analyze_derives_domain_tags_from_tech_stack() -> None:
    engine = GithubAnalysisEngine()

    analysis = engine.analyze(_make_raw_data())

    assert analysis.domain_tags == ["backend", "devops"]


def test_analyze_computes_commit_frequency_per_week() -> None:
    engine = GithubAnalysisEngine()

    analysis = engine.analyze(_make_raw_data())

    assert analysis.commit_frequency == pytest.approx(10.0)


def test_analyze_scores_readme_quality() -> None:
    engine = GithubAnalysisEngine()

    analysis = engine.analyze(_make_raw_data())

    assert analysis.readme_quality_score == pytest.approx(1.0)


def test_analyze_builds_candidate_for_filter_policy() -> None:
    engine = GithubAnalysisEngine()

    analysis = engine.analyze(_make_raw_data())
    candidate = analysis.candidate

    assert candidate.readme_length == 511
    assert candidate.readme_has_headings is True
    assert candidate.code_line_count == 250
    assert candidate.file_extension_count == 3
    assert candidate.last_activity_at == _CREATED_AT + timedelta(weeks=10)


def test_analyze_handles_missing_readme_and_no_markers() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(file_paths=["src/main.py"], readme_text=None)

    analysis = engine.analyze(raw)

    assert analysis.has_tests is False
    assert analysis.has_ci is False
    assert analysis.has_docker is False
    assert analysis.tech_stack == ["Python", "HTML"]
    assert analysis.domain_tags == []
    assert analysis.readme_quality_score == pytest.approx(0.0)
    assert analysis.candidate.readme_length == 0
    assert analysis.candidate.readme_has_headings is False


def test_commit_frequency_floors_active_weeks_at_one() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(pushed_at=_CREATED_AT, commit_count=5)

    analysis = engine.analyze(raw)

    assert analysis.commit_frequency == pytest.approx(5.0)


def test_detects_root_level_test_file_by_filename_pattern() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(file_paths=["test_utils.py"], readme_text=None)

    analysis = engine.analyze(raw)

    assert analysis.has_tests is True


def test_detects_suffix_based_markers_for_terraform_and_notebooks() -> None:
    engine = GithubAnalysisEngine()
    raw = _make_raw_data(
        file_paths=["infra/main.tf", "notebooks/eda.ipynb"], readme_text=None
    )

    analysis = engine.analyze(raw)

    assert "Terraform" in analysis.tech_stack
    assert "Jupyter Notebook" in analysis.tech_stack
    assert "data-science" in analysis.domain_tags


def test_to_evidence_uses_the_supplied_quality_score() -> None:
    engine = GithubAnalysisEngine()
    analysis = engine.analyze(_make_raw_data())

    evidence = analysis.to_evidence(quality_score=0.77)

    assert evidence.repo_name == "devlens"
    assert evidence.quality_score == pytest.approx(0.77)
    assert evidence.readme_quality_score == pytest.approx(1.0)
    assert evidence.domain_tags == ["backend", "devops"]
    assert evidence.tech_stack == analysis.tech_stack
