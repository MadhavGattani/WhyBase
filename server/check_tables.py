import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from api.db import Base

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

print("Creating all tables...")
Base.metadata.create_all(engine)
print("✅ All tables created!")