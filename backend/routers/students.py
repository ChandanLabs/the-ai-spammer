import io
import csv
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import Student, Campaign
from ..schemas import StudentOut, StudentCreate, StudentUpdate, UploadResult

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=List[StudentOut])
def list_students(
    campaign_id: Optional[int] = Query(None),
    is_registered: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Student)
    if campaign_id is not None:
        q = q.filter(Student.campaign_id == campaign_id)
    if is_registered is not None:
        q = q.filter(Student.is_registered == is_registered)
    if search:
        term = f"%{search}%"
        q = q.filter(
            or_(
                Student.name.ilike(term),
                Student.email.ilike(term),
                Student.roll_no.ilike(term),
            )
        )
    return q.order_by(Student.id.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=StudentOut, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.roll_no == payload.roll_no).first()
    if existing:
        raise HTTPException(status_code=409, detail="Student with this roll_no already exists")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()


@router.post("/upload/csv", response_model=UploadResult)
async def upload_csv(
    file: UploadFile = File(...),
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    try:
        text = contents.decode("utf-8-sig")  # handle BOM
    except UnicodeDecodeError:
        text = contents.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    
    # Normalize headers
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV file is empty or malformed")

    headers = [h.strip().lower() for h in reader.fieldnames]
    required = {"name", "email", "roll_no"}
    if not required.issubset(set(headers)):
        missing = required - set(headers)
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(missing)}. Found: {', '.join(headers)}"
        )

    inserted = updated = skipped = 0
    errors: List[str] = []

    # Validate campaign exists if provided
    if campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    for row_num, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        
        name = row.get("name", "").strip()
        email = row.get("email", "").strip()
        roll_no = row.get("roll_no", "").strip()

        if not name or not email or not roll_no:
            errors.append(f"Row {row_num}: Missing required fields (name/email/roll_no)")
            skipped += 1
            continue

        existing = db.query(Student).filter(Student.roll_no == roll_no).first()
        if existing:
            # Update non-sensitive fields
            existing.name = name
            existing.email = email
            existing.branch = row.get("branch") or existing.branch
            existing.year = row.get("year") or existing.year
            existing.phone = row.get("phone") or existing.phone
            if campaign_id:
                existing.campaign_id = campaign_id
            db.add(existing)
            updated += 1
        else:
            student = Student(
                name=name,
                email=email,
                roll_no=roll_no,
                branch=row.get("branch") or None,
                year=row.get("year") or None,
                phone=row.get("phone") or None,
                campaign_id=campaign_id,
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
