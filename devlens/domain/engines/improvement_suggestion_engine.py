from devlens.config.career_radar_thresholds import (
    DEFAULT_IMPROVEMENT_SUGGESTION_THRESHOLDS,
    ImprovementSuggestionThresholds,
)
from devlens.domain.models.improvement_suggestion import ImprovementSuggestion
from devlens.domain.models.repository_evidence import RepositoryEvidence


class ImprovementSuggestionEngine:
    """Turns the exact signals CareerIntelligenceEngine reads into concrete, per-repository
    action items — e.g. "add tests to X" — instead of just a low axis score.

    Only covers axes with a single, unambiguous fix (tests/CI/Docker/README/commit cadence).
    project_experience and programming aren't included: their signals (repo count breadth,
    skill list) aren't something a single suggestion can meaningfully act on.
    """

    def __init__(
        self,
        thresholds: ImprovementSuggestionThresholds = DEFAULT_IMPROVEMENT_SUGGESTION_THRESHOLDS,
    ) -> None:
        self._thresholds = thresholds

    def suggest(self, evidences: list[RepositoryEvidence]) -> list[ImprovementSuggestion]:
        suggestions: list[ImprovementSuggestion] = []
        for evidence in evidences:
            suggestions.extend(self._suggest_for(evidence))
        return suggestions

    def _suggest_for(self, evidence: RepositoryEvidence) -> list[ImprovementSuggestion]:
        suggestions: list[ImprovementSuggestion] = []

        if not evidence.has_tests:
            suggestions.append(
                ImprovementSuggestion(
                    repo_name=evidence.repo_name,
                    axis="software_engineering",
                    message=(
                        f"{evidence.repo_name}에 테스트가 없습니다. 테스트를 추가하면 "
                        "Software Engineering 점수가 오릅니다."
                    ),
                )
            )

        if not evidence.has_ci:
            suggestions.append(
                ImprovementSuggestion(
                    repo_name=evidence.repo_name,
                    axis="software_engineering",
                    message=(
                        f"{evidence.repo_name}에 CI 워크플로우가 없습니다. GitHub Actions 등을 "
                        "추가하면 Software Engineering 점수가 오릅니다."
                    ),
                )
            )

        if not evidence.has_docker:
            suggestions.append(
                ImprovementSuggestion(
                    repo_name=evidence.repo_name,
                    axis="deployment_devops",
                    message=(
                        f"{evidence.repo_name}에 Dockerfile이 없습니다. 컨테이너화하면 "
                        "Deployment & DevOps 점수가 오릅니다."
                    ),
                )
            )

        if evidence.readme_quality_score < self._thresholds.readme_quality_score_threshold:
            suggestions.append(
                ImprovementSuggestion(
                    repo_name=evidence.repo_name,
                    axis="documentation",
                    message=(
                        f"{evidence.repo_name}의 README 품질이 낮습니다. 설치 방법과 사용 "
                        "예시를 추가하면 Documentation 점수가 오릅니다."
                    ),
                )
            )

        if evidence.commit_frequency < self._thresholds.commit_frequency_threshold:
            suggestions.append(
                ImprovementSuggestion(
                    repo_name=evidence.repo_name,
                    axis="activity",
                    message=(
                        f"{evidence.repo_name}의 커밋 빈도가 낮습니다. 꾸준히 커밋하면 "
                        "Activity 점수가 오릅니다."
                    ),
                )
            )

        return suggestions
