"""
scheduler.py — APScheduler nudge loop
Runs every NUDGE_INTERVAL_MINUTES and sends level-appropriate
Telegram messages to unregistered students.
"""
import asyncio
import logging
import uuid
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.models import SessionLocal, Student, HiringDrive, NudgeLog, StudentStatus
from backend.services.nudge_engine import generate_nudge_message, get_nudge_level
from backend.config import settings

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler = None


def _send_telegram(chat_id: int, text: str):
    """Synchronous Telegram send using raw HTTP."""
    import httpx
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = httpx.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
        data = resp.json()
        if data.get("ok"):
            logger.info(f"✅ Nudge sent to chat_id={chat_id}")
            return True
        else:
            logger.warning(f"Telegram error: {data.get('description')}")
            return False
    except Exception as e:
        logger.error(f"Failed to send to {chat_id}: {e}")
        return False


def run_nudge_job():
    """
    Main nudge loop:
    1. Query PENDING students in active drives (deadline not passed)
    2. Determine nudge level based on nudge_count
    3. Generate AI message
    4. Send via Telegram
    5. Log result
    """
    logger.info("⏰ [Scheduler] Running nudge job...")
    db = SessionLocal()
    total_sent = total_failed = total_skipped = 0

    try:
        now = datetime.utcnow()
        active_drives = (
            db.query(HiringDrive)
            .filter(HiringDrive.is_active == True, HiringDrive.deadline > now)
            .all()
        )

        if not active_drives:
            logger.info("[Scheduler] No active drives.")
            return

        for drive in active_drives:
            students = (
                db.query(Student)
                .filter(
                    Student.drive_id == drive.id,
                    Student.status == StudentStatus.PENDING,
                    Student.telegram_chat_id != None,
                )
                .all()
            )

            logger.info(f"[Drive: {drive.company_name}] {len(students)} PENDING students to nudge")

            for student in students:
                level = get_nudge_level(student.nudge_count)
                status = "failed"
                error_msg = None
                message = "(generation failed)"

                try:
                    message = asyncio.run(
                        generate_nudge_message(
                            name=student.name,
                            roll_number=student.roll_number,
                            company_name=drive.company_name,
                            deadline=drive.deadline,
                            nudge_count=student.nudge_count,
                        )
                    )
                    logger.info(f"Nudge sent to {student.name} (Level {level})")
                    ok = _send_telegram(student.telegram_chat_id, message)
                    status = "sent" if ok else "failed"
                    if ok:
                        student.nudge_count += 1
                        student.last_nudge_sent_at = now
                        db.add(student)
                        total_sent += 1
                    else:
                        total_failed += 1
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error nudging {student.name}: {e}")
                    total_failed += 1

                log = NudgeLog(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    drive_id=drive.id,
                    message_sent=message,
                    nudge_level=level,
                    status=status,
                    error_message=error_msg,
                )
                db.add(log)

        db.commit()
        logger.info(f"[Scheduler] Done. Sent={total_sent}, Failed={total_failed}, Skipped={total_skipped}")

    except Exception as e:
        logger.error(f"Nudge job crash: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    minutes = settings.NUDGE_INTERVAL_MINUTES

    _scheduler.add_job(
        run_nudge_job,
        trigger=IntervalTrigger(minutes=minutes),
        id="nudge_job",
        name="Placement Nudge Job",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(f"📅 APScheduler started — nudge every {minutes} minute(s)")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
