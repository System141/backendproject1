"""
Unified auto-migration helpers: add missing columns to existing tables safely.

Both main.py lifespan startup and admin.py seed endpoint consume this single
source of truth instead of duplicating the column definitions.
"""
import logging
from sqlalchemy import text

logger = logging.getLogger("bidmont.migrations")

# Single source of truth: table -> list of (column_name, sql_type)
MISSING_COLUMNS = {
    "users": [
        ("accepted_terms", "BOOLEAN DEFAULT FALSE"),
        ("accepted_privacy", "BOOLEAN DEFAULT FALSE"),
        ("marketing_consent", "BOOLEAN DEFAULT FALSE"),
        ("reset_token_hash", "VARCHAR"),
        ("reset_token_expires_at", "TIMESTAMP"),
        ("phone", "VARCHAR"),
        ("credits_balance", "FLOAT DEFAULT 0"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "auctions": [
        ("brand", "VARCHAR"),
        ("model", "VARCHAR"),
        ("year", "INTEGER"),
        ("mileage", "INTEGER"),
        ("fuel_type", "VARCHAR"),
        ("transmission", "VARCHAR"),
        ("damage_status", "VARCHAR"),
        ("equipment_brand", "VARCHAR"),
        ("serial_number", "VARCHAR"),
        ("condition", "VARCHAR"),
        ("location", "VARCHAR"),
        ("winner_user_id", "VARCHAR"),
        ("is_featured", "BOOLEAN DEFAULT FALSE"),
        ("listing_fee", "FLOAT"),
    ],
    "bids": [
        ("ip_address", "VARCHAR"),
    ],
    "payments": [
        ("stripe_session_id", "VARCHAR"),
        ("buyer_service_fee", "FLOAT"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "support_tickets": [
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "audit_logs": [
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
}


async def run_migration_async(conn):
    """Add missing columns using async connection. Safe for repeated runs."""
    for table, columns in MISSING_COLUMNS.items():
        for col_name, col_type in columns:
            try:
                sql = text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS {col_name} {col_type}')
                await conn.execute(sql)
                logger.info(f"Migration: added {table}.{col_name}")
            except Exception as e:
                logger.warning(f"Migration: skipped {table}.{col_name} ({e})")


async def run_migration_raw(db_session):
    """Add missing columns using an existing async session (raw SQL)."""
    for table, columns in MISSING_COLUMNS.items():
        for col_name, col_type in columns:
            try:
                sql = text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS {col_name} {col_type}')
                await db_session.execute(sql)
                await db_session.commit()
                logger.info(f"Migration: added {table}.{col_name}")
            except Exception as e:
                await db_session.rollback()
                logger.warning(f"Migration: skipped {table}.{col_name} ({e})")