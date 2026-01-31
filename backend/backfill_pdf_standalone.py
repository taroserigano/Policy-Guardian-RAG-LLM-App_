"""
Standalone script to backfill file_data for existing PDF documents
Does not import from app to avoid conflicts with running server
"""
import base64
import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    exit(1)

def backfill_pdf_data():
    """Add file_data to existing PDF documents that don't have it"""
    
    # Create engine without pooling
    engine = create_engine(DATABASE_URL, poolclass=NullPool)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as db:
        try:
            # Query PDFs without file_data using raw SQL
            result = db.execute(text("""
                SELECT id, filename, file_path 
                FROM documents 
                WHERE content_type = 'application/pdf' 
                AND (file_data IS NULL OR file_data = '')
            """))
            
            documents = result.fetchall()
            
            if not documents:
                print("✅ No PDFs need backfilling")
                return
            
            print(f"Found {len(documents)} PDFs without file data")
            
            sample_docs_path = Path(__file__).parent / "sample_docs"
            updated_count = 0
            
            for doc in documents:
                doc_id, filename, file_path = doc
                print(f"Processing: {filename}")
                
                # Try to find the file in sample_docs
                pdf_path = sample_docs_path / filename
                
                if not pdf_path.exists():
                    print(f"  ⚠️  File not found: {pdf_path}")
                    continue
                
                try:
                    # Read and encode the PDF
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                    
                    # Update the database
                    db.execute(
                        text("UPDATE documents SET file_data = :file_data WHERE id = :id"),
                        {"file_data": pdf_base64, "id": doc_id}
                    )
                    
                    print(f"  ✅ Stored {len(pdf_base64)} chars for {filename}")
                    updated_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Error processing {filename}: {str(e)}")
            
            db.commit()
            print(f"\n✅ Successfully backfilled {updated_count} PDF documents")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error during backfill: {str(e)}")
            raise

if __name__ == "__main__":
    backfill_pdf_data()
