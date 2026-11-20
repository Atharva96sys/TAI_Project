import pytest
from backend.app.core.database import async_session_factory, init_db
from backend.app.services.evaluation.benchmark_suite import BenchmarkSuite
from backend.app.services.retrieval.engine import retrieval_engine


@pytest.mark.asyncio
async def test_evaluation_lab_10_point_benchmark():
    await init_db()
    async with async_session_factory() as session:
        # Sync retrieval index
        await retrieval_engine.sync_from_database(session)

        # Run 10-point benchmark
        run_res = await BenchmarkSuite.run_benchmark(session, run_name="PyTest Benchmark Run")

        assert run_res.total_cases == 10
        assert run_res.passed_cases >= 8  # Substantial pass rate across all 10 adversarial/clinical cases
        assert run_res.injection_detection_rate >= 90.0
        assert run_res.pii_recall >= 90.0
        assert run_res.mean_latency_ms > 0.0
