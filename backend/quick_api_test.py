#!/usr/bin/env python
"""Quick API test for image upload"""
import requests
import io
from PIL import Image

BASE_URL = "http://localhost:8001"

# Create simple test image
print("Creating test image...")
img = Image.new('RGB', (100, 100), color='yellow')
buffer = io.BytesIO()
img.save(buffer, format='PNG')
buffer.seek(0)

# Test without AI description first (faster)
print("\nTesting upload WITHOUT AI description...")
files = {'file': ('test_yellow.png', buffer, 'image/png')}
data = {
    'generate_description': 'false',
    'vision_provider': 'ollama'
}

try:
    response = requests.post(
        f"{BASE_URL}/api/images/upload",
        files=files,
        data=data,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Image ID: {result.get('image_id') or result.get('id')}")
        print(f"Filename: {result.get('filename')}")
        print(f"Description: {result.get('description')}")
        print("SUCCESS!")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

# Now test WITH AI description 
print("\n\nTesting upload WITH AI description (may take ~60 seconds)...")
img2 = Image.new('RGB', (100, 100), color='cyan')
buffer2 = io.BytesIO()
img2.save(buffer2, format='PNG')
buffer2.seek(0)

files2 = {'file': ('test_cyan.png', buffer2, 'image/png')}
data2 = {
    'generate_description': 'true',
    'vision_provider': 'ollama'
}

try:
    response = requests.post(
        f"{BASE_URL}/api/images/upload",
        files=files2,
        data=data2,
        timeout=120  # 2 minute timeout for AI
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Image ID: {result.get('image_id') or result.get('id')}")
        print(f"Filename: {result.get('filename')}")
        print(f"Description: {result.get('description')}")
        print("SUCCESS!")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
