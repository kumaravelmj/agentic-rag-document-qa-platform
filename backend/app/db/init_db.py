"""Initialize the PostgreSQL schema and search indexes.

Run from the backend directory with: python -m app.db.init_db
"""
from app.core.logging import configure_logging, get_logger
from app.db.database import init_db as initialize_database

configure_logging()
logger = get_logger(__name__)


def init_db() -> None:
    initialize_database()
    logger.info("Database initialization complete.")


if __name__ == "__main__":
    init_db()
