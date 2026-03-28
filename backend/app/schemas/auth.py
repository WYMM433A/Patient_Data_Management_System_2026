from pydantic import BaseModel, EmailStr
from uuid import UUID


# ---------- Request ----------

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Response ----------

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class UserInfo(BaseModel):
    user_id:    UUID
    username:   str
    email:      str
    role:       str
    first_name: str
    last_name:  str

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          UserInfo
