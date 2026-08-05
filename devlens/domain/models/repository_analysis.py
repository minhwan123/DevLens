from pydantic import BaseModel

from devlens.domain.models.repository_candidate import RepositoryCandidate
from devlens.domain.models.repository_evidence import RepositoryEvidence


class RepositoryAnalysis(BaseModel):
    """Everything GithubAnalysisEngine can derive from raw GitHub data for one repository.

    `candidate` feeds RepositoryFilterPolicy; combined with the filter's resulting quality_score,
    the remaining fields are enough to build the final RepositoryEvidence via `to_evidence`.
    """

    candidate: RepositoryCandidate
    tech_stack: list[str]
    has_tests: bool
    has_ci: bool
    has_docker: bool
    commit_frequency: float
    readme_quality_score: float
    domain_tags: list[str]

    def to_evidence(self, quality_score: float) -> RepositoryEvidence:
        return RepositoryEvidence(
            repo_name=self.candidate.repo_name,
            tech_stack=self.tech_stack,
            has_tests=self.has_tests,
            has_ci=self.has_ci,
            has_docker=self.has_docker,
            commit_frequency=self.commit_frequency,
            quality_score=quality_score,
            readme_quality_score=self.readme_quality_score,
            domain_tags=self.domain_tags,
        )
