import io
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime
from pydantic import BaseModel

from backend.models import get_db, HiringDrive, Student, NudgeLog, StudentStatus
from backend.routers.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class DriveCreate(BaseModel):
    company_name: str
    registration_link: Optional[str] = None
    deadline: datetime
    is_active: bool = True

class DriveOut(BaseModel):
    id: str
    company_name: str
    registration_link: Optional[str]
    deadline: datetime
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class StudentOut(BaseModel):
    id: str
    name: str
    roll_number: str
    email: Optional[str]
    branch: Optional[str]
    year: Optional[str]
    phone: Optional[str]
    telegram_chat_id: Optional[int]
    status: StudentStatus
    nudge_count: int
    last_nudge_sent_at: Optional[datetime]
    drive_id: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class StudentUpdate(BaseModel):
    status: Optional[StudentStatus] = None
    drive_id: Optional[str] = None

class DashboardStats(BaseModel):
    total_students: int
    registered: int
    pending: int
    blocked: int
    with_telegram: int
    active_drives: int
    nudges_today: int
    nudges_total: int
    registration_rate: float

class UploadResult(BaseModel):
    total_rows: int
    inserted: int
    updated: int
    skipped: int
    errors: List[str] = []

class NudgeLogOut(BaseModel):
    id: str
    student_id: str
    drive_id: str
    message_sent: str
    nudge_level: int
    sent_at: datetime
    status: str
    error_message: Optional[str]
    student: Optional[StudentOut] = None
    model_config = {"from_attributes": True}


# ─── Stats ───────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db), _: str = Depends(get_current_admin)):
    from datetime import date
    total = db.query(func.count(Student.id)).scalar() or 0
    registered = db.query(func.count(Student.id)).filter(Student.status == StudentStatus.REGISTERED).scalar() or 0
    pending = db.query(func.count(Student.id)).filter(Student.status == StudentStatus.PENDING).scalar() or 0
    blocked = db.query(func.count(Student.id)).filter(Student.status == StudentStatus.BLOCKED).scalar() or 0
    with_telegram = db.query(func.count(Student.id)).filter(Student.telegram_chat_id != None).scalar() or 0
    active_drives = db.query(func.count(HiringDrive.id)).filter(
        HiringDrive.is_active == True, HiringDrive.deadline > datetime.utcnow()
    ).scalar() or 0
    nudges_today = db.query(func.count(NudgeLog.id)).filter(
        func.date(NudgeLog.sent_at) == date.today()
    ).scalar() or 0
    nudges_total = db.query(func.count(NudgeLog.id)).scalar() or 0
    return DashboardStats(
        total_students=total,
        registered=registered,
        pending=pending,
        blocked=blocked,
        with_telegram=with_telegram,
        active_drives=active_drives,
        nudges_today=nudges_today,
        nudges_total=nudges_total,
        registration_rate=round((registered / total * 100) if total > 0 else 0.0, 1),
    )


# ─── Hiring Drives ───────────────────────────────────────────────────────────

@router.get("/drives", response_model=List[DriveOut])
def list_drives(db: Session = Depends(get_db), _: str = Depends(get_current_admin)):
    return db.query(HiringDrive).order_by(HiringDrive.created_at.desc()).all()


@router.post("/drives", response_model=DriveOut, status_code=201)
def create_drive(payload: DriveCreate, db: Session = Depends(get_db), _: str = Depends(get_current_admin)):
    import uuid
    drive = HiringDrive(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(drive)
    db.commit()
    db.refresh(drive)
    return drive


@router.patch("/drives/{drive_id}", response_model=DriveOut)
def update_drive(drive_id: str, payload: dict, db: Session = Depends(get_db), _: str = Depends(get_current_admin)):
    drive = db.query(HiringDrive).filter(HiringDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    for k, v in payload.items():
        setattr(drive, k, v)
    db.commit()
    db.refresh(drive)
    return drive


@router.delete("/drives/{drive_id}", status_code=204)
def delete_drive(drive_id: str, db: Session = Depends(get_db), _: str = Depends(get_current_admin)):
    drive = db.query(HiringDrive).filter(HiringDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    db.delete(drive)
    db.commit()


# ─── CSV Upload ───────────────────────────────────────────────────────────────

@router.post("/upload-csv", response_model=UploadResult)
async def upload_csv(
    file: UploadFile = File(...),
    drive_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files accepted")

    contents = await file.read()
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = contents.decode("latin-1")

    import csv
    import uuid as uuid_mod
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="Empty or malformed CSV")

    headers = {h.strip().lower() for h in reader.fieldnames}
    # Accept roll_no or roll_number
    has_roll = "roll_no" in headers or "roll_number" in headers
    if not ({"name"}.issubset(headers) and has_roll):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have 'name' and 'roll_no'/'roll_number' columns. Found: {headers}"
        )

    if drive_id:
        drive = db.query(HiringDrive).filter(HiringDrive.id == drive_id).first()
        if not drive:
            raise HTTPException(status_code=404, detail=f"Drive {drive_id} not found")

    inserted = updated = skipped = 0
    errors: List[str] = []

    for row_num, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items() if k}
        name = row.get("name", "")
        roll = row.get("roll_number") or row.get("roll_no", "")
        email = row.get("email", "") or None

        if not name or not roll:
            errors.append(f"Row {row_num}: Missing name or roll number")
            skipped += 1
            continue

        existing = db.query(Student).filter(Student.roll_number == roll).first()
        if existing:
            existing.name = name
            existing.email = email or existing.email
            existing.branch = row.get("branch") or existing.branch
            existing.year = row.get("year") or existing.year
            existing.phone = row.get("phone") or existing.phone
            if drive_id:
                existing.drive_id = drive_id
            db.add(existing)
            updated += 1
        else:
            student = Student(
                id=str(uuid_mod.uuid4()),
                name=name,
                roll_number=roll,
                email=email,
                branch=row.get("branch") or None,
                year=row.get("year") or None,
                phone=row.get("phone") or None,
                drive_id=drive_id,
            )
            db.add(student)
            inserted += 1

    db.commit()
    return UploadResult(
        total_rows=inserted + updated + skipped,
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        errors=errors,
    )


# ─── Students ────────────────────────────────────────────────────────────────

@router.get("/students", response_model=List[StudentOut])
def list_students(
    drive_id: Optional[str] = Query(None),
    status: Optional[StudentStatus] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    q = db.query(Student)
    if drive_id:
        q = q.filter(Student.drive_id == drive_id)
    if status:
        q = q.filter(Student.status == status)
    if search:
        t = f"%{search}%"
        q = q.filter(or_(Student.name.ilike(t), Student.roll_number.ilike(t), Student.email.ilike(t)))
    return q.order_by(Student.created_at.desc()).offset(skip).limit(limit).all()


@router.patch("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: str, payload: StudentUpdate, db: Session = Depends(get_db), _: str = Depends(get_current_admin)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(student, k, v)
    db.commit()
    db.refresh(student)
    return student


# ─── Logs ────────────────────────────────────────────────────────────────────

@router.get("/logs", response_model=List[NudgeLogOut])
def list_logs(
    drive_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    from sqlalchemy.orm import joinedload
    q = db.query(NudgeLog).options(joinedload(NudgeLog.student))
    if drive_id:
        q = q.filter(NudgeLog.drive_id == drive_id)
    if student_id:
        q = q.filter(NudgeLog.student_id == student_id)
    return q.order_by(NudgeLog.sent_at.desc()).limit(limit).all()


# ─── Manual Nudge Trigger ────────────────────────────────────────────────────

@router.post("/nudge/trigger")
def trigger_nudge(_: str = Depends(get_current_admin)):
    from backend.services.scheduler import run_nudge_job
    run_nudge_job()
    return {"status": "ok", "message": "Nudge job triggered"}
