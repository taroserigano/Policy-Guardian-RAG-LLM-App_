#!/usr/bin/env python
"""Test script for image upload API"""
import requests
from pathlib import Path
import io
from PIL import Image

BASE_URL = "http://localhost:8001"

def create_test_image(color='red'):
    """Create a simple test image in memory"""
    img = Image.new('RGB', (100, 100), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def test_image_upload():
    """Test the image upload endpoint"""
    print("Testing image upload API...")
    
    # Test without AI description
    print("\n1. Testing upload without AI description...")
    image_buffer = create_test_image('blue')  # Use different color for unique hash
    files = {'file': ('test_image_blue.png', image_buffer, 'image/png')}
    data = {
        'generate_description': 'false',
        'vision_provider': 'ollama'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/images/upload",
            files=files,
            data=data,
            timeout=60
        )
        print(f"   Status: {response.status_code}")
        if response.ok:
            result = response.json()
            print(f"   Image ID: {result.get('image_id')}")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Description: {result.get('description', 'None')}")
            print("   ✓ Upload without AI description: SUCCESS")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test with AI description
    print("\n2. Testing upload with AI description (ollama/llava)...")
    image_buffer = create_test_image('green')  # Use different color for unique hash
    files = {'file': ('test_image_green.png', image_buffer, 'image/png')}
    data = {
        'generate_description': 'true',
        'vision_provider': 'ollama'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/images/upload",
            files=files,
            data=data,
            timeout=120  # Vision models can be slow
        )
        print(f"   Status: {response.status_code}")
        if response.ok:
            result = response.json()
            print(f"   Image ID: {result.get('image_id')}")
            print(f"   Filename: {result.get('filename')}")
            desc = result.get('description')
            if desc:
                print(f"   Description: {desc[:100]}...")
                print("   ✓ Upload with AI description: SUCCESS - AI generated description!")
            else:
                print("   Description: None (AI description failed)")
                print("   ⚠ Upload succeeded but AI description was not generated")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # List images
    print("\n3. Testing list images...")
    try:
        response = requests.get(f"{BASE_URL}/api/images/")
        print(f"   Status: {response.status_code}")
        if response.ok:
            images = response.json()
            print(f"   Total images: {len(images)}")
            for img in images[:5]:
                desc = img.get('description', 'No description')
                if desc:
                    desc = desc[:50] + "..." if len(desc) > 50 else desc
                else:
                    desc = "No description"
                print(f"   - {img.get('filename')}: {desc}")
            print("   ✓ List images: SUCCESS")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

if __name__ == "__main__":
    test_image_upload()
