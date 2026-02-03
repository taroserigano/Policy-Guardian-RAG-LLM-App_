"""
Quick test script to verify the baggage damage endpoint is working
"""
import requests
import json
from pathlib import Path

# Test endpoint exists
url = "http://localhost:8001/api/compliance/baggage/damage-refund/check"

print("Testing baggage damage endpoint...")
print(f"URL: {url}\n")

# Test 1: Check if endpoint exists (should return 422 for missing file)
print("Test 1: Checking if endpoint is registered...")
response = requests.post(url)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}\n")

if response.status_code == 404:
    print("❌ ERROR: Endpoint not found!")
    print("The route is not registered. Backend needs to be restarted.")
elif response.status_code == 422:
    print("✅ SUCCESS: Endpoint exists (422 = validation error, expected without file)")
else:
    print(f"⚠️  Unexpected status: {response.status_code}")

# Test 2: Check OpenAPI spec
print("\nTest 2: Checking OpenAPI spec...")
spec_response = requests.get("http://localhost:8001/openapi.json")
if spec_response.ok:
    spec = spec_response.json()
    if "/api/compliance/baggage/damage-refund/check" in spec.get("paths", {}):
        print("✅ Endpoint found in OpenAPI spec")
    else:
        print("❌ Endpoint NOT in OpenAPI spec")
        print("\nAvailable compliance endpoints:")
        for path in spec.get("paths", {}).keys():
            if "compliance" in path:
                print(f"  - {path}")
else:
    print("❌ Could not fetch OpenAPI spec")

print("\nDone!")
