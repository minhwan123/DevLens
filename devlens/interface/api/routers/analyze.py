import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response

from devlens.application.generate_career_report import GenerateCareerReportUseCase
from devlens.application.jobs import Job
from devlens.infrastructure.persistence.job_repository import JobRepository
from devlens.infrastructure.reporting import build_pdf_report
from devlens.interface.api.dependencies import (
    get_generate_career_report_use_case,
    get_job_repository,
)
from devlens.interface.api.schemas import (
    AnalyzeJobCreatedResponse,
    AnalyzeRequest,
    JobResultResponse,
    JobStatusResponse,
)

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("", response_model=AnalyzeJobCreatedResponse, status_code=202)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    use_case: Annotated[
        GenerateCareerReportUseCase, Depends(get_generate_career_report_use_case)
    ],
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
) -> AnalyzeJobCreatedResponse:
    job_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    job = Job(
        job_id=job_id,
        status="pending",
        username=request.username,
        career_goal=request.career_goal,
        created_at=now,
        updated_at=now,
    )
    await job_repository.save(job)

    background_tasks.add_task(
        _run_job, job_id, request.username, request.career_goal, use_case, job_repository
    )
    return AnalyzeJobCreatedResponse(job_id=job_id, status="pending")


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_analysis_status(
    job_id: str,
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
) -> JobStatusResponse:
    job = await job_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result = None
    if job.result is not None:
        result = JobResultResponse(
            profile=job.result.profile,
            filter_results=job.result.filter_results,
            partial=job.result.partial,
            radar=job.result.radar,
            recommendations=job.result.recommendations.recommendations,
            suggestions=job.result.suggestions,
            role_fit=job.result.role_fit,
            history=job.result.history,
            roadmap=job.result.recommendations.roadmap,
            strengths=job.result.strengths,
            growth_areas=job.result.growth_areas,
            ai_commentary=job.result.ai_commentary,
        )
    return JobStatusResponse(job_id=job.job_id, status=job.status, result=result, error=job.error)


@router.get("/{job_id}/report.pdf")
async def get_analysis_report_pdf(
    job_id: str,
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
) -> Response:
    job = await job_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or job.result is None:
        raise HTTPException(status_code=409, detail=f"Job is not completed (status={job.status})")

    pdf_bytes = build_pdf_report(job.result, job.username, job.career_goal)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="devlens-report-{job_id}.pdf"'},
    )


async def _run_job(
    job_id: str,
    username: str,
    career_goal: str,
    use_case: GenerateCareerReportUseCase,
    job_repository: JobRepository,
) -> None:
    job = await job_repository.get(job_id)
    if job is None:
        return

    job.status = "running"
    job.updated_at = datetime.now(UTC)
    await job_repository.save(job)

    try:
        result = await use_case.execute(username, career_goal)
    except Exception as exc:
        # A background task's exceptions are otherwise swallowed by Starlette and never
        # surface to the client — recording them on the job is the only way to report failure.
        job.status = "failed"
        job.error = str(exc)
        job.updated_at = datetime.now(UTC)
        await job_repository.save(job)
        return

    job.status = "completed"
    job.result = result
    job.updated_at = datetime.now(UTC)
    await job_repository.save(job)
