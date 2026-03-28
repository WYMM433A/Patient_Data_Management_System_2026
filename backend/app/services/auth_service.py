from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse, UserInfo


def login(req: LoginRequest, db: Session) -> LoginResponse:
    user = (
        db.query(User)
        .filter(User.username == req.username)
        .first()
    )

    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Update last_login timestamp
    db.query(User).filter(User.user_id == user.user_id).update(
        {"last_login": func.getdate()}, synchronize_session=False
    )
    db.commit()
    db.refresh(user)

    access_token  = create_access_token(user.user_id, user.role.role_name)
    refresh_token = create_refresh_token(user.user_id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role.role_name,
            first_name=user.first_name,
            last_name=user.last_name,
        ),
    )


def refresh(refresh_token: str, db: Session) -> TokenResponse:
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return TokenResponse(
        access_token=create_access_token(user.user_id, user.role.role_name),
        refresh_token=create_refresh_token(user.user_id),
    )
