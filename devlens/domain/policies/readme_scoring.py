def score_readme(length: int, has_headings: bool, length_target: int) -> float:
    """0..1 quality score from README length and heading structure.

    The length component saturates at `length_target` characters; a README with at least one
    markdown heading earns a flat structure bonus. Shared by RepositoryFilterPolicy (candidate
    scoring) and GithubAnalysisEngine (RepositoryEvidence.readme_quality_score).
    """
    length_score = min(length / length_target, 1.0) if length_target > 0 else 1.0
    structure_score = 1.0 if has_headings else 0.0
    return 0.7 * length_score + 0.3 * structure_score
