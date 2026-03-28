from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.user import User, Role
from app.core.security import hash_password
from app.schemas.users import UserCreate, UserUpdate


def _get_or_404(db: Session, user_id: UUID) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.user_id == str(user_id))
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def list_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    return (
        db.query(User)
        .options(joinedload(User.role))
        .order_by(User.created_at)
        .offset(skip).limit(limit).all()
    )


def get_user(db: Session, user_id: UUID) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.user_id == str(user_id))
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def create_user(db: Session, payload: UserCreate) -> User:
    # Username / email uniqueness check
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Validate role exists
    role = db.query(Role).filter(Role.role_id == str(payload.role_id)).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        email=payload.email,
        role_id=str(payload.role_id),
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: UUID, payload: UserUpdate) -> User:
    user = _get_or_404(db, user_id)

    if payload.email is not None:
        conflict = db.query(User).filter(User.email == payload.email, User.user_id != str(user_id)).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user.email = payload.email

    if payload.role_id is not None:
        role = db.query(Role).filter(Role.role_id == str(payload.role_id)).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")
        user.role_id = str(payload.role_id)

    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: UUID) -> User:
    user = _get_or_404(db, user_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def list_roles(db: Session) -> list:
    return db.query(Role).all()
