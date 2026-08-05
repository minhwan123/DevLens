import asyncio
import sqlite3
from pathlib import Path

from devlens.domain.models.career_radar_profile import CareerRadarProfile
from devlens.domain.models.radar_snapshot import RadarSnapshot
from devlens.infrastructure.persistence.snapshot_repository import SnapshotRepository


class SqliteSnapshotRepository(SnapshotRepository):
    """Persists radar snapshots to a local SQLite file so score trends survive process
    restarts. Uses the stdlib sqlite3 driver (synchronous) via asyncio.to_thread rather than
    an async driver dependency — the same offload pattern EmbeddingSimilarityService.rank uses
    for its own blocking call.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS radar_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    career_goal TEXT NOT NULL,
                    radar_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_radar_snapshots_username "
                "ON radar_snapshots(username)"
            )
            conn.commit()
        finally:
            conn.close()

    async def save(self, username: str, snapshot: RadarSnapshot) -> None:
        await asyncio.to_thread(self._save_sync, username, snapshot)

    def _save_sync(self, username: str, snapshot: RadarSnapshot) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO radar_snapshots (username, created_at, career_goal, radar_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    username,
                    snapshot.created_at,
                    snapshot.career_goal,
                    snapshot.radar.model_dump_json(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    async def list_for_username(self, username: str) -> list[RadarSnapshot]:
        return await asyncio.to_thread(self._list_sync, username)

    def _list_sync(self, username: str) -> list[RadarSnapshot]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT created_at, career_goal, radar_json FROM radar_snapshots "
                "WHERE username = ? ORDER BY created_at ASC",
                (username,),
            ).fetchall()
        finally:
            conn.close()
        return [
            RadarSnapshot(
                created_at=row[0],
                career_goal=row[1],
                radar=CareerRadarProfile.model_validate_json(row[2]),
            )
            for row in rows
        ]
