import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("🗑️  Dropping embeddings table...")
    conn.execute(text("DROP TABLE IF EXISTS embeddings;"))
    conn.commit()
    print("✅ Table dropped!")