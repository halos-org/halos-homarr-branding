#!/usr/bin/env python3
"""
Generate Homarr seed database with bootstrap API key.

This script creates a pre-configured SQLite database for Homarr with:
- Complete Homarr v1.x schema (from homarr-schema-template.sql)
- Drizzle migration records (so Homarr skips migrations)
- Onboarding already complete
- Two users: halos-sync (service account) and admin (human admin)
- A bootstrap API key owned by halos-sync (rotated on first boot)
- Default server settings
- Default groups (everyone, admins) with both users in admins group

Two users are created:
1. halos-sync: Service account for API key ownership and programmatic access.
   The homarr-container-adapter uses this user's API key for sync operations.
2. admin: Human administrator for OIDC login. When a user logs in via OIDC
   with a matching email, Homarr links the OIDC account to this user.

Both users have provider='oidc' to enable OIDC account linking.
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

try:
    import bcrypt
except ImportError:
    print("Error: bcrypt module not found. Install with: pip install bcrypt", file=sys.stderr)
    sys.exit(1)

# Well-known bootstrap API key credentials
# This key is intentionally static and will be rotated on first boot
# Note: bcrypt has a 72-byte limit, so we use a shorter token
BOOTSTRAP_API_KEY_ID = "halos-bootstrap"
BOOTSTRAP_API_KEY_TOKEN = "halos-bootstrap-rotate-me-on-first-boot-abc123"

# Service account for API key ownership and programmatic access
HALOS_SYNC_USER_ID = "halos-sync"
# Service account email uses example.local (RFC 2606 reserved domain)
HALOS_SYNC_USER_EMAIL = "halos-sync@example.local"

# Human admin user for OIDC login
ADMIN_USER_ID = "admin"
# Admin email uses example.local (RFC 2606 reserved domain)
# In production, the OIDC provider supplies the actual email
ADMIN_USER_EMAIL = "admin@example.local"

# Group IDs (must match template)
ADMINS_GROUP_ID = "z4qbfvum6cs94sr6s5pslxq6"


def get_schema_template_path() -> Path:
    """Get path to the SQL schema template."""
    script_dir = Path(__file__).parent
    return script_dir / "homarr-schema-template.sql"


def create_database_from_template(conn: sqlite3.Connection) -> None:
    """Create database by executing the SQL template.

    The template contains:
    - All Homarr table definitions
    - Drizzle migration records
    - Default icon repositories
    - Default groups (everyone, admins)
    """
    template_path = get_schema_template_path()
    if not template_path.exists():
        raise FileNotFoundError(f"Schema template not found: {template_path}")

    print(f"Loading schema from: {template_path}")
    sql = template_path.read_text()

    # Remove the marker comments (they're just for documentation)
    sql = sql.replace("-- {{ONBOARDING}}", "")
    sql = sql.replace("-- {{USER}}", "")
    sql = sql.replace("-- {{API_KEY}}", "")
    sql = sql.replace("-- {{SERVER_SETTINGS}}", "")
    sql = sql.replace("-- {{GROUP_MEMBERS}}", "")

    # Execute the template SQL
    conn.executescript(sql)


def insert_onboarding_complete(conn: sqlite3.Connection) -> None:
    """Mark onboarding as complete."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO onboarding (id, step, previous_step)
        VALUES ('init', 'finish', 'settings')
    """)
    conn.commit()


def insert_halos_sync_user(conn: sqlite3.Connection) -> None:
    """Create the halos-sync service account for API key ownership.

    This user owns the bootstrap API key (and the rotated permanent key).
    The homarr-container-adapter uses this user's API key for all sync operations.

    We use provider='oidc' for consistency, though this user won't log in via OIDC.
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user (id, name, email, email_verified, provider, color_scheme)
        VALUES (?, 'HaLOS Sync Service', ?, 1, 'oidc', 'dark')
    """, (HALOS_SYNC_USER_ID, HALOS_SYNC_USER_EMAIL))
    conn.commit()


def insert_admin_user(conn: sqlite3.Connection) -> None:
    """Create the admin user for human OIDC login.

    Homarr's custom adapter filters getUserByEmail by BOTH email AND provider,
    so when an OIDC user logs in, it only finds users with provider='oidc'.

    We create the user with provider='oidc' so that when admin logs in via OIDC
    with a matching email, Homarr finds this existing user and links the OIDC
    account to it instead of creating a new user.

    Note: email_verified must be set to 1 (true) for account linking to work.
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user (id, name, email, email_verified, provider, color_scheme)
        VALUES (?, 'Administrator', ?, 1, 'oidc', 'dark')
    """, (ADMIN_USER_ID, ADMIN_USER_EMAIL))
    conn.commit()


def insert_group_members(conn: sqlite3.Connection) -> None:
    """Add both users to the admins group."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO groupMember (group_id, user_id)
        VALUES (?, ?)
    """, (ADMINS_GROUP_ID, HALOS_SYNC_USER_ID))
    cursor.execute("""
        INSERT INTO groupMember (group_id, user_id)
        VALUES (?, ?)
    """, (ADMINS_GROUP_ID, ADMIN_USER_ID))
    conn.commit()


def insert_bootstrap_api_key(conn: sqlite3.Connection) -> str:
    """Create the bootstrap API key owned by halos-sync user.

    The API key is owned by halos-sync (not admin) to separate programmatic
    API access from human OIDC login.
    """
    # Generate bcrypt salt and hash
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(BOOTSTRAP_API_KEY_TOKEN.encode('utf-8'), salt)

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO apiKey (id, api_key, salt, user_id)
        VALUES (?, ?, ?, ?)
    """, (
        BOOTSTRAP_API_KEY_ID,
        hashed.decode('utf-8'),
        salt.decode('utf-8'),
        HALOS_SYNC_USER_ID
    ))
    conn.commit()

    # Return the full API key in Homarr's format: {id}.{token}
    return f"{BOOTSTRAP_API_KEY_ID}.{BOOTSTRAP_API_KEY_TOKEN}"


def insert_server_settings(conn: sqlite3.Connection) -> None:
    """Insert default server settings."""
    cursor = conn.cursor()

    # Analytics settings - all disabled
    analytics = {
        "json": {
            "enableGeneral": False,
            "enableWidgetData": False,
            "enableIntegrationData": False,
            "enableUserData": False
        }
    }

    # Crawling settings - all disabled
    crawling = {
        "json": {
            "noIndex": True,
            "noFollow": True,
            "noTranslate": True,
            "noSiteLinksSearchBox": True
        }
    }

    cursor.execute("""
        INSERT INTO serverSetting (setting_key, value) VALUES (?, ?)
    """, ('analytics', json.dumps(analytics)))

    cursor.execute("""
        INSERT INTO serverSetting (setting_key, value) VALUES (?, ?)
    """, ('crawlingAndIndexing', json.dumps(crawling)))

    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Homarr seed database with bootstrap API key"
    )
    parser.add_argument(
        "--output-db",
        type=Path,
        default=Path("db-seed.sqlite3"),
        help="Output path for the seed database (default: db-seed.sqlite3)"
    )
    parser.add_argument(
        "--output-key",
        type=Path,
        default=Path("bootstrap-api-key"),
        help="Output path for the bootstrap API key file (default: bootstrap-api-key)"
    )
    args = parser.parse_args()

    # Create parent directories if needed
    args.output_db.parent.mkdir(parents=True, exist_ok=True)
    args.output_key.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database if present
    if args.output_db.exists():
        args.output_db.unlink()

    print(f"Creating seed database: {args.output_db}")

    # Create database from template and add seed data
    conn = sqlite3.connect(args.output_db)
    try:
        create_database_from_template(conn)
        insert_onboarding_complete(conn)
        insert_halos_sync_user(conn)
        insert_admin_user(conn)
        insert_group_members(conn)
        api_key = insert_bootstrap_api_key(conn)
        insert_server_settings(conn)
    finally:
        conn.close()

    # Write the bootstrap API key to a file
    print(f"Writing bootstrap API key to: {args.output_key}")
    args.output_key.write_text(api_key + "\n")

    print("Done!")
    print(f"  Database: {args.output_db}")
    print(f"  API Key:  {args.output_key}")
    print(f"\nBootstrap API key ID: {BOOTSTRAP_API_KEY_ID}")
    print("This key should be rotated by homarr-container-adapter on first boot.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
