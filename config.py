import os
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()


def _normalize_db_url(url: str) -> str:
    """Always use the psycopg2 driver for PostgreSQL, whatever prefix the provider gives."""
    url = url.strip().strip('"').strip("'")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    parsed = make_url(url)
    if parsed.drivername.startswith("postgresql"):
        parsed = parsed.set(drivername="postgresql+psycopg2")
    return parsed.render_as_string(hide_password=False)


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