import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class LabTestTemplate(Base):
    __tablename__ = "lab_test_templates"

    template_id   = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    test_name     = Column(String(200), nullable=False)
    test_code     = Column(String(20),  nullable=False, unique=True)
    test_category = Column(String(50),  nullable=False)
    description   = Column(String,      nullable=True)
    is_active     = Column(Boolean,     nullable=False, default=True)

    parameters = relationship("LabTestParameter", back_populates="template")


class LabTestParameter(Base):
    __tablename__ = "lab_test_parameters"

    parameter_id      = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    template_id       = Column(UNIQUEIDENTIFIER, ForeignKey("lab_test_templates.template_id"), nullable=False)
    parameter_name    = Column(String(100), nullable=False)
    display_order     = Column(Integer,     nullable=False)
    unit              = Column(String(30),  nullable=True)
    normal_range_min  = Column(Numeric(10, 3), nullable=True)
    normal_range_max  = Column(Numeric(10, 3), nullable=True)
    normal_range_text = Column(String(100), nullable=True)
    value_type        = Column(String(20),  nullable=False, default="numeric")
    is_required       = Column(Boolean,     nullable=False, default=True)

    template = relationship("LabTestTemplate", back_populates="parameters")


class LabOrder(Base):
    __tablename__ = "lab_orders"
    # Audit trigger — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    order_id      = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    encounter_id  = Column(UNIQUEIDENTIFIER, ForeignKey("encounters.encounter_id"), nullable=False)
    patient_id    = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),     nullable=False)
    ordered_by    = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),           nullable=False)
    template_id   = Column(UNIQUEIDENTIFIER, ForeignKey("lab_test_templates.template_id"), nullable=True)
    test_name     = Column(String(200), nullable=False)
    test_code     = Column(String(20),  nullable=True)
    test_category = Column(String(100), nullable=True)
    priority      = Column(String(20),  nullable=False, default="routine")
    status        = Column(String(20),  nullable=False, default="ordered")
    ordered_at    = Column(DateTime,    nullable=False, server_default="GETDATE()")
    event_date    = Column(DateTime,    nullable=True)

    template = relationship("LabTestTemplate", foreign_keys=[template_id])
    results  = relationship("LabResult", back_populates="order")


class LabResult(Base):
    __tablename__ = "lab_results"
    # Audit trigger — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    result_id       = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    order_id        = Column(UNIQUEIDENTIFIER, ForeignKey("lab_orders.order_id"),              nullable=False)
    patient_id      = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),              nullable=False)
    parameter_id    = Column(UNIQUEIDENTIFIER, ForeignKey("lab_test_parameters.parameter_id"), nullable=True)
    uploaded_by     = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),                    nullable=False)
    parameter_name  = Column(String(100), nullable=False)
    result_value    = Column(String(100), nullable=False)
    unit            = Column(String(30),  nullable=True)
    normal_range    = Column(String(100), nullable=True)
    is_abnormal     = Column(Boolean,     nullable=False, default=False)
    abnormal_level  = Column(String(20),  nullable=True)
    notes           = Column(String,      nullable=True)
    result_file_url = Column(String(500), nullable=True)
    resulted_at     = Column(DateTime,    nullable=False, server_default="GETDATE()")
    validated_at    = Column(DateTime,    nullable=True)
    validated_by    = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=True)

    order     = relationship("LabOrder",          back_populates="results", foreign_keys=[order_id])
    parameter = relationship("LabTestParameter",  foreign_keys=[parameter_id])
