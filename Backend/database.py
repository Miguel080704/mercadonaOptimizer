"""
Configuración centralizada de la BBDD.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    """Dependency para FastAPI: abre y cierra sesión automáticamente."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
