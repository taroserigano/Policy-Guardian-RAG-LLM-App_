"""
Comprehensive test suite for multimodal chat functionality
Tests image + document queries with proper description usage
"""
import requests
import json
import base64
from pathlib import Path
import time

BASE_URL = "http://localhost:8001"
SAMPLE_DOCS = Path(__file__).parent / "sample_docs"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_test(test_name):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}▶ {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

def print_pass(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_fail(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_server_health():
    """Test 1: Server health check"""
    print_test("Test 1: Server Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_pass("Server is running")
            return True
        else:
            print_fail(f"Server returned status {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Cannot connect to server: {e}")
        return False

def get_available_resources():
    """Test 2: Get available documents and images"""
    print_test("Test 2: Get Available Resources")
    
    docs = []
    images = []
    
    try:
        # Get documents
        response = requests.get(f"{BASE_URL}/api/docs")
        if response.status_code == 200:
            docs = response.json()
            print_pass(f"Found {len(docs)} documents")
        else:
            print_fail(f"Failed to get documents: {response.status_code}")
        
        # Get images
        response = requests.get(f"{BASE_URL}/api/images/")
        if response.status_code == 200:
            images = response.json()
            print_pass(f"Found {len(images)} images")
        else:
            print_fail(f"Failed to get images: {response.status_code}")
        
        return docs, images
    except Exception as e:
        print_fail(f"Error getting resources: {e}")
        return [], []

def test_multimodal_query(doc_id, image_id, question, expected_keywords):
    """Test multimodal query with specific document and image"""
    print_test(f"Multimodal Query Test: {question[:60]}...")
    
    try:
        payload = {
            "user_id": "test-user-multimodal",
            "provider": "ollama",
            "question": question,
            "doc_ids": [doc_id] if doc_id else [],
            "image_ids": [image_id] if image_id else [],
            "top_k": 5
        }
        
        print_info(f"Querying with doc_id={doc_id}, image_id={image_id}")
        print_info(f"Question: {question}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print_fail(f"Request failed: {response.status_code}")
            print_fail(f"Response: {response.text}")
            return False
        
        # Collect streaming response
        full_answer = ""
        citations = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        data = json.loads(data_str)
                        if data['type'] == 'token':
                            full_answer += data['data']
                        elif data['type'] == 'citations':
                            citations = data['data']
                    except json.JSONDecodeError:
                        pass
        
        print_info(f"\n{Colors.CYAN}Response ({len(full_answer)} chars):{Colors.END}")
        print(f"{full_answer[:500]}...")
        
        # Check if expected keywords are in response
        keywords_found = []
        keywords_missing = []
        
        for keyword in expected_keywords:
            if keyword.lower() in full_answer.lower():
                keywords_found.append(keyword)
            else:
                keywords_missing.append(keyword)
        
        if keywords_missing:
            print_warning(f"Missing expected keywords: {keywords_missing}")
        
        if keywords_found:
            print_pass(f"Found keywords: {keywords_found}")
        
        if citations:
            print_pass(f"Got {len(citations)} citations")
        
        # Success if we got a response with some expected content
        success = len(full_answer) > 50 and len(keywords_found) >= len(expected_keywords) // 2
        
        if success:
            print_pass("Multimodal query successful")
        else:
            print_fail("Response quality insufficient")
        
        return success
        
    except Exception as e:
        print_fail(f"Error in multimodal query: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_image_description_usage():
    """Test 3: Verify LLM uses image descriptions properly"""
    print_test("Test 3: Image Description Usage Test")
    
    # Get images with descriptions
    try:
        response = requests.get(f"{BASE_URL}/api/images/")
        images = response.json()
        
        # Find image with detailed description
        test_image = None
        for img in images:
            if img.get('description') and len(img['description']) > 100:
                test_image = img
                break
        
        if not test_image:
            print_warning("No images with detailed descriptions found")
            return False
        
        print_info(f"Testing with image: {test_image['filename']}")
        print_info(f"Description preview: {test_image['description'][:100]}...")
        
        # Ask a question that requires using the description
        question = "Describe what you see in the image in detail, including colors and clothing items."
        
        payload = {
            "user_id": "test-user-desc",
            "provider": "ollama",
            "question": question,
            "image_ids": [test_image['id']],
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            timeout=60
        )
        
        full_answer = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        data = json.loads(data_str)
                        if data['type'] == 'token':
                            full_answer += data['data']
                    except:
                        pass
        
        print_info(f"Response: {full_answer[:300]}...")
        
        # Check if response contains details from description
        desc_words = test_image['description'].lower().split()
        significant_words = [w for w in desc_words if len(w) > 5 and w not in ['wearing', 'holding', 'standing']][:10]
        
        matches = sum(1 for word in significant_words if word in full_answer.lower())
        match_rate = matches / len(significant_words) if significant_words else 0
        
        print_info(f"Description word match rate: {match_rate*100:.1f}% ({matches}/{len(significant_words)})")
        
        # Check that response doesn't say "not described" or "no description"
        bad_phrases = ["not described", "no description", "cannot see", "don't have information about the image"]
        has_bad_phrase = any(phrase in full_answer.lower() for phrase in bad_phrases)
        
        if has_bad_phrase:
            print_fail("Response incorrectly claims lack of information")
            return False
        
        if match_rate > 0.3:
            print_pass(f"LLM properly used image description ({match_rate*100:.1f}% match)")
            return True
        else:
            print_warning(f"Low description usage ({match_rate*100:.1f}% match)")
            return False
            
    except Exception as e:
        print_fail(f"Error testing description usage: {e}")
        return False

def test_compliance_check():
    """Test 4: Policy compliance check with image"""
    print_test("Test 4: Policy Compliance Check")
    
    try:
        # Get workplace compliance doc and an image
        response = requests.get(f"{BASE_URL}/api/docs")
        docs = response.json()
        
        compliance_doc = None
        for doc in docs:
            if 'compliance' in doc['filename'].lower() or 'workplace' in doc['filename'].lower():
                compliance_doc = doc
                break
        
        if not compliance_doc:
            print_warning("No compliance document found")
            return False
        
        response = requests.get(f"{BASE_URL}/api/images/")
        images = response.json()
        
        if not images:
            print_warning("No images found")
            return False
        
        test_image = images[0]
        
        print_info(f"Using document: {compliance_doc['filename']}")
        print_info(f"Using image: {test_image['filename']}")
        
        question = "Does the person's attire comply with the workplace dress code policy? Be specific about what items match or don't match the requirements."
        
        payload = {
            "user_id": "test-user-compliance",
            "provider": "ollama",
            "question": question,
            "doc_ids": [compliance_doc['id']],
            "image_ids": [test_image['id']],
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            timeout=60
        )
        
        full_answer = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        data = json.loads(data_str)
                        if data['type'] == 'token':
                            full_answer += data['data']
                    except:
                        pass
        
        print_info(f"\n{Colors.CYAN}Compliance Analysis:{Colors.END}")
        print(full_answer)
        
        # Check for specific analysis
        has_policy_reference = any(word in full_answer.lower() for word in ['policy', 'requirement', 'dress code', 'attire'])
        has_specific_items = any(word in full_answer.lower() for word in ['shirt', 'pants', 'top', 'blouse', 'skirt'])
        has_assessment = any(word in full_answer.lower() for word in ['comply', 'complies', 'compliant', 'not compliant', 'does not comply', 'appropriate', 'inappropriate'])
        
        if has_policy_reference:
            print_pass("Response references policy")
        else:
            print_fail("No policy reference in response")
            
        if has_specific_items:
            print_pass("Response mentions specific clothing items")
        else:
            print_fail("No specific clothing items mentioned")
            
        if has_assessment:
            print_pass("Response provides compliance assessment")
        else:
            print_fail("No compliance assessment provided")
        
        success = has_policy_reference and has_specific_items and has_assessment
        
        if success:
            print_pass("Compliance check test passed")
        else:
            print_fail("Compliance check needs improvement")
        
        return success
        
    except Exception as e:
        print_fail(f"Error in compliance check: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_image_only_query():
    """Test 5: Image-only query (no documents)"""
    print_test("Test 5: Image-Only Query")
    
    try:
        response = requests.get(f"{BASE_URL}/api/images/")
        images = response.json()
        
        if not images:
            print_warning("No images available")
            return False
        
        test_image = images[0]
        
        question = "What is happening in this image? Describe the scene, clothing, and environment."
        
        payload = {
            "user_id": "test-user-image-only",
            "provider": "ollama",
            "question": question,
            "image_ids": [test_image['id']],
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            timeout=60
        )
        
        full_answer = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        data = json.loads(data_str)
                        if data['type'] == 'token':
                            full_answer += data['data']
                    except:
                        pass
        
        print_info(f"Response: {full_answer[:300]}...")
        
        if len(full_answer) > 50:
            print_pass("Got detailed image-only response")
            return True
        else:
            print_fail("Response too short")
            return False
            
    except Exception as e:
        print_fail(f"Error in image-only query: {e}")
        return False

def test_multiple_images():
    """Test 6: Query with multiple images"""
    print_test("Test 6: Multiple Images Query")
    
    try:
        response = requests.get(f"{BASE_URL}/api/images/")
        images = response.json()
        
        if len(images) < 2:
            print_warning("Need at least 2 images for this test")
            return False
        
        image_ids = [img['id'] for img in images[:2]]
        
        question = "Compare and contrast these images. What are the similarities and differences?"
        
        payload = {
            "user_id": "test-user-multi-image",
            "provider": "ollama",
            "question": question,
            "image_ids": image_ids,
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            timeout=60
        )
        
        full_answer = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        data = json.loads(data_str)
                        if data['type'] == 'token':
                            full_answer += data['data']
                    except:
                        pass
        
        # Check if response mentions both images
        mentions_comparison = any(word in full_answer.lower() for word in ['both', 'comparison', 'similar', 'different', 'contrast'])
        
        if mentions_comparison and len(full_answer) > 100:
            print_pass("Successfully compared multiple images")
            print_info(f"Response: {full_answer[:200]}...")
            return True
        else:
            print_warning("Response may not properly address multiple images")
            return False
            
    except Exception as e:
        print_fail(f"Error in multiple images test: {e}")
        return False

def main():
    """Run all multimodal tests"""
    print("\n" + "="*70)
    print(f"{Colors.CYAN}MULTIMODAL CHAT - COMPREHENSIVE TEST SUITE{Colors.END}")
    print("="*70)
    
    results = {}
    
    # Test 1: Server health
    results['server_health'] = test_server_health()
    if not results['server_health']:
        print_fail("\n❌ Server not running. Aborting tests.")
        return
    
    time.sleep(1)
    
    # Test 2: Get resources
    docs, images = get_available_resources()
    if not docs or not images:
        print_fail("\n❌ Need both documents and images. Please upload test data.")
        return
    
    time.sleep(1)
    
    # Test 3: Description usage
    results['description_usage'] = test_image_description_usage()
    time.sleep(2)
    
    # Test 4: Compliance check
    results['compliance_check'] = test_compliance_check()
    time.sleep(2)
    
    # Test 5: Image-only query
    results['image_only'] = test_image_only_query()
    time.sleep(2)
    
    # Test 6: Multiple images
    results['multiple_images'] = test_multiple_images()
    
    # Summary
    print("\n" + "="*70)
    print(f"{Colors.CYAN}TEST SUMMARY{Colors.END}")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed_test else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name:25s}: {status}")
    
    print("="*70)
    percentage = (passed/total*100) if total > 0 else 0
    print(f"Results: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if passed == total:
        print(f"{Colors.GREEN}✅ ALL TESTS PASSED - Multimodal feature is working!{Colors.END}")
    elif passed >= total * 0.7:
        print(f"{Colors.YELLOW}⚠️  Most tests passed - some improvements needed{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Many tests failed - needs fixes{Colors.END}")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
