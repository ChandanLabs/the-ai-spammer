from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import NudgeLog
from ..schemas import NudgeLogOut

router = APIRouter(prefix="/api/logs", tags=["Nudge Logs"])


@router.get("", response_model=List[NudgeLogOut])
def list_logs(
    campaign_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(NudgeLog).options(joinedload(NudgeLog.student))
    if campaign_id is not None:
        q = q.filter(NudgeLog.campaign_id == campaign_id)
    if student_id is not None:
        q = q.filter(NudgeLog.student_id == student_id)
    if status:
        q = q.filter(NudgeLog.status == status)
    return q.order_by(NudgeLog.sent_at.desc()).offset(skip).limit(limit).all()
