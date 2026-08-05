from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from devlens.application.generate_career_report import GenerateCareerReportResult

JobStatus = Literal["pending", "running", "completed", "failed"]


@dataclass
class Job:
    """Async job state for one POST /analyze run. See infrastructure/persistence for storage.

    Deliberately a plain (mutable) dataclass, not a pydantic schema: it is internal
    bookkeeping, never serialized directly — interface/api maps it into response schemas.
    """

    job_id: str
    status: JobStatus
    username: str
    career_goal: str
    created_at: datetime
    updated_at: datetime
    result: GenerateCareerReportResult | None = None
    error: str | None = None
