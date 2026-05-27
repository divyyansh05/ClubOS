from fastapi.testclient import TestClient

from app.main import app
from app.services import priority_service

client = TestClient(app)


def _get_any_priority_id() -> str:
    response = client.get("/priorities/latest")
    assert response.status_code == 200
    items = response.json().get("items", [])
    assert items, "Expected at least one priority in snapshot data"
    return items[0]["priority_id"]


def test_priority_detail_peer_values_include_is_estimated_flag() -> None:
    priority_id = _get_any_priority_id()
    response = client.get(f"/priorities/{priority_id}")
    assert response.status_code == 200
    payload = response.json()

    peer_values = payload.get("peer_values") or []
    if not peer_values:
        return

    assert all("is_estimated" in row for row in peer_values)
    # Real Madrid row should be explicitly non-estimated.
    rm_rows = [row for row in peer_values if row.get("club") == "Real Madrid"]
    if rm_rows:
        assert rm_rows[0]["is_estimated"] is False


def test_priority_detail_handles_anomaly_context_failure_gracefully(monkeypatch) -> None:
    priority_id = _get_any_priority_id()

    def _boom(*args, **kwargs):
        raise RuntimeError("forced anomaly classifier failure")

    monkeypatch.setattr(priority_service.anomaly_context_service, "classify_metric_movement", _boom)

    response = client.get(f"/priorities/{priority_id}")
    assert response.status_code == 200
    payload = response.json()

    # Fallback should preserve API availability and return safe default context.
    anomaly_context = payload.get("anomaly_context")
    assert isinstance(anomaly_context, dict)
    assert anomaly_context.get("context_type") == "unexplained"


def test_priority_response_keeps_legacy_contract_fields() -> None:
    response = client.get("/priorities/latest")
    assert response.status_code == 200
    payload = response.json()
    items = payload.get("items", [])
    assert isinstance(items, list)
    if not items:
        return

    item = items[0]
    # Guard against accidental contract regressions while adding enriched fields.
    for field in [
        "priority_id",
        "month",
        "title",
        "category",
        "score",
        "rank",
        "asset_name",
        "primary_metric",
        "summary_text",
        "why_it_matters",
        "suggested_next_investigation",
    ]:
        assert field in item
