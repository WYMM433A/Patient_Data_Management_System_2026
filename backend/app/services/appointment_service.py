from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User
from app.schemas.appointments import AppointmentCreate, AppointmentUpdate

# Slot window: a doctor cannot have two appointments within 30 minutes of each other
_SLOT_MINUTES = 30


def _get_or_404(db: Session, appointment_id: UUID) -> Appointment:
    appt = db.query(Appointment).filter(
        Appointment.appointment_id == str(appointment_id)
    ).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appt


def _check_patient(db: Session, patient_id: UUID):
    if not db.query(Patient).filter(Patient.patient_id == str(patient_id)).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")


def _check_doctor(db: Session, doctor_id: UUID):
    if not db.query(User).filter(User.user_id == str(doctor_id), User.is_active == True).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found or inactive")


def _check_conflict(db: Session, doctor_id: UUID, scheduled_at: datetime, exclude_id: Optional[UUID] = None):
    """Raise 409 if doctor already has an active appointment within ±30 min of scheduled_at."""
    window_start = scheduled_at - timedelta(minutes=_SLOT_MINUTES)
    window_end   = scheduled_at + timedelta(minutes=_SLOT_MINUTES)

    q = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id    == str(doctor_id),
            Appointment.status.in_(["scheduled", "confirmed", "checked_in"]),
            Appointment.scheduled_at >  window_start,
            Appointment.scheduled_at <  window_end,
        )
    )
    if exclude_id:
        q = q.filter(Appointment.appointment_id != str(exclude_id))

    if q.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Doctor already has an appointment within {_SLOT_MINUTES} minutes of the requested time",
        )


# -------------------------------------------------------------------
# CRUD
# -------------------------------------------------------------------

def book_appointment(db: Session, payload: AppointmentCreate, created_by: UUID) -> Appointment:
    _check_patient(db, payload.patient_id)
    _check_doctor(db, payload.doctor_id)
    _check_conflict(db, payload.doctor_id, payload.scheduled_at)

    appt = Appointment(
        patient_id   = str(payload.patient_id),
        doctor_id    = str(payload.doctor_id),
        scheduled_at = payload.scheduled_at,
        reason       = payload.reason,
        notes        = payload.notes,
        status       = "scheduled",
        created_by   = str(created_by),
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def list_appointments(
    db: Session,
    patient_id: Optional[UUID] = None,
    doctor_id:  Optional[UUID] = None,
    date:       Optional[str]  = None,   # "YYYY-MM-DD"
    appt_status: Optional[str] = None,
    skip:  int = 0,
    limit: int = 50,
) -> List[Appointment]:
    q = db.query(Appointment)

    if patient_id:
        q = q.filter(Appointment.patient_id == str(patient_id))
    if doctor_id:
        q = q.filter(Appointment.doctor_id == str(doctor_id))
    if date:
        try:
            day = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date must be YYYY-MM-DD")
        day_end = day + timedelta(days=1)
        q = q.filter(Appointment.scheduled_at >= day, Appointment.scheduled_at < day_end)
    if appt_status:
        q = q.filter(Appointment.status == appt_status)

    return q.order_by(Appointment.scheduled_at).offset(skip).limit(limit).all()


def get_appointment(db: Session, appointment_id: UUID) -> Appointment:
    return _get_or_404(db, appointment_id)


def update_appointment(db: Session, appointment_id: UUID, payload: AppointmentUpdate) -> Appointment:
    appt = _get_or_404(db, appointment_id)

    if appt.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify a cancelled appointment")

    if payload.scheduled_at and payload.scheduled_at != appt.scheduled_at:
        _check_conflict(db, UUID(str(appt.doctor_id)), payload.scheduled_at, exclude_id=appointment_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appt, field, value)

    db.commit()
    db.refresh(appt)
    return appt


def cancel_appointment(db: Session, appointment_id: UUID) -> Appointment:
    appt = _get_or_404(db, appointment_id)

    if appt.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an appointment with status '{appt.status}'",
        )

    appt.status = "cancelled"
    db.commit()
    db.refresh(appt)
    return appt


def check_in(db: Session, appointment_id: UUID) -> Appointment:
    appt = _get_or_404(db, appointment_id)

    if appt.status not in ("scheduled", "confirmed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot check in an appointment with status '{appt.status}'",
        )

    appt.status     = "checked_in"
    appt.checked_at = datetime.utcnow()
    db.commit()
    db.refresh(appt)
    return appt
