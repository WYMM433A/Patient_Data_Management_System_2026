import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, func
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


# Junction table (no ORM class needed — accessed via relationship)
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id",       UNIQUEIDENTIFIER, ForeignKey("roles.role_id"),       primary_key=True),
    Column("permission_id", UNIQUEIDENTIFIER, ForeignKey("permissions.permission_id"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"

    permission_id   = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    permission_name = Column(String(100), nullable=False, unique=True)
    module          = Column(String(50), nullable=False)
    action          = Column(String(20), nullable=False)
    description     = Column(String, nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Role(Base):
    __tablename__ = "roles"

    role_id     = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    role_name   = Column(String(50), nullable=False, unique=True)
    description = Column(String, nullable=True)
    created_at  = Column(DateTime, nullable=False, server_default=func.getdate())

    users       = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    user_id       = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    username      = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    email         = Column(String(150), nullable=False, unique=True)
    role_id       = Column(UNIQUEIDENTIFIER, ForeignKey("roles.role_id"), nullable=False)
    first_name    = Column(String(100), nullable=False)
    last_name     = Column(String(100), nullable=False)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime, nullable=False, server_default=func.getdate())
    last_login    = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users")
