from devlens.domain.models import CareerRadarProfile, RadarSnapshot
from devlens.infrastructure.persistence import InMemorySnapshotRepository

_A_RADAR = CareerRadarProfile(
    programming=50,
    project_experience=50,
    software_engineering=50,
    deployment_devops=50,
    documentation=50,
    activity=50,
)


def _make_snapshot(**overrides: object) -> RadarSnapshot:
    defaults: dict[str, object] = {
        "created_at": "2026-01-01T00:00:00+00:00",
        "career_goal": "Backend",
        "radar": _A_RADAR,
    }
    defaults.update(overrides)
    return RadarSnapshot(**defaults)


async def test_list_for_unknown_username_returns_empty() -> None:
    repo = InMemorySnapshotRepository()

    assert await repo.list_for_username("nobody") == []


async def test_save_then_list_returns_the_snapshot() -> None:
    repo = InMemorySnapshotRepository()
    snapshot = _make_snapshot()

    await repo.save("octocat", snapshot)

    assert await repo.list_for_username("octocat") == [snapshot]


async def test_multiple_saves_accumulate_in_order() -> None:
    repo = InMemorySnapshotRepository()
    first = _make_snapshot(created_at="2026-01-01T00:00:00+00:00")
    second = _make_snapshot(created_at="2026-01-02T00:00:00+00:00")

    await repo.save("octocat", first)
    await repo.save("octocat", second)

    assert await repo.list_for_username("octocat") == [first, second]


async def test_different_usernames_are_isolated() -> None:
    repo = InMemorySnapshotRepository()
    await repo.save("octocat", _make_snapshot())

    assert await repo.list_for_username("someone-else") == []
