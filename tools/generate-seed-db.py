#!/usr/bin/env python3
"""
Generate Homarr seed database with bootstrap API key.

This script creates a pre-configured SQLite database for Homarr with:
- Onboarding already complete
- A service account user (for API key ownership)
- A bootstrap API key (to be rotated on first boot)
- Default server settings

The bootstrap API key is a well-known value that the homarr-container-adapter
uses on first boot to create a random permanent API key, then deletes.
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
SERVICE_USER_ID = "halos-service"


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the Homarr database tables."""
    cursor = conn.cursor()

    # Onboarding table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onboarding (
            id TEXT PRIMARY KEY NOT NULL,
            step TEXT NOT NULL,
            previousStep TEXT
        )
    """)

    # User table (simplified - only fields we need)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id TEXT PRIMARY KEY NOT NULL,
            name TEXT,
            email TEXT,
            emailVerified INTEGER,
            image TEXT,
            password TEXT,
            salt TEXT,
            provider TEXT DEFAULT 'credentials',
            homeBoardId TEXT,
            mobileHomeBoardId TEXT,
            defaultSearchEngineId TEXT,
            openSearchInNewTab INTEGER DEFAULT 1,
            colorScheme TEXT DEFAULT 'dark',
            firstDayOfWeek INTEGER DEFAULT 1,
            pingIconsEnabled INTEGER DEFAULT 0
        )
    """)

    # API key table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apiKey (
            id TEXT PRIMARY KEY NOT NULL,
            apiKey TEXT NOT NULL,
            salt TEXT NOT NULL,
            userId TEXT REFERENCES user(id) ON DELETE CASCADE
        )
    """)

    # Server settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS serverSetting (
            settingKey TEXT PRIMARY KEY NOT NULL UNIQUE,
            value TEXT NOT NULL DEFAULT '{}'
        )
    """)

    conn.commit()


def insert_onboarding_complete(conn: sqlite3.Connection) -> None:
    """Mark onboarding as complete."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO onboarding (id, step, previousStep)
        VALUES ('init', 'finish', 'settings')
    """)
    conn.commit()


def insert_service_user(conn: sqlite3.Connection) -> None:
    """Create the service account user."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user (id, name, provider, colorScheme)
        VALUES (?, 'HaLOS Service Account', 'credentials', 'dark')
    """, (SERVICE_USER_ID,))
    conn.commit()


def insert_bootstrap_api_key(conn: sqlite3.Connection) -> str:
    """Create the bootstrap API key and return the full key string."""
    # Generate bcrypt salt and hash
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(BOOTSTRAP_API_KEY_TOKEN.encode('utf-8'), salt)

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO apiKey (id, apiKey, salt, userId)
        VALUES (?, ?, ?, ?)
    """, (
        BOOTSTRAP_API_KEY_ID,
        hashed.decode('utf-8'),
        salt.decode('utf-8'),
        SERVICE_USER_ID
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
        INSERT INTO serverSetting (settingKey, value) VALUES (?, ?)
    """, ('analytics', json.dumps(analytics)))

    cursor.execute("""
        INSERT INTO serverSetting (settingKey, value) VALUES (?, ?)
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

    # Create database and tables
    conn = sqlite3.connect(args.output_db)
    try:
        create_tables(conn)
        insert_onboarding_complete(conn)
        insert_service_user(conn)
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
