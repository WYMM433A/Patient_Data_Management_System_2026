from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.routers import auth, users, patients, appointments

app = FastAPI(
    title="PDMS - Patient Data Management System",
    version="1.0.0",
    description="Outpatient clinic management API",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(appointments.router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "debug": settings.DEBUG,
    }
