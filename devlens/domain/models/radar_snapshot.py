from pydantic import BaseModel

from devlens.domain.models.career_radar_profile import CareerRadarProfile


class RadarSnapshot(BaseModel):
    """A point-in-time CareerRadarProfile for a username, used to chart score trends across
    repeated analyses.

    Keyed by the raw GitHub username string, not an authenticated account — this app has no
    login system, so history is per-username: re-analyzing the same username, from anywhere,
    surfaces the same trend.
    """

    created_at: str
    career_goal: str
    radar: CareerRadarProfile
