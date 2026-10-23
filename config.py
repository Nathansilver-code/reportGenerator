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