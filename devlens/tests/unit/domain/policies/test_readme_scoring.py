import pytest

from devlens.domain.policies.readme_scoring import score_readme


def test_full_length_and_headings_saturates_at_one() -> None:
    assert score_readme(length=1000, has_headings=True, length_target=500) == pytest.approx(1.0)


def test_empty_readme_scores_zero() -> None:
    assert score_readme(length=0, has_headings=False, length_target=500) == pytest.approx(0.0)


def test_headings_contribute_the_structure_bonus() -> None:
    without_headings = score_readme(length=0, has_headings=False, length_target=500)
    with_headings = score_readme(length=0, has_headings=True, length_target=500)

    assert with_headings - without_headings == pytest.approx(0.3)


def test_zero_length_target_treats_length_as_saturated() -> None:
    assert score_readme(length=0, has_headings=False, length_target=0) == pytest.approx(0.7)
