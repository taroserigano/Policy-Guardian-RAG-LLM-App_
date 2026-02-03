"""
Load sample documents into the database and Pinecone
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import hashlib
from enhanced_server_v2 import Document, Base, get_embedding, chunk_text
from pinecone import Pinecone

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Pinecone setup
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "policy-rag"))

# Sample documents
sample_docs = [
    {
        "filename": "employee_leave_policy.txt",
        "content": """EMPLOYEE LEAVE POLICY

Annual Leave: All full-time employees are entitled to 20 days of paid annual leave per year. Leave must be requested at least 2 weeks in advance and approved by the direct supervisor.

Sick Leave: Employees receive 10 days of paid sick leave annually. Medical documentation is required for absences exceeding 3 consecutive days.

Parental Leave: Eligible employees may receive up to 16 weeks of leave for a primary caregiver following birth, adoption, or placement, and up to 2 weeks for a secondary caregiver (subject to local law and HR guidance).

Bereavement Leave: Employees may take up to 5 days of paid leave for the death of an immediate family member.

Personal Days: 3 paid personal days are available per year for personal matters that cannot be scheduled outside work hours.

Leave Carryover: Up to 5 days of unused annual leave may be carried over to the next year. Sick leave does not carry over.

Unpaid Leave: Extended unpaid leave may be granted at management discretion for special circumstances."""
    },
    {
        "filename": "remote_work_policy.txt",
        "content": """REMOTE WORK POLICY

Hybrid Work Model: Our standard model allows employees to work remotely up to 2 days per week. In-office presence is required Monday, Wednesday, and one additional day of your choice.

Full Remote Eligibility: Employees may apply for full remote work (3+ days per week) after 6 months of employment. Approval requires manager consent and demonstration of consistent performance.

Core Hours: All remote workers must be available during core hours of 9 AM - 4 PM in their local timezone for meetings and collaboration.

Home Office Requirements: Remote workers must have a dedicated workspace with reliable high-speed internet, a webcam, and a quiet environment for video calls.

Equipment: Company will provide a laptop and essential peripherals. Additional equipment requests (monitors, chairs, etc.) may be approved based on role requirements.

Communication: Remote workers must respond within reasonable timeframes during core hours and join scheduled team meetings.

Performance Monitoring: Remote work privileges may be revoked if performance standards are not maintained or communication expectations are not met.

Security: All remote work must comply with company security policies. Use of VPN (or equivalent secure access) is required when accessing internal resources."""
    },
    {
        "filename": "data_privacy_policy.txt",
        "content": """DATA PRIVACY POLICY

Scope: This policy applies to all employee, customer, and partner data collected, processed, and stored by the company.

Data Collection: We collect only data necessary for business operations. All data collection must have a documented business purpose and be disclosed to data subjects.

Data Retention: Employee data is retained for 7 years post-employment. Customer data is retained for the duration of the business relationship plus 3 years. Financial records are retained for 10 years per regulatory requirements.

Data Security: All personal data must be encrypted at rest and in transit. Access is restricted to authorized personnel only. Multi-factor authentication is required for all systems containing personal data.

GDPR/CCPA Compliance: We comply with GDPR, CCPA, and other applicable privacy regulations. Data subjects have the right to access, correct, and request deletion of their personal data.

Breach Notification: Any data breach must be reported to the security team immediately. Affected individuals will be notified within 72 hours as required by law.

Third-Party Sharing: Personal data is never sold. Data may be shared with service providers under strict data processing agreements. Any third-party access must be documented and approved.

Employee Responsibilities: All employees must complete annual privacy training. Employees must not share login credentials or leave sensitive data exposed on screens or in unsecured locations."""
    },
    {
        "filename": "non_disclosure_agreement.txt",
        "content": """NON-DISCLOSURE AGREEMENT (NDA)

Agreement Term: This NDA is effective from the date of signing and remains in effect for 3 years from the date of termination of employment or contract.

Confidential Information Definition: Includes but not limited to: trade secrets, business strategies, customer lists, financial data, product roadmaps, source code, proprietary processes, and any information marked as confidential.

Obligations: The receiving party agrees to:
- Keep all confidential information strictly confidential
- Not disclose confidential information to any third party without prior written consent
- Use confidential information only for the purposes of employment or contract
- Return or destroy all confidential materials upon termination

Confidentiality Period: The obligation to maintain confidentiality extends for 5 years from the date of disclosure, even after employment or contract termination.

Exclusions: This NDA does not apply to information that:
- Is or becomes publicly available through no breach of this agreement
- Was rightfully possessed before disclosure
- Is independently developed without use of confidential information
- Is required to be disclosed by law or court order

Legal Remedies: Breach of this NDA may result in immediate termination and legal action including injunctive relief and monetary damages.

Non-Compete: For senior positions, a 12-month non-compete clause applies to prevent joining direct competitors in similar roles."""
    }
]

def load_samples():
    db = SessionLocal()
    try:
        print("[INFO] Loading sample documents...")
        
        for doc_data in sample_docs:
            filename = doc_data["filename"]
            content = doc_data["content"]
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if exists
            existing = db.query(Document).filter(Document.content_hash == content_hash).first()
            if existing:
                print(f"  ⚠️  {filename} already exists")
                continue
            
            # Save to database
            doc = Document(
                filename=filename,
                content=content,
                content_hash=content_hash,
                content_type="text/plain",
                size=len(content)
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Chunk and embed
            chunks = chunk_text(content)
            print(f"  📄 {filename}: {len(chunks)} chunks")
            
            # Upload to Pinecone
            vectors = []
            for i, chunk in enumerate(chunks):
                emb = get_embedding(chunk)
                vectors.append({
                    "id": f"{doc.id}-chunk-{i}",
                    "values": emb,
                    "metadata": {
                        "doc_id": doc.id,
                        "filename": filename,
                        "chunk_index": i,
                        "text": chunk[:500]
                    }
                })
            
            pinecone_index.upsert(vectors=vectors)
            print(f"  ✅ {filename} indexed successfully")
        
        print("\n[SUCCESS] Sample documents loaded!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to load samples: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_samples()
