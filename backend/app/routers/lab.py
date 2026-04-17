from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.lab import (
    LabOrderCreate, LabOrderOut, LabOrderStatusUpdate,
    LabResultBulkCreate, LabResultOut,
    LabTestTemplateOut, LabTestTemplateDetailOut,
)
from app.services import lab_service

router = APIRouter(tags=["Lab"])


# ---------------------------------------------------------------------------
# Templates (read-only catalogue)
# ---------------------------------------------------------------------------

@router.get("/lab/templates", response_model=List[LabTestTemplateOut])
def list_templates(
    active_only: bool = True,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_lab_orders")),
):
    return lab_service.list_templates(db, active_only)


@router.get("/lab/templates/{template_id}", response_model=LabTestTemplateDetailOut)
def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_lab_orders")),
):
    return lab_service.get_template(db, template_id)


# ---------------------------------------------------------------------------
# Lab Orders — scoped under encounter
# ---------------------------------------------------------------------------

@router.post(
    "/encounters/{encounter_id}/lab-orders",
    response_model=LabOrderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    encounter_id: UUID,
    payload: LabOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("order_lab_test")),
):
    return lab_service.create_order(db, encounter_id, payload, current_user.user_id)


@router.get("/encounters/{encounter_id}/lab-orders", response_model=List[LabOrderOut])
def list_orders_by_encounter(
    encounter_id: UUID,
    order_status: Optional[str] = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_lab_orders")),
):
    return lab_service.list_orders(db, encounter_id=encounter_id, order_status=order_status, skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# Lab Orders — global (filter by patient / status)
# ---------------------------------------------------------------------------

@router.get("/lab-orders", response_model=List[LabOrderOut])
def list_orders(
    patient_id:   Optional[UUID] = None,
    order_status: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_lab_orders")),
):
    return lab_service.list_orders(db, patient_id=patient_id, order_status=order_status, skip=skip, limit=limit)


@router.get("/lab-orders/{order_id}", response_model=LabOrderOut)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_lab_orders")),
):
    return lab_service.get_order(db, order_id)


@router.patch("/lab-orders/{order_id}/status", response_model=LabOrderOut)
def update_order_status(
    order_id: UUID,
    payload: LabOrderStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("upload_lab_result")),
):
    return lab_service.update_order_status(db, order_id, payload)


# ---------------------------------------------------------------------------
# Lab Results — scoped under order
# ---------------------------------------------------------------------------

@router.post(
    "/lab-orders/{order_id}/results",
    response_model=List[LabResultOut],
    status_code=status.HTTP_201_CREATED,
)
def submit_results(
    order_id: UUID,
    payload: LabResultBulkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("upload_lab_result")),
):
    return lab_service.submit_results(db, order_id, payload.results, current_user.user_id)


@router.get("/lab-orders/{order_id}/results", response_model=List[LabResultOut])
def list_results(
    order_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_lab_results")),
):
    return lab_service.list_results(db, order_id)
