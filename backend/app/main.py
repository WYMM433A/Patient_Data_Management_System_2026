from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import jwt, JWTError

from app.database import get_db, _current_user_id
from app.config import settings
from app.routers import auth, users, patients, prescriptions, appointments, encounters, lab, imaging, referrals, care_plans, audit_logs, ai

app = FastAPI(
    title="PDMS - Patient Data Management System",
    version="1.0.0",
    description="Outpatient clinic management API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def set_db_user_context(request: Request, call_next):
    """Extract the authenticated user's UUID from the JWT and store it in
    a ContextVar so get_db() can forward it to SQL Server SESSION_CONTEXT.
    This lets audit triggers record the real user instead of NULL."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            raw_token = auth_header[7:]
            payload = jwt.decode(
                raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            uid = payload.get("sub")
            if uid and payload.get("type") == "access":
                ctx_token = _current_user_id.set(uid)
                try:
                    return await call_next(request)
                finally:
                    _current_user_id.reset(ctx_token)
        except (JWTError, Exception):
            pass
    return await call_next(request)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(encounters.router)
app.include_router(prescriptions.router)
app.include_router(lab.router)
app.include_router(imaging.router)
app.include_router(referrals.router)
app.include_router(care_plans.router)
app.include_router(audit_logs.router)
app.include_router(ai.router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "debug": settings.DEBUG,
    }
