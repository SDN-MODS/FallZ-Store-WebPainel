import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base, StoreSettings

DB_FILE = os.getenv("DATABASE_URL", "sqlite:///dayz_store.db")

engine = create_engine(DB_FILE, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))

def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        settings = session.query(StoreSettings).filter_by(id="default").first()
        if not settings:
            settings = StoreSettings(id="default")
            session.add(settings)
            session.commit()
    finally:
        session.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
