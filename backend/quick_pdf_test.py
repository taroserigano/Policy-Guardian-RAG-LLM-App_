"""
Simple standalone test for PDF viewer - doesn't import from app
"""
import requests
import time

BASE_URL = "http://localhost:8001"

print("\n" + "="*60)
print("PDF VIEWER FEATURE - QUICK TEST")
print("="*60 + "\n")

# Test 1: Server Health
print("1️⃣  Testing server health...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=3)
    if r.status_code == 200:
        print("✅ Server is running\n")
    else:
        print(f"❌ Server error: {r.status_code}\n")
        exit(1)
except Exception as e:
    print(f"❌ Cannot connect to server: {e}\n")
    exit(1)

time.sleep(0.5)

# Test 2: List documents
print("2️⃣  Listing documents...")
try:
    r = requests.get(f"{BASE_URL}/api/docs", timeout=3)
    docs = r.json()
    pdfs = [d for d in docs if d.get('content_type') == 'application/pdf']
    print(f"✅ Found {len(docs)} documents ({len(pdfs)} PDFs)\n")
except Exception as e:
    print(f"❌ Error listing documents: {e}\n")
    pdfs = []

time.sleep(0.5)

# Test 3: Test PDF file endpoint for each PDF
if pdfs:
    print(f"3️⃣  Testing PDF file endpoint for {len(pdfs)} PDFs...")
    passed = 0
    failed = 0
    
    for pdf in pdfs[:5]:  # Test first 5 PDFs
        doc_id = pdf['id']
        filename = pdf['filename']
        
        try:
            r = requests.get(f"{BASE_URL}/api/docs/{doc_id}/file", timeout=5)
            
            if r.status_code == 200:
                if r.content[:4] == b'%PDF':
                    print(f"   ✅ {filename} - {len(r.content)} bytes")
                    passed += 1
                else:
                    print(f"   ❌ {filename} - invalid PDF content")
                    failed += 1
            elif r.status_code == 404:
                print(f"   ❌ {filename} - file_data missing (needs backfill)")
                failed += 1
            else:
                print(f"   ❌ {filename} - status {r.status_code}")
                failed += 1
        except Exception as e:
            print(f"   ❌ {filename} - error: {e}")
            failed += 1
        
        time.sleep(0.3)
    
    print(f"\n   Results: {passed} passed, {failed} failed\n")
    
    if failed > 0:
        print("⚠️  Some PDFs missing file_data - run backfill script:")
        print("   python backfill_pdf_standalone.py\n")
else:
    print("3️⃣  No PDFs found to test\n")

time.sleep(0.5)

# Test 4: Invalid doc_id
print("4️⃣  Testing error handling...")
try:
    r = requests.get(f"{BASE_URL}/api/docs/00000000-0000-0000-0000-000000000000/file", timeout=3)
    if r.status_code == 404:
        print("✅ Correctly returns 404 for invalid doc_id\n")
    else:
        print(f"⚠️  Expected 404, got {r.status_code}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

time.sleep(0.5)

# Test 5: Upload new PDF
print("5️⃣  Testing PDF upload with file_data storage...")
try:
    # Create a minimal test PDF
    test_pdf = b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Count 1/Kids[3 0 R]>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n210\n%%EOF'
    
    files = {'file': ('test_upload.pdf', test_pdf, 'application/pdf')}
    r = requests.post(f"{BASE_URL}/api/docs/upload", files=files, timeout=10)
    
    if r.status_code == 200:
        data = r.json()
        new_doc_id = data.get('doc_id')
        print(f"✅ PDF uploaded: {new_doc_id}")
        
        # Try to retrieve it
        time.sleep(1)
        r2 = requests.get(f"{BASE_URL}/api/docs/{new_doc_id}/file", timeout=5)
        
        if r2.status_code == 200 and r2.content[:4] == b'%PDF':
            print(f"✅ PDF retrieved successfully ({len(r2.content)} bytes)\n")
        else:
            print(f"❌ Failed to retrieve uploaded PDF: {r2.status_code}\n")
    else:
        print(f"❌ Upload failed: {r.status_code} - {r.text}\n")
except Exception as e:
    print(f"❌ Error uploading PDF: {e}\n")

# Summary
print("="*60)
print("TEST COMPLETE")
print("="*60)
print("\n✨ Frontend test: Open chat page and click preview icon on any PDF")
print("   Should show PDF in native format with browser controls\n")
