# server/api/utils/add_logo_url_column.py
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1) Locate and load server/.env
# __file__ = server/api/utils/add_logo_url_column.py
# parents[0] = utils, [1] = api, [2] = server
BASE_DIR = Path(__file__).resolve().parents[2]
env_path = BASE_DIR / ".env"

print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

# 2) Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(f"DATABASE_URL is not set. Check {env_path}")

print(f"Using DATABASE_URL = {DATABASE_URL}")

# 3) Connect and add column
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Adding logo_url column to organizations table...")
    try:
        conn.execute(text("ALTER TABLE organizations ADD COLUMN logo_url VARCHAR(512);"))
        conn.commit()
        print("✅ logo_url column added successfully.")
    except Exception as e:
        print("⚠️ Error while adding column (maybe it already exists?):", e)
