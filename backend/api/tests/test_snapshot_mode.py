from fastapi.testclient import TestClient

from app.config.settings import settings
from app.main import app


def test_priorities_returns_503_when_snapshot_not_configured() -> None:
    original = settings.clubos_gold_snapshot_dir
    settings.clubos_gold_snapshot_dir = None
    client = TestClient(app)
    try:
        response = client.get("/priorities/latest")
    finally:
        settings.clubos_gold_snapshot_dir = original

    assert response.status_code == 503
    payload = response.json()
    assert payload["error_code"] == "snapshot_unavailable"
    assert "CLUBOS_GOLD_SNAPSHOT_DIR" in payload["message"]


def test_snapshot_backed_priorities_and_refresh(tmp_path) -> None:
    (tmp_path / "gold_priority_board.csv").write_text(
        "\n".join(
            [
                "month,priority_id,priority_title,priority_category,priority_score,priority_rank,asset_name,primary_metric,summary_text,why_it_matters,suggested_next_investigation,supporting_metrics_json",
                '2025-01-01,p1,Conversion Weakness In Ecommerce,conversion weakness,0.91,1,ecommerce,conversion_rate,"conversion_rate is down versus prior month with seasonal deviation -0.1000.","matters","investigate","{}"',
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "gold_kpi_health.csv").write_text(
        "\n".join(
            [
                "month,asset_name,metric_name,metric_value,prior_month_value,prior_season_same_month_value,rolling_12m_avg,seasonal_baseline,deviation_from_seasonal_baseline,trend_direction,health_status",
                "2025-01-01,ecommerce,conversion_rate,0.20,0.22,,0.21,0.21,-0.0476,down,stable",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "silver_data_quality_checks.csv").write_text(
        "\n".join(
            [
                "run_id,table_name,check_name,severity,status,issue_count,issue_details,run_timestamp",
                "run-1,clubos_silver.silver_internal_asset_metrics,No null months,REQUIRED,PASS,0,ok,2026-05-01T00:00:00+00:00",
            ]
        ),
        encoding="utf-8",
    )

    original = settings.clubos_gold_snapshot_dir
    settings.clubos_gold_snapshot_dir = str(tmp_path)
    client = TestClient(app)
    try:
        priorities = client.get("/priorities/latest")
        refresh = client.get("/refresh/status")
    finally:
        settings.clubos_gold_snapshot_dir = original

    assert priorities.status_code == 200
    p = priorities.json()
    assert p["latest_month"] == "2025-01-01"
    assert len(p["items"]) == 1
    assert p["items"][0]["priority_id"] == "p1"

    assert refresh.status_code == 200
    r = refresh.json()
    assert r["latest_gold_month"] == "2025-01-01"
    assert r["required_failed_checks_count"] == 0
