import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class StudentStatus(str, enum.Enum):
    PENDING = "PENDING"
    REGISTERED = "REGISTERED"
    BLOCKED = "BLOCKED"


class HiringDrive(Base):
    __tablename__ = "hiring_drives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    students: Mapped[list["Student"]] = relationship("Student", back_populates="drive")
    nudge_logs: Mapped[list["NudgeLog"]] = relationship("NudgeLog", back_populates="drive")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    drive_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("hiring_drives.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    telegram_chat_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus, native_enum=False, create_constraint=False),
        default=StudentStatus.PENDING,
        nullable=False,
    )
    last_nudge_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    nudge_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    drive: Mapped[Optional["HiringDrive"]] = relationship("HiringDrive", back_populates="students")
    nudge_logs: Mapped[list["NudgeLog"]] = relationship("NudgeLog", back_populates="student")


class NudgeLog(Base):
    __tablename__ = "nudge_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    drive_id: Mapped[str] = mapped_column(String(36), ForeignKey("hiring_drives.id"), nullable=False)
    message_sent: Mapped[str] = mapped_column(Text, nullable=False)
    nudge_level: Mapped[int] = mapped_column(Integer, default=1)  # 1=polite, 2=urgent, 3=fomo
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    status: Mapped[str] = mapped_column(String(20), default="sent")  # sent | failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="nudge_logs")
    drive: Mapped["HiringDrive"] = relationship("HiringDrive", back_populates="nudge_logs")
