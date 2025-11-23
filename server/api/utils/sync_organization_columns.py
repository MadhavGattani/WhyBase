# server/api/utils/sync_organization_columns.py
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1) Load server/.env
BASE_DIR = Path(__file__).resolve().parents[2]
env_path = BASE_DIR / ".env"

print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(f"DATABASE_URL is not set. Check {env_path}")

print(f"Using DATABASE_URL = {DATABASE_URL}")

engine = create_engine(DATABASE_URL)

# 2) Define the columns we expect on organizations table
REQUIRED_COLUMNS = {
    "logo_url": "ALTER TABLE organizations ADD COLUMN logo_url VARCHAR(512);",
    "website": "ALTER TABLE organizations ADD COLUMN website VARCHAR(255);",
    "is_personal": "ALTER TABLE organizations ADD COLUMN is_personal BOOLEAN DEFAULT FALSE;",
    "is_active": "ALTER TABLE organizations ADD COLUMN is_active BOOLEAN DEFAULT TRUE;",
    "max_members": "ALTER TABLE organizations ADD COLUMN max_members INTEGER DEFAULT 50;",
    "plan_type": "ALTER TABLE organizations ADD COLUMN plan_type VARCHAR(50) DEFAULT 'free';",
    "billing_email": "ALTER TABLE organizations ADD COLUMN billing_email VARCHAR(255);",
    "updated_at": "ALTER TABLE organizations ADD COLUMN updated_at TIMESTAMP;"
}

with engine.connect() as conn:
    # 3) Find existing columns
    result = conn.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_name = 'organizations';")
    )
    existing_columns = {row[0] for row in result}

    print("Existing columns on organizations:", existing_columns)

    # 4) Add any missing columns
    for col, alter_sql in REQUIRED_COLUMNS.items():
        if col not in existing_columns:
            print(f"Adding missing column: {col}")
            try:
                conn.execute(text(alter_sql))
                conn.commit()
                print(f"✅ Added column: {col}")
            except Exception as e:
                print(f"⚠️ Error while adding column {col}: {e}")
        else:
            print(f"Column already exists: {col}")

    print("Done syncing organization columns.")
