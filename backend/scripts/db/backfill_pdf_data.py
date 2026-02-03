"""
Backfill file_data for existing PDF documents
Reads PDFs from sample_docs and stores them in the database
"""
import base64
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from app.db.models import Document
from app.core.config import get_settings

def backfill_pdf_data():
    """Add file_data to existing PDF documents that don't have it"""
    settings = get_settings()
    
    # Create engine without pooling to avoid Neon issues
    engine = create_engine(settings.database_url, poolclass=NullPool)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Get all PDF documents without file_data
        documents = db.query(Document).filter(
            Document.content_type == "application/pdf",
            Document.file_data.is_(None)
        ).all()
        
        print(f"Found {len(documents)} PDFs without file data")
        
        sample_docs_dir = Path(__file__).parent / "sample_docs"
        updated_count = 0
        
        for doc in documents:
            pdf_path = sample_docs_dir / doc.filename
            
            if pdf_path.exists():
                print(f"Processing: {doc.filename}")
                
                # Read PDF file
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                
                # Encode to base64
                file_data_base64 = base64.b64encode(pdf_content).decode('utf-8')
                
                # Update database
                doc.file_data = file_data_base64
                updated_count += 1
                
                print(f"  ✅ Stored {len(file_data_base64)} chars for {doc.filename}")
            else:
                print(f"  ⚠️  File not found: {pdf_path}")
        
        db.commit()
        print(f"\n✅ Successfully backfilled {updated_count} PDF documents")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_pdf_data()
