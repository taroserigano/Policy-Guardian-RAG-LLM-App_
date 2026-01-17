"""
Test PostgreSQL database connection
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

# Fix postgres:// to postgresql:// if needed
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables")
    exit(1)

print(f"🔗 Connecting to database...")
print(f"   URL: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Database connected successfully!")
        print(f"   PostgreSQL version: {version[:80]}...")
        
        # Test creating a simple table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.commit()
        print(f"✅ Table creation test passed")
        
        # Clean up
        connection.execute(text("DROP TABLE IF EXISTS connection_test"))
        connection.commit()
        print(f"✅ All database tests passed!")
        
except Exception as e:
    print(f"❌ Database connection failed:")
    print(f"   Error: {str(e)}")
    exit(1)
