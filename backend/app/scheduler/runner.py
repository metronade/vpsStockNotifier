"""APScheduler integration — one interval job per active provider.

Race-condition protection: each provider has its own job with max_instances=1
and coalesce=True. If a scan is still running when the next interval fires,
the new fire is skipped (not queued) — this is intentional, since queues can
grow unbounded if scans are slower than the interval.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.models.provider import Provider
from app.scheduler.orchestrator import scan_provider

_scheduler: AsyncIOScheduler | None = None


def _job_id(provider_id: int) -> str:
    return f"provider_scan_{provider_id}"


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


def schedule_provider(provider: Provider) -> None:
    sched = get_scheduler()
    if not provider.is_active:
        unschedule_provider(provider.id)
        return
    sched.add_job(
        scan_provider,
        trigger=IntervalTrigger(seconds=provider.scan_interval_seconds),
        id=_job_id(provider.id),
        args=[provider.id],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )


def unschedule_provider(provider_id: int) -> None:
    sched = get_scheduler()
    try:
        sched.remove_job(_job_id(provider_id))
    except Exception:
        pass  # job not present — nothing to do


def start_scheduler() -> None:
    sched = get_scheduler()
    if not sched.running:
        sched.start()
    db = SessionLocal()
    try:
        for provider in db.query(Provider).filter(Provider.is_active.is_(True)).all():
            schedule_provider(provider)
    finally:
        db.close()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
