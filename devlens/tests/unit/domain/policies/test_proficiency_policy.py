from devlens.config.proficiency_thresholds import ProficiencyThresholds
from devlens.domain.policies.proficiency_policy import ProficiencyPolicy


def test_below_intermediate_threshold_is_beginner() -> None:
    policy = ProficiencyPolicy()

    assert policy.evaluate(0) == "beginner"
    assert policy.evaluate(1) == "beginner"


def test_at_intermediate_threshold_is_intermediate() -> None:
    policy = ProficiencyPolicy()

    assert policy.evaluate(2) == "intermediate"
    assert policy.evaluate(3) == "intermediate"


def test_at_advanced_threshold_is_advanced() -> None:
    policy = ProficiencyPolicy()

    assert policy.evaluate(4) == "advanced"
    assert policy.evaluate(100) == "advanced"


def test_custom_thresholds_shift_the_boundaries() -> None:
    policy = ProficiencyPolicy(
        thresholds=ProficiencyThresholds(intermediate_min_repos=1, advanced_min_repos=2)
    )

    assert policy.evaluate(0) == "beginner"
    assert policy.evaluate(1) == "intermediate"
    assert policy.evaluate(2) == "advanced"
