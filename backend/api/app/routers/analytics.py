from fastapi import APIRouter, HTTPException
from app.services import seasonal_service

router = APIRouter()


@router.get("/{asset}/{metric}")
def get_seasonal_baseline(asset: str, metric: str):
    """
    Get full 12-month seasonal baseline for a metric.

    Returns dict with seasonal statistics for each calendar month (1-12).
    Used by frontend to draw seasonal bands on charts.
    """
    baseline = seasonal_service.compute_seasonal_baseline(asset, metric)

    if not baseline:
        raise HTTPException(
            status_code=404,
            detail=f"No seasonal baseline data found for {asset}/{metric}"
        )

    return {
        "asset": asset,
        "metric": metric,
        "baseline": baseline
    }
