import pytest

from devlens.domain.policies.scoring_utils import clamped_ratio


def test_ratio_below_target_is_proportional() -> None:
    assert clamped_ratio(5, 10) == pytest.approx(0.5)


def test_ratio_at_or_above_target_is_clamped_to_one() -> None:
    assert clamped_ratio(10, 10) == pytest.approx(1.0)
    assert clamped_ratio(20, 10) == pytest.approx(1.0)


def test_non_positive_target_is_treated_as_already_saturated() -> None:
    assert clamped_ratio(0, 0) == pytest.approx(1.0)
    assert clamped_ratio(5, -1) == pytest.approx(1.0)
