#!/usr/bin/env python3
"""
Scheduled monthly briefing runner. Invoked by cron on the 1st of each month.
Runs the briefing for the PREVIOUS complete calendar month.

Example crontab:
  0 6 1 * * cd /path/to/clubos && python scripts/scheduled_monthly_briefing.py

Idempotent: repeated runs on the same month return the cached briefing without
regenerating.

Exit codes:
  0 — success (either newly generated or returned from cache)
  1 — briefing generation failed
"""
import asyncio
import logging
import sys
from calendar import monthrange
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> int:
    from clubos2.briefer.orchestrator import run_briefing
    from clubos2.briefer.agent_schemas import BriefingInput, BriefingType

    # Compute last complete calendar month
    now = datetime.utcnow()
    first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_of_prev = first_of_this - timedelta(seconds=1)
    year, month = last_of_prev.year, last_of_prev.month
    last_day = monthrange(year, month)[1]

    year_month = f"{year:04d}-{month:02d}"
    scope_key = f"monthly:{year_month}"

    logger.info(f"Running scheduled monthly briefing for {year_month} (scope: {scope_key})")

    briefing_input = BriefingInput(
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key=scope_key,
        period_start=datetime(year, month, 1),
        period_end=datetime(year, month, last_day, 23, 59, 59),
        triggered_by="scheduled_cron",
        freshness_days=7,
    )

    result = await run_briefing(briefing_input)

    if result.status == "cached":
        logger.info(f"Briefing already generated (cached): {result.briefing_id}")
        return 0
    if result.status == "completed":
        logger.info(
            f"Briefing generated: {result.briefing_id} "
            f"(latency: {result.latency_seconds:.1f}s)"
        )
        return 0

    logger.error(f"Briefing failed: {result.error}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
