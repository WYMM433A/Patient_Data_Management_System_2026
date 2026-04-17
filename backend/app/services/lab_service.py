from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.lab import LabTestTemplate, LabTestParameter, LabOrder, LabResult
from app.models.encounter import Encounter
from app.schemas.lab import LabOrderCreate, LabOrderStatusUpdate, LabResultCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_order_or_404(db: Session, order_id: UUID) -> LabOrder:
    order = db.query(LabOrder).filter(LabOrder.order_id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")
    return order


def _get_encounter_or_404(db: Session, encounter_id: UUID) -> Encounter:
    enc = db.query(Encounter).filter(Encounter.encounter_id == str(encounter_id)).first()
    if not enc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    return enc


def _classify_abnormal(value_str: str, param: Optional[LabTestParameter]):
    """
    Returns (is_abnormal, abnormal_level) by comparing result_value against
    normal_range_min / normal_range_max on the parameter definition.
    Falls back to (False, None) for text/positive_negative types or missing param.
    """
    if param is None or param.value_type != "numeric":
        return False, None
    try:
        val = float(value_str)
    except (ValueError, TypeError):
        return False, None

    lo  = float(param.normal_range_min) if param.normal_range_min is not None else None
    hi  = float(param.normal_range_max) if param.normal_range_max is not None else None

    if lo is not None and val < lo:
        level = "critical" if val < lo * 0.7 else "low"
        return True, level
    if hi is not None and val > hi:
        level = "critical" if val > hi * 1.3 else "high"
        return True, level
    return False, None


# ---------------------------------------------------------------------------
# Templates (read-only)
# ---------------------------------------------------------------------------

def list_templates(db: Session, active_only: bool = True) -> List[LabTestTemplate]:
    q = db.query(LabTestTemplate)
    if active_only:
        q = q.filter(LabTestTemplate.is_active == True)
    return q.order_by(LabTestTemplate.test_category, LabTestTemplate.test_name).all()


def get_template(db: Session, template_id: UUID) -> LabTestTemplate:
    tmpl = (
        db.query(LabTestTemplate)
        .options(joinedload(LabTestTemplate.parameters))
        .filter(LabTestTemplate.template_id == str(template_id))
        .first()
    )
    if not tmpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test template not found")
    return tmpl


# ---------------------------------------------------------------------------
# Lab Orders
# ---------------------------------------------------------------------------

def create_order(
    db: Session,
    encounter_id: UUID,
    payload: LabOrderCreate,
    ordered_by: UUID,
) -> LabOrder:
    enc = _get_encounter_or_404(db, encounter_id)
    if enc.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot order lab tests on a closed encounter",
        )

    # If template_id given, denormalize test_name/test_code/test_category from template
    test_name     = payload.test_name
    test_code     = payload.test_code
    test_category = payload.test_category

    if payload.template_id:
        tmpl = db.query(LabTestTemplate).filter(
            LabTestTemplate.template_id == str(payload.template_id)
        ).first()
        if not tmpl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test template not found")
        test_name     = tmpl.test_name
        test_code     = tmpl.test_code
        test_category = tmpl.test_category

    order = LabOrder(
        encounter_id  = str(encounter_id),
        patient_id    = str(enc.patient_id),
        ordered_by    = str(ordered_by),
        template_id   = str(payload.template_id) if payload.template_id else None,
        test_name     = test_name,
        test_code     = test_code,
        test_category = test_category,
        priority      = payload.priority,
        status        = "ordered",
        event_date    = payload.event_date,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_orders(
    db: Session,
    encounter_id: Optional[UUID] = None,
    patient_id:   Optional[UUID] = None,
    order_status: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
) -> List[LabOrder]:
    q = db.query(LabOrder)
    if encounter_id:
        q = q.filter(LabOrder.encounter_id == str(encounter_id))
    if patient_id:
        q = q.filter(LabOrder.patient_id == str(patient_id))
    if order_status:
        q = q.filter(LabOrder.status == order_status)
    return q.order_by(LabOrder.ordered_at.desc()).offset(skip).limit(limit).all()


def get_order(db: Session, order_id: UUID) -> LabOrder:
    return _get_order_or_404(db, order_id)


def update_order_status(
    db: Session,
    order_id: UUID,
    payload: LabOrderStatusUpdate,
) -> LabOrder:
    order = _get_order_or_404(db, order_id)
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order


# ---------------------------------------------------------------------------
# Lab Results
# ---------------------------------------------------------------------------

def submit_results(
    db: Session,
    order_id: UUID,
    result_items: List[LabResultCreate],
    uploaded_by: UUID,
) -> List[LabResult]:
    """
    Bulk-insert results for an order.
    For each item that has a parameter_id, auto-detect is_abnormal / abnormal_level
    by comparing the numeric value against the parameter's normal range.
    Also advances the order status to 'completed'.
    """
    order = _get_order_or_404(db, order_id)

    created = []
    for item in result_items:
        param = None
        if item.parameter_id:
            param = db.query(LabTestParameter).filter(
                LabTestParameter.parameter_id == str(item.parameter_id)
            ).first()
        elif item.parameter_name and order.template_id:
            param = db.query(LabTestParameter).filter(
                LabTestParameter.template_id   == str(order.template_id),
                LabTestParameter.parameter_name == item.parameter_name,
            ).first()

        is_abnormal, abnormal_level = _classify_abnormal(item.result_value, param)

        # Denormalize normal_range from parameter if not supplied by caller
        normal_range = item.normal_range
        if normal_range is None and param:
            if param.normal_range_text:
                normal_range = param.normal_range_text
            elif param.normal_range_min is not None and param.normal_range_max is not None:
                normal_range = f"{param.normal_range_min} – {param.normal_range_max}"

        # Resolve parameter_id — use supplied value, or auto-fill from name lookup
        resolved_param_id = str(item.parameter_id) if item.parameter_id else (
            str(param.parameter_id) if param else None
        )

        result = LabResult(
            order_id        = str(order_id),
            patient_id      = str(order.patient_id),
            parameter_id    = resolved_param_id,
            uploaded_by     = str(uploaded_by),
            parameter_name  = item.parameter_name,
            result_value    = item.result_value,
            unit            = item.unit or (param.unit if param else None),
            normal_range    = normal_range,
            is_abnormal     = is_abnormal,
            abnormal_level  = abnormal_level,
            notes           = item.notes,
            result_file_url = item.result_file_url,
        )
        db.add(result)
        created.append(result)

    # Advance order to completed
    order.status = "completed"
    db.commit()
    for r in created:
        db.refresh(r)
    return created


def list_results(db: Session, order_id: UUID) -> List[LabResult]:
    _get_order_or_404(db, order_id)
    return (
        db.query(LabResult)
        .filter(LabResult.order_id == str(order_id))
        .order_by(LabResult.resulted_at)
        .all()
    )
