from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


# ---------- Role ----------

class RoleOut(BaseModel):
    role_id:   UUID
    role_name: str

    model_config = {"from_attributes": True}


# ---------- User ----------

class UserCreate(BaseModel):
    username:   str
    password:   str
    email:      str
    role_id:    UUID
    first_name: str
    last_name:  str


class UserUpdate(BaseModel):
    email:      Optional[str]  = None
    role_id:    Optional[UUID] = None
    first_name: Optional[str]      = None
    last_name:  Optional[str]      = None
    is_active:  Optional[bool]     = None


class UserOut(BaseModel):
    user_id:    UUID
    username:   str
    email:      str
    role:       RoleOut
    first_name: str
    last_name:  str
    is_active:  bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}
