"""
Add file_data column to documents table for PDF viewing support
"""
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()

def migrate():
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='documents' AND column_name='file_data'
        """))
        
        if result.fetchone():
            print("✅ Column 'file_data' already exists")
        else:
            # Add the column
            conn.execute(text("ALTER TABLE documents ADD COLUMN file_data TEXT"))
            conn.commit()
            print("✅ Added 'file_data' column to documents table")

if __name__ == "__main__":
    migrate()
