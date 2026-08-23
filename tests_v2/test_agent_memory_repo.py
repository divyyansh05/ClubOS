from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.watchdog.memory_repo import AgentMemoryRepository, bootstrap_agent_memory_db, _now_utc
from clubos2.watchdog.memory_schema import AgentMemoryORM


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("dbs") / "test_agent_memory.duckdb"
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
    bootstrap_agent_memory_db(test_db_url)
    engine = db_mod.get_engine(test_db_url)
    monkeypatch_module.setattr(db_mod, "_default_engine", engine)
    monkeypatch_module.setattr(db_mod, "_SessionFactory", sessionmaker(bind=engine))


@pytest.fixture
def repo() -> AgentMemoryRepository:
    return AgentMemoryRepository()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_remember_and_has_recent_within_ttl(repo):
    """After remember(), has_recent() within the TTL window returns True."""
    agent = "watchdog"
    subject_key = f"metric_a::{uuid4().hex[:8]}::present_in_top_n"

    await repo.remember(
        agent_name=agent,
        memory_type="present_in_top_n",
        subject_key=subject_key,
        ttl=timedelta(days=7),
    )

    found = await repo.has_recent(
        agent_name=agent, subject_key=subject_key, within=timedelta(hours=1)
    )
    assert found is True


async def test_has_recent_different_agent_returns_false(repo):
    """has_recent() for a different agent_name with the same subject_key returns False."""
    subject_key = f"shared_subject::{uuid4().hex[:8]}"

    await repo.remember(
        agent_name="agent_alpha",
        memory_type="test_type",
        subject_key=subject_key,
    )

    found = await repo.has_recent(
        agent_name="agent_beta",
        subject_key=subject_key,
        within=timedelta(hours=1),
    )
    assert found is False


async def test_last_seen_returns_most_recent(repo):
    """last_seen() returns the most recently occurred memory for agent+subject."""
    agent = "watchdog"
    subject_key = f"multi_entry::{uuid4().hex[:8]}"

    # Insert two memories
    await repo.remember(agent_name=agent, memory_type="type_a", subject_key=subject_key)
    second = await repo.remember(agent_name=agent, memory_type="type_b", subject_key=subject_key)

    result = await repo.last_seen(agent_name=agent, subject_key=subject_key)

    assert result is not None
    assert result.memory_id == second.memory_id
    assert result.memory_type == "type_b"


async def test_purge_expired_removes_only_expired_records(repo, test_db_url):
    """purge_expired() deletes memories with expires_at in the past, not active ones."""
    agent = "cleanup_agent"
    subject_key_expired = f"expired_subject::{uuid4().hex[:8]}"
    subject_key_active = f"active_subject::{uuid4().hex[:8]}"

    # Create an active memory (long TTL)
    active = await repo.remember(
        agent_name=agent,
        memory_type="active_type",
        subject_key=subject_key_active,
        ttl=timedelta(days=30),
    )

    # Directly insert an expired memory by inserting into DB with past expires_at
    engine = db_mod.get_engine(test_db_url)
    factory = sessionmaker(bind=engine)
    past_expires = _now_utc() - timedelta(hours=1)
    expired_mem = AgentMemoryORM(
        memory_id=f"mem_{uuid4().hex[:16]}",
        agent_name=agent,
        memory_type="expired_type",
        subject_key=subject_key_expired,
        occurred_at=_now_utc() - timedelta(hours=2),
        expires_at=past_expires,
        created_at=_now_utc() - timedelta(hours=2),
    )
    with factory() as session:
        session.add(expired_mem)
        session.commit()

    # Purge
    deleted = await repo.purge_expired()
    assert deleted >= 1

    # Active record must still exist
    still_there = await repo.last_seen(agent_name=agent, subject_key=subject_key_active)
    assert still_there is not None
    assert still_there.memory_id == active.memory_id

    # Expired record must be gone
    gone = await repo.last_seen(agent_name=agent, subject_key=subject_key_expired)
    assert gone is None


async def test_count_within_returns_correct_count(repo):
    """count_within() counts active, non-expired memories in the time window."""
    agent = "count_agent"
    subject_key = f"countable::{uuid4().hex[:8]}"

    # Insert 3 memories
    for _ in range(3):
        await repo.remember(
            agent_name=agent,
            memory_type="countable_type",
            subject_key=subject_key,
            ttl=timedelta(days=1),
        )

    count = await repo.count_within(
        agent_name=agent, subject_key=subject_key, within=timedelta(hours=1)
    )
    assert count == 3


async def test_remember_top_n_presence_creates_entries(repo):
    """remember_top_n_presence() creates one entry per metric_name."""
    run_id = uuid4().hex
    metrics = [f"m_{uuid4().hex[:6]}" for _ in range(3)]

    await repo.remember_top_n_presence(metric_names=metrics, run_id=run_id)

    for metric in metrics:
        subject_key = f"{metric}::present_in_top_n"
        found = await repo.has_recent(
            agent_name="watchdog",
            subject_key=subject_key,
            within=timedelta(hours=1),
        )
        assert found is True, f"Expected to find memory for {subject_key}"
