from fastapi import APIRouter

from app.schemas.benchmark import BenchmarkResponse
from app.services.benchmark_service import get_benchmark_view

router = APIRouter()


@router.get("/{asset}/{metric}", response_model=BenchmarkResponse)
def benchmark_view(asset: str, metric: str) -> BenchmarkResponse:
    return BenchmarkResponse(**get_benchmark_view(asset, metric))
