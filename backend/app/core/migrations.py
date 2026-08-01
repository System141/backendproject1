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
        ("city", "VARCHAR"),
        ("address", "VARCHAR"),
        ("preferred_language", "VARCHAR"),
        ("credits_balance", "FLOAT DEFAULT 0"),
        ("totp_secret", "VARCHAR"),
        ("totp_enabled", "BOOLEAN DEFAULT FALSE"),
        ("email_verified", "BOOLEAN DEFAULT FALSE"),
        ("email_verification_token_hash", "VARCHAR"),
        ("email_verification_expires_at", "TIMESTAMP"),
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
        ("defect_exterior", "VARCHAR"),
        ("defect_interior", "VARCHAR"),
        ("defect_mechanical", "VARCHAR"),
        ("defect_tyres", "VARCHAR"),
        ("defect_missing_parts", "VARCHAR"),
        ("equipment_brand", "VARCHAR"),
        ("serial_number", "VARCHAR"),
        ("condition", "VARCHAR"),
        ("location", "VARCHAR"),
        ("operating_hours", "INTEGER"),
        ("engine_power", "VARCHAR"),
        ("operating_weight", "VARCHAR"),
        ("service_history", "TEXT"),
        ("inspection_availability", "BOOLEAN"),
        ("dimensions", "VARCHAR"),
        ("included_items", "TEXT"),
        ("quantity", "INTEGER"),
        ("winner_user_id", "VARCHAR"),
        ("is_featured", "BOOLEAN DEFAULT FALSE"),
        ("listing_fee", "FLOAT"),
        ("lot_code", "VARCHAR"),
        ("participation_credit_cost", "FLOAT"),
        ("review_notes", "TEXT"),
        ("contact_flagged", "BOOLEAN DEFAULT FALSE"),
    ],
    "bids": [
        ("ip_address", "VARCHAR"),
        ("idempotency_key", "VARCHAR"),
        ("invalidated", "BOOLEAN DEFAULT FALSE"),
        ("invalidated_reason", "TEXT"),
        ("invalidated_by", "VARCHAR"),
        ("invalidated_at", "TIMESTAMP"),
    ],
    "support_tickets": [
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("category", "VARCHAR DEFAULT 'other'"),
        ("lot_code", "VARCHAR"),
    ],
    "auction_images": [
        ("media_type", "VARCHAR DEFAULT 'image'"),
        ("visibility", "VARCHAR DEFAULT 'public'"),
        ("doc_category", "VARCHAR"),
    ],
    "audit_logs": [
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "notifications": [
        ("event_key", "VARCHAR"),
    ],
}

# Postgres native enum types don't gain new labels automatically when the
# Python enum grows - ADD VALUE IF NOT EXISTS is the idempotent equivalent of
# ADD COLUMN IF NOT EXISTS above. No-op on SQLite (no such type), caught below.
MISSING_ENUM_VALUES = {
    "auctionstatus": ["draft", "under_review", "upcoming", "live", "extended", "ended", "cancelled"],
}

# ADD COLUMN can't declare UNIQUE inline on an already-existing table (Postgres
# rejects it on ALTER), so these get a separate unique index. New tables
# created via Base.metadata.create_all get the constraint natively - this
# list only matters for columns bolted onto pre-existing deployed tables.
MISSING_UNIQUE_INDEXES = [
    ("bids", "idempotency_key", "uq_bids_idempotency_key"),
    ("auctions", "lot_code", "uq_auctions_lot_code"),
    ("notifications", "event_key", "uq_notifications_event_key"),
    ("credit_purchases", "stripe_session_id", "uq_credit_purchases_stripe_session_id"),
]


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
    for enum_name, values in MISSING_ENUM_VALUES.items():
        for value in values:
            try:
                sql = text(f"ALTER TYPE \"{enum_name}\" ADD VALUE IF NOT EXISTS '{value}'")
                await conn.execute(sql)
                logger.info(f"Migration: added enum value {enum_name}.{value}")
            except Exception as e:
                logger.warning(f"Migration: skipped enum value {enum_name}.{value} ({e})")
    for table, col_name, index_name in MISSING_UNIQUE_INDEXES:
        try:
            sql = text(f'CREATE UNIQUE INDEX IF NOT EXISTS "{index_name}" ON "{table}" ({col_name})')
            await conn.execute(sql)
            logger.info(f"Migration: added unique index {index_name}")
        except Exception as e:
            logger.warning(f"Migration: skipped unique index {index_name} ({e})")


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
    for enum_name, values in MISSING_ENUM_VALUES.items():
        for value in values:
            try:
                sql = text(f"ALTER TYPE \"{enum_name}\" ADD VALUE IF NOT EXISTS '{value}'")
                await db_session.execute(sql)
                await db_session.commit()
                logger.info(f"Migration: added enum value {enum_name}.{value}")
            except Exception as e:
                await db_session.rollback()
                logger.warning(f"Migration: skipped enum value {enum_name}.{value} ({e})")
    for table, col_name, index_name in MISSING_UNIQUE_INDEXES:
        try:
            sql = text(f'CREATE UNIQUE INDEX IF NOT EXISTS "{index_name}" ON "{table}" ({col_name})')
            await db_session.execute(sql)
            await db_session.commit()
            logger.info(f"Migration: added unique index {index_name}")
        except Exception as e:
            await db_session.rollback()
            logger.warning(f"Migration: skipped unique index {index_name} ({e})")