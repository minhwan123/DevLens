from pathlib import Path

from devlens.domain.models import CareerRadarProfile, RadarSnapshot
from devlens.infrastructure.persistence import SqliteSnapshotRepository

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


def test_the_db_file_and_parent_directory_are_created_automatically(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "snapshots.db"

    SqliteSnapshotRepository(str(db_path))

    assert db_path.exists()


async def test_save_then_list_returns_the_snapshot(tmp_path: Path) -> None:
    repo = SqliteSnapshotRepository(str(tmp_path / "snapshots.db"))
    snapshot = _make_snapshot()

    await repo.save("octocat", snapshot)

    assert await repo.list_for_username("octocat") == [snapshot]


async def test_multiple_saves_are_returned_oldest_first(tmp_path: Path) -> None:
    repo = SqliteSnapshotRepository(str(tmp_path / "snapshots.db"))
    first = _make_snapshot(created_at="2026-01-01T00:00:00+00:00")
    second = _make_snapshot(created_at="2026-01-02T00:00:00+00:00")

    await repo.save("octocat", second)
    await repo.save("octocat", first)

    assert await repo.list_for_username("octocat") == [first, second]


async def test_different_usernames_are_isolated(tmp_path: Path) -> None:
    repo = SqliteSnapshotRepository(str(tmp_path / "snapshots.db"))
    await repo.save("octocat", _make_snapshot())

    assert await repo.list_for_username("someone-else") == []


async def test_data_survives_a_new_repository_instance_against_the_same_file(
    tmp_path: Path,
) -> None:
    db_path = str(tmp_path / "snapshots.db")
    await SqliteSnapshotRepository(db_path).save("octocat", _make_snapshot())

    reopened = SqliteSnapshotRepository(db_path)

    assert await reopened.list_for_username("octocat") == [_make_snapshot()]
