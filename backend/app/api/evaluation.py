from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.evaluation import EvaluationRun
from backend.app.schemas.evaluation import EvaluationRunRead, TriggerBenchmarkRequest
from backend.app.services.evaluation.benchmark_suite import BenchmarkSuite

router = APIRouter(prefix="/evaluation", tags=["Evaluation Lab"])


@router.post("/run", response_model=EvaluationRunRead, summary="Trigger automated 10-point benchmark evaluation suite")
async def trigger_benchmark_run(
    req: TriggerBenchmarkRequest = TriggerBenchmarkRequest(),
    db: AsyncSession = Depends(get_db),
):
    run_obj = await BenchmarkSuite.run_benchmark(session=db, run_name=req.run_name)
    # Reload with case_results eagerly loaded
    stmt = (
        select(EvaluationRun)
        .where(EvaluationRun.id == run_obj.id)
        .options(selectinload(EvaluationRun.case_results))
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.get("/runs", response_model=list[EvaluationRunRead], summary="List historical benchmark evaluation runs")
async def get_evaluation_runs(limit: int = 10, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(EvaluationRun)
        .order_by(desc(EvaluationRun.created_at))
        .limit(limit)
        .options(selectinload(EvaluationRun.case_results))
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/runs/{run_id}", response_model=EvaluationRunRead, summary="Get details of a specific evaluation run")
async def get_evaluation_run_detail(run_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(EvaluationRun)
        .where(EvaluationRun.id == run_id)
        .options(selectinload(EvaluationRun.case_results))
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")
    return item
