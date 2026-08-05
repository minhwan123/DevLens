from devlens.domain.engines.improvement_suggestion_engine import ImprovementSuggestionEngine
from devlens.domain.models import RepositoryEvidence

_engine = ImprovementSuggestionEngine()


def _make_evidence(**overrides: object) -> RepositoryEvidence:
    defaults: dict[str, object] = {
        "repo_name": "repo-a",
        "tech_stack": ["Python"],
        "has_tests": True,
        "has_ci": True,
        "has_docker": True,
        "commit_frequency": 6.0,
        "quality_score": 0.8,
        "readme_quality_score": 1.0,
        "domain_tags": ["backend"],
    }
    defaults.update(overrides)
    return RepositoryEvidence(**defaults)


def test_a_repo_meeting_every_signal_gets_no_suggestions() -> None:
    suggestions = _engine.suggest([_make_evidence()])

    assert suggestions == []


def test_missing_tests_suggests_software_engineering() -> None:
    suggestions = _engine.suggest([_make_evidence(has_tests=False)])

    assert len(suggestions) == 1
    assert suggestions[0].repo_name == "repo-a"
    assert suggestions[0].axis == "software_engineering"
    assert "테스트" in suggestions[0].message


def test_missing_ci_suggests_software_engineering() -> None:
    suggestions = _engine.suggest([_make_evidence(has_ci=False)])

    assert len(suggestions) == 1
    assert suggestions[0].axis == "software_engineering"
    assert "CI" in suggestions[0].message


def test_missing_docker_suggests_deployment_devops() -> None:
    suggestions = _engine.suggest([_make_evidence(has_docker=False)])

    assert len(suggestions) == 1
    assert suggestions[0].axis == "deployment_devops"


def test_low_readme_quality_suggests_documentation() -> None:
    suggestions = _engine.suggest([_make_evidence(readme_quality_score=0.1)])

    assert len(suggestions) == 1
    assert suggestions[0].axis == "documentation"


def test_low_commit_frequency_suggests_activity() -> None:
    suggestions = _engine.suggest([_make_evidence(commit_frequency=0.5)])

    assert len(suggestions) == 1
    assert suggestions[0].axis == "activity"


def test_a_repo_missing_everything_gets_one_suggestion_per_signal() -> None:
    evidence = _make_evidence(
        has_tests=False,
        has_ci=False,
        has_docker=False,
        readme_quality_score=0.0,
        commit_frequency=0.0,
    )

    suggestions = _engine.suggest([evidence])

    assert len(suggestions) == 5


def test_suggestions_span_multiple_repos_independently() -> None:
    evidences = [
        _make_evidence(repo_name="repo-a", has_tests=False),
        _make_evidence(repo_name="repo-b", has_docker=False),
    ]

    suggestions = _engine.suggest(evidences)

    repo_names = {suggestion.repo_name for suggestion in suggestions}
    assert repo_names == {"repo-a", "repo-b"}


def test_no_evidences_yields_no_suggestions() -> None:
    assert _engine.suggest([]) == []
