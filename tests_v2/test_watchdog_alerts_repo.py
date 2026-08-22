from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.watchdog.alerts_repo import AlertsRepository, bootstrap_watchdog_alerts_db
from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType, WatchdogAlertCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_alert(
    run_id: str,
    metric_name: str = "total_revenue",
    severity: AlertSeverity = AlertSeverity.WARNING,
    alert_type: AlertType = AlertType.NEW_IN_TOP_N,
) -> WatchdogAlertCreate:
    return WatchdogAlertCreate(
        alert_id=f"alert_{uuid4().hex[:16]}",
        metric_name=metric_name,
        alert_type=alert_type,
        severity=severity,
        current_rank=1,
        previous_rank=5,
        rank_delta=-4,
        score_current=0.95,
        score_previous=0.60,
        triggered_by_rule="top_n_entry",
        context_snapshot='{"top_n": 5}',
        source="test_suite",
        run_id=run_id,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("dbs") / "test_watchdog_alerts.duckdb"
    return f"duckdb:///{db_file}"


@pytest.fixture(scope="module")
def monkeypatch_module():
    """A module-scoped monkeypatch fixture."""
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="module", autouse=True)
def setup_test_db(test_db_url, monkeypatch_module):
    """Bootstrap the test DB and redirect the module-level session factory."""
    bootstrap_watchdog_alerts_db(test_db_url)
    engine = db_mod.get_engine(test_db_url)
    monkeypatch_module.setattr(db_mod, "_default_engine", engine)
    monkeypatch_module.setattr(db_mod, "_SessionFactory", sessionmaker(bind=engine))


@pytest.fixture
def repo() -> AlertsRepository:
    return AlertsRepository()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_create_single_alert(repo):
    """create() returns a WatchdogAlertRead with alert_id and created_at set."""
    from datetime import datetime

    run_id = uuid4().hex
    alert_in = _make_alert(run_id=run_id)

    result = await repo.create(alert_in)

    assert result.alert_id == alert_in.alert_id
    assert result.created_at is not None
    assert isinstance(result.created_at, datetime)
    assert result.run_id == run_id
    assert result.metric_name == "total_revenue"


async def test_create_batch_returns_five(repo):
    """create_batch() with 5 alerts sharing a run_id returns 5 results."""
    run_id = uuid4().hex
    alerts_in = [_make_alert(run_id=run_id, metric_name=f"metric_{i}") for i in range(5)]

    results = await repo.create_batch(alerts_in)

    assert len(results) == 5
    for r in results:
        assert r.run_id == run_id
        assert r.created_at is not None


async def test_list_recent_metric_name_filter(repo):
    """list_recent() with metric_name filter returns only matching alerts."""
    run_id = uuid4().hex
    target_metric = f"unique_metric_{uuid4().hex[:8]}"
    other_metric = f"other_metric_{uuid4().hex[:8]}"

    alerts_in = [
        _make_alert(run_id=run_id, metric_name=target_metric),
        _make_alert(run_id=run_id, metric_name=target_metric),
        _make_alert(run_id=run_id, metric_name=other_metric),
    ]
    await repo.create_batch(alerts_in)

    results = await repo.list_recent(limit=100, metric_name=target_metric)

    assert all(r.metric_name == target_metric for r in results)
    assert len(results) >= 2


async def test_acknowledge_sets_fields(repo):
    """acknowledge() sets acknowledged_at and acknowledged_by on the alert."""
    from datetime import datetime

    run_id = uuid4().hex
    alert_in = _make_alert(run_id=run_id)

    # Create first
    created = await repo.create(alert_in)
    assert created.acknowledged_at is None
    assert created.acknowledged_by is None

    # Acknowledge
    acked = await repo.acknowledge(created.alert_id, by_user="test_user")

    assert acked.acknowledged_at is not None
    assert isinstance(acked.acknowledged_at, datetime)
    assert acked.acknowledged_by == "test_user"


async def test_get_by_run_returns_correct_subset(repo):
    """get_by_run() returns only alerts for the specified run_id."""
    run_id_a = uuid4().hex
    run_id_b = uuid4().hex

    alerts_a = [_make_alert(run_id=run_id_a, metric_name=f"m_{i}") for i in range(3)]
    alerts_b = [_make_alert(run_id=run_id_b, metric_name=f"m_{i}") for i in range(2)]

    await repo.create_batch(alerts_a)
    await repo.create_batch(alerts_b)

    results_a = await repo.get_by_run(run_id_a)
    results_b = await repo.get_by_run(run_id_b)

    assert len(results_a) == 3
    assert len(results_b) == 2
    assert all(r.run_id == run_id_a for r in results_a)
    assert all(r.run_id == run_id_b for r in results_b)


async def test_create_batch_empty_returns_empty(repo):
    """create_batch([]) returns an empty list without error."""
    result = await repo.create_batch([])
    assert result == []
