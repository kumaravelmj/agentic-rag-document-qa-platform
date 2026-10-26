from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_pgvector_extension() -> None:
    """Enable pgvector before creating tables that use the VECTOR type."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def validate_vector_dimension() -> None:
    """Check an existing embedding column against the configured dimension."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT atttypmod FROM pg_attribute "
                "JOIN pg_class ON pg_class.oid = pg_attribute.attrelid "
                "JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace "
                "WHERE pg_class.relname = 'document_chunks' "
                "AND pg_attribute.attname = 'embedding' "
                "AND pg_namespace.nspname = current_schema() "
                "AND NOT pg_attribute.attisdropped"
            )
        ).fetchone()
    if result and result[0] > 0 and result[0] != settings.VECTOR_DIMENSION:
        raise RuntimeError(
            f"VECTOR_DIMENSION mismatch: schema={result[0]}, "
            f"config={settings.VECTOR_DIMENSION}. Update VECTOR_DIMENSION "
            "or recreate/migrate the document_chunks table."
        )
    logger.info("Vector dimension checked: %s", settings.VECTOR_DIMENSION)


def verify_vector_dimension() -> None:
    """Backward-compatible alias for vector dimension validation."""
    validate_vector_dimension()


def init_db() -> None:
    """Initialize pgvector, ORM tables, and SQL search indexes."""
    import app.models  # noqa: F401 - register all ORM models

    ensure_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    validate_vector_dimension()

    migration_dir = Path(__file__).parent / "migrations"
    for migration in sorted(migration_dir.glob("*.sql")):
        with engine.begin() as conn:
            conn.execute(text(migration.read_text(encoding="utf-8")))
        logger.info("Applied database migration: %s", migration.name)
    logger.info("Database initialized successfully.")
