import os
from dotenv import load_dotenv

load_dotenv()

def _normalize_db_url(url: str) -> str:
    """SQLAlchemy 1.4+ requires 'postgresql://', but some providers still hand out 'postgres://'."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

class Config:

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-secret-key")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/marksheet_db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }