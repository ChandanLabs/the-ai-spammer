from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Student, Campaign, NudgeLog
from ..schemas import DashboardStats

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Student.id)).scalar() or 0
    registered = db.query(func.count(Student.id)).filter(Student.is_registered == True).scalar() or 0
    with_telegram = db.query(func.count(Student.id)).filter(Student.telegram_id != None).scalar() or 0
    active_campaigns = db.query(func.count(Campaign.id)).filter(
        Campaign.is_active == True,
        Campaign.deadline > datetime.utcnow(),
    ).scalar() or 0
    nudges_today = db.query(func.count(NudgeLog.id)).filter(
        func.date(NudgeLog.sent_at) == date.today()
    ).scalar() or 0
    nudges_total = db.query(func.count(NudgeLog.id)).scalar() or 0

    return DashboardStats(
        total_students=total,
        registered=registered,
        unregistered=total - registered,
        with_telegram=with_telegram,
        active_campaigns=active_campaigns,
        nudges_sent_today=nudges_today,
        nudges_sent_total=nudges_total,
        registration_rate=round((registered / total * 100) if total > 0 else 0.0, 1),
    )
