from pydantic import BaseModel


class ImprovementSuggestion(BaseModel):
    """A concrete, per-repository action item tied to one CareerRadarProfile axis —
    e.g. "add tests to X" instead of just a low software_engineering score."""

    repo_name: str
    axis: str
    message: str
