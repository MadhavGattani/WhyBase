import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    issues = conn.execute(text("SELECT COUNT(*) FROM issues")).scalar()
    repos = conn.execute(text("SELECT COUNT(*) FROM repositories")).scalar()
    integrations = conn.execute(text("SELECT COUNT(*) FROM integrations")).scalar()
    
    print(f"Integrations: {integrations}")
    print(f"Repositories: {repos}")
    print(f"Issues: {issues}")