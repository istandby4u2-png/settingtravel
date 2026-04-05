"""내장 스케줄러 – 매일 자동으로 브런치·네이버 글을 아카이브합니다.

env  AUTO_ARCHIVE_HOUR  (기본 3)  한국시간(KST) 기준 실행 시각
env  AUTO_ARCHIVE_ENABLED  (기본 true)  "false"로 끄기
"""

import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

log = logging.getLogger("scheduler")

_scheduler: AsyncIOScheduler | None = None


def _is_enabled() -> bool:
    return os.getenv("AUTO_ARCHIVE_ENABLED", "true").lower() not in ("0", "false", "no")


async def _archive_job() -> None:
    from routers.scrape import _begin_scrape_job

    result = _begin_scrape_job()
    started = result.get("started", False)
    log.info("Scheduled archive triggered – started=%s  msg=%s", started, result.get("message"))


def start_scheduler() -> None:
    global _scheduler
    if not _is_enabled():
        log.info("AUTO_ARCHIVE_ENABLED is off; scheduler will not start.")
        return

    hour = int(os.getenv("AUTO_ARCHIVE_HOUR", "3"))

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _archive_job,
        CronTrigger(hour=hour, minute=0, timezone="Asia/Seoul"),
        id="blog_archive",
        replace_existing=True,
    )
    _scheduler.start()
    log.info("Blog archive scheduler started – runs daily at %02d:00 KST", hour)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("Blog archive scheduler stopped.")
