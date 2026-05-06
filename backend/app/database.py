from contextvars import ContextVar

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# Stores the current authenticated user's UUID string for the lifetime of a request.
# Set by the HTTP middleware in main.py so every DB session can call
# sp_set_session_context and the SQL Server audit triggers can record who acted.
_current_user_id: ContextVar[str] = ContextVar('current_user_id', default='')


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        uid = _current_user_id.get()
        if uid:
            db.execute(
                text("EXEC sys.sp_set_session_context @key=N'user_id', @value=:uid"),
                {"uid": uid},
            )
        yield db
    finally:
        db.close()
