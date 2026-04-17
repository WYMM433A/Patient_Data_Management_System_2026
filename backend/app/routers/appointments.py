from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.appointments import AppointmentCreate, AppointmentUpdate, AppointmentOut
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("book_appointment")),
):
    return appointment_service.book_appointment(db, payload, current_user.user_id)


@router.get("", response_model=List[AppointmentOut])
def list_appointments(
    patient_id:  Optional[UUID] = None,
    doctor_id:   Optional[UUID] = None,
    date:        Optional[str]  = None,
    appt_status: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("book_appointment")),
):
    return appointment_service.list_appointments(db, patient_id, doctor_id, date, appt_status, skip, limit)


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("book_appointment")),
):
    return appointment_service.get_appointment(db, appointment_id)


@router.patch("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: UUID,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("cancel_appointment")),
):
    return appointment_service.update_appointment(db, appointment_id, payload)


@router.delete("/{appointment_id}", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("cancel_appointment")),
):
    return appointment_service.cancel_appointment(db, appointment_id)


@router.post("/{appointment_id}/check-in", response_model=AppointmentOut)
def check_in(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("book_appointment")),
):
    return appointment_service.check_in(db, appointment_id)
